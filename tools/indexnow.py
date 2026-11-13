#!/usr/bin/env python3
"""
Tell IndexNow which URLs changed after a deploy. One submission reaches every
engine in the protocol (Bing, Yandex, Seznam, Naver and others).

Google is not in IndexNow and finds changes through sitemap.xml. The Google
Indexing API is deliberately not used: it only accepts JobPosting and
BroadcastEvent pages and would ignore a portfolio.

    python tools/indexnow.py                  URLs changed since the last ping
    python tools/indexnow.py --since <rev>    URLs changed since a git revision
    python tools/indexnow.py --all            every URL in sitemap.xml
    add --dry-run to print the list without sending anything

On GitHub Pages, pushing to main is the deploy. Run this after the push (the
GitHub Action in .github/workflows/indexnow.yml does it for you). It waits
until the live site serves the pushed version of the changed pages, so it
never announces a URL before the new content is there. The last commit it
announced is kept in .cache/indexnow.json.

Standard library only.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, SITE, BuildError   # noqa: E402

ENDPOINT = "https://api.indexnow.org/indexnow"
STATE = os.path.join(ROOT, ".cache", "indexnow.json")
HOST = SITE.split("://", 1)[1]


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        raise BuildError("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout


def find_key():
    """The IndexNow key: a <32 hex>.txt file at the site root holding its own name."""
    for path in glob.glob(os.path.join(ROOT, "*.txt")):
        name = os.path.basename(path)[:-4]
        if re.fullmatch(r"[0-9a-f]{32}", name):
            with open(path, encoding="utf-8") as f:
                if f.read().strip() == name:
                    return name
    raise BuildError("no IndexNow key file (<32 hex chars>.txt containing its own name) "
                     "at the site root")


def sitemap_urls():
    with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as f:
        return re.findall(r"<loc>([^<]+)</loc>", f.read())


def url_for(path):
    if path == "index.html":
        return SITE + "/"
    if path.endswith("/index.html"):
        return SITE + "/" + path[:-len("index.html")]
    return SITE + "/" + path


def changed_urls(since, until):
    """(url, expected live status, path at `until` or None) for each changed page."""
    listed = set(sitemap_urls())
    out = []
    for line in git("diff", "--name-status", "--no-renames", since, until).splitlines():
        status, path = line.split("\t", 1)
        if not path.endswith(".html"):
            continue
        url = url_for(path)
        if status == "D":
            out.append((url, 404, None))          # tell engines the page is gone
        elif url in listed:
            out.append((url, 200, path))
    return out


def fetch(url):
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + "v=%d" % time.time(),
                                 headers={"User-Agent": "indexnow-deploy-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as err:
        return err.code, b""
    except (urllib.error.URLError, OSError):
        return None, b""


def wait_until_live(key, items, commit, timeout):
    """Block until the key file and a sample of changed pages serve `commit`'s bytes."""
    checks = [(SITE + "/%s.txt" % key, 200, None)] + items[:3] + \
             [i for i in items if i[1] == 404][:2]
    deadline = time.time() + timeout
    while True:
        pending = []
        for url, want, path in checks:
            status, body = fetch(url)
            if status != want:
                pending.append("%s (HTTP %s, want %d)" % (url, status, want))
            elif path:
                local = subprocess.run(["git", "show", "%s:%s" % (commit, path)], cwd=ROOT,
                                       capture_output=True).stdout
                if hashlib.sha1(body).digest() != hashlib.sha1(local).digest():
                    pending.append("%s (still the old version)" % url)
        if not pending:
            return
        if time.time() > deadline:
            raise BuildError("the deploy isn't live after %ds:\n  %s"
                             % (timeout, "\n  ".join(pending)))
        print("waiting for the deploy: %s" % pending[0])
        time.sleep(15)


def submit(key, urls):
    for i in range(0, len(urls), 10000):
        body = json.dumps({"host": HOST, "key": key,
                           "keyLocation": "%s/%s.txt" % (SITE, key),
                           "urlList": urls[i:i + 10000]}).encode("utf-8")
        req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "indexnow-deploy-check"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                status = r.status
        except urllib.error.HTTPError as err:
            status = err.code
        except (urllib.error.URLError, OSError) as err:
            raise BuildError("could not reach IndexNow: %s" % err)
        meaning = {200: "accepted", 202: "accepted, key check pending",
                   400: "bad request", 403: "key not valid for this host",
                   422: "URLs don't belong to the host or key mismatch",
                   429: "too many requests, try later"}.get(status, "unexpected")
        if status not in (200, 202):
            raise BuildError("IndexNow answered HTTP %d (%s)" % (status, meaning))
        print("IndexNow: HTTP %d %s, %d URLs" % (status, meaning, len(urls[i:i + 10000])))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="git revision the previous deploy was built from")
    ap.add_argument("--until", default="HEAD", help="deployed revision (default HEAD)")
    ap.add_argument("--all", action="store_true", help="submit every sitemap URL")
    ap.add_argument("--dry-run", action="store_true", help="print, don't wait or send")
    ap.add_argument("--timeout", type=int, default=600, help="seconds to wait for the deploy")
    args = ap.parse_args()

    key = find_key()
    until = git("rev-parse", args.until).strip()
    state = {}
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)

    if args.all:
        items = [(u, 200, None) for u in sitemap_urls()]
    else:
        since = args.since or state.get("last")
        if not since:
            raise BuildError("no previous ping recorded. Pass --since <rev> or --all.")
        if re.fullmatch(r"0+", since):              # first push of a branch
            items = [(u, 200, None) for u in sitemap_urls()]
        else:
            items = changed_urls(since, until)

    urls = [u for u, _, _ in items]
    print("%d URL(s) to announce for %s" % (len(urls), until[:7]))
    for u in urls[:20]:
        print("  " + u)
    if len(urls) > 20:
        print("  ... and %d more" % (len(urls) - 20))
    if args.dry_run or not urls:
        return

    wait_until_live(key, items, until, args.timeout)
    submit(key, urls)
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"last": until, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f)


if __name__ == "__main__":
    main()
