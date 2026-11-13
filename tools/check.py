"""
Post-build checks over every HTML file the site serves. Any problem stops the
build with BUILD FAILED, so a broken page never gets committed by accident.

Every page:
  - a non-empty <title>, unique across the whole site
  - exactly one <h1>
  - every JSON-LD block parses and has @context and @type
  - no internal link points at a file that doesn't exist
Every indexable page (no "noindex"):
  - a meta description, unique across the site
  - a canonical URL that matches the file's own URL
  - og:title, og:description, og:url (= canonical), og:image, twitter:card,
    twitter:title, twitter:image; an og:image on this domain must exist on disk
  - listed in sitemap.xml, and every sitemap URL is a real indexable page
  - reachable by following plain <a href> links from the homepage, with no
    JavaScript; project pages within two clicks
The homepage: a Person with name, jobTitle, url and a non-empty sameAs list.
robots.txt: points at the sitemap and doesn't block the site.
"""

import json
import os
import re
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from common import AUTHOR, ROOT, SITE, BuildError

SKIP_DIRS = {".git", ".cache", ".fonts", "node_modules", "tools", ".playwright-mcp"}
REQUIRED_SOCIAL = ("og:title", "og:description", "og:url", "og:image",
                   "twitter:card", "twitter:title", "twitter:image")
MAX_PROJECT_DEPTH = 2


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.in_title = None, False
        self.meta, self.canonical, self.ld, self.h1 = {}, None, [], 0
        self.links = []
        self.in_ld, self.buf = False, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title, self.title = True, ""
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta.setdefault(key, []).append(a.get("content") or "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "script" and a.get("type") == "application/ld+json":
            self.in_ld, self.buf = True, []
        elif tag == "h1":
            self.h1 += 1
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "script" and self.in_ld:
            self.in_ld = False
            self.ld.append("".join(self.buf))

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_ld:
            self.buf.append(data)

    def first(self, key):
        return (self.meta.get(key) or [""])[0]

    @property
    def noindex(self):
        return "noindex" in " ".join(self.meta.get("robots", []))

    @property
    def og_image(self):
        return self.first("og:image")


def parse(path):
    p = Page()
    with open(path, encoding="utf-8") as f:
        p.feed(f.read())
    return p


def html_files():
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f.endswith(".html"):
                yield os.path.join(dirpath, f)


def url_for(path):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[:-len("index.html")]
    return SITE + "/" + rel


def file_for(url):
    """Local file a site URL is served from, or None if it isn't on this site."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or parts.netloc != urlsplit(SITE).netloc:
        return None
    path = parts.path or "/"
    if path.endswith("/"):
        path += "index.html"
    return os.path.join(ROOT, *path.lstrip("/").split("/"))


def _entities(obj):
    """Yield every dict in a JSON-LD tree."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _entities(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _entities(v)


def _page_checks(path, p, seen_title, seen_desc, bad):
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    title = " ".join((p.title or "").split())
    if not title:
        bad("missing <title>")
    elif title in seen_title:
        bad("same <title> as %s: %r" % (seen_title[title], title))
    else:
        seen_title[title] = rel
    if p.h1 != 1:
        bad("has %d <h1> elements, expected 1" % p.h1)

    blocks = []
    for raw in p.ld:
        try:
            data = json.loads(raw)
        except ValueError as err:
            bad("JSON-LD does not parse: %s" % err)
            continue
        for top in (data if isinstance(data, list) else [data]):
            if "@context" not in top or "@type" not in top:
                bad("JSON-LD block without @context/@type")
            blocks.append(top)

    if p.noindex:
        return
    desc = " ".join(p.first("description").split())
    if not desc:
        bad("missing meta description")
    elif desc in seen_desc:
        bad("same meta description as %s" % seen_desc[desc])
    else:
        seen_desc[desc] = rel
    own = url_for(path)
    if p.canonical != own:
        bad("canonical is %r, expected %r" % (p.canonical, own))
    for key in REQUIRED_SOCIAL:
        if not p.first(key).strip():
            bad("missing %s" % key)
    if p.first("og:url") != own:
        bad("og:url does not match the canonical URL")
    img_file = file_for(p.og_image)
    if img_file and not os.path.exists(img_file):
        bad("og:image %s does not exist" % p.og_image)

    if rel == "index.html":
        people = [x for b in blocks for x in _entities(b)
                  if x.get("@type") == "Person" and x.get("jobTitle")]
        if not people:
            bad("homepage has no Person with a jobTitle")
        for person in people:
            if person.get("name") != AUTHOR or not person.get("url"):
                bad("Person needs name %r and url" % AUTHOR)
            same = person.get("sameAs") or []
            if not same or not all(str(u).startswith("https://") for u in same):
                bad("Person sameAs must be a non-empty list of https URLs")


def run():
    problems, seen_title, seen_desc = [], {}, {}
    pages, graph = {}, {}

    for path in html_files():
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        p = parse(path)
        url = url_for(path)
        pages[url] = p

        def bad(msg, rel=rel):
            problems.append("%s: %s" % (rel, msg))

        _page_checks(path, p, seen_title, seen_desc, bad)

        # internal links: every target must exist; remember page-to-page edges
        graph[url] = set()
        for href in p.links:
            if re.match(r"^(mailto:|tel:|javascript:|#)", href):
                continue
            target = urljoin(url, href)
            local = file_for(target)
            if local is None:
                continue
            if not os.path.exists(local):
                bad("broken link %r" % href)
            elif local.endswith(".html"):
                graph[url].add(url_for(local))

    indexable = {u for u, p in pages.items() if not p.noindex}

    # sitemap: exactly the indexable pages
    with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as f:
        listed = re.findall(r"<loc>([^<]+)</loc>", f.read())
    if len(listed) != len(set(listed)):
        problems.append("sitemap.xml: duplicate <loc> entries")
    for u in sorted(indexable - set(listed)):
        problems.append("sitemap.xml: missing %s" % u)
    for u in sorted(set(listed) - indexable):
        problems.append("sitemap.xml: lists %s, which is not an indexable page" % u)

    # reachability from the homepage, links only, no JavaScript
    depth, queue = {SITE + "/": 0}, deque([SITE + "/"])
    while queue:
        u = queue.popleft()
        for v in graph.get(u, ()):
            if v not in depth:
                depth[v] = depth[u] + 1
                queue.append(v)
    for u in sorted(indexable - set(depth)):
        problems.append("%s: orphan, not reachable from the homepage" % u[len(SITE):])
    projects = [u for u in indexable if u.startswith(SITE + "/projects/")]
    for u in sorted(projects):
        if depth.get(u, 99) > MAX_PROJECT_DEPTH:
            problems.append("%s: %s clicks from the homepage (max %d)"
                            % (u[len(SITE):], depth.get(u, "unreachable"), MAX_PROJECT_DEPTH))

    with open(os.path.join(ROOT, "robots.txt"), encoding="utf-8") as f:
        robots = f.read()
    if "Sitemap: %s/sitemap.xml" % SITE not in robots:
        problems.append("robots.txt: no 'Sitemap: %s/sitemap.xml' line" % SITE)
    if re.search(r"^Disallow:\s*/\s*$", robots, re.M):
        problems.append("robots.txt: 'Disallow: /' blocks the whole site")

    if problems:
        raise BuildError("%d check(s) failed:\n  %s" % (len(problems), "\n  ".join(problems)))
    reach = [depth[u] for u in indexable]
    print("checks: %d pages OK; %d indexable, all in the sitemap and reachable from / "
          "(deepest %d clicks, projects <= %d)"
          % (len(pages), len(indexable), max(reach), max(depth[u] for u in projects)))
