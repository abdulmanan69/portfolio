---
title: From Figma to Code — My Design Workflow
date: 2026-08-14
excerpt: How I go from a blank Figma canvas to a working, responsive website — the decisions, the handoff, and the details that make it feel finished.
cover: posts/images/figma-to-code-workflow.png
tags: design, figma, ui, workflow
---

# From Figma to Code — My Design Workflow

Good websites don't start in the code editor — they start with a plan. Here's how I
move from an idea to a shipped, responsive site.

## 1. Decide the feeling first

Before any pixels, I pick a direction: calm and minimal, bold and loud, playful?
That one decision drives type, colour and spacing.

## 2. Set up a tiny design system

- **Type scale** — a few sizes, not fifteen
- **Colour tokens** — background, ink, one accent
- **Spacing scale** — 4 / 8 / 16 / 24 / 40
- **Radius and shadows** — consistent everywhere

## 3. Design mobile and desktop together

I lay out the phone version next to the desktop one so responsive isn't an
afterthought.

## 4. Translate tokens straight to CSS variables

```css
:root { --ink: #16151a; --accent: #ff5a3c; --radius: 18px; }
```

## 5. Build, then add the delight

Structure and spacing first. Then the small interactive touches — a hover lift, a
cursor trail, a soft reveal. Motion last, so it enhances a solid layout.

## 6. Polish the details nobody asks for

Focus states, consistent alignment, real content, dark mode that looks intentional.
The details are the difference between fine and finished.
