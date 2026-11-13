---
title: My first post
date: 2026-07-24
excerpt: A short one-line summary — shows on the blog card and is used for SEO.
updated: 2026-07-30
cover: https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&q=60
tags: web, design, learning
---

# My first post

This whole post is just a **markdown file** in the `posts/` folder.
`python tools/build.py` turns it into a static page at `/blog/<file-name>/`.

## You can write anything

- Bullet points
- **Bold** and *italic*
- `inline code`
- Links: [my GitHub](https://github.com/abdulmanan69)

## Images work too

Just use normal markdown image syntax and it renders:

![alt text](https://images.unsplash.com/photo-1517180102446-f3ece451e9d8?w=1000&q=60)

## Code blocks

```js
console.log("Hello from Abdul Manan's blog");
```

> Every post is credited to Abdul Manan and gets its own SEO title,
> description and structured data automatically.

---

### How to publish
1. Add a new `.md` file to the `posts/` folder (e.g. `learning-react.md`).
2. Change the front-matter at the top (title, date, excerpt, cover, tags).
   `updated` is optional: set it to the day you last changed the content.
3. Write, then run `python tools/build.py`.
4. Commit everything and push to `main`. GitHub Pages publishes it and the
   IndexNow workflow tells search engines.
