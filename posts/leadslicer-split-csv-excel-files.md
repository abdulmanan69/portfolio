---
title: LeadSlicer — Split and Clean CSV Files Offline
date: 2026-09-04
updated: 2026-11-14
excerpt: How LeadSlicer dedupes, filters and splits CSV or Excel lead files in the browser, with no uploads and no dates turned into serial numbers.
cover: posts/images/leadslicer-split-csv-excel-files.png
tags: javascript, csv, excel, tools, privacy
---

# LeadSlicer — Split and Clean CSV Files Offline

[LeadSlicer](https://github.com/abdulmanan69/leadslicer) does one narrow job. It takes a CSV or Excel lead file, removes duplicates and empty rows, keeps only the columns you pick, and cuts the rest into smaller files: one per rep, territory or campaign batch.

Lead files are customer contact data, so I wanted that work to happen without the file going anywhere, in something a non-developer could open from a link. The result is a static page with no backend and no build step; everything runs in the browser tab. It is live at [leadslicer.abdulmanan.tech](https://leadslicer.abdulmanan.tech), with a summary on the [project page](/projects/leadslicer/).

## What the wizard does

The app is a six-step wizard: Upload, Header, Columns, Filter, Configure, Download. (The README counts the preview as a seventh step; in the app it is part of Upload.)

1. **Upload.** Drop or browse for a `.csv`, `.xlsx` or `.xls` file and see row and column counts plus the first five rows. Only a workbook's first sheet is read, with a warning if there are more.
2. **Header.** Use the first row as names or generate `Column1`, `Column2` and so on. A repeated name becomes `Email (2)`.
3. **Columns.** Pick the columns to keep, and the identifier columns for duplicates, such as Email or Phone.
4. **Filter.** Skip it, or toggle three filters: empty rows, duplicates, and rows missing a required value.
5. **Configure.** Type a chunk size and see how many files it makes.
6. **Download.** Each chunk gets a preview of its first 15 rows and a download button, plus one button to zip them all.

CSV in gives CSV out; Excel in gives `.xlsx` out. Part numbers are zero-padded "so 10+ chunks sort correctly in a file manager".

## How it is put together

There is no framework. `index.html` loads four vendored libraries from `lib/` (SheetJS, PapaParse, JSZip, FileSaver) and four scripts of mine, all IIFEs: `FileProcessor` parses and filters, `ChunkExporter` writes CSV, XLSX and ZIP, `ThemeManager` handles appearance, and `app.js` drives the wizard. None of them calls `fetch` or XHR. A service worker pre-caches the page and libraries, so after one visit the app works offline and installs as a PWA.

Inside the pipeline, every row is an array of strings. Next to the rows sits one object per column, `{ z, isDate, isNumeric }`, where `z` is the first Excel number format seen in that column below the first row. The filters run in a fixed order:

1. **Empty rows.** Empty means every *kept* column is blank. Rows blank across the whole file are already dropped by the parsers.
2. **Duplicates.** The key is the identifier columns' values, trimmed, lowercased and joined with a NUL character. The first row with a key wins.
3. **Missing required values.** Rows with a blank required column go.

One consequence of that order: if the first copy of a lead is missing a required value that a later copy has, the later copy is dropped as a duplicate, then the first is dropped as incomplete. Neither survives.

Comments show the sizes the code was written for. `filterData` filters by reference and copies once at the end because "On a 500k-row file this avoids a full duplicate of the dataset." The XLSX writer avoids `[headers, ...data]`, which "blows the call stack once a chunk holds a few hundred thousand rows." CSVs over 3 MB parse in a PapaParse worker, retried on the main thread if the worker fails to start. The repo has no benchmarks, so these are design targets, not measured limits.

## The bug that shaped it

The history is three commits: the initial version and a CNAME in March 2026 (`bfbd1ee`, `3e46c21`), then one large commit in July 2026, [`12b5cff`](https://github.com/abdulmanan69/leadslicer/commit/12b5cff6c418dfeab4836cfeecedb6faef540f2f): "fix: preserve date and number formats through slicing; add theme system".

The first version read workbooks with `XLSX.read(e.target.result, { type: 'array' })` and then `sheet_to_json`. The commit message explains the result:

> Dates were being destroyed on import. XLSX stores a date as a serial number and only renders it as dd/mm/yyyy via the cell's number format, but the reader used sheet_to_json with raw values, so 05/03/2026 came back as 46086 and every exported chunk contained integers instead of dates.

The fix reads the workbook with `cellDates`, `cellNF` and `cellText`, then converts each cell to the text the spreadsheet showed. From [js/fileProcessor.js](https://github.com/abdulmanan69/leadslicer/blob/12b5cff6c418dfeab4836cfeecedb6faef540f2f/js/fileProcessor.js):

```js
    /** Convert one worksheet cell to the text the spreadsheet displayed. */
    function cellToText(cell) {
        if (!cell) return '';
        const t = cell.t;
        // ...
        // Dates: always prefer the rendered text so dd/mm/yyyy stays dd/mm/yyyy.
        if (t === 'd') return cell.w ? String(cell.w).trim() : isoFromDate(cell.v);
        // Numbers: use the rendered text only when a real format is attached,
        // otherwise String(v) keeps the full precision that "General" would round.
        if (cell.z && cell.z !== 'General' && typeof cell.w === 'string' && cell.w !== '') {
            return cell.w.trim();
        }
        return String(cell.v);
    }
```

The number branch matters too. A long number in a General column, such as a phone number entered as a number, keeps every digit.

## The tradeoff: text first, types only when sure

Carrying every cell as display text keeps filtering, deduplication and CSV output simple: the filters compare what you saw, and that is what gets written back. The cost lands on Excel output, where text has to become typed cells again, and the exporter only does that when sure. The rule opens `applyColumnFormats` in [js/chunkExporter.js](https://github.com/abdulmanan69/leadslicer/blob/12b5cff6c418dfeab4836cfeecedb6faef540f2f/js/chunkExporter.js):

```js
        for (let c = 0; c < colCount; c++) {
            const meta = formats[c];
            if (!meta || !meta.z) continue;

            const order = meta.isDate ? dateFieldOrder(meta.z) : null;
            if (meta.isDate && !order) continue;      // keep as text — safest
            if (!meta.isDate && !meta.isNumeric) continue;
            // ...
```

`dateFieldOrder` reads the day, month and year order from a format like `dd/mm/yyyy`. It returns null for formats with times or month and weekday names, "in which case the text is written unchanged." Impossible dates such as `31/02` also stay text. The commit message states the policy: "Values that cannot be parsed confidently stay as literal text instead of being guessed at."

In an exported `.xlsx`, that costs:

- Columns formatted like `dd-mmm-yyyy` or `dd/mm/yyyy hh:mm` come out as text that looks the same, not real dates.
- General number columns, and values like `$1,234.50`, are written as text.
- Precision hidden by a format is gone: a cell holding 1234.6 but showing `1,235` comes back holding 1235.
- Each column is rebuilt with its first format, so in a column that mixes date formats a cell can come back reformatted, or as a different date.

What it buys: in a consistently formatted column, every cell shows what it showed before, and nothing is guessed. A wrong guess on `03/04` gives a valid-looking date that is wrong.

CSV skips all this. PapaParse runs without type conversion, so fields stay strings and are written back as is. The file around them is rewritten: output is always comma-separated with CRLF line endings and a UTF-8 BOM, whatever the input delimiter was.

## Other fixes in the same commit

The same message lists other fixes, including:

- **A default got reversed.** The first version skipped deduplication when no identifier column was ticked. Now it keys on all kept columns and says so: "No unique column picked — duplicates were matched on the full row."
- **Choices were lost on Back.** Each step rebuilds its checkboxes on entry, and selections lived only there. They now live in `Set`s in `app.js`, because otherwise "walking Back would silently discard them."
- **The service worker never refreshed.** `addAll` aborted the install on a single 404, and refreshed files went to a different cache from the one being read. The install now caches per file, and `cacheOwnerOf()` routes each refresh to the right cache.

It also replaced the original light/dark toggle with Light, Dark and System modes and six accent colours.

## Try it

Use it at [leadslicer.abdulmanan.tech](https://leadslicer.abdulmanan.tech) or run it locally:

```bash
git clone https://github.com/abdulmanan69/leadslicer.git
cd leadslicer
# then open index.html in a browser
```

Opening the file from disk is enough for slicing. Offline mode needs it served over HTTP, since the page registers `/sw.js` from the site root. It is MIT licensed.

[ToolForge](/blog/toolforge-browser-pdf-tools/) and [CV Studio](/blog/cv-studio-free-resume-builder/) follow the same idea: a job people expect to need a server, done in the browser tab. If your team has a file-wrangling job that eats an afternoon every week, [tell me about it](/#contact).
