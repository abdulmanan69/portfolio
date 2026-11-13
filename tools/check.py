"""
Post-build checks over every HTML file the site serves. Any problem stops the
build with BUILD FAILED, so a broken page never gets committed by accident.

Checked on every page:
  - a non-empty <title>, unique across the whole site
  - exactly one <h1>
  - every JSON-LD block parses and has @context and @type
Checked on every indexable page (no "noindex"):
  - a meta description, unique across the site
  - a canonical URL that matches the file's own URL
  - og:title, og:description, og:url (= canonical), og:image, twitter:card,
    twitter:title, twitter:image; an og:image on this domain must exist on disk
Checked on the homepage:
  - a Person with name, jobTitle, url and a non-empty sameAs list
"""

import json
import os
from html.parser import HTMLParser

from common import AUTHOR, ROOT, SITE, BuildError

SKIP_DIRS = {".git", ".cache", ".fonts", "node_modules", "tools", ".playwright-mcp"}
REQUIRED_SOCIAL = ("og:title", "og:description", "og:url", "og:image",
                   "twitter:card", "twitter:title", "twitter:image")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.in_title = None, False
        self.meta, self.canonical, self.ld, self.h1 = {}, None, [], 0
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


def _entities(obj):
    """Yield every dict in a JSON-LD tree."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _entities(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _entities(v)


def run():
    problems, seen_title, seen_desc, pages = [], {}, {}, 0
    for path in html_files():
        pages += 1
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        p = Page()
        with open(path, encoding="utf-8") as f:
            p.feed(f.read())

        def bad(msg):
            problems.append("%s: %s" % (rel, msg))

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

        if "noindex" in " ".join(p.meta.get("robots", [])):
            continue

        desc = " ".join((p.meta.get("description") or [""])[0].split())
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
            if not (p.meta.get(key) or [""])[0].strip():
                bad("missing %s" % key)
        if (p.meta.get("og:url") or [""])[0] != own:
            bad("og:url does not match the canonical URL")
        img = (p.meta.get("og:image") or [""])[0]
        if img.startswith(SITE + "/") and not os.path.exists(
                os.path.join(ROOT, *img[len(SITE) + 1:].split("/"))):
            bad("og:image %s does not exist" % img)

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

    if problems:
        raise BuildError("%d check(s) failed:\n  %s" % (len(problems), "\n  ".join(problems)))
    print("checks: %d pages OK (titles and descriptions unique, JSON-LD parses, "
          "canonical/OG/Twitter tags present)" % pages)
