"""
GitHub repo pipeline: fetch public repos at build time, filter, sort, cache.

The build stops with an error if GitHub can't be reached, rate-limits us, or
returns nothing usable, so a bad API day never ships an empty project list.
`python tools/build.py --offline` rebuilds from the last good cache on purpose.

Set GITHUB_TOKEN to lift the 60 requests/hour unauthenticated limit. A
fine-grained token with read-only access to public repos is enough. READMEs
are cached per repo and only refetched when the repo's pushed_at changes, so
a normal rebuild costs one or two requests.

Edit DENYLIST, FEATURED and OVERRIDES below.
"""

import http.client
import json
import os
import re
import time
import urllib.error
import urllib.request

from common import GH_USER, ROOT, SITE, BuildError

# ---------------------------------------------------------------- edit these

# Repos that never get a page. Case-insensitive. Forks and archived repos are
# already excluded automatically.
DENYLIST = {
    # offensive-security tooling: not promoted on the personal site
    "botnt", "C2",
    # this site, the GitHub profile README repo, and the old portfolio
    "portfolio", "abdulmanan69", "abdulmanan69.github.io",
    # scratch or empty repos with nothing to show
    "files", "pablotest", "boson", "fyp", "server",
    # coursework
    "2048-java",
    # no README yet, so the page would be a title and nothing else.
    # Remove a name once its repo has a README.
    "advice", "etcportal", "favicon", "readme-gen", "salaryslip",
}

# Repo names, in display order, pinned first on the homepage and /projects/.
# These are the projects with a full write-up on the blog, newest first.
FEATURED = ["bulwark", "pdf-toolkit", "cv-maker", "leadslicer", "saferoutes",
            "InvoiceApp", "lancall"]

# Facts GitHub doesn't hold. Only put true things here.
#   name         display name (defaults to the repo name)
#   demo         live URL (defaults to the repo's "Website" field)
#   description  replaces the GitHub description (better: fix it on GitHub)
# Display names below come from the titles of your own blog posts.
OVERRIDES = {
    # demo URLs below were checked live (HTTP 200) on 2026-11-14
    "bulwark": {"name": "Bulwark"},
    "cv-maker": {"name": "CV Studio", "demo": "https://abdulmanan69.github.io/cv-maker/"},
    "InvoiceApp": {"name": "InvoiceApp"},
    "lancall": {"name": "LanCall"},
    "leadslicer": {"name": "LeadSlicer", "demo": "https://leadslicer.abdulmanan.tech/"},
    "saferoutes": {"name": "SafeRoute"},
    "pdf-toolkit": {"name": "ToolForge", "demo": "https://abdulmanan69.github.io/pdf-toolkit/"},
}

# ---------------------------------------------------------------- internals

API = "https://api.github.com"
CACHE = os.path.join(ROOT, ".cache", "github")


def _request(url, accept, attempts=3):
    """(status, body). Retries network errors and 5xx; raises BuildError when out of tries."""
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": "portfolio-static-build",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    problem = None
    for attempt in range(attempts):
        if attempt:
            time.sleep(2 ** attempt)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as err:
            if err.code in (403, 429) and err.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(err.headers.get("X-RateLimit-Reset", "0"))
                wait = max(0, reset - int(time.time())) // 60 + 1
                raise BuildError(
                    "GitHub rate limit hit (%s). Resets in ~%d min. Set GITHUB_TOKEN "
                    "to raise the limit, or run with --offline to use the cache."
                    % (url, wait))
            if err.code < 500:
                return err.code, err.read()
            problem = "HTTP %d" % err.code
        except urllib.error.URLError as err:
            problem = str(err.reason)
        except (http.client.HTTPException, OSError) as err:   # IncompleteRead, resets, timeouts
            problem = "%s: %s" % (type(err).__name__, err)
    raise BuildError("could not fetch %s after %d tries (%s)" % (url, attempts, problem))


def _get_json(url):
    status, body = _request(url, "application/vnd.github+json")
    if status != 200:
        raise BuildError("GitHub returned HTTP %d for %s: %s"
                         % (status, url, body[:200].decode("utf-8", "replace")))
    return json.loads(body)


