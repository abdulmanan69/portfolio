# Abdul Manan — Portfolio

Static, single-page portfolio. No build step. Deploys by **drag-and-drop to Netlify**
or by pushing to **GitHub Pages**. Projects and the blog fill themselves from GitHub.

## Files
- `index.html` — page + SEO meta + JSON-LD structured data
- `style.css` — clean-minimal design, light **+ dark theme**, mouse interactions
- `script.js` — cursor, magnetic buttons, 3D tilt, reveal, theme toggle, loader,
  **live GitHub projects/stats**, and the **GitHub-driven blog engine**
- `SAMPLE-POST.md` — copy this into your blog repo to make your first post
- `robots.txt`, `sitemap.xml`, `site.webmanifest`, `favicon.svg`, `.nojekyll` — SEO / PWA / Pages
- `og-image.png`, `resume.pdf` — **you add these** (see below)

---

## What updates itself from GitHub (no code edits, no redeploy)
| On the site | Comes from |
|---|---|
| Projects grid | your repos at `github.com/abdulmanan69` (top 6 by stars/recency) |
| Stats strip | live GitHub API — repos, followers, stars, gists |
| Stats / langs / contribution graph / streak | auto-refreshing image cards |
| **Blog posts** | markdown files in your `blog` repo → `posts/` folder |

---

## ✍️ Blog — add posts from GitHub
1. Create a **public** GitHub repo named **`blog`**.
2. Inside it, make a folder **`posts/`**.
3. Copy `SAMPLE-POST.md` into `posts/`, rename it (e.g. `learning-react.md`).
4. Edit the front-matter at the top:
   ```
   ---
   title: Learning React
   date: 2026-07-24
   excerpt: Short summary for the card + SEO.
   cover: https://link-to-an-image.png
   tags: react, web
   ---
   Body in markdown — images, code, links all work.
   ```
5. Commit. Refresh the site → the post appears in the **Blog** section, credited to
   Abdul Manan, with its own SEO title/description + structured data.

Everything is markdown — edit or delete a file on GitHub and the site follows.
> Using a different repo/folder/username? Change `GH_USER` and the `BLOG` object at the
> top of `script.js`.

---

## Deploy — option A: Netlify (drag & drop)
1. https://app.netlify.com/drop → drag the whole `portfolio` folder.
2. Site settings → Domain management → add `abdulmanan.tech`, set DNS as shown.
3. HTTPS is automatic. Contact form works (Netlify Forms → Forms tab in dashboard).

## Deploy — option B: GitHub Pages
1. Create a repo (e.g. `portfolio`) and upload everything in this folder.
2. Repo → Settings → Pages → Source: `main` branch, `/root`. Save.
3. Site goes live at `https://abdulmanan69.github.io/portfolio/`.
4. For `abdulmanan.tech`: Settings → Pages → Custom domain → enter it, then set your
   DNS (CNAME to `abdulmanan69.github.io`). `.nojekyll` is already included.
   > Note: the Netlify contact form only works on Netlify. On Pages, swap it for
   > [Formspree](https://formspree.io) (change the form `action`).

---

## You still need to add
- **`og-image.png`** (1200×630) — the preview thumbnail when the link is shared.
- **`resume.pdf`** — makes the "Download résumé" button work.
- **Social links** — in `index.html`, replace the `USERNAME` placeholders
  (LinkedIn, X, Instagram) with your real handles.
- **Testimonials** — real quotes in the `#testimonials` section of `index.html`
  (currently placeholder text).
- **Google Search Console** — add the site, submit `sitemap.xml` so "Abdul Manan"
  indexes fast: https://search.google.com/search-console
