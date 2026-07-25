---
title: Responsive Web Design — One Site, Every Screen
date: 2026-07-28
excerpt: How I make websites that look right on a 360px phone and a 4K monitor, using fluid layouts, sensible breakpoints and a mobile-first mindset.
cover: posts/images/responsive-web-design.png
tags: web, css, responsive, mobile
---

# Responsive Web Design — One Site, Every Screen

Most people will see your site on a phone. If it only looks good on your laptop,
it doesn't look good. Here's how I build sites that adapt to any screen.

## Mobile-first, always

I write the base styles for the smallest screen first, then *add* complexity for
bigger ones with `min-width` media queries. It keeps the CSS simple and forces me
to decide what actually matters before I have room for extras.

```css
.card { padding: 20px; }
@media (min-width: 640px) {
  .card { padding: 40px; }
}
```

## Fluid before fixed

Fixed pixel widths are the enemy of responsive design. I lean on:

- **clamp()** for type that scales smoothly
- **min() / max()** so grids never demand more width than the screen has
- **Flexbox and CSS grid** with auto-fit / minmax() for layouts that reflow themselves

```css
.grid { grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr)); }
```

That one line means: as many 300px columns as fit — but never wider than the screen.
No horizontal scroll, ever.

## Test the extremes

I check 360px small phones and very wide screens, not just the comfy middle. The
edges are where layouts break.

## Touch matters too

On phones there's no hover, so nothing important should hide behind a hover state,
and tap targets need to be big enough to hit with a thumb.

Responsive isn't a feature you bolt on at the end — it's the default. Build for the
phone, and the desktop takes care of itself.
