"""
Blog: reads posts/*.md and writes blog/<slug>/index.html, tag pages at
blog/tags/<tag>/, the blog hub, the homepage post cards and feed.xml.

Front matter keys: title, date, excerpt, cover, tags, plus optional
`updated: YYYY-MM-DD` (last content change) and `noindex: true` (keep the
post on the site but out of search results and the sitemap).
"""

import os
import re
from datetime import datetime, timezone
from urllib.parse import quote

import og
from common import (AUTHOR, GH_USER, INDEX, NOINDEX, ROOT, SITE, BuildError, abs_url,
                    breadcrumbs, e, inject, page, person_ref, prune, write)
from md import markdown

WPM = 200
TAG_INDEX_MIN = 3   # a tag page is indexable once this many indexable posts share it
BLOG_ID = SITE + "/blog/#blog"


def tag_slug(tag):
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")


def parse_post(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
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
    for key in ("date", "updated"):
        if (key == "date" or meta.get(key)) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta.get(key, "")):
            raise BuildError("%s: '%s' must be YYYY-MM-DD, got %r" % (path, key, meta.get(key)))
    words = len(re.sub(r"[#>*`_\[\]()-]", " ", body).split())
    return {
        "slug": slug,
        "title": meta.get("title", slug),
        "date": meta.get("date", ""),
        # last real content change; set "updated: YYYY-MM-DD" when you edit a post
        "updated": max(meta.get("date", ""), meta.get("updated", "")),
        "excerpt": meta.get("excerpt", ""),
        "cover": meta.get("cover", ""),
        "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
        "noindex": meta.get("noindex", "").lower() == "true",
        "body": body,
        "words": words,
        "minutes": max(1, round(words / WPM)),
        "url": "%s/blog/%s/" % (SITE, slug),
        "path": "/blog/%s/" % slug,
    }


def load_posts():
    post_dir = os.path.join(ROOT, "posts")
    files = sorted(f for f in os.listdir(post_dir) if f.endswith(".md"))
    posts = [parse_post(os.path.join(post_dir, f)) for f in files]
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def rfc822(date):
    d = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return d.strftime("%a, %d %b %Y 00:00:00 GMT")


def related_for(post, posts):
    """Three posts that share the most tags; newest first inside each group."""
    others = [p for p in posts if p["slug"] != post["slug"]]
    others.sort(key=lambda p: (len(set(p["tags"]) & set(post["tags"])), not p["noindex"],
                               p["date"]), reverse=True)
    return others[:3]


def projects_for(post, repos):
    """Repos this post links to that have a project page."""
    found = []
    for r in repos:
        pat = r"github\.com/%s/%s(?![A-Za-z0-9_-])" % (re.escape(GH_USER), re.escape(r["name"]))
        if re.search(pat, post["body"], re.I):
            found.append(r)
    return found


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