def _readme_html(name):
    """Rendered README HTML from GitHub, or None if the repo has no README."""
    status, body = _request("%s/repos/%s/%s/readme" % (API, GH_USER, name),
                            "application/vnd.github.html+json")
    if status == 404:
        return None
    if status != 200:
        raise BuildError("README fetch for %s returned HTTP %d" % (name, status))
    return body.decode("utf-8")


def _cache_path(*parts):
    return os.path.join(CACHE, *parts)


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _fetch_all():
    repos, page = [], 1
    while True:
        batch = _get_json("%s/users/%s/repos?per_page=100&type=owner&page=%d"
                          % (API, GH_USER, page))
        if not isinstance(batch, list):
            raise BuildError("unexpected repo list payload from GitHub")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def _keep(r):
    return (not r["fork"] and not r["archived"] and not r.get("private")
            and r["name"].lower() not in {d.lower() for d in DENYLIST})


def load(offline=False):
    """Return the filtered, sorted list of repo dicts, each with a 'readme' key."""
    list_path = _cache_path("repos.json")
    if offline:
        if not os.path.exists(list_path):
            raise BuildError("--offline but no cache at %s; run once online first"
                             % os.path.relpath(list_path, ROOT))
        raw = _load(list_path)
    else:
        raw = _fetch_all()
        if not raw:
            raise BuildError("GitHub returned zero public repos for %s" % GH_USER)
        _save(list_path, raw)

    unknown = [n for n in FEATURED if n.lower() not in {r["name"].lower() for r in raw}]
    if unknown:
        raise BuildError("FEATURED lists repos that don't exist publicly: %s"
                         % ", ".join(unknown))

    repos = [r for r in raw if _keep(r)]
    if not repos:
        raise BuildError("every repo was filtered out; check DENYLIST")

    # stars first, then most recently pushed
    repos.sort(key=lambda r: (r["stargazers_count"], r["pushed_at"]), reverse=True)

    seen, fetched = {}, 0
    for r in repos:
        slug = slugify(r["name"])
        if slug in seen:
            raise BuildError("slug collision: %s and %s" % (seen[slug], r["name"]))
        seen[slug] = r["name"]
        r["slug"] = slug

        path = _cache_path("readme", slug + ".json")
        cached = _load(path) if os.path.exists(path) else None
        if cached and cached["pushed_at"] == r["pushed_at"]:
            r["readme"] = cached["html"]
        elif offline:
            raise BuildError("--offline but README for %s isn't cached" % r["name"])
        else:
            r["readme"] = _readme_html(r["name"])
            _save(path, {"pushed_at": r["pushed_at"], "html": r["readme"]})
            fetched += 1

        o = OVERRIDES.get(r["name"], {})
        r["display_name"] = o.get("name") or r["name"]
        r["description"] = o.get("description") or _plain(r.get("description"))
        r["demo"] = o.get("demo") or _demo_url(r.get("homepage"))
        r["featured"] = r["name"].lower() in {n.lower() for n in FEATURED}

    print("repos: %d public, %d kept, %d READMEs fetched, %d from cache"
          % (len(raw), len(repos), fetched, len(repos) - fetched))
    return repos


def _plain(text):
    """GitHub descriptions are plain text, but some contain markdown emphasis."""
    text = re.sub(r"(\*\*|__|`)(.+?)\1", r"\2", text or "")
    return " ".join(text.split())


def _demo_url(homepage):
    """The repo's Website field, unless it points back at GitHub or at this site
    (setting it to the project's page here is fine, but that isn't a demo)."""
    h = (homepage or "").strip()
    if not h.startswith("http") or re.match(r"https?://(www\.)?github\.com/", h):
        return ""
    if re.match(r"https?://(www\.)?%s(/|$)" % re.escape(SITE.split("://", 1)[1]), h):
        return ""
    return h


def featured_first(repos):
    """FEATURED repos in the listed order, then everything else in sort order."""
    order = {n.lower(): i for i, n in enumerate(FEATURED)}
    pinned = sorted((r for r in repos if r["featured"]), key=lambda r: order[r["name"].lower()])
    return pinned + [r for r in repos if not r["featured"]]
