# Studio Receipt Harvester

`tools/studio_receipt_harvester.py` pulls every studio-gear receipt out of a mailbox,
reads the totals out of email bodies and PDF invoices, and writes a ledger CSV
(optionally straight into a Google Sheet). Run it once to build the ledger, then
schedule it monthly and the ledger stays live.

## One-time setup (Gmail)

1. Go to https://console.cloud.google.com and create a project (any name).
2. **APIs & Services > Library**: enable **Gmail API**. Enable **Google Sheets API** too if
   you want `--sheet`.
3. **APIs & Services > OAuth consent screen**: External, add your Gmail address as a test user.
4. **APIs & Services > Credentials > Create credentials > OAuth client ID > Desktop app**.
   Download the JSON and save it as `credentials.json` in the repo root.
5. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

6. First run opens a browser tab for Google sign-in once. The token is cached in
   `token.json` and refreshed automatically afterwards.

   ```bash
   python tools/studio_receipt_harvester.py --since 2020-01-01
   ```

   Output: `studio_ledger.csv` plus `receipts/<vendor>/*.pdf`.

## Push straight into a Google Sheet

```bash
python tools/studio_receipt_harvester.py --since 2020-01-01 \
    --sheet 1AbC...yourSheetId... --tab "Studio Ledger"
```

The tab is cleared and rewritten on every run, so the sheet always mirrors the CSV.

## AOL (or any IMAP mailbox)

```bash
export RECEIPTS_IMAP_PASS='your-aol-app-password'
python tools/studio_receipt_harvester.py --imap-host imap.aol.com \
    --imap-user you@aol.com --out studio_ledger_aol.csv
```

AOL needs an app password (AOL account > Security > Generate app password).

## Useful flags

| Flag | What it does |
|---|---|
| `--vendor reverb --vendor sxpro` | limit to specific vendors (`--list-vendors` shows keys) |
| `--since YYYY-MM-DD` | only mail after that date |
| `--no-pdf` | skip attachment download (faster, body totals only) |
| `--out-dir /path` | where `receipts/` PDFs go |
| `--selftest` | run the parser checks with no network |

## Ledger columns

`date, vendor, order_ref, item_summary, currency, total, total_source, confidence,
subject, sender, message_id, pdf_paths, notes`

* `total_source` is `pdf` when the figure came from an attached invoice, `body` when it
  came from the email text.
* `confidence` is `high` when a "total"-labelled line was found, `medium` for a
  table-layout total, `low` when it fell back to the largest amount in the text. Eyeball
  the low ones.

## Adding a vendor

Add an entry to `VENDORS` in the script:

```python
"my_shop": {"senders": ["myshop.co.uk"]},
```

`senders` are domains or addresses; they become Gmail `from:` terms or IMAP `FROM` filters.

## Monthly automation (n8n)

Create a Schedule trigger (1st of the month) feeding an **Execute Command** node:

```bash
cd /path/to/Joemoyo- && python tools/studio_receipt_harvester.py \
    --since 2020-01-01 --sheet <SHEET_ID> --tab "Studio Ledger"
```

`token.json` must already exist from a manual first run (n8n can't do the browser sign-in).
