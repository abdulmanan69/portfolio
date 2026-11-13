"""
Project pages: one static page per repo at /projects/<slug>/, the /projects/
hub, and the project cards baked into index.html.

All of it is plain HTML in the response, so crawlers see the content without
running JavaScript.
"""

import html
import os
import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

import og
from common import (AUTHOR, GH_USER, ROOT, SITE, breadcrumbs, e, inject, page,
                    person_ref, prune, write)
from repos import featured_first

HOME_CARDS = 6

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26", "CSS": "#563d7c",
    "SCSS": "#c6538c", "Python": "#3572A5", "Java": "#b07219", "C++": "#f34b7d", "C": "#555555",
    "C#": "#178600", "PHP": "#4F5D95", "Ruby": "#701516", "Go": "#00ADD8", "Rust": "#dea584",
    "Shell": "#89e051", "Dart": "#00B4AB", "Kotlin": "#A97BFF", "Swift": "#F05138",
    "Vue": "#41b883", "Astro": "#ff5a03", "Jupyter Notebook": "#DA5B0B",
}


# ---------------------------------------------------------------- README cleanup

DROP_WITH_CONTENT = {"svg", "script", "style", "iframe", "object", "embed", "template",
                     "noscript", "form", "button", "clipboard-copy", "include-fragment"}
UNWRAP = {"article", "g-emoji", "themed-picture",
          "markdown-accessiblity-table", "markdown-accessibility-table"}
VOID = {"img", "br", "hr", "source", "input", "wbr", "col", "area"}
ALLOWED_ATTRS = {"href", "src", "alt", "title", "width", "height", "colspan", "rowspan",
                 "open", "start", "srcset", "media", "align", "id"}
HEADING = re.compile(r"^h([1-6])$")


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


