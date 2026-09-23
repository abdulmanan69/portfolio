---
title: ToolForge — 93 Browser Tools, Zero Uploads
date: 2026-09-16
excerpt: Most free PDF tools upload your file to someone else's server. ToolForge does the whole job inside your browser tab, and works offline.
cover: posts/images/toolforge-browser-pdf-tools.png
tags: javascript, privacy, pdf, browser, open-source
---

# ToolForge — 93 Browser Tools, Zero Uploads

Search "merge PDF" and every result asks you to upload the file. Your contract,
your payslip, your ID scan — onto a stranger's server, with a promise that it'll
be deleted in an hour.

The strange part is that none of it needs a server. Browsers have had the APIs to
do this work locally for years. So I built
**[ToolForge](https://github.com/abdulmanan69/pdf-toolkit)**: 93 document, image,
text and utility tools that run entirely in your browser. No uploads, no accounts,
no tracking — and it keeps working with no connection at all.

[Try it live](https://abdulmanan69.github.io/pdf-toolkit/) · MIT licensed

## "Client-side" here means there is no server

ToolForge is a static single-page app. Once the page has loaded there is no server
left to talk to. Every merge, render, hash and conversion happens inside your tab,
using:

- **Canvas** for rendering pages, resizing and filtering images
- **Web Crypto** for hashing and password work
- **IndexedDB** for holding large files without blowing up memory
- a handful of well-known client-side libraries for PDF and archive formats

The privacy claim isn't a policy you have to trust. Open DevTools, watch the
Network tab, drop in a file. Nothing leaves.

## What's actually in it

The tools cover six categories. A few overlap — Compress PDF is listed under both
PDF and Compression — so the lists add up to a little more than 93 distinct tools.

**PDF.** Merge, split, extract pages, delete pages, rearrange with drag & drop
plus undo/redo, rotate, crop, duplicate pages, insert blanks, compress, add or
remove watermarks, page numbers, metadata editor, flatten, sign by drawing or
uploading, add text, highlight, underline, sticky notes, fill AcroForms, password
protect, unlock, view, search text, extract text, extract embedded images, PDF to
images, images to PDF, contact-sheet generator.

**Images.** Resize, compress by quality or target size, crop by drag or numbers,
rotate, flip, convert between JPG / PNG / WebP / SVG, GIF conversion, image to PDF,
watermark, blur, grayscale, brightness, contrast, saturation, background colour,
QR generator and QR scanner from file or camera.

**Text.** Word and character counters, remove duplicate lines, strip extra spaces,
sort lines, reverse text, Base64 and URL encode/decode, JSON formatter and
validator, XML and HTML formatters, Markdown preview.

**Conversion.** JPG/PNG/WebP to PDF, PDF to PNG/JPG, ZIP creator and extractor,
CSV to JSON, JSON to CSV, Markdown to HTML.

**Security.** Password generator with an entropy readout, SHA-256, SHA-512, MD5,
UUID v4, JWT decoder, JWT viewer with local HS256 verification, random strings,
PDF encryption and decryption.

**Utilities.** QR codes for text, URL, Wi-Fi and vCard, barcodes (CODE128, EAN,
UPC and more), colour picker with contrast checks, palette generator, timestamp
converter, Unix clock, lorem ipsum, random numbers, dice, coin flip.

## The interesting engineering problems

**Memory, not CPU, is the limit.** A 200-page scanned PDF will happily exhaust a
tab if you hold every rendered page as a bitmap. Pages get rendered on demand and
cached to IndexedDB rather than kept in JavaScript memory.

**The UI has to stay alive.** Hashing a large file or rasterising a long document
blocks the main thread, and a frozen tab reads as a crash. Heavy work goes off the
main thread and reports progress, so the page always looks like it's doing
something.

**Offline is a feature, not a fallback.** Because everything is local, the app
caches itself and stays usable on a plane or a bad hotel connection. Any tool that
*would* need the network simply isn't in the app.

**93 tools can't be 93 pages.** They share one workspace shell — file picker,
preview, options panel, download — so adding a tool means adding a module, not a
new page and a new set of bugs.

## Who it's for

People handling documents they'd rather not hand to a stranger: HR files, invoices,
ID scans, medical letters, signed contracts. Also anyone on a locked-down office
machine where installing Acrobat isn't happening and uploading client documents is
a fireable offence.

That privacy-first, no-server approach is the same one behind
[LeadSlicer](/blog/leadslicer-split-csv-excel-files/) and
[CV Studio](/blog/cv-studio-free-resume-builder/) — once you've built the pattern
once, a surprising number of "you need an account for this" products turn out not
to need one.

## Run it yourself

It's a static site. Clone it and open `index.html`, or fork it and publish to
GitHub Pages in two clicks — there's no build step and nothing to configure.

```bash
git clone https://github.com/abdulmanan69/pdf-toolkit.git
```

The code is [on GitHub](https://github.com/abdulmanan69/pdf-toolkit). If a tool
you need is missing, open an issue — or [tell me about it](/#contact).
