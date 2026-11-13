# SEO notes: what you need to do by hand

The site now does the technical part on its own: a static page per project,
unique titles and descriptions, structured data, OG cards, a sitemap built from
the real pages, and IndexNow pings after each deploy. These are the steps no
script can do for you. Do them roughly in this order.

## 1. Search engines (one-time, about 20 minutes)

- [ ] **Google Search Console → Sitemaps:** submit `https://abdulmanan.tech/sitemap.xml`.
      Come back after a few days and check that it says "Success" with 62+ discovered URLs.
- [ ] **Search Console → URL Inspection → Request indexing**, one URL at a time
      (there is a small daily quota, so start with these):
  - `https://abdulmanan.tech/`
  - `https://abdulmanan.tech/projects/`
  - `https://abdulmanan.tech/blog/`
  - your featured project pages and their write-ups, once `FEATURED` is filled in
- [ ] **Bing Webmaster Tools:** sign in and use "Import from Google Search Console".
      IndexNow already pings Bing on every deploy, but the import gives you Bing's reports.
- [ ] **Rich Results Test** (search.google.com/test/rich-results) on `/` and on one
      project page, e.g. `/projects/bulwark/`. Expect ProfilePage and Breadcrumbs to be
      detected. The build already checks that all JSON-LD parses; this confirms Google
      reads it the same way.
- [ ] **One-time IndexNow ping for everything:** the workflow only announces pages that
      change in each push, and the first big deploy happened before it existed. Run
      `python tools/indexnow.py --all` once (or ask me to).

## 2. Fill in the TODOs in the code

- [ ] `tools/common.py` → `SAME_AS`: add your X profile and any other real profiles.
- [ ] `tools/common.py` → `JOB_TITLE`: currently "Web Developer & Designer", taken from the
      old site copy. Change it if you want something else.
- [ ] `tools/repos.py` → `FEATURED`: the repos you want pinned first on the homepage.
- [ ] `index.html` → résumé link: the old link pointed at a `resume.pdf` that was never in
      the repo (a 404). Add the PDF to the repo root and restore the commented-out link.
- [ ] Testimonials on the homepage are placeholders ("Placeholder Name"). Replace them
      with real quotes or delete the section; don't leave fake ones live.

## 3. Fix things on GitHub (these feed your page titles)

The build uses each repo's GitHub description as the page title and meta
description. Edit the "About" box on GitHub for:

- [ ] `apexquant` ("Paper analysis only")
- [ ] `gamesite` (Vite template boilerplate)
- [ ] `ott` (description is a sentence fragment about TMDB)
- [ ] `umt-portal` (description is a fragment about CORS headers)
- [ ] `active-noise-cancellation` (no description)
- [ ] `saferoutes` (no description)
- [ ] Bulwark's README shows a red "ci failing" badge. Fix CI or drop the badge.
- [ ] Review before they stay public on your domain: `monkeytype` ("stealth autotyper"),
      `BulkMessageSender`, `SaferWebTweak`, the client sites `alysonwarranty` and
      `alysonautowarrantyus`, and `hrms` (its README lists `@wavetech.pk` addresses).
      Add any you don't want shown to `DENYLIST` in `tools/repos.py` and rebuild.

Then rebuild with `python tools/build.py` and push.

## 4. Backlinks and name signals (ongoing)

"Abdul Manan" is a common name, so ranking for the bare name takes months of
consistent signals. The goal is that every profile says the same name and
points at the same site.

- [ ] **GitHub profile:** set the Website field to `https://abdulmanan.tech` and put the
      link at the top of your profile README (`abdulmanan69/abdulmanan69`).
- [ ] **Each repo's Website field:** set it to its page here, e.g.
      `https://abdulmanan.tech/projects/bulwark/`, unless it has a live demo. The build
      knows these aren't demos and won't show a "Live demo" button for them.
- [ ] **LinkedIn:** Website field → the site; add your best project pages and posts
      to the Featured section; use exactly "Abdul Manan" as the name.
- [ ] **Instagram bio** and **X bio:** link to the site.
- [ ] **Cross-post the write-ups** to dev.to or Hashnode with the canonical URL set to
      the post on abdulmanan.tech, so the original keeps the ranking.
- [ ] **Real communities, real projects:** Bulwark fits "awesome MCP" / AI-security lists;
      ToolForge, CV Studio and LeadSlicer fit "Show HN" or relevant subreddits. One
      genuine post per project, not spam.
- [ ] Keep the same photo and name on every profile; Google uses that consistency to
      treat them as one person.

## 5. What to watch

- Search Console → Performance, filtered by queries containing "abdul manan".
  Expect "Abdul Manan portfolio" and "Abdul Manan developer" first; the bare name later.
- Search Console → Pages: anything under "Crawled, currently not indexed" is usually a
  thin project page. Improve its README or add it to `DENYLIST`.
