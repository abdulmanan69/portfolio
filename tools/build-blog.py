#!/usr/bin/env python3
"""
Static blog builder for abdulmanan.tech.

Reads every post in posts/*.md and regenerates the crawlable side of the blog:

    blog/<slug>/index.html   one static page per post (meta, JSON-LD, share, related)
    blog/index.html          the blog hub
    feed.xml                 RSS 2.0
    sitemap.xml              every page + image entries

The site itself renders posts client-side from GitHub, so this exists purely so
Google, Bing and social crawlers get real HTML instead of an empty shell.

    python tools/build-blog.py

No dependencies. Re-runnable: it rewrites its own output and touches nothing else.
"""

import html
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://abdulmanan.tech"
AUTHOR = "Abdul Manan"
SAME_AS = [
    "https://github.com/abdulmanan69",
    "https://www.linkedin.com/in/abdulxmanan",
    "https://www.instagram.com/abdul_x_manan",
]
STATIC_PAGES = [
    ("/", "weekly", "1.0", "og-image.png"),
    ("/blog/", "weekly", "0.9", None),
]
WPM = 200

# ----------------------------------------------------------------- front matter


def parse_post(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if not m:
        raise SystemExit("%s has no front matter" % path)
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    body = m.group(2).strip()
    slug = os.path.splitext(os.path.basename(path))[0]
    words = len(re.sub(r"[#>*`_\[\]()-]", " ", body).split())
    return {
        "slug": slug,
        "title": meta.get("title", slug),
        "date": meta.get("date", ""),
        "excerpt": meta.get("excerpt", ""),
        "cover": meta.get("cover", ""),
        "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
        "body": body,
        "words": words,
        "minutes": max(1, round(words / WPM)),
        "url": "%s/blog/%s/" % (SITE, slug),
        "path": "/blog/%s/" % slug,
    }


# ----------------------------------------------------------------- markdown


def inline(text):
    """Inline markdown -> HTML. Code spans are protected from the other rules."""
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
                  r'<img loading="lazy" alt="\1" src="\2">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    for i, code in enumerate(spans):
        text = text.replace("\x00%d\x00" % i,
                            "<code>%s</code>" % html.escape(code, quote=False))
    return text


def markdown(md):
    """A small block-level renderer: headings, lists, code, quotes, tables."""
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):                               # fenced code
            lang, i, buf = line[3:].strip(), i + 1, []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="language-%s"' % lang if lang else ""
            out.append("<pre><code%s>%s</code></pre>"
                       % (cls, html.escape("\n".join(buf), quote=False)))
            continue

        if re.match(r"^#{1,4} ", line):                          # heading
            level = len(line) - len(line.lstrip("#"))
            out.append("<h%d>%s</h%d>" % (level, inline(line[level:].strip()), level))
            i += 1
            continue

        if re.match(r"^(---|\*\*\*)\s*$", line):                 # rule
            out.append("<hr>")
            i += 1
            continue

        if line.startswith("|") and i + 1 < len(lines) and re.match(
                r"^\|[\s:|-]+\|$", lines[i + 1].strip()):        # table
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = "".join("<th>%s</th>" % inline(c) for c in head)
            tbody = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r)
                for r in rows)
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                       % (thead, tbody))
            continue

        if re.match(r"^\s*[-*] ", line) or re.match(r"^\s*\d+\. ", line):  # list
            ordered = bool(re.match(r"^\s*\d+\. ", line))
            items = []
            while i < len(lines):
                m = re.match(r"^\s*(?:[-*]|\d+\.) (.*)$", lines[i])
                if m:
                    items.append(m.group(1).strip())
                    i += 1
                elif lines[i].strip() and items and not lines[i].startswith(
                        ("#", "```", ">", "|")):
                    items[-1] += " " + lines[i].strip()          # wrapped line
                    i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>"
                       % (tag, "".join("<li>%s</li>" % inline(t) for t in items), tag))
            continue

        if line.startswith(">"):                                 # blockquote
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(buf)))
            continue

        if not line.strip():
            i += 1
            continue

        buf = []                                                 # paragraph
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(
                ("#", "```", ">", "|", "- ", "* ")) and not re.match(r"^\d+\. ", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out)


