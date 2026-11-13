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
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import blog                          # noqa: E402
import projects                      # noqa: E402
import repos as repo_data            # noqa: E402
from common import ROOT, SITE, write  # noqa: E402


def build_sitemap(entries):
    """entries: (path, lastmod YYYY-MM-DD, image url or None)."""
    seen, urls = set(), []
    for path, lastmod, image in entries:
        if path in seen:
            raise SystemExit("duplicate sitemap entry: %s" % path)
        seen.add(path)
        img = ("    <image:image><image:loc>%s</image:loc></image:image>\n" % image) if image else ""
        urls.append("  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n%s  </url>\n"
                    % (SITE, path, lastmod, img))
    write(os.path.join(ROOT, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n%s</urlset>\n'
          % "".join(urls))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="use the cached GitHub data")
    args = ap.parse_args()

    repos = repo_data.load(offline=args.offline)
    posts = blog.load_posts()
    print("building %d projects, %d posts" % (len(repos), len(posts)))

    project_entries = projects.build(repos, posts)
    blog_entries = blog.build(posts, repos)

    home_lastmod = max(e[1] for e in project_entries + blog_entries)
    build_sitemap([("/", home_lastmod, SITE + "/og-image.png")] + project_entries + blog_entries)
    print("done")


if __name__ == "__main__":
    main()
