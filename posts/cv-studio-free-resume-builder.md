---
title: CV Studio — A Free, Private Resume Builder
date: 2026-09-10
excerpt: 12 templates, live A4 pagination and PDF export, with no account and no server. Your CV never leaves the browser.
cover: posts/images/cv-studio-free-resume-builder.png
tags: javascript, tools, career, privacy, open-source
---

# CV Studio — A Free, Private Resume Builder

The online CV builder script is always the same. You fill in everything, you get
a nice preview, you click Download — and there's the paywall. You've just typed
your full employment history, address and phone number into a database to get
nothing back.

**[CV Studio](https://github.com/abdulmanan69/cv-maker)** is my answer: a free,
fast, 100% client-side CV / resume builder. No accounts, no server, and your data
never leaves your browser. MIT licensed.

## 12 templates that cover real formats

Classic, Horizon, Minimal, Executive, Bold, Tech, Timeline, Swiss, Gradient,
Compact, Paper and Onyx — spanning ATS-friendly single-column, sidebar layouts,
timelines, dark, serif and dense formats.

The ATS-friendly ones matter more than they look. A lot of applications go through
an applicant tracking system before a human sees them, and a two-column design
with text in boxes can come out scrambled. Having both kinds in one tool means you
can keep a plain version for the robots and a designed version for the human.

## The pagination engine was the hard part

A CV is a *paged* document, and the web has no native concept of one. The preview
renders real A4 or US Letter pages, and content flows across them automatically —
which means measuring rendered blocks and deciding where each one is allowed to
break.

On top of that sits **Fit to 1 / 2 / 3 pages**, which auto-shrinks type, spacing
and margins until the content lands on the target page count. Everyone's real
constraint is "it must be one page", so the tool solves for that directly instead
of leaving you to nudge a font-size slider twenty times.

## Everything is adjustable, live

- **Accent colour** from a palette, hue/lightness sliders, or a hex value
- **Body and heading fonts**, text size, line height, section spacing, margins
- **Heading style** and date format
- **Photo upload and editor** — drag & drop an image, then pan, zoom, rotate and
  tune brightness / contrast / saturation / grayscale / sepia; circle, rounded or
  square
- **Drag & drop everything** — sections, entries, skills and links reorder with
  smooth FLIP animations
- **A QR code on your CV**, generated entirely locally — no external QR service
  ever sees the link — pointing at your site, GitHub, LinkedIn, email, phone or a
  scannable contact card

Colour, font and spacing changes render while you drag, because a preview that
updates on blur makes you guess.

## Ten section types, plus your own

Experience, education, skills, languages, projects, certifications, awards,
interests, references — and unlimited custom sections, because someone always
needs "Publications" or "Volunteering" and a fixed schema always loses.

## Losing work is the real failure mode

For a tool with no accounts, "my browser crashed" cannot mean "start again". So:

- **Undo / redo** on Ctrl+Z / Ctrl+Y
- **Autosave** to `localStorage` as you type
- **JSON backup import / export** — your CV as a portable file you own, which also
  means you can keep three tailored versions and switch between them
- **Sample data** to start from, and dark mode for late-night applications

## PDF export without a server

Export uses `html2canvas` + `jsPDF`, loaded from a CDN only when you click
download, with a **print fallback** when you're offline. Ctrl+P → Save as PDF gives
you a vector-quality copy that is often *better* than the rasterised one, and it
works with nothing loaded at all.

That's the general rule in this app: the primary path can use a library, but there
always has to be a path that works with nothing.

## The stack

Vanilla JavaScript, hand-written CSS, canvas-based image editing and a custom
pagination engine. No framework and no build step — open `index.html` and it runs.

Every form control is hand-built too: dropdowns, month/year picker, sliders, colour
picker and toggles. Native browser popups look wrong inside a designed app and
behave differently on every OS, so they're gone.

It also ships with full SEO wiring — meta tags, Open Graph, JSON-LD
(`WebApplication` + FAQ + author), `robots.txt`, `sitemap.xml`, an `llms.txt` for
AI crawlers, and a PWA manifest — the same checklist I wrote about in
[SEO for Developers](/blog/seo-for-developers/).

## Use it or fork it

```bash
git clone https://github.com/abdulmanan69/cv-maker.git
# then just open index.html
```

Deploying your own copy is Settings → Pages → `main` / root. Search-and-replace the
site URL in `index.html`, `robots.txt` and `sitemap.xml` once and you're live.

Code and issues: [github.com/abdulmanan69/cv-maker](https://github.com/abdulmanan69/cv-maker).
Building something similar and want a hand? [Say hi](/#contact).