# ----------------------------------------------------------------- helpers


def e(s):
    return html.escape(s or "", quote=True)


def abs_url(p):
    return p if p.startswith("http") else "%s/%s" % (SITE, p.lstrip("/"))


def rfc822(date):
    d = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return d.strftime("%a, %d %b %Y 00:00:00 GMT")


def related_for(post, posts):
    """Three posts that share the most tags; newest first inside each group."""
    others = [p for p in posts if p["slug"] != post["slug"]]
    others.sort(key=lambda p: (len(set(p["tags"]) & set(post["tags"])), p["date"]),
                reverse=True)
    return others[:3]


HEAD = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{desc}" />
<meta name="author" content="{author}" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<link rel="canonical" href="{url}" />
<meta name="theme-color" content="#faf8f5" />
<meta property="og:type" content="{ogtype}" />
<meta property="og:site_name" content="{author}" />
<meta property="og:locale" content="en_US" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{image}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="675" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{image}" />
<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="alternate" type="application/rss+xml" title="{author} - Blog" href="/feed.xml" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300..700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/style.css" />
{ld}
</head>
<body>
<header class="post-topbar">
  <a href="/" class="nav__logo">AM<span>.</span></a>
  <a href="/#blog" data-hover>All posts</a>
</header>
"""

PAGE_CSS = """<style>
.post-topbar{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;
padding:16px clamp(20px,6vw,40px);background:color-mix(in srgb,var(--paper) 85%,transparent);
backdrop-filter:blur(12px);border-bottom:1px solid var(--line);font-weight:600}
.post-topbar a[data-hover]{color:var(--ink-soft)}
.post-topbar a[data-hover]:hover{color:var(--accent)}
.post-hero-img{border-radius:var(--radius);border:1px solid var(--line);margin:0 0 34px;width:100%}
.hub{max-width:1100px;margin:0 auto;padding:60px clamp(20px,5vw,64px) 100px}
.hub h1{font-family:"Fraunces",serif;font-weight:500;font-size:clamp(2.2rem,6vw,3.4rem);letter-spacing:-.02em;margin-bottom:10px}
.hub__sub{color:var(--ink-soft);margin-bottom:44px}
.share{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:34px 0;padding:18px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.share span{font-weight:600;margin-right:4px}
.share a,.share button{font:inherit;font-size:.88rem;font-weight:600;cursor:pointer;border:1px solid var(--line);
background:var(--card);color:var(--ink);border-radius:100px;padding:8px 16px;transition:.25s}
.share a:hover,.share button:hover{border-color:var(--accent);color:var(--accent)}
.related{margin-top:70px}
.related h2{font-family:"Fraunces",serif;font-weight:500;font-size:1.7rem;margin-bottom:22px}
.related__grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,240px),1fr));gap:18px}
.related__card{border:1px solid var(--line);border-radius:var(--radius);background:var(--card);padding:22px;transition:.3s}
.related__card:hover{box-shadow:var(--shadow);border-color:transparent;transform:translateY(-4px)}
.related__card span{font-family:"JetBrains Mono",monospace;font-size:.72rem;color:var(--accent)}
.related__card h3{font-family:"Fraunces",serif;font-weight:500;font-size:1.15rem;margin-top:6px}
.prevnext{display:flex;justify-content:space-between;gap:16px;margin-top:40px;font-weight:600}
.prevnext a{color:var(--accent)}
.reader__body table{width:100%;border-collapse:collapse;margin:22px 0;font-size:.95rem}
.reader__body th,.reader__body td{border:1px solid var(--line);padding:10px 12px;text-align:left}
.reader__body th{background:var(--paper-2);font-weight:600}
</style>
</body>
</html>"""

FOOTER = """<footer class="footer">
  <span>(c) 2026 Abdul Manan</span>
  <span>Built &amp; designed by Abdul Manan - abdulmanan.tech</span>
  <a href="/" data-hover>Home</a>
