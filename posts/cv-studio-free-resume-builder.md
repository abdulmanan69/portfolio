---
title: CV Studio — A Free, Private Resume Builder
date: 2026-09-10
updated: 2026-11-14
excerpt: How my browser-only CV builder paginates 12 templates onto A4 or Letter pages, fits a CV to 1-3 pages, and why its PDF button makes an image.
cover: posts/images/cv-studio-free-resume-builder.png
tags: javascript, tools, career, privacy, open-source
---

# CV Studio — A Free, Private Resume Builder

The online CV builder script is always the same. You fill in everything, you get a nice preview, you click Download, and there's the paywall. You've just typed your full employment history, address and phone number into a database to get nothing back.

[CV Studio](https://github.com/abdulmanan69/cv-maker) is my answer: a CV builder that runs entirely in the browser, with no account and no backend. The README licenses it under MIT, and the [project page](/projects/cv-maker/) has the short version. This post is about how it works inside.

## What "no server" means in the code

Everything you enter lives in one `{ data, settings }` object, saved to `localStorage` under `cvmaker:v1` 350 ms after your last edit. Your photo is in there too, as a 640×640 JPEG data URL. The code makes no `fetch` or XHR calls and has no analytics. The only third-party requests are Google Fonts and, when you click Download PDF, html2canvas and jsPDF from jsDelivr.

There is one storage slot, so separate versions per application, or moving to another device, means JSON backups (Export backup, or Ctrl+S). One gap: if a big photo exceeds the storage quota, `saveNow` swallows the error. The comment says "storage full — photo too big; user still has export", and the save indicator still pulses.

## Templates emit blocks, the engine owns pages

There's no framework and no build step: `index.html` loads 24 plain scripts in order, each an IIFE hanging off `window.CV`. The [template contract](https://github.com/abdulmanan69/cv-maker/blob/0035be896ec754e1f92a7b51995f9b41c43f9ea4/docs/TEMPLATE_CONTRACT.md) sets the rule:

> Templates are plain-script IIFEs loaded via `<script>` tags (no modules, no build step). They must work from `file://` and GitHub Pages, with **zero external assets**.

A template's `render(data, S, T)` never deals with pages. It returns ordered arrays of blocks: `main`, an optional `side` column, and an optional `header` for page 1. The contract asks for "one block per section heading (`T.headBlk`) and one block per item", because the block is what the paginator moves.

Six of the 12 templates are single-column (Classic, Minimal, Executive, Paper, Tech, Timeline) and six have a side column (Horizon, Onyx, Gradient, Bold, Swiss, Compact). Only Classic is tagged "ATS friendly" in code. Settings reach every template as CSS custom properties on `.cv-root`, such as `--accent`, `--fs` and `--pad`.

## Pagination: append until it overflows

Each page is a fixed-size `div` (794×1123 px for A4, 816×1056 for US Letter) built off-screen, with `overflow:hidden` columns. Then `buildPages` pours blocks in:

```js
  function fillCol(col, queue) {
    if (!col) return 0;
    let count = 0;
    while (queue.length) {
      const b = queue[0];
      col.appendChild(b);
      if (col.scrollHeight > col.clientHeight + 1) {
        col.removeChild(b);
        if (!col.childElementCount) { // block taller than a whole column — place anyway
          col.appendChild(b);
          queue.shift();
          count++;
        }
        break;
      }
      queue.shift();
      count++;
    }
    // keep-with-next: don't leave a section heading orphaned at the page bottom
    const last = col.lastElementChild;
    if (count > 0 && queue.length && last && last.classList.contains('blk-head') && col.childElementCount > 1) {
      col.removeChild(last);
      queue.unshift(last);
      count--;
    }
    return count;
  }
```

From [js/paginate.js](https://github.com/abdulmanan69/cv-maker/blob/0035be896ec754e1f92a7b51995f9b41c43f9ea4/js/paginate.js#L36-L62). Append a block, ask the browser whether the column overflows, and if so take it back for the next page. Blocks never split, so a job entry stays whole. The side and main queues fill separately, so a sidebar can run onto page 2 by itself.

Two limits: the page loop stops at 12 (`while (n < 12 && ...)`) and anything still queued is not rendered. And because measurement depends on real fonts, the app renders again when `document.fonts.ready` resolves.

## Fit to 1, 2 or 3 pages is a binary search

Everyone's real constraint is "it must be one page". The "Fit content to" setting handles it by rerunning the whole paginator at different scales:

```js
    let fit = 1;
    if (S.targetPages !== 'auto') {
      const target = parseInt(S.targetPages, 10) || 1;
      if (buildPages(def, data, S, 1).length > target) {
        let lo = 0.45, hi = 1;
        for (let i = 0; i < 8; i++) {
          const mid = (lo + hi) / 2;
          if (buildPages(def, data, S, mid).length <= target) lo = mid;
          else hi = mid;
        }
        fit = lo;
      }
    }
```

From [js/paginate.js](https://github.com/abdulmanan69/cv-maker/blob/0035be896ec754e1f92a7b51995f9b41c43f9ea4/js/paginate.js#L160-L172). `fit` scales the base text size, the gaps and the page padding. Eight halvings land within about 0.002 of the best scale, for up to ten full page builds per render. If the content won't fit even at 0.45, you get 0.45 and the extra pages. The CV guide in the repo says what to do instead: "tighten the writing before shrinking the type".

## Live preview without repaginating every pixel

A comment in `design.js` describes how sliders stay smooth:

> var-backed settings restyle already-rendered pages instantly (zero lag while dragging), then the throttled full render repaginates

`CV.retint` pushes the new CSS variables onto the pages on screen, and `CV.refreshSoon` repaginates at most every 140 ms, plus one trailing render. The template gallery uses the same engine: each thumbnail is page 1 of *your* CV, scaled down.

## The tradeoff: the big PDF button makes a picture

Download PDF is the primary button in the top bar, with Print beside it as a ghost button. They produce different files.

Download PDF lazy-loads the two libraries, then for each page calls `html2canvas` with `scale: 2`, converts the canvas with `toDataURL('image/jpeg', 0.95)`, and places that image edge to edge with `pdf.addImage` ([js/export.js](https://github.com/abdulmanan69/cv-maker/blob/0035be896ec754e1f92a7b51995f9b41c43f9ea4/js/export.js#L123-L131)). You get one click, no print dialog, and a file named after you (`abdul-manan-cv.pdf` for me). You lose the text layer: nobody can select the words, and neither can a parser.

Print clones the same paginated pages into a `#print-holder`, hides the app, breaks after each page and injects an `@page{size:A4;margin:0}` rule. The README puts the result plainly: "Ctrl+P → Save as PDF gives a vector-quality copy".

That matters because the guide in the same repo says "Export a PDF with real, selectable text, never a screenshot or scan". Picking Classic for a job portal only helps if you export through Print. Download PDF is fine for emailing a person.

Download PDF also falls back to Print. If anything fails, including a 20-second timeout per library, the app offers the print dialog and promises "an identical result". That holds for how the pages look, not for what's inside the file. The primary path can use a library, but there has to be a path that doesn't need one.

## The smaller pieces

- **QR code.** `qr.js` is a from-scratch encoder: "Byte mode, ECC level M, versions 1-10, full mask evaluation". Version 10 caps the payload at 213 bytes, so an over-long custom link gets no code. The contact-card option writes a `MECARD:` string.
- **Photo editor.** Canvas pan, zoom, rotate and five filters, baked into a 640×640 JPEG on Apply. Reopening it edits that JPEG, not your original.
- **Sections.** Nine built-in types, each addable once, plus a repeatable Custom type.
- **Controls.** Dropdowns, month picker, sliders, colour picker and dialogs are custom (`widgets.js`: "no native dropdowns/calendars"). The file chooser is the one native picker left.

## What the commit history shows

Not much. There are two commits, both on 23 July 2026. The first added the whole app at once, 37 files and 4,593 lines, so the log can't show how the paginator evolved.

The second, 36 minutes later, fixed a bug I'd shipped. `index.html` carries static intro content for crawlers and no-JS visitors, and boot threw it away ([js/app.js at 5b3decf](https://github.com/abdulmanan69/cv-maker/blob/5b3decf6bcf202c5f808e906360fbcc01ad6be18/js/app.js#L259)):

```js
    app.textContent = ''; // remove the static SEO/crawler content
```

The [fix commit](https://github.com/abdulmanan69/cv-maker/commit/0035be896ec754e1f92a7b51995f9b41c43f9ea4) explains: "The app deleted the static intro block on boot, leaving the rendered page with no headings or descriptive text for search engines." Boot now moves that block into a new About tab. The same commit added `templates.html`, `guide.html` and a 404 page, but not a README update: its deploy notes still name three files to edit when six site files hardcode the URL.

## Run it or fork it

```bash
git clone https://github.com/abdulmanan69/cv-maker.git
# then open index.html in a browser
```

To host a copy on GitHub Pages, set Settings → Pages → Source to `main` and `/ (root)`, then replace `https://abdulmanan69.github.io/cv-maker/` in `index.html`, `templates.html`, `guide.html`, `robots.txt`, `sitemap.xml` and `llms.txt`. The basics from [SEO for Developers](/blog/seo-for-developers/) are already in them.

To add a 13th template, follow `docs/TEMPLATE_CONTRACT.md`: one file in `js/templates/`, one `<script>` tag in `index.html`, and a `render` that survives blank data.

Building something similar and want a hand? [Say hi](/#contact).
