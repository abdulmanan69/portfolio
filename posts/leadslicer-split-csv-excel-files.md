---
title: LeadSlicer — Split and Clean CSV Files Offline
date: 2026-09-04
excerpt: Dedupe, filter and split 50,000-row CSV or Excel lead files into chunks, entirely in the browser, with nothing uploaded anywhere.
cover: posts/images/leadslicer-split-csv-excel-files.png
tags: javascript, csv, excel, tools, privacy
---

# LeadSlicer — Split and Clean CSV Files Offline

Anyone who has worked in a sales or dispatch office knows this job. A 50,000-row
lead list arrives. It needs the duplicates removed, the empty rows stripped, three
columns kept out of nineteen, and then it has to be cut into 500-row chunks — one
per agent.

The usual options are all bad. Excel struggles and mangles your phone numbers into
scientific notation. An online splitter wants you to upload a file full of
customer phone numbers to a site with no name on it. A Python script works, but
the person who actually needs this doesn't have Python.

**[LeadSlicer](https://leadslicer.abdulmanan.tech)** is the fourth option: free,
offline, browser-based. Your files never leave your device.

## The seven-step flow

1. **Upload** — drag & drop any `.csv`, `.xlsx` or `.xls` file
2. **Preview** — first rows, total row and column counts
3. **Configure headers** — use the first row, or auto-generate column names
4. **Select columns** — keep only the fields you need
5. **Filter & clean** — remove duplicates, empty rows and rows with missing values
6. **Chunk** — split into files of any size: 100, 500, 1000+ rows
7. **Download** — individual files, or everything as one ZIP

Each chunk can be previewed before you download it, because finding out the split
was wrong *after* you've emailed eight agents is how the afternoon disappears.

## Formats come out the way they went in

This is the detail that decides whether a tool like this is usable. Dates, currency
and number formats are preserved exactly. No `+923001234567` turning into
`9.23E+11`, no leading zeros eaten, no `03/04` silently becoming April 3rd.

Deduplication runs on **any column you choose** — Email, Phone, Company — not on
whole-row equality, because two records for the same person are almost never
byte-identical.

## Why in-browser is the right call here

Three reasons, in the order that actually matters to a sales office:

**Privacy.** Lead files are customer data. In most companies, uploading them to an
unvetted website is a policy breach even when nobody notices. A tool that runs
locally sidesteps the entire conversation.

**No install.** It's a web page. The agent who needs it opens a link. There's no
IT ticket, no admin password, no Python.

**Offline.** It's an installable PWA, so once loaded it works with no internet at
all — on Android, iOS or desktop. Handy when the office Wi-Fi is the bottleneck.

## Details that make it pleasant

- Light / dark / system themes with six accent colours
- Keyboard navigable, semantic HTML — it works with a screen reader
- Responsive down to a phone, because half the people using it are on one
- ZIP download so you get one file instead of forty

None of that is clever engineering. It's the difference between a tool people use
twice and a tool people keep in their bookmarks bar.

## The same pattern, again

LeadSlicer is the third tool I've built on the same idea as
[ToolForge](/blog/toolforge-browser-pdf-tools/) and
[CV Studio](/blog/cv-studio-free-resume-builder/): take a job that everyone assumes
needs a server, and notice that the browser has been able to do it for years.

Parsing spreadsheets, hashing, zipping, rendering PDFs, reading the camera — all
local APIs now. Most "upload your file here" products are charging for a round
trip that doesn't need to happen.

## Try it

**Online:** [leadslicer.abdulmanan.tech](https://leadslicer.abdulmanan.tech) — no
install, no account.

**Locally:**

```bash
git clone https://github.com/abdulmanan69/leadslicer.git
cd leadslicer
# open index.html — that's the whole setup
```

MIT licensed, source on [GitHub](https://github.com/abdulmanan69/leadslicer). If
your team has a file-wrangling job that eats an afternoon every week,
[tell me about it](/#contact) — those are my favourite things to build.