</footer>
"""


def share_block(post):
    t, u = quote(post["title"]), quote(post["url"], safe="")
    return (
        '<div class="share"><span>Share:</span>\n'
        '<a href="https://twitter.com/intent/tweet?text=%s&url=%s" target="_blank" rel="noopener">X</a>\n'
        '<a href="https://www.linkedin.com/sharing/share-offsite/?url=%s" target="_blank" rel="noopener">LinkedIn</a>\n'
        '<a href="https://api.whatsapp.com/send?text=%s%%20%s" target="_blank" rel="noopener">WhatsApp</a>\n'
        '<a href="https://www.facebook.com/sharer/sharer.php?u=%s" target="_blank" rel="noopener">Facebook</a>\n'
        '<button type="button" onclick="navigator.clipboard.writeText(\'%s\');this.textContent=\'Copied!\'">Copy link</button></div>'
        % (t, u, u, t, u, u, post["url"]))


def build_post(post, posts, idx):
    prev = posts[idx - 1] if idx > 0 else None                   # newer
    nxt = posts[idx + 1] if idx + 1 < len(posts) else None       # older
    image = abs_url(post["cover"]) if post["cover"] else "%s/og-image.png" % SITE
    title = "%s - %s" % (post["title"], AUTHOR)

    blogposting = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": post["title"], "description": post["excerpt"], "image": image,
        "wordCount": post["words"],
        "author": {"@type": "Person", "name": AUTHOR, "url": SITE, "sameAs": SAME_AS},
        "publisher": {"@type": "Person", "name": AUTHOR, "url": SITE},
        "datePublished": post["date"], "dateModified": post["date"],
        "keywords": ", ".join(post["tags"]),
        "mainEntityOfPage": post["url"], "url": post["url"],
    }
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": post["title"], "item": post["url"]},
        ],
    }
    ld = "\n".join('<script type="application/ld+json">%s</script>' % json.dumps(x)
                   for x in (blogposting, crumbs))

    parts = [HEAD.format(title=e(title), desc=e(post["excerpt"]), author=AUTHOR,
                         url=post["url"], ogtype="article", image=e(image), ld=ld)]
    parts.append('<main class="reader__body">')
    parts.append('<nav aria-label="Breadcrumb" style="font-size:.85rem;color:var(--muted);margin-bottom:22px">\n'
                 '<a href="/" style="color:var(--muted)">Home</a> / '
                 '<a href="/blog/" style="color:var(--muted)">Blog</a> / %s\n</nav>'
                 % e(post["title"]))
    parts.append("<h1>%s</h1>" % e(post["title"]))
    parts.append('<div class="reader__meta">By %s - %s - %d min read - %s</div>'
                 % (AUTHOR, post["date"], post["minutes"],
                    " ".join("#" + t for t in post["tags"])))
    if post["cover"]:
        parts.append('<img class="post-hero-img" alt="%s" src="%s">'
                     % (e(post["title"]), e(image)))
    # the H1 is already part of the page furniture, so drop a repeated one from the body
    body = re.sub(r"^#\s+.*\n", "", post["body"], count=1)
    parts.append(markdown(body))
    parts.append(share_block(post))

    nav = []
    if prev:
        nav.append('<a href="%s">&larr; %s</a>' % (prev["path"], e(prev["title"])))
    if nxt:
        nav.append('<a href="%s">%s &rarr;</a>' % (nxt["path"], e(nxt["title"])))
    if nav:
        parts.append('<nav class="prevnext">%s</nav>' % "".join(nav))

    rel = related_for(post, posts)
    if rel:
        cards = "".join(
            '<a class="related__card" href="%s"><span>%s</span><h3>%s</h3></a>'
            % (r["path"], r["date"], e(r["title"])) for r in rel)
        parts.append('<section class="related"><h2>Related posts</h2>'
                     '<div class="related__grid">%s</div></section>' % cards)

    parts.append("</main>")
    parts.append(FOOTER)
    parts.append(PAGE_CSS)

    out_dir = os.path.join(ROOT, "blog", post["slug"])
    os.makedirs(out_dir, exist_ok=True)
    write(os.path.join(out_dir, "index.html"), "\n".join(parts))


def build_hub(posts):
    desc = "Articles by Abdul Manan on web development, design, SEO and learning to code."
    ld = {"@context": "https://schema.org", "@type": "Blog",
          "name": "%s - Blog" % AUTHOR, "url": "%s/blog/" % SITE,
          "author": {"@type": "Person", "name": AUTHOR, "url": SITE},
          "blogPost": [{"@type": "BlogPosting", "headline": p["title"],
                        "url": p["url"], "datePublished": p["date"]} for p in posts]}
    parts = [HEAD.format(title="Blog - %s" % AUTHOR, desc=e(desc), author=AUTHOR,
                         url="%s/blog/" % SITE, ogtype="website",
                         image="%s/og-image.png" % SITE,
                         ld='<script type="application/ld+json">%s</script>' % json.dumps(ld))]
    parts.append('<main class="hub">')
    parts.append("<h1>Writing by %s</h1>" % AUTHOR)
    parts.append('<p class="hub__sub">Thoughts on web development, design, SEO and '
                 "learning to build for the web.</p>")
    cards = []
    for p in posts:
        cover = ('<img class="post__cover" loading="lazy" alt="%s" src="%s">'
                 % (e(p["title"]), e(abs_url(p["cover"])))) if p["cover"] else ""
        tags = "".join("<span>#%s</span>" % e(t) for t in p["tags"])
        cards.append(
            '<a class="post" href="%s">\n%s\n<div class="post__body">\n'
            '<span class="post__date">%s &middot; %d min</span>\n<h3>%s</h3>\n<p>%s</p>\n'
            '<div class="post__tags">%s</div>\n</div></a>'
            % (p["path"], cover, p["date"], p["minutes"], e(p["title"]),
               e(p["excerpt"]), tags))
    parts.append('<div class="blog__grid">%s</div>' % "".join(cards))
    parts.append("</main>")
    parts.append(FOOTER)
    parts.append(PAGE_CSS)
    write(os.path.join(ROOT, "blog", "index.html"), "\n".join(parts))


def build_feed(posts):
    items = "".join(
        "  <item>\n"
        "    <title>%s</title>\n"
        "    <link>%s</link>\n"
        "    <guid>%s</guid>\n"
        "    <pubDate>%s</pubDate>\n"
        "    <description>%s</description>\n"
        "  </item>\n" % (e(p["title"]), p["url"], p["url"],
                         rfc822(p["date"]), e(p["excerpt"]))
        for p in posts)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
           "  <title>%s - Blog</title>\n"
           "  <link>%s/blog/</link>\n"
           '  <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml" />\n'
           "  <description>Web development, design, SEO and learning to code - by %s.</description>\n"
           "  <language>en-us</language>\n"
           "  <lastBuildDate>%s</lastBuildDate>\n%s</channel>\n</rss>\n"
           % (AUTHOR, SITE, SITE, AUTHOR, rfc822(posts[0]["date"]), items))
    write(os.path.join(ROOT, "feed.xml"), xml)


def build_sitemap(posts):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = []
    for loc, freq, prio, img in STATIC_PAGES:
        image = ("    <image:image><image:loc>%s</image:loc></image:image>\n"
                 % abs_url(img)) if img else ""
        urls.append("  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n"
                    "    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n%s  </url>\n"
                    % (SITE, loc, today, freq, prio, image))
    for p in posts:
        image = ("    <image:image><image:loc>%s</image:loc></image:image>\n"
                 % abs_url(p["cover"])) if p["cover"] else ""
        urls.append("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n"
                    "    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n%s  </url>\n"
                    % (p["url"], p["date"], image))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n%s</urlset>\n'
           % "".join(urls))
    write(os.path.join(ROOT, "sitemap.xml"), xml)


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("  wrote %s" % os.path.relpath(path, ROOT).replace("\\", "/"))


def main():
    post_dir = os.path.join(ROOT, "posts")
    files = sorted(f for f in os.listdir(post_dir) if f.endswith(".md"))
    posts = [parse_post(os.path.join(post_dir, f)) for f in files]
    posts.sort(key=lambda p: p["date"], reverse=True)
    print("building %d posts" % len(posts))
    for i, p in enumerate(posts):
        build_post(p, posts, i)
    build_hub(posts)
    build_feed(posts)
    build_sitemap(posts)
    print("done")


if __name__ == "__main__":
    main()