class ReadmeCleaner(HTMLParser):
    """Turns GitHub's rendered README into markup that fits inside our page.

    - drops the first heading when it just repeats the project name
    - shifts heading levels so the README's top level becomes <h3>
      (the page has its own <h1> and an <h2> above the README)
    - rewrites relative links and images to absolute GitHub URLs
    - removes permalink icons, scripts and every attribute not on the allowlist
    """

    def __init__(self, repo, names):
        super().__init__(convert_charrefs=False)
        branch = repo.get("default_branch") or "main"
        self.blob = "https://github.com/%s/%s/blob/%s/" % (GH_USER, repo["name"], branch)
        self.raw = "https://raw.githubusercontent.com/%s/%s/%s/" % (GH_USER, repo["name"], branch)
        self.names = {_norm(n) for n in names}
        self.out = []            # strings, plus ("h", level, closing) heading markers
        self.skip = 0            # depth inside a dropped element
        self.in_anchor = False   # inside GitHub's <a class="anchor"> permalink
        self.heading = None      # [start index in out, level] of the open heading
        self.seen_heading = False
        self.para = None         # [start index in out, text parts] of the open <p>
        self.first_para = ""
        self.first_para_span = None

    # -- url handling

    def _url(self, value, kind):
        v = (value or "").strip()
        if not v:
            return None
        if v.startswith("#"):
            return v if v.startswith("#user-content-") else "#user-content-" + v[1:]
        if re.match(r"^(https?:|mailto:)", v, re.I):
            return v
        if re.match(r"^[a-z][a-z0-9+.-]*:", v, re.I):     # javascript:, data:, etc.
            return None
        if v.startswith("//"):
            return "https:" + v
        if v.lower().startswith("/%s/" % GH_USER.lower()):  # GitHub root-relative
            return "https://github.com" + v
        base = self.raw if kind == "src" else self.blob
        return urljoin(base, v.lstrip("/"))

    def _attrs(self, tag, attrs):
        out = []
        for k, v in attrs:
            k = k.lower()
            if k not in ALLOWED_ATTRS:
                continue
            if k == "id" and not (v or "").startswith("user-content-"):
                continue
            if k in ("href", "src"):
                v = self._url(v, k)
                if v is None:
                    continue
            if k == "srcset":
                v = ", ".join(
                    " ".join(filter(None, [self._url(p.split()[0], "src") or ""] + p.split()[1:]))
                    for p in (v or "").split(",") if p.strip())
            out.append((k, v))
        names = {k for k, _ in out}
        if tag == "img":
            if "alt" not in names:
                out.append(("alt", ""))
            out += [("loading", "lazy"), ("decoding", "async")]
        return "".join(' %s="%s"' % (k, html.escape(v or "", quote=True))
                       if v is not None else " " + k for k, v in out)

    # -- parser callbacks

    def handle_starttag(self, tag, attrs):
        if self.skip:
            if tag not in VOID:
                self.skip += 1
            return
        if tag in DROP_WITH_CONTENT:
            self.skip = 1
            return
        if tag == "a" and "anchor" in (dict(attrs).get("class") or "").split():
            # keep the id so in-page links still land, drop the icon link itself
            self.in_anchor = True
            anchor_id = dict(attrs).get("id") or ""
            if anchor_id.startswith("user-content-"):
                self.out.append('<span id="%s"></span>' % html.escape(anchor_id, quote=True))
            return
        if tag in UNWRAP or tag == "input":
            return
        m = HEADING.match(tag)
        if m:
            self.heading = [len(self.out), int(m.group(1))]
            self.out.append(("h", int(m.group(1)), False))
            return
        if tag == "p":
            self.para = [len(self.out), []]
        self.out.append("<%s%s>" % (tag, self._attrs(tag, attrs)))

    def handle_startendtag(self, tag, attrs):
        if self.skip or tag in DROP_WITH_CONTENT or tag == "input":
            return
        self.out.append("<%s%s>" % (tag, self._attrs(tag, attrs)))

    def handle_endtag(self, tag):
        if self.skip:
            if tag not in VOID:
                self.skip -= 1
            return
        if tag == "a" and self.in_anchor:
            self.in_anchor = False
            return
        if tag in UNWRAP or tag in VOID:
            return
        m = HEADING.match(tag)
        if m and self.heading:
            start, level = self.heading
            self.heading = None
            text = "".join(x for x in self.out[start + 1:] if isinstance(x, str))
            text = re.sub(r"<[^>]+>", "", text)
            if not self.seen_heading and _norm(html.unescape(text)) in self.names:
                del self.out[start:]                 # title repeats the page <h1>
            else:
                self.out.append(("h", level, True))
            self.seen_heading = True
            return
        self.out.append("</%s>" % tag)
        if tag == "p" and self.para is not None:
            start, chunks = self.para
            text = " ".join("".join(chunks).split())
            if not self.first_para and len(text) >= 40:
                self.first_para = text
                self.first_para_span = (start, len(self.out))
            self.para = None

    def handle_data(self, data):
        if self.skip or self.in_anchor:
            return
        if self.para is not None:
            self.para[1].append(html.unescape(data))
        self.out.append(html.escape(html.unescape(data), quote=False))

    def handle_entityref(self, name):
        self.handle_data("&%s;" % name)

    def handle_charref(self, name):
        self.handle_data("&#%s;" % name)

    def drop_first_para(self):
        """Remove the first paragraph (used when it repeats the page lead)."""
        if self.first_para_span:
            start, end = self.first_para_span
            self.out[start:end] = []

    def result(self):
        """Join the output. The README's top heading level becomes <h3> and no
        heading ever jumps more than one level below the previous one."""
        levels = [x[1] for x in self.out if isinstance(x, tuple)]
        shift = 3 - min(levels) if levels else 0
        parts, prev, current = [], 2, 3
        for x in self.out:
            if not isinstance(x, tuple):
                parts.append(x)
                continue
            _, level, closing = x
            if not closing:
                current = min(6, level + shift, prev + 1)
                prev = current
            parts.append("<%sh%d>" % ("/" if closing else "", current))
        return "".join(parts).strip()


def clean_readme(repo):
    """(html, first_paragraph_text) for the repo's README, or ("", "")."""
    if not repo.get("readme"):
        return "", ""
    p = ReadmeCleaner(repo, [repo["name"], repo["display_name"]])
    p.feed(repo["readme"])
    p.close()
    first = p.first_para
    if first and _norm(first) == _norm(repo["description"]):
        p.drop_first_para()                         # already shown as the page lead
    return p.result(), first


# ---------------------------------------------------------------- copy helpers

def clip(text, limit):
    """Shorten to <= limit chars on a word boundary."""
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:-–— ")
    return cut + "…"


def summary(repo):
    """One honest sentence about the repo: GitHub description, else README."""
    return repo["description"] or repo.get("excerpt", "")


def page_title(repo):
    name = repo["display_name"]
    tail = " | %s" % AUTHOR
    desc = re.split(r"(?<=[a-z0-9)])[.:;]\s|\s[—–-]\s", summary(repo))[0].strip().rstrip(".")
    if desc:
        cand = "%s: %s%s" % (name, desc, tail)
        if len(cand) <= 65:
            return cand
        room = 65 - len(name) - len(tail) - 2
        if room >= 25:
            return "%s: %s%s" % (name, clip(desc, room), tail)
    if repo.get("language"):
        return "%s, a %s project%s" % (name, repo["language"], tail)
    return "%s, a project by %s" % (name, AUTHOR)


