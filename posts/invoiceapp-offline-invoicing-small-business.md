---
title: InvoiceApp — Offline Invoicing and Stock Control
date: 2026-08-25
updated: 2026-11-14
excerpt: A Windows desktop app that keeps invoices, stock and payments in one local SQLite file, with optional Supabase sync between PCs.
cover: posts/images/invoiceapp-offline-invoicing-small-business.png
tags: python, sqlite, desktop, business, pdf
---

# InvoiceApp — Offline Invoicing and Stock Control

[InvoiceApp](https://github.com/abdulmanan69/InvoiceApp) is a Windows desktop app I built for small shops. Customers, vendors, products, stock, purchases, invoices, quotations, payments and returns all live in one local SQLite file. It is Python 3.11+ with Tkinter and ttkbootstrap for the UI and reportlab for the PDFs, with Pakistani Rupee as the default currency. There is also a short [project page](/projects/invoiceapp/).

## The problem

The job is ordinary counter work: quote a price, turn the quote into an invoice, take part of the money now and the rest later, accept a return, restock from a vendor. It has to run on a shop PC with no server and no internet, and it has to refuse the mistakes a spreadsheet allows, like selling fifty units of something you have thirty of.

The second problem came later. A shop with more than one PC needs them to agree, but billing cannot stop when the connection drops. Versions 2.7 to 3.0 add cloud sync through Supabase without making the local file depend on it.

## How it is put together

`db.py` owns the schema, migrations and settings. `models.py` holds the business logic as plain functions over dicts. `pdf_templates.py` draws the documents, each screen is its own `ui_*.py`, and `cloud.py` plus `sync.py` handle Supabase. One `sqlite3` connection, opened with `check_same_thread=False` and guarded by an `RLock`, is shared by the UI and the background sync thread.

Business values are settings rows, not constants. The comment above `DEFAULT_SETTINGS` states the rule: "Every brandable / business-specific value lives here, never in the UI or PDF code."

### Stock is a ledger

The `products` table has no stock column. Purchases, sales, restocked customer returns, vendor returns and manual adjustments each write a signed row to `stock_movements`, and the level is the sum:

```python
def stock_level(db: Database, product_id, exclude_ref: tuple | None = None) -> float:
    sql = "SELECT SUM(qty) FROM stock_movements WHERE product_id = ?"
    params: list = [product_id]
    if exclude_ref:
        sql += " AND NOT (ref_type = ? AND ref_id = ?)"
        params += list(exclude_ref)
    return round2(db.scalar(sql, params, 0) or 0)
```

From [models.py](https://github.com/abdulmanan69/InvoiceApp/blob/5a6601e20d4081a45e2a97c1779ac24be7fcc94b/models.py) at v3.0.0.

`exclude_ref` is what makes editing work. Change an invoice line from 10 to 12 and the stock check leaves out that invoice's own movements, so it does not fail against stock the invoice is already holding. `save_document` then replaces those movements in the same transaction as the line items. Unless the owner turns on `allow_negative_stock`, an invoice that needs more than is on hand raises a `StockError` naming each short line.

### Money is derived, not typed

Invoice status is never stored. `compute_status` works it out on every read from the total, payments plus return credits, and the due date. It checks Paid, then Overdue, then Partially Paid, then Unpaid, so a partly paid invoice past its due date shows as Overdue.

`add_payment` stops an amount above the remaining balance with an `OverpaymentError`, which the payment dialog turns into an explicit "record it anyway?" question. "Mark as paid" records a payment for whatever is left, so the payments log and the invoice cannot disagree. Each saved line copies the product's SKU and cost price "so profit and PDFs stay stable later".

### PDFs and roles

There are eight reportlab templates, Ledger being the newest, in A4 or Letter. The items table uses `repeatRows=1`, so long invoices repeat the column header on every page.

Accounts are owner or employee, with PBKDF2-SHA256 password hashes. Roles are enforced by the UI, not by `models.py`: `main.py` never builds the Vendors, Payments and Settings pages for an employee, and the documents page only adds Delete and the payment buttons for owners.

## Sync without giving up offline

The `sync.py` docstring sets the rule: "Local SQLite stays the source of truth." Phase A (`9a65061`) prepared the database and synced nothing. Phase B (`b86e6a4`) synced customers only. Phase C (`5a6601e`, v3.0.0) covers all 11 tables.

SQLite triggers append every local insert, update and delete to a `sync_outbox` table. Pulled rows already carry a UUID and are written with a `sync_suppress` flag set, so the triggers do not queue them again. With auto-sync on, a daemon thread runs every 30 seconds: it pushes the outbox, then pulls rows newer than a per-table cursor.

Integer ids differ per machine, so every foreign key crosses the wire as the parent row's UUID and is translated back on arrival. Tables are pulled parents first, and a child that arrives before its parent stops that table's pull until the next cycle.

On Supabase each entity is one table with a `jsonb` `data` column, "so this schema never has to change when the app adds fields", per `SUPABASE_SETUP.sql`. A server trigger stamps `updated_at` "regardless of each PC's clock", and conflicts are last-write-wins by that timestamp, except that a local row still waiting in the outbox beats an incoming one.

## The tradeoff: duplicate invoice numbers

Numbering is local. `next_number` reads a counter from settings and checks only the local `documents` table, which has `UNIQUE (doc_type, number)`. Two PCs offline at the same time can both issue INV-0007, and the second to arrive on either machine cannot be inserted as is.

Blocking numbering until a PC is online would defeat offline billing. Renumbering the incoming invoice would change a number that may already be printed. The v3.0.0 commit message records the choice I made instead: "UNIQUE number collisions from offline PCs are kept by tagging the later arrival (INV-0007-ab12)."

```python
    def _write_row(self, t: str, cols: list[str], uid: str, r: dict, data: dict) -> bool:
        vals = [data.get(c) for c in cols]
        local = self.db.query_one(f"SELECT id FROM {t} WHERE uuid = ?", (uid,))
        try:
            self._exec_row(t, cols, vals, uid, r, local)
            return True
        except sqlite3.IntegrityError as e:
            # two PCs can mint the same invoice/purchase/return number while offline; keep both
            # rows by tagging the later arrival's number
            if "UNIQUE" in str(e).upper() and data.get("number"):
                data["number"] = f"{data['number']}-{uid[:4]}"
                # ...
```

From [sync.py](https://github.com/abdulmanan69/InvoiceApp/blob/5a6601e20d4081a45e2a97c1779ac24be7fcc94b/sync.py) at v3.0.0.

Nothing is lost, and `test_duplicate_offline_numbers_both_survive` checks that both rows exist. The cost: the rename happens while `sync_suppress` is on, so the rename itself is never queued for push. Each PC keeps its own document as INV-0007 and shows the other with a suffix, so one number points at different invoices on different machines. The stock rule has the same limit, since the check reads the local file and only counts sales from other PCs once they have synced.

## What the commit history shows

The public history is 29 commits. v1.0 (`8c846b7`) had invoices, quotations, payments and three PDF templates. v2.0 (`421e64f`) added roles, inventory, returns and seven templates. The Ledger template (`7780eb0`) needed two follow-up fixes for its footer overlapping the table and the totals (`0c3ebbd`, `4fdcfd6`).

One approach changed during sync. Phase B soft-deleted customers, which meant adding `deleted = 0` to customer queries. Phase C added AFTER DELETE triggers that write tombstones instead, "so models' hard deletes + FK cascades sync without touching any query." Customers still use the soft delete.

The cloud work also produced real bugs:

- The `members` access policies queried `members` itself, and Supabase answered with an infinite-recursion 500. Routing those checks through `SECURITY DEFINER` helpers fixed it (`c0a9257`).
- Supabase rotates refresh tokens, so when the UI and the background sync refreshed at once, one got "400 Refresh Token Not Found". `cloud_refresh` now takes a lock and re-reads the stored session (`cc85e79`).
- `cloud.py` uses only `urllib`, "no extra dependency". Cloudflare in front of `api.supabase.com` rejected the default Python-urllib User-Agent with "403 error code: 1010", so every request now sends its own (`3b08759`).

## Run it

```bat
python -m pip install -r requirements.txt
python main.py
```

Data lives in `data\invoice_app.db` next to `main.py` or the exe. `python -m unittest tests.test_flow -v` runs the end-to-end tests. `tests/test_sync.py` runs the sync engine against an in-memory fake of Supabase, with deliberately different local ids on each "PC".

If your shop needs something shaped like this, [get in touch](/#contact).
