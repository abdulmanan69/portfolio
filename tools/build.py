#!/usr/bin/env python3
"""
Static build for abdulmanan.tech. Run it before committing; GitHub Pages
serves the generated files as-is.

    python tools/build.py             fetch repos from GitHub, rebuild everything
    python tools/build.py --offline   rebuild from the last good GitHub cache

Writes:
    projects/<slug>/index.html   one page per public repo (see tools/repos.py)
    projects/index.html          project hub
    index.html                   project cards between the build:projects markers
    blog/<slug>/index.html       one page per post in posts/
    blog/index.html, feed.xml
    sitemap.xml

Standard library only.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import blog                          # noqa: E402
import check                         # noqa: E402
import og                            # noqa: E402
import projects                      # noqa: E402
import repos as repo_data            # noqa: E402
from common import (AUTHOR, PERSON_ID, ROOT, SITE, BuildError, inject,  # noqa: E402
                    ld_script, person, write)


def build_home_ld(lastmod):
    """ProfilePage (with the full Person) and WebSite, written into index.html."""
    profile = {
        "@context": "https://schema.org", "@type": "ProfilePage", "@id": SITE + "/#profile",
        "url": SITE + "/", "name": "%s — Web Developer Portfolio" % AUTHOR,
        "dateModified": lastmod, "mainEntity": person(),
    }
    website = {
        "@context": "https://schema.org", "@type": "WebSite", "@id": SITE + "/#website",
        "name": AUTHOR, "alternateName": "abdulmanan.tech", "url": SITE + "/",
        "publisher": {"@id": PERSON_ID},
    }
    inject("index.html", "ld-home", "\n".join(ld_script(x) for x in (profile, website)))


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def git_lastmod(path):
    """Date of the last commit touching path, or today if it has uncommitted edits."""
    rel = os.path.relpath(path, ROOT)
    dirty = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        return today()
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    if not out:
        raise BuildError("can't date %s for the sitemap: not in git" % rel)
    return out


def build_sitemap(lastmods):
    """List every indexable HTML page on disk, so the sitemap is the real route
    list. lastmods maps URL paths to content dates from the page builders; a
    hand-written page uses its git date."""
    urls = []
    for path in check.html_files():
        page_info = check.parse(path)
        if page_info.noindex:
            continue
        loc = check.url_for(path)
        rel = loc[len(SITE):]
        lastmod = lastmods.get(rel) or git_lastmod(path)
        img = page_info.og_image
        img = ("    <image:image><image:loc>%s</image:loc></image:image>\n" % img
               if img.startswith(SITE + "/") else "")
        urls.append((rel, "  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n%s  </url>\n"
                     % (loc, lastmod, img)))
    urls.sort(key=lambda u: (u[0] != "/", u[0]))          # homepage first, then by path
    write(os.path.join(ROOT, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n%s</urlset>\n'
          % "".join(u[1] for u in urls))
    print("sitemap: %d URLs" % len(urls))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="use the cached GitHub data")
    args = ap.parse_args()

    repos = repo_data.load(offline=args.offline)
    posts = blog.load_posts()
    print("building %d projects, %d posts" % (len(repos), len(posts)))

    lastmods = {}
    lastmods.update(projects.build(repos, posts))
    lastmods.update(blog.build(posts, repos))

    # Anything the homepage shows (cards, counts, copy) lives in index.html, so the
    # file's own date is the page's date: last commit, or today if it has edits.
    lastmods["/"] = git_lastmod(os.path.join(ROOT, "index.html"))
    build_home_ld(lastmods["/"])
    og.save_manifest()
    build_sitemap(lastmods)
    check.run()
    print("done")


if __name__ == "__main__":
    main()
