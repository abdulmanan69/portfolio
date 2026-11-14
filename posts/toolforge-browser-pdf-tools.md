---
title: ToolForge — 92 Browser Tools, Zero Uploads
date: 2026-09-16
updated: 2026-11-14
excerpt: How ToolForge runs 92 PDF, image and text tools inside the browser tab, and what offline-first cost in memory and updates.
cover: posts/images/toolforge-browser-pdf-tools.png
tags: javascript, privacy, pdf, browser, open-source
---

# ToolForge — 92 Browser Tools, Zero Uploads

Most free PDF tools want the file uploaded before they will merge or compress it. For a contract, a payslip or an ID scan, that means trusting someone else's server and their deletion policy.

[ToolForge](https://github.com/abdulmanan69/pdf-toolkit) is my answer: a static React app where every merge, render, hash and conversion runs inside the tab. There is no backend. The only `fetch()` calls in `src/` read `data:` URLs the app generated itself, and one of the README's contributing rules is "Never add a network call." It is MIT licensed, with a [live demo](https://abdulmanan69.github.io/pdf-toolkit/) and a [project page](/projects/pdf-toolkit/).

## 92 tools, not 93

Every tool is an entry in `src/tools/catalog.json`, which has 93 entries. One of them, OCR, carries `"status": "soon"` and is a placeholder, so 92 tools are implemented today. The first version of this post said 93.

By primary category: PDF 29 (including the OCR placeholder), Image 17, Text 15, Conversion, Security and Utilities 10 each, and Compression 2. 21 entries also name extra categories in an `alsoIn` field, so Compress PDF, for example, appears under both PDF and Compression.

## The stack

React 18 and TypeScript, built with Vite 6, deployed to GitHub Pages by a workflow that type-checks, runs the unit tests and builds on every push to `main`. Inside the tab:

- **Writing PDFs:** `@cantoo/pdf-lib`, a pdf-lib fork with AES encryption, because upstream pdf-lib cannot read or write password-protected files. Every module imports it through `src/lib/pdf.ts`.
- **Reading PDFs:** PDF.js, imported on first use by `getPdfjs()` and run in its own worker.
- **Images:** one canvas pipeline in `src/lib/image.ts`. Tools describe resize, filter and watermark steps as data; brightness or blur become a CSS filter string on `ctx.filter`.
- **Hashes:** Web Crypto for SHA and HMAC JWT verification. MD5 is not available there, so `src/lib/crypto.ts` carries an RFC 1321 version, kept "only for checksum comparison, never for passwords."
- **The rest:** JSZip, `qrcode`, `jsqr`, `jsbarcode` and `marked`.

## One catalogue, one workbench

The first commit message sums up the design: the catalogue is "plain data (src/tools/catalog.json) joined to icons and lazy components, so the build scripts and the app share one source of truth", and "FileWorkbench owns the whole file loop", so "a tool is ~30 lines."

The join happens in [src/tools/registry.ts](https://github.com/abdulmanan69/pdf-toolkit/blob/10f017fb6912b07cf4d305787a34eff320ecd302/src/tools/registry.ts):

```ts
export const TOOLS: ToolDefinition[] = (catalog as ToolCatalogEntry[]).map((entry) => {
  const implementation = IMPLEMENTATIONS[entry.id];
  const icon = ICONS[entry.id];
  if (!implementation || !icon) {
    throw new Error(
      `Tool "${entry.id}" is in catalog.json but has no ${implementation ? 'icon' : 'implementation'}.`,
    );
  }
  const [loader, exportName] = implementation;
  return {
    ...entry,
    icon,
    component: lazy(async () => ({ default: (await loader())[exportName] })),
  };
});
```

`IMPLEMENTATIONS` maps each id to a category module and a named export, so a module is not imported until one of its tools is opened. An entry with no code or icon throws as soon as the registry loads instead of shipping a dead page.

The same JSON drives the build. `scripts/seo.mjs` writes the sitemap from it, then prerenders 102 HTML files (home, 7 categories, 93 tools, About), each with its own title, description, canonical URL and JSON-LD. GitHub Pages has no rewrite rules, so this is how a real path like `/pdf-toolkit/tool/merge-pdf` gets its own metadata. A copy of `index.html` becomes `404.html` so unknown URLs still boot the router.

`FileWorkbench` handles drop and paste, reordering, progress, errors, per-file downloads and a ZIP of everything. A tool supplies options and an async `run(files, report)`. Each run takes a token, and an older run's results are discarded if a newer one has started, so changing an option mid-run cannot show stale output.

## Where the files actually live

The first version of this post said rendered pages were cached in IndexedDB and heavy work ran off the main thread. Neither matches the code.

Files you add are ordinary `File` objects in React state. The update prompt says it directly: "open files are held in memory, not saved." The app has no Web Workers of its own. PDF.js parses in its worker; pdf-lib, the canvas pipeline and MD5 run on the main thread, and long jobs keep the progress bar moving through the workbench's `report(value, label)` callback.

Page thumbnails are rendered once per file at 0.3 scale and kept as JPEG object URLs, so selecting, rotating or reordering pages never re-renders the document.

IndexedDB has a different job. `FileWorkbench` writes every added file to a `recent` store capped at 12 files and 60 MB. A comment says it is for a "Recent Files panel", but no code reads the store back yet. In Settings, Clear recent files empties it; Clear all local data only removes the `toolforge:` localStorage keys.

The README states the limit plainly: "Very large files are bounded by device memory, not by an upload quota."

## Compress PDF does two different things

Lossless mode re-saves the PDF with pdf-lib using object streams, and returns the original if the result is not smaller.

Balanced (150 DPI, JPEG quality 0.75) and Strong (96 DPI, 0.55) render every page to a canvas and rebuild the PDF from JPEGs. The lossless preset's label, "Structure only — text stays selectable", is the hint: the other two produce image-only pages. They also hold every rendered page in memory until the rebuild, since `renderPdfPages` returns the whole array.

## The tradeoff: ask before updating

In an offline-first app, the service worker decides when a new version takes over. The [first commit](https://github.com/abdulmanan69/pdf-toolkit/blob/8adb3fed70fea2eca4cde918d56fa05f625a1bd8/vite.config.ts) used `registerType: 'autoUpdate'`, with a comment in `main.tsx` saying "new versions apply on the next visit". The [second commit](https://github.com/abdulmanan69/pdf-toolkit/commit/10f017fb6912b07cf4d305787a34eff320ecd302) reversed that, and `vite.config.ts` explains why:

> A tool that holds unsaved work in memory must never swap itself out underneath the user — an autoUpdate service worker can reload the page mid-operation and take a half-finished document with it.

Workbox now runs with `skipWaiting: false` and `clientsClaim: false`, and a `PwaManager` component shows "A new version is ready" with Reload now and Later buttons.

The cost is freshness: someone can keep running an old build for as long as they press Later. So `pwa.tsx` polls for updates every hour. Its comment: "Without this a long-lived installed window can run an old build for days, because a standalone app rarely gets a cold navigation." I would rather someone run a stale build for a while than lose a half-finished document.

## The offline bug in the first release

The first commit precached `**/*.{js,css,html,svg,png,ico,woff2}`. That looked complete and was not. The fix from the second commit, in [vite.config.ts](https://github.com/abdulmanan69/pdf-toolkit/blob/10f017fb6912b07cf4d305787a34eff320ecd302/vite.config.ts):

```ts
        /*
          `mjs` is load-bearing and easy to miss: Vite emits the PDF.js worker
          as `pdf.worker.min-[hash].mjs`, and a `js` glob does not match
          it. Without it the app precached a healthy-looking manifest and then
          failed to open a single PDF offline — the worker was the one request
          that still went to the network.
        */
        globPatterns: ['**/*.{js,mjs,css,html,svg,png,ico,woff2,bcmap,pfb,wasm,json}'],
```

The same line adds `bcmap` and `pfb`, PDF.js's character maps and standard fonts, which `scripts/copy-pdfjs-assets.mjs` copies into `public/pdfjs/` before every dev run and build. Without them, the config notes, "a cold offline load opens documents with missing glyphs, which reads as corruption rather than as a missing cache."

That commit fixed a quieter bug too: the Reduce motion setting wrote `data-reduce-motion` on the `html` element, but, as a comment in `App.tsx` admits, the first build "never read it anywhere". Now it drives Framer Motion's `MotionConfig`.

## OCR waits for an opt-in download

OCR is the one entry that is not implemented yet, and the reason is size. The placeholder page says:

> Recognising text in scans needs a language model of roughly 10–15 MB per language. Shipping it eagerly would break the promise that this app loads fast and works offline after one visit, so OCR will arrive as an opt-in download: you pick a language, the model is cached, and recognition then runs entirely on your device like every other tool here.

Until then the page does one useful thing: drop a PDF in and it counts the text PDF.js can extract. Over 40 characters, it sends you to Extract Text; fewer, and the file is "almost certainly a scan that will need OCR."

## Running it

It is a Vite project, so it needs Node 20 or newer and a build: clone it, run `npm install`, then `npm run dev`. `npm run build` copies the PDF.js assets, writes the sitemap, type-checks, builds and prerenders the 102 routes into `dist/`.

If a tool you need is missing, open an issue or [tell me about it](/#contact).
