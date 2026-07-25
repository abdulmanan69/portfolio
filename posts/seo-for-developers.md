---
title: SEO for Developers — How I Get Pages to Rank
date: 2026-08-02
excerpt: Search engine optimization isn't magic. It's clean HTML, fast pages, good metadata and structured data. Here's the practical checklist I use.
cover: posts/images/seo-for-developers.png
tags: seo, web, google, performance
---

# SEO for Developers — How I Get Pages to Rank

You can build a beautiful site that nobody finds. SEO is how people find it. The
good news: most of it is just good engineering.

## The basics that actually move the needle

- **One clear title and meta description per page** — this is what shows up in
  Google results. Make it read well and include the words people search.
- **A single H1** that says what the page is about.
- **Semantic HTML** — real headings, nav, article, section. Search engines read
  structure, not just text.

## Structured data (the secret weapon)

Adding JSON-LD tells Google exactly what your content is. On my site I use a Person
schema so a search for my name can show a rich result, and BlogPosting on every
article.

## Speed is a ranking factor

Google measures Core Web Vitals. I keep pages fast by shipping little JavaScript,
compressing images, lazy-loading below-the-fold media, and avoiding layout shift.
A fast site ranks better and feels better.

## Mobile-friendly or invisible

Google indexes the mobile version of your site first. If it isn't responsive, you're
already losing.

## The boring, essential files

- robots.txt tells crawlers they're welcome
- sitemap.xml hands them a map of your pages
- Submit both in Google Search Console, then watch what indexes

## SEO is a long game

You don't rank overnight. Publish consistently, keep the site fast and honest, earn
a few links, and results compound. Do the fundamentals well and you'll climb.