def nice_date(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return "%s %d, %d" % (d.strftime("%b"), d.day, d.year)


def tag_links(tags):
    return " ".join('<a href="/blog/tags/%s/">#%s</a>' % (tag_slug(t), e(t)) for t in tags)


def build_post(post, posts, idx, repos):
    prev = posts[idx - 1] if idx > 0 else None                   # newer
    nxt = posts[idx + 1] if idx + 1 < len(posts) else None       # older
    image = abs_url(post["cover"]) if post["cover"] else "%s/og-image.png" % SITE
    linked = projects_for(post, repos)

    article = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "@id": post["url"] + "#article",
        "headline": post["title"], "description": post["excerpt"], "image": [image],
        "inLanguage": "en", "wordCount": post["words"],
        "timeRequired": "PT%dM" % post["minutes"],
        "author": person_ref(), "publisher": person_ref(),
        "datePublished": post["date"], "dateModified": post["updated"],
        "keywords": ", ".join(post["tags"]),
        "isPartOf": {"@id": BLOG_ID},
        "mainEntityOfPage": post["url"], "url": post["url"],
    }
    if linked:
        article["about"] = [{"@id": "%s/projects/%s/#code" % (SITE, r["slug"])} for r in linked]
    crumbs = breadcrumbs(("Blog", "/blog/"), (post["title"], post["path"]))

    updated = (' &middot; updated <time datetime="%s">%s</time>'
               % (post["updated"], nice_date(post["updated"]))
               if post["updated"] != post["date"] else "")
    parts = ['<main class="reader__body">',
             '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / '
             '<a href="/blog/">Blog</a> / <span aria-current="page">%s</span></nav>' % e(post["title"]),
             "<h1>%s</h1>" % e(post["title"]),
             '<div class="reader__meta">By <a href="/">%s</a> &middot; <time datetime="%s">%s</time>%s'
             ' &middot; %d min read<div class="reader__tags">%s</div></div>'
             % (AUTHOR, post["date"], nice_date(post["date"]), updated, post["minutes"],
                tag_links(post["tags"]))]
    if post["cover"]:
        parts.append('<img class="post-hero-img" alt="%s" src="%s" width="1200" height="675">'
                     % (e(post["title"]), e(image)))
    # the H1 is already part of the page furniture, so drop a repeated one from the body
    body = re.sub(r"^#\s+.*\n", "", post["body"], count=1)
    parts.append(markdown(body))

    if linked:
        parts.append('<aside class="project-writing"><h2>Project page</h2><ul>%s</ul></aside>' % "".join(
            '<li><a href="/projects/%s/">%s</a></li>' % (r["slug"], e(r["display_name"])) for r in linked))

    parts.append(share_block(post))

    nav = []
    if prev:
        nav.append('<a href="%s" rel="prev">&larr; %s</a>' % (prev["path"], e(prev["title"])))
    if nxt:
        nav.append('<a href="%s" rel="next">%s &rarr;</a>' % (nxt["path"], e(nxt["title"])))
    if nav:
        parts.append('<nav class="prevnext" aria-label="More posts">%s</nav>' % "".join(nav))

    rel = related_for(post, posts)
    if rel:
        cards = "".join(
            '<a class="related__card" href="%s"><span>%s</span><h3>%s</h3></a>'
            % (r["path"], r["date"], e(r["title"])) for r in rel)
        parts.append('<section class="related"><h2>Related posts</h2>'
                     '<div class="related__grid">%s</div></section>' % cards)
    parts.append("</main>")

    meta = [("article:published_time", post["date"]), ("article:modified_time", post["updated"]),
            ("article:author", SITE + "/")] + [("article:tag", t) for t in post["tags"]]
    doc = page(title="%s - %s" % (post["title"], AUTHOR), desc=post["excerpt"],
               path=post["path"], body="\n".join(parts), og_type="article",
               image=(image, 1200, 675) if post["cover"] else None,
               image_alt="Cover: %s" % post["title"], ld=(article, crumbs),
               robots=NOINDEX if post["noindex"] else INDEX, meta=meta)
    write(os.path.join(ROOT, "blog", post["slug"], "index.html"), doc)


def card(p, heading, reveal=False):
    """Post card for the blog hub and tag pages (heading h2) and the homepage (h3)."""
    cover = ('<img class="post__cover" loading="lazy" decoding="async" alt="" src="/%s" '
             'width="1200" height="675">' % e(p["cover"].lstrip("/"))) if p["cover"] else ""
    tags = "".join("<span>#%s</span>" % e(t) for t in p["tags"])
    return ('<a class="post%s" href="%s">\n%s\n<div class="post__body">\n'
            '<span class="post__date">%s &middot; %d min read</span>\n'
            '<%s class="post__title">%s</%s>\n<p>%s</p>\n'
            '<div class="post__tags">%s</div>\n</div></a>'
            % (" reveal" if reveal else "", p["path"], cover, p["date"], p["minutes"],
               heading, e(p["title"]), heading, e(p["excerpt"]), tags))


HOME_POSTS = 6


def inject_home(posts):
    """Latest indexable posts on the homepage; the rest are a click away on /blog/."""
    shown = [p for p in posts if not p["noindex"]][:HOME_POSTS]
    inject("index.html", "posts", "\n".join(card(p, "h3", reveal=True) for p in shown))
    inject("index.html", "posts-count", "All %d posts &rarr;" % len(posts), inline=True)


def tags_index(posts):
    """{tag: [posts]} in post order."""
    tags = {}
    for p in posts:
        for t in p["tags"]:
            tags.setdefault(t, []).append(p)
    return tags


def tag_indexable(tagged):
    return sum(not p["noindex"] for p in tagged) >= TAG_INDEX_MIN


def build_hub(posts):
    desc = "Articles by Abdul Manan on web development, design, SEO and learning to code."
    ld = {"@context": "https://schema.org", "@type": "Blog", "@id": BLOG_ID,
          "name": "%s - Blog" % AUTHOR, "url": "%s/blog/" % SITE,
          "author": person_ref(), "inLanguage": "en",
          "blogPost": [{"@type": "BlogPosting", "@id": p["url"] + "#article", "headline": p["title"],
                        "url": p["url"], "datePublished": p["date"]} for p in posts]}
    topics = sorted(((t, ps) for t, ps in tags_index(posts).items() if len(ps) >= 2),
                    key=lambda x: (-len(x[1]), x[0]))
    parts = ['<main class="hub">',
             "<h1>Writing by %s</h1>" % AUTHOR,
             '<p class="hub__sub">How my projects were built, plus notes on web development, '
             "design and SEO.</p>"]
    if topics:
        parts.append('<nav class="tag-list" aria-label="Topics">%s</nav>' % "".join(
            '<a href="/blog/tags/%s/">#%s <span>%d</span></a>' % (tag_slug(t), e(t), len(ps))
            for t, ps in topics))
    parts.append('<div class="blog__grid">%s</div>' % "".join(card(p, "h2") for p in posts))
    parts.append("</main>")
    image = og.card("og/blog.png", "Blog", "Writing by %s" % AUTHOR,
                    "Web development, design, SEO and the projects behind them.")
    doc = page(title="Blog - %s" % AUTHOR, desc=desc, path="/blog/", body="\n".join(parts),
               image=image, ld=(ld, breadcrumbs(("Blog", "/blog/"))))
    write(os.path.join(ROOT, "blog", "index.html"), doc)


