---
title: InvoiceApp — Offline Invoicing and Stock Control
date: 2026-08-25
excerpt: Invoices, quotations, inventory, payments and returns in one local SQLite file. No server, no internet, no subscription.
cover: posts/images/invoiceapp-offline-invoicing-small-business.png
tags: python, sqlite, desktop, business, pdf
---

# InvoiceApp — Offline Invoicing and Stock Control

Small shops run on a monthly subscription they resent, or on a spreadsheet nobody
trusts. Both fail the same way: the subscription needs internet and a card that
keeps working, and the spreadsheet lets you sell fifty units of something you have
thirty of.

**[InvoiceApp](https://github.com/abdulmanan69/InvoiceApp)** is a standalone
Windows desktop app that keeps customers, vendors, products, stock, purchases,
invoices, quotations, payments and returns in **one local SQLite file**. No
server, no internet, no subscription. Default currency is Pakistani Rupee
(PKR, "Rs"), changeable in Settings.

## Documents that behave like documents

Invoices and quotations share a searchable, filterable list and an editor with
product auto-fill that shows what's actually in stock. Per-line tax override,
percentage or fixed discount, live totals, duplicate, print, PDF export — and
**one-click convert quotation → invoice**, which is the step every shop does daily
and most software makes you retype.

**Seven PDF templates** — Modern, Classic, Minimal, Bold, Corporate, Elegant,
Compact — in A4 or Letter. Big company name and bill-to details, logo, itemised
table with grid borders, totals, status badge, notes and terms, bank details, and
**signature boxes** (prepared by / received by, with names). Long item lists
paginate with the table header repeated, which sounds trivial until you've
received page 3 of an invoice with no column labels.

Every document also gets a *Show / hide sections & columns* panel: turn off the
status badge, due date, currency, logo, any table column, the discount, tax or
paid lines, notes, terms, bank details, signatures or the grid. Defaults live in
Settings → PDF layout. Different customers want different paperwork, and hardcoding
one opinion means someone maintains a second template forever.

Numbering is prefix + counter + padding per document type, editable, with
duplicates rejected.

## Money, computed rather than typed

Payments support partial amounts and guard against overpayment. "Mark as paid"
writes a real payment row instead of flipping a flag, so the payments log and the
invoice can't disagree. There's a global payments log with CSV export.

Status is **always computed** — Unpaid, Partially Paid, Paid, Overdue. Nobody sets
it by hand, so nobody forgets to.

Customer returns credit the invoice, dropping the balance, and can optionally put
items back into stock. A return that fixes the money but not the shelf is how
inventory drifts away from reality.

## Inventory that says no

Products carry a **cost price** (what you paid) and a **sale price**, with margin
shown to owners. Purchases from vendors add stock and update the cost price;
returns to vendor remove it.

The rule that matters: **invoices cannot sell more than is in stock.** Fifty in
stock means fifty is the maximum on an invoice. Owners can allow negative stock in
Settings if their business genuinely works that way, but the default is the safe
one. Editing an existing invoice frees its own stock first, so changing a line
from 10 to 12 doesn't fail against stock the same invoice is holding.

On top: stock levels, low-stock alerts (global threshold or per product), stock
adjustments, a full movement history, and best sellers by quantity, revenue and
gross profit over a date range.

## Roles, because not everyone should see the margin

First run creates the **owner**. Owners see everything — payments, purchases, costs,
profit, vendors, settings, users. **Employees** work with invoices, quotations,
customers, products (sale prices only) and can view stock — no payments, no costs,
no deletes.

That split isn't paranoia, it's ordinary: the person at the counter needs to issue
an invoice and should not be able to see what you paid the vendor, or quietly
delete a document.

The owner dashboard shows outstanding, paid this month, overdue, open quotes, gross
profit, stock value, low stock, purchases, best sellers and an activity feed. The
employee dashboard shows counts only.

## Nothing business-specific is hardcoded

Company profile and logo, currency, tax defaults, numbering, payment methods,
default notes and terms, template and page size, bill-to heading, signature labels
and names, PDF defaults, low-stock rules, live theme colours, backup and restore.

That list *is* the product. Software for small businesses usually dies on the one
assumption the author never questioned — a currency symbol, a tax rate, a document
label — and at that point it's someone else's tool you're fighting.

## Why SQLite and why offline

One file holds everything. Backup is copying it. Restore is copying it back. There
is no connection string, no migration server, no "the internet is down so we can't
bill anyone."

And because it's a real database rather than a spreadsheet, the constraints above —
stock limits, computed status, atomic payments — are actually enforced instead of
being a convention everyone violates when it's busy.

## Run from source

```bat
python -m pip install -r requirements.txt
```

Source: [github.com/abdulmanan69/InvoiceApp](https://github.com/abdulmanan69/InvoiceApp).
If your business needs something shaped like this — or the web version of it —
[get in touch](/#contact).