def meta_description(repo):
    s = summary(repo)
    if s:
        return clip("%s by %s. %s" % (repo["display_name"], AUTHOR, s.rstrip(".") + "."), 160)
    lang = (" written in %s" % repo["language"]) if repo.get("language") else ""
    return "%s is an open-source project by %s%s. Source code and README on GitHub." % (
        repo["display_name"], AUTHOR, lang)


def nice_date(iso):
    d = datetime.strptime(iso[:10], "%Y-%m-%d")
    return "%d %s %d" % (d.day, d.strftime("%b"), d.year)


# ---------------------------------------------------------------- markup pieces

def card(repo, reveal=False):
    lang = repo.get("language")
    lang_html = ('<span class="project__lang"><span class="project__dot" style="background:%s">'
                 '</span>%s</span>' % (LANG_COLORS.get(lang, "var(--accent)"), e(lang))) if lang else ""
    badge = '<span class="project__badge">Featured</span>' if repo["featured"] else "<span></span>"
    text = summary(repo) or "Source code and README on GitHub."
    return """<a class="project%s" href="/projects/%s/">
  <div class="project__top">%s%s</div>
  <h3>%s</h3>
  <p>%s</p>
  <div class="project__meta"><span aria-label="%d stars">&#9733; %d</span><span>Updated %s</span></div>
</a>""" % (" reveal" if reveal else "", repo["slug"], badge, lang_html, e(repo["display_name"]),
           e(clip(text, 150)), repo["stargazers_count"], repo["stargazers_count"],
           nice_date(repo["pushed_at"]))


def related_posts(repo, posts):
    pat = re.compile(r"github\.com/%s/%s(?![A-Za-z0-9_-])" % (re.escape(GH_USER), re.escape(repo["name"])), re.I)
    return [p for p in posts if pat.search(p["body"])]


def more_projects(repo, repos, n=3):
    topics = set(repo.get("topics") or [])

    def score(r):
        return (len(topics & set(r.get("topics") or [])) + (r.get("language") == repo.get("language")),
                r["featured"], r["pushed_at"])
    others = [r for r in repos if r["slug"] != repo["slug"]]
    return sorted(others, key=score, reverse=True)[:n]


def build_project(repo, repos, posts):
    name = repo["display_name"]
    facts = []
    if repo.get("language"):
        facts.append(("Language", e(repo["language"])))
    if repo.get("topics"):
        facts.append(("Topics", '<span class="project-tags">%s</span>'
                      % "".join("<span>%s</span>" % e(t) for t in repo["topics"])))
    facts.append(("Stars", str(repo["stargazers_count"])))
    facts.append(("Last updated", '<time datetime="%s">%s</time>'
                  % (repo["pushed_at"][:10], nice_date(repo["pushed_at"]))))
    if repo.get("license") and repo["license"].get("spdx_id") not in (None, "NOASSERTION"):
        facts.append(("License", e(repo["license"]["spdx_id"])))

    links = ['<a class="btn btn--solid" href="%s" rel="noopener">View source on GitHub</a>'
             % e(repo["html_url"])]
    if repo["demo"]:
        links.append('<a class="btn btn--ghost" href="%s" rel="noopener">Live demo</a>' % e(repo["demo"]))

    parts = [
        '<main class="reader__body project-page">',
        '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / '
        '<a href="/projects/">Projects</a> / <span aria-current="page">%s</span></nav>' % e(name),
        "<h1>%s</h1>" % e(name),
    ]
    if summary(repo):
        parts.append('<p class="project-page__lead">%s</p>' % e(summary(repo)))
    parts.append('<dl class="project-facts">%s</dl>' % "".join(
        "<div><dt>%s</dt><dd>%s</dd></div>" % f for f in facts))
    parts.append('<div class="project-links">%s</div>' % "".join(links))

    writing = related_posts(repo, posts)
    if writing:
        parts.append('<aside class="project-writing"><h2>Write-up</h2><ul>%s</ul></aside>' % "".join(
            '<li><a href="%s">%s</a></li>' % (p["path"], e(p["title"])) for p in writing))

    if repo["readme_html"]:
        parts.append('<section class="readme" aria-labelledby="readme-h">'
                     '<h2 id="readme-h">From the README</h2>\n%s\n</section>' % repo["readme_html"])
    else:
        parts.append('<p class="project-page__note">This repository has no README yet. '
                     'The code is on <a href="%s">GitHub</a>.</p>' % e(repo["html_url"]))

    more = more_projects(repo, repos)
    if more:
        parts.append('<section class="related"><h2>More projects</h2>'
                     '<div class="related__grid">%s</div></section>' % "".join(
                         '<a class="related__card" href="/projects/%s/"><span>%s</span><h3>%s</h3></a>'
                         % (r["slug"], e(r.get("language") or "Project"), e(r["display_name"]))
                         for r in more))
    parts.append("</main>")

    path = "/projects/%s/" % repo["slug"]
    label = "Project · %s" % repo["language"] if repo.get("language") else "Project"
    image = og.card("og/projects/%s.png" % repo["slug"], label, name, summary(repo))
    code = {
        "@context": "https://schema.org", "@type": "SoftwareSourceCode",
        "@id": SITE + path + "#code",
        "name": name,
        "description": summary(repo) or meta_description(repo),
        "url": SITE + path,
        "mainEntityOfPage": SITE + path,
        "codeRepository": repo["html_url"],
        "author": person_ref(),
        "dateCreated": repo["created_at"][:10],
        "dateModified": repo["pushed_at"][:10],
        "image": SITE + image[0],
    }
    if repo.get("language"):
        code["programmingLanguage"] = repo["language"]
    if repo.get("topics"):
        code["keywords"] = ", ".join(repo["topics"])
    spdx = (repo.get("license") or {}).get("spdx_id")
    if spdx and spdx != "NOASSERTION":
        code["license"] = "https://spdx.org/licenses/%s.html" % spdx

    doc = page(title=page_title(repo), desc=meta_description(repo), path=path,
               body="\n".join(parts), image=image,
               image_alt="%s, a project by %s" % (name, AUTHOR),
               ld=(code, breadcrumbs(("Projects", "/projects/"), (name, path))))
    write(os.path.join(ROOT, "projects", repo["slug"], "index.html"), doc)


