---
title: How I Built This Portfolio
date: 2026-07-24
excerpt: A behind-the-scenes look at building a fast, GitHub-driven portfolio with zero build step — projects and blog posts that update themselves.
cover: posts/images/how-i-built-this-portfolio.png
tags: web, javascript, build-log
---

# How I Built This Portfolio

I wanted a portfolio that felt like *me* — clean, a little playful, and, most
importantly, one I'd never have to babysit. No redeploys every time I ship a new
project or write a post. Here's how it came together.

## The rule: everything lives on GitHub

The core idea is simple: **if it's on my GitHub, it shows up on the site.**

- The **projects** grid is pulled straight from the GitHub API — my top repos by
  stars and recency, with language, stars and forks. Push a new repo, it appears.
- This **blog** is just markdown files in a `posts/` folder. The file you're
  reading right now is one of them.
- The stats, contribution graph and streak are live cards that refresh on their own.

No CMS. No database. No build pipeline. Just files.

## The stack (or lack of one)

- **Plain HTML, CSS and JavaScript.** One `index.html`, one stylesheet, one script.
- **No framework.** For a site this size, React would be more ceremony than value.
- **`marked`** to turn markdown posts into HTML in the browser.
- **Netlify / GitHub Pages** for hosting — both are a drag-and-drop or a `git push`.

```js
// projects, straight from GitHub — no hardcoding
const repos = await fetch(`https://api.github.com/users/${user}/repos`)
  .then(r => r.json());
```

## Making it feel alive

Clean and minimal doesn't have to mean static. There's a custom cursor that lags
slightly behind your mouse, buttons that lean toward the pointer, cards that tilt
in 3D, and a soft accent blob that follows you around the hero. Small touches, but
together they make the page feel *responsive to you*.

## SEO from day one

Every page — including each blog post — sets its own title, description and
structured data, so search engines understand exactly who "Abdul Manan" is and
what I do.

## What's next

More posts, more projects, and probably a few more interactive experiments. The
best part: I can add all of it from GitHub, and the site just keeps up.
