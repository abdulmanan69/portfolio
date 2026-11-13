"""
Shared constants and page furniture for the static build.

Every generated page (projects, blog) goes through page() so the <head>,
top bar and footer stay identical across the site.
"""

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://abdulmanan.tech"
AUTHOR = "Abdul Manan"
GH_USER = "abdulmanan69"
SAME_AS = [
    "https://github.com/abdulmanan69",
    "https://www.linkedin.com/in/abdulxmanan",
    "https://www.instagram.com/abdul_x_manan",
]
DEFAULT_IMAGE = ("/og-image.png", 1200, 630)


def e(s):
    """Escape text for HTML content and attribute values."""
    return html.escape(s or "", quote=True)


def abs_url(p):
    return p if p.startswith("http") else "%s/%s" % (SITE, p.lstrip("/"))


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
  <span>&copy; {year} Abdul Manan</span>
  <span>Built and designed by Abdul Manan &middot; <a href="https://github.com/abdulmanan69">github.com/abdulmanan69</a></span>
  <a href="/">Home</a>
</footer>"""


def page(*, title, desc, path, body, og_type="website", image=None, ld=(), year="2026"):
    """Render a full HTML document.

    path   site-relative URL of this page, e.g. "/projects/lancall/"
    image  (url, width, height) for og:image; defaults to the site card
    ld     iterable of JSON-LD dicts
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
<meta name="robots" content="index, follow, max-image-preview:large" />
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
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<meta name="twitter:description" content="{desc}" />
<meta name="twitter:image" content="{img}" />
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
           ld="\n".join(ld_script(x) for x in ld))
    return "%s%s\n%s\n%s\n</body>\n</html>\n" % (head, TOPBAR, body, FOOTER.format(year=year))