def build_tags(posts):
    """One page per tag. Indexable only when TAG_INDEX_MIN indexable posts share it,
    so a tag with one post doesn't become a thin duplicate of that post."""
    lastmods, keep, cards_kept = {}, set(), set()
    for tag, tagged in sorted(tags_index(posts).items()):
        slug = tag_slug(tag)
        keep.add(slug)
        path = "/blog/tags/%s/" % slug
        indexable = tag_indexable(tagged)
        titles = ", ".join(p["title"].split(" — ")[0] for p in tagged[:3])
        desc = "%d post%s by %s tagged %s: %s." % (len(tagged), "" if len(tagged) == 1 else "s",
                                                   AUTHOR, tag, titles)
        image = None
        if indexable:
            image = og.card("og/tags/%s.png" % slug, "Blog · Topic", "#" + tag,
                            "%d posts by %s" % (len(tagged), AUTHOR))
            cards_kept.add(slug)
        ld = {"@context": "https://schema.org", "@type": "CollectionPage",
              "name": "Posts tagged %s" % tag, "url": SITE + path, "isPartOf": {"@id": BLOG_ID},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": p["url"]}
                  for i, p in enumerate(tagged)]}}
        body = "\n".join([
            '<main class="hub">',
            '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / '
            '<a href="/blog/">Blog</a> / <span aria-current="page">#%s</span></nav>' % e(tag),
            "<h1>Posts tagged #%s</h1>" % e(tag),
            '<p class="hub__sub">%d post%s by %s. <a class="link-underline" href="/blog/">All posts</a></p>'
            % (len(tagged), "" if len(tagged) == 1 else "s", AUTHOR),
            '<div class="blog__grid">%s</div>' % "".join(card(p, "h2") for p in tagged),
            "</main>"])
        doc = page(title="Posts tagged %s - %s" % (tag, AUTHOR), desc=desc, path=path, body=body,
                   image=image, ld=(ld, breadcrumbs(("Blog", "/blog/"), ("#" + tag, path))),
                   robots=INDEX if indexable else NOINDEX)
        write(os.path.join(ROOT, "blog", "tags", slug, "index.html"), doc)
        lastmods[path] = max(p["updated"] for p in tagged)
    prune(os.path.join("blog", "tags"), keep)
    og.prune("tags", cards_kept)
    return lastmods


def build_feed(posts):
    items = "".join(
        "  <item>\n"
        "    <title>%s</title>\n"
        "    <link>%s</link>\n"
        '    <guid isPermaLink="true">%s</guid>\n'
        "    <pubDate>%s</pubDate>\n"
        "    <dc:creator>%s</dc:creator>\n"
        "%s"
        "    <description>%s</description>\n"
        "  </item>\n" % (e(p["title"]), p["url"], p["url"], rfc822(p["date"]), AUTHOR,
                         "".join("    <category>%s</category>\n" % e(t) for t in p["tags"]),
                         e(p["excerpt"]))
        for p in posts)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" '
           'xmlns:dc="http://purl.org/dc/elements/1.1/">\n<channel>\n'
           "  <title>%s - Blog</title>\n"
           "  <link>%s/blog/</link>\n"
           '  <atom:link href="%s/feed.xml" rel="self" type="application/rss+xml" />\n'
           "  <description>How my projects were built, plus web development, design and SEO - by %s.</description>\n"
           "  <language>en-us</language>\n"
           "  <lastBuildDate>%s</lastBuildDate>\n%s</channel>\n</rss>\n"
           % (AUTHOR, SITE, SITE, AUTHOR, rfc822(max(p["updated"] for p in posts)), items))
    write(os.path.join(ROOT, "feed.xml"), xml)


def build(posts, repos):
    """Write every post page, tag pages, the hub and the feed; return lastmods."""
    prune("blog", {p["slug"] for p in posts} | {"tags"})
    for i, p in enumerate(posts):
        build_post(p, posts, i, repos)
    build_hub(posts)
    lastmods = build_tags(posts)
    build_feed(posts)
    inject_home(posts)
    lastmods["/blog/"] = max(p["updated"] for p in posts)
    lastmods.update({p["path"]: p["updated"] for p in posts})
    return lastmods
