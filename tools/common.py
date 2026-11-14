"""
Shared constants and page furniture for the static build.

Every generated page (projects, blog) goes through page() so the <head>,
top bar and footer stay identical across the site.
"""

import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://abdulmanan.tech"
AUTHOR = "Abdul Manan"
GH_USER = "abdulmanan69"
# Every profile that is you. Google uses these to tie the name to one person.
# TODO(Abdul): add your X profile URL and any others (dev.to, Stack Overflow...).
SAME_AS = [
    "https://github.com/abdulmanan69",
    "https://www.linkedin.com/in/abdulxmanan",
    "https://www.instagram.com/abdul_x_manan",
]
# Taken from the existing site copy. Change it here and rebuild.
JOB_TITLE = "Web Developer & Designer"
PERSON_ID = SITE + "/#person"
DEFAULT_IMAGE = ("/og-image.png", 1200, 630)


def person():
    """The full Person entity. Used once, on the homepage; other pages point at PERSON_ID."""
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": AUTHOR,
        "url": SITE + "/",
        "image": "https://github.com/abdulmanan69.png",
        "jobTitle": JOB_TITLE,
        "description": "Web developer and designer who builds full-stack apps and "
                       "self-hosts them.",
        "email": "mailto:manan999999999@gmail.com",
        "sameAs": SAME_AS,
        "knowsAbout": ["Web Development", "Full-Stack Development", "UI Design",
                       "JavaScript", "TypeScript", "React", "Next.js", "Node.js",
                       "Python", "Supabase", "PostgreSQL", "Docker"],
    }


def person_ref():
    """Short reference to the Person defined on the homepage."""
    return {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR, "url": SITE + "/"}


def breadcrumbs(*trail):
    """BreadcrumbList from (name, path) pairs, starting at Home."""
    items = [("Home", "/")] + list(trail)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n,
                                 "item": SITE + p} for i, (n, p) in enumerate(items)]}


def e(s):
    """Escape text for HTML content and attribute values."""
    return html.escape(s or "", quote=True)


def abs_url(p):
    return p if p.startswith("http") else "%s/%s" % (SITE, p.lstrip("/"))


class BuildError(SystemExit):
    """Stops the build with a readable message and a non-zero exit code."""

    def __init__(self, msg):
        super().__init__("\nBUILD FAILED: %s\n" % msg)


def inject(rel_path, name, content, inline=False):
    """Replace the text between <!-- build:NAME --> and <!-- /build:NAME --> in a
    hand-written file such as index.html. Everything outside the markers is kept."""
    path = os.path.join(ROOT, rel_path)
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    start, end = "<!-- build:%s -->" % name, "<!-- /build:%s -->" % name
    if text.count(start) != 1 or text.count(end) != 1:
        raise BuildError("%s needs exactly one %s ... %s pair" % (rel_path, start, end))
    sep = "" if inline else "\n"
    new = re.sub(re.escape(start) + r".*?" + re.escape(end),
                 lambda m: start + sep + content + sep + end, text, count=1, flags=re.S)
    if new != text:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print("  updated %s (%s)" % (rel_path, name))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("  wrote %s" % os.path.relpath(path, ROOT).replace("\\", "/"))


def prune(folder, keep):
    """Delete generated page folders under ROOT/folder whose slug isn't in keep.

    Only touches subfolders that hold nothing but an index.html, so a
    hand-made folder is never removed.
    """
    base = os.path.join(ROOT, folder)
    if not os.path.isdir(base):
        return
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        if name in keep or not os.path.isdir(path):
            continue
        if os.listdir(path) == ["index.html"]:
            os.remove(os.path.join(path, "index.html"))
            os.rmdir(path)
            print("  removed stale %s/%s/" % (folder, name))


def ld_script(obj):
    """A JSON-LD <script>. '</' is escaped so a string can never close the tag."""
    return ('<script type="application/ld+json">%s</script>'
            % json.dumps(obj, ensure_ascii=False).replace("</", "<\\/"))


# Runs before first paint so subpages honour the theme picked on the homepage.
THEME_SCRIPT = ("<script>try{var t=localStorage.getItem('theme')||"
                "(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');"
                "document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>")

TOPBAR = """<header class="post-topbar">
  <a href="/" class="nav__logo" aria-label="Abdul Manan, home">AM<span>.</span></a>
  <nav class="post-topbar__links" aria-label="Site">
    <a href="/projects/">Projects</a>
    <a href="/blog/">Blog</a>
  </nav>
</header>"""

FOOTER = """<footer class="footer">
  <span>Abdul Manan &copy; {year}</span>
  <span>Built and designed by Abdul Manan &middot; <a href="https://github.com/abdulmanan69">github.com/abdulmanan69</a></span>
  <a href="/">Home</a>
</footer>"""


INDEX = "index, follow, max-image-preview:large"
NOINDEX = "noindex, follow"


def page(*, title, desc, path, body, og_type="website", image=None, image_alt=None,
         ld=(), year="2026", robots=INDEX, meta=()):
    """Render a full HTML document.

    path       site-relative URL of this page, e.g. "/projects/lancall/"
    image      (url, width, height) for og:image; defaults to the site card
    image_alt  alt text for the card; defaults to the title
    ld         iterable of JSON-LD dicts
    robots     INDEX or NOINDEX (noindex pages stay out of the sitemap)
    meta       extra (property, content) pairs, e.g. article:published_time
    """
    url = SITE + path
    img_url, img_w, img_h = image or DEFAULT_IMAGE
    img_url = abs_url(img_url)
    head = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{title}</title>
<meta name="description" content="{desc}" />
<meta name="author" content="{author}" />
<meta name="robots" content="{robots}" />
<link rel="canonical" href="{url}" />
<meta name="theme-color" content="#faf8f5" />
{theme}
<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="{author}" />
<meta property="og:locale" content="en_US" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{img}" />
<meta property="og:image:width" content="{img_w}" />
<meta property="og:image:height" content="{img_h}" />
<meta property="og:image:alt" content="{img_alt}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{img}" />
<meta name="twitter:image:alt" content="{img_alt}" />{extra}
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
""".format(title=e(title), desc=e(desc), author=AUTHOR, url=url, theme=THEME_SCRIPT,
           og_type=og_type, img=e(img_url), img_w=img_w, img_h=img_h,
           img_alt=e(image_alt or title), robots=robots,
           extra="".join('\n<meta property="%s" content="%s" />' % (e(k), e(v)) for k, v in meta),
           ld="\n".join(ld_script(x) for x in ld))
    return "%s%s\n%s\n%s\n</body>\n</html>\n" % (head, TOPBAR, body, FOOTER.format(year=year))