def build_hub(repos):
    ordered = featured_first(repos)
    featured = [r for r in ordered if r["featured"]]
    rest = [r for r in ordered if not r["featured"]]
    parts = ['<main class="hub">',
             "<h1>Projects by %s</h1>" % AUTHOR,
             '<p class="hub__sub">Public repositories from my GitHub, each with its README. '
             'Sorted by stars, then most recent activity.</p>']
    if featured:
        parts.append('<h2 class="hub__h2">Featured</h2><div class="projects__grid">%s</div>'
                     % "".join(card(r) for r in featured))
    parts.append('<h2 class="hub__h2">%s (%d)</h2><div class="projects__grid">%s</div>'
                 % ("More projects" if featured else "All projects", len(rest),
                    "".join(card(r) for r in rest)))
    parts.append('<p class="hub__more"><a class="link-underline" '
                 'href="https://github.com/%s?tab=repositories">Everything else is on GitHub</a></p>'
                 % GH_USER)
    parts.append("</main>")
    title = "Projects by %s: Open-Source Code and Apps" % AUTHOR
    image = og.card("og/projects.png", "Projects", title.split(":")[0],
                    "Open-source code, READMEs and live demos from my GitHub.")
    collection = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "@id": SITE + "/projects/#page", "name": title, "url": SITE + "/projects/",
        "author": person_ref(),
        "mainEntity": {"@type": "ItemList", "numberOfItems": len(ordered),
                       "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                            "url": "%s/projects/%s/" % (SITE, r["slug"]),
                                            "name": r["display_name"]}
                                           for i, r in enumerate(ordered)]},
    }
    doc = page(title=title,
               desc="Open-source projects by %s on GitHub, each with its language, topics, "
                    "README and links to the code and live demos." % AUTHOR,
               path="/projects/", body="\n".join(parts), image=image,
               ld=(collection, breadcrumbs(("Projects", "/projects/"))))
    write(os.path.join(ROOT, "projects", "index.html"), doc)


def inject_home(repos):
    """Bake the top project cards into index.html between the build markers."""
    top = featured_first(repos)[:HOME_CARDS]
    inject("index.html", "projects", "\n".join(card(r, reveal=True) for r in top))
    inject("index.html", "projects-count", "All %d projects &rarr;" % len(repos), inline=True)


def build(repos, posts):
    """Write every project page and the hub; return sitemap entries."""
    for r in repos:
        r["readme_html"], r["excerpt"] = clean_readme(r)
    prune("projects", {r["slug"] for r in repos})
    og.prune("projects", {r["slug"] for r in repos})
    for r in repos:
        build_project(r, repos, posts)
    build_hub(repos)
    inject_home(repos)
    latest = max(r["pushed_at"][:10] for r in repos)
    return ([("/projects/", latest, None)] +
            [("/projects/%s/" % r["slug"], r["pushed_at"][:10], None) for r in repos])
