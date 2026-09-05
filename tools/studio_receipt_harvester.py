#!/usr/bin/env python3
"""
Studio Receipt Harvester
========================

Pulls every studio-gear receipt out of a mailbox and writes a ledger CSV.

Pipeline
--------
1. Query each vendor in VENDORS (Gmail search syntax, or IMAP FROM filters).
2. Keep only receipt-shaped mail (order / receipt / invoice / payment / confirmation)
   and drop marketing, feedback requests, tracking pings and cart reminders.
3. Download every PDF attachment into ./receipts/<vendor>/ and read its text.
4. Pull the largest "total"-labelled figure from the PDF text, falling back to
   the email body, and write one ledger row per order.
5. Optionally push the ledger straight into a Google Sheet tab.

Backends
--------
* Gmail  -> Google OAuth (Desktop app credentials.json, one-time browser sign-in)
* IMAP   -> any IMAP mailbox, e.g. AOL (imap.aol.com) with an app password

Usage
-----
    python tools/studio_receipt_harvester.py                    # Gmail, all vendors
    python tools/studio_receipt_harvester.py --since 2021-01-01
    python tools/studio_receipt_harvester.py --vendor reverb --vendor sxpro
    python tools/studio_receipt_harvester.py --sheet <SPREADSHEET_ID> --tab Ledger
    python tools/studio_receipt_harvester.py --imap-host imap.aol.com \
        --imap-user you@aol.com            # password from RECEIPTS_IMAP_PASS env
    python tools/studio_receipt_harvester.py --selftest         # no network

Environment
-----------
    RECEIPTS_CREDENTIALS   path to Google OAuth client file (default credentials.json)
    RECEIPTS_TOKEN         path to cached OAuth token      (default token.json)
    RECEIPTS_IMAP_PASS     IMAP password / app password for --imap-host
"""

from __future__ import annotations

import argparse
import base64
import csv
import email
import email.policy
import html
import imaplib
import json
import os
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable, Optional

# --------------------------------------------------------------------------- #
# Vendor catalogue
# --------------------------------------------------------------------------- #
# name -> dict(
#   senders: list of sender domains / addresses (used for Gmail from: and IMAP FROM)
#   gmail_extra: optional extra Gmail query fragment (e.g. marketplace payouts)
# )
VENDORS: dict[str, dict] = {
    "reverb": {"senders": ["info@reverb.com", "support@reverb.com"]},
    "sxpro": {
        "senders": ["sxpro.co.uk"],
        "gmail_extra": '(from:paypal.co.uk "Studioxchange")',
    },
    "gear4music": {"senders": ["gear4music.com"]},
    "native_instruments": {"senders": ["native-instruments.com"]},
    "bax": {"senders": ["bax-shop.co.uk", "bax-shop.nl", "bax-shop.com"]},
    "andertons": {"senders": ["andertons.co.uk"]},
    "avid": {"senders": ["noreply@avid.com", "avid.com"]},
    "celemony": {"senders": ["celemony.com"]},
    "universal_audio": {"senders": ["uaudio.com"]},
    "waves": {"senders": ["waves.com"]},
    "plugin_boutique": {"senders": ["pluginboutique.com"]},
    "thomann": {"senders": ["thomann.de"]},
    "ssl": {"senders": ["solidstatelogic.com"]},
    "studiocare": {"senders": ["studiocare.com"]},
    "studiospares": {"senders": ["studiospares.com", "email-studiospares.com"]},
    "izotope": {"senders": ["izotope.com"]},
    "fabfilter": {"senders": ["fabfilter.com"]},
    "arturia": {"senders": ["arturia.com"]},
    "sweetwater": {"senders": ["sweetwater.com"]},
    "kmr": {"senders": ["kmraudio.com"]},
    "funky_junk": {"senders": ["funky-junk.com"]},
}

# Subject / body must match one of these to count as a receipt.
RECEIPT_WORDS = re.compile(
    r"\b(order|receipt|invoice|payment|confirmation|confirmed|purchase|"
    r"despatch|dispatch|shipped|shipping confirmation|your goods|thank you for your order)\b",
    re.I,
)
# Anything matching these in the SUBJECT is thrown away.
NOISE_SUBJECT = re.compile(
    r"(newsletter|sale\b|deal|% off|discount|voucher|coupon|feedback|review|"
    r"rate |how did we do|share your experience|abandoned|in your cart|left something|"
    r"we.?re ready when you are|pre-?order now|last chance|black friday|cyber|"
    r"password|reset|welcome to|new arrivals|now available|update now available|"
    r"tracking has been added|is on its way|will be delivered|delivery time|"
    r"message about|you have an offer|offer for .* has been accepted|unpaid|"
    r"transaction failed|subscription has been paused|auto-renews|renewing|"
    r"wishlist|quote awaits|custom .* quote)",
    re.I,
)
# Lines that look like a total. Ordered from strongest to weakest signal.
TOTAL_LINE = re.compile(
    r"(grand total|order total|total amount paid|amount paid|you paid|total paid|"
    r"total \(including|order summary total|\btotal\b)",
    re.I,
)
NOT_A_TOTAL = re.compile(
    r"(sub\s*-?total|total savings|total payments|total saved|you saved|"
    r"monthly payments|^\s*vat\b|^\s*tax\b|discount)",
    re.I,
)
# Amount grammar: either grouped thousands (1,285.00 / 1.285,00 / 1 285.00) or a plain
# run of digits with an optional 1-2 digit decimal (2500.00 / 208.8 / 464,95).
_AMT = r"\d{1,3}(?:[,.\s]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?"
MONEY = re.compile(
    rf"(?P<cur>£|\$|€|GBP|USD|EUR)\s?(?P<amt>{_AMT})"
    rf"|(?P<amt2>{_AMT})\s?(?P<cur2>GBP|USD|EUR)\b",
    re.I,
)
# Lines where the label is unambiguous: accept even if VAT/tax also appears on the line.
STRONG_TOTAL = re.compile(
    r"(grand total|order total|total amount paid|amount paid|you paid|total paid|total \(incl)",
    re.I,
)
# Marketing senders never carry receipts, whatever the subject says.
NOISE_SENDER = re.compile(
    r"(newsletter|news@|hello@info|marketing@|promo|mailer|private-relay|"
    r"e\.bax-shop|hi\.avid|hello\.avid|email\.pmtonline|e\.sweetwater|hello\.izotope)",
    re.I,
)
ORDER_REF = re.compile(
    r"(?:order|invoice|receipt|ref(?:erence)?|transaction)\s*(?:number|no\.?|id|#)?\s*[:#]?\s*"
    r"(?P<ref>[A-Z]{0,3}[-#]?\d{4,}[A-Z0-9-]*|[A-Z0-9]{8,})",
    re.I,
)
CURRENCY_MAP = {"£": "GBP", "$": "USD", "€": "EUR", "gbp": "GBP", "usd": "USD", "eur": "EUR"}


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class LedgerRow:
    date: str
    vendor: str
    order_ref: str
    item_summary: str
    currency: str
    total: Optional[float]
    total_source: str          # pdf | body | none
    confidence: str            # high | medium | low
    subject: str
    sender: str
    message_id: str
    pdf_paths: str
    notes: str = ""

    def csv_row(self) -> dict:
        d = asdict(self)
        d["total"] = "" if self.total is None else f"{self.total:.2f}"
        return d


CSV_FIELDS = [f for f in LedgerRow.__dataclass_fields__]


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
def html_to_text(raw: str) -> str:
    """Cheap HTML -> text: drop scripts/styles, tags, collapse whitespace, keep line breaks."""
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", raw)
    raw = re.sub(r"(?i)</td>|</th>", " | ", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in raw.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def parse_amount(text: str) -> Optional[float]:
    """Normalise '1,285.00', '464,95', '1.285,00', '1 285.00' -> float."""
    t = text.strip().replace(" ", "")
    if not t:
        return None
    # Decide decimal separator: the last '.' or ',' followed by 1-2 digits.
    m = re.search(r"([.,])(\d{1,2})$", t)
    if m:
        dec = m.group(1)
        whole = t[: m.start()]
        whole = re.sub(r"[.,]", "", whole)
        try:
            return float(f"{whole}.{m.group(2)}")
        except ValueError:
            return None
    t = re.sub(r"[.,]", "", t)
    try:
        return float(t)
    except ValueError:
        return None


def money_in(line: str) -> list[tuple[str, float]]:
    out = []
    for m in MONEY.finditer(line):
        cur = m.group("cur") or m.group("cur2") or ""
        amt = m.group("amt") or m.group("amt2") or ""
        val = parse_amount(amt)
        if val is None:
            continue
        out.append((CURRENCY_MAP.get(cur.lower(), cur.upper()), val))
    return out


def extract_total(text: str) -> tuple[Optional[float], str, str]:
    """
    Return (total, currency, confidence).
    Strategy: the largest amount on a line that mentions a total (and isn't a
    subtotal / VAT / savings / finance-instalment line). Fall back to the largest
    amount anywhere in the text with low confidence.
    """
    best: Optional[tuple[float, str]] = None
    for line in text.splitlines():
        if not TOTAL_LINE.search(line):
            continue
        if not STRONG_TOTAL.search(line) and NOT_A_TOTAL.search(line):
            continue
        for cur, val in money_in(line):
            if best is None or val > best[0]:
                best = (val, cur)
    if best:
        return best[0], best[1], "high"
    # Fallback: 'Total' label on one line and the figure on the next (table layouts)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.fullmatch(r"\s*(order |grand )?total:?\s*", line, re.I) and i + 1 < len(lines):
            for cur, val in money_in(lines[i + 1]):
                return val, cur, "medium"
    every = [mv for ln in lines for mv in money_in(ln)]
    if every:
        cur, val = max(every, key=lambda cv: cv[1])
        return val, cur, "low"
    return None, "", "low"


def extract_order_ref(subject: str, text: str) -> str:
    for hay in (subject, text[:4000]):
        m = ORDER_REF.search(hay)
        if m:
            return m.group("ref").strip("#:- ")
    return ""


def summarise_items(text: str, subject: str) -> str:
    """Best-effort product line: first '1 x Foo' / 'Qty' style line, else the subject."""
    for line in text.splitlines():
        if re.match(r"^\s*\d+\s*[x×]\s+\S", line):
            return line.strip()[:120]
        if re.search(r"\b(thank you for ordering|one item purchased from)\b", line, re.I):
            continue
    m = re.search(r"your order of (.+?) on reverb", subject, re.I)
    if m:
        return m.group(1)[:120]
    return subject[:120]


def is_receipt(subject: str, body: str, sender: str = "") -> bool:
    if NOISE_SENDER.search(sender) or NOISE_SUBJECT.search(subject):
        return False
    return bool(RECEIPT_WORDS.search(subject) or RECEIPT_WORDS.search(body[:2000]))


def pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("pypdf not installed - PDF totals will be skipped", file=sys.stderr)
        return ""
    try:
        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! could not read {path.name}: {exc}", file=sys.stderr)
        return ""


# --------------------------------------------------------------------------- #
# Mail abstraction
# --------------------------------------------------------------------------- #
@dataclass
class Mail:
    message_id: str
    subject: str
    sender: str
    date: datetime
    body: str
    attachments: list[tuple[str, bytes]] = field(default_factory=list)  # (filename, data)


class GmailBackend:
    SCOPES_RO = ["https://www.googleapis.com/auth/gmail.readonly"]
    SCOPES_SHEET = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, credentials: str, token: str, want_sheets: bool):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        scopes = self.SCOPES_RO + (self.SCOPES_SHEET if want_sheets else [])
        creds = None
        if os.path.exists(token):
            creds = Credentials.from_authorized_user_file(token, scopes)
        if not creds or not creds.valid or not set(scopes) <= set(creds.scopes or []):
            if creds and creds.expired and creds.refresh_token and set(scopes) <= set(creds.scopes or []):
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials):
                    sys.exit(
                        f"Missing {credentials}. Create a Desktop-app OAuth client in Google Cloud "
                        "(Gmail API enabled) and download it as credentials.json."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(credentials, scopes)
                creds = flow.run_local_server(port=0)
            Path(token).write_text(creds.to_json())
        self.creds = creds
        self.svc = build("gmail", "v1", credentials=creds, cache_discovery=False)

    @staticmethod
    def query_for(vendor: str, spec: dict, since: Optional[str]) -> str:
        froms = " OR ".join(f"from:{s}" for s in spec["senders"])
        q = f"({froms})"
        if spec.get("gmail_extra"):
            q = f"({q} OR {spec['gmail_extra']})"
        q += " -in:spam -in:trash -category:promotions"
        if since:
            q += f" after:{since.replace('-', '/')}"
        return q

    def search(self, query: str) -> Iterable[str]:
        page = None
        while True:
            resp = (
                self.svc.users()
                .messages()
                .list(userId="me", q=query, pageToken=page, maxResults=100)
                .execute()
            )
            for m in resp.get("messages", []):
                yield m["id"]
            page = resp.get("nextPageToken")
            if not page:
                break

    def fetch(self, msg_id: str) -> Mail:
        msg = self.svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        plain, htm, atts = [], [], []

        def walk(part):
            mime = part.get("mimeType", "")
            body = part.get("body", {})
            fname = part.get("filename")
            if fname and body.get("attachmentId"):
                if fname.lower().endswith(".pdf") or mime == "application/pdf":
                    data = (
                        self.svc.users()
                        .messages()
                        .attachments()
                        .get(userId="me", messageId=msg_id, id=body["attachmentId"])
                        .execute()
                    )
                    atts.append((fname, base64.urlsafe_b64decode(data["data"])))
            elif body.get("data"):
                text = base64.urlsafe_b64decode(body["data"]).decode("utf-8", "replace")
                (plain if mime == "text/plain" else htm if mime == "text/html" else []).append(text)
            for sub in part.get("parts", []) or []:
                walk(sub)

        walk(msg["payload"])
        body = "\n".join(plain) if plain else html_to_text("\n".join(htm))
        ts = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=timezone.utc)
        return Mail(msg_id, headers.get("subject", ""), headers.get("from", ""), ts, body, atts)


class ImapBackend:
    def __init__(self, host: str, user: str, password: str, folder: str = "INBOX"):
        self.conn = imaplib.IMAP4_SSL(host)
        self.conn.login(user, password)
        self.conn.select(folder, readonly=True)

    @staticmethod
    def query_for(vendor: str, spec: dict, since: Optional[str]) -> list[str]:
        # IMAP has no OR-chain sugar; we return one criterion per sender and union results.
        crit = []
        for s in spec["senders"]:
            c = f'FROM "{s}"'
            if since:
                c += " SINCE " + datetime.strptime(since, "%Y-%m-%d").strftime("%d-%b-%Y")
            crit.append(c)
        return crit

    def search(self, criteria: list[str]) -> Iterable[str]:
        seen = set()
        for c in criteria:
            typ, data = self.conn.search(None, c)
            if typ != "OK":
                continue
            for uid in data[0].split():
                if uid not in seen:
                    seen.add(uid)
                    yield uid.decode()

    def fetch(self, uid: str) -> Mail:
        typ, data = self.conn.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(data[0][1], policy=email.policy.default)
        plain, htm, atts = [], [], []
        for part in msg.walk():
            ctype = part.get_content_type()
            fname = part.get_filename()
            if fname and (fname.lower().endswith(".pdf") or ctype == "application/pdf"):
                atts.append((fname, part.get_payload(decode=True) or b""))
            elif ctype == "text/plain":
                plain.append(part.get_content())
            elif ctype == "text/html":
                htm.append(part.get_content())
        body = "\n".join(plain) if plain else html_to_text("\n".join(htm))
        try:
            ts = parsedate_to_datetime(msg["Date"])
        except Exception:  # noqa: BLE001
            ts = datetime.now(timezone.utc)
        return Mail(f"imap-{uid}", msg["Subject"] or "", msg["From"] or "", ts, body, atts)


# --------------------------------------------------------------------------- #
# Harvest
# --------------------------------------------------------------------------- #
def harvest(backend, vendors: dict[str, dict], since: Optional[str], out_dir: Path,
            save_pdfs: bool = True) -> list[LedgerRow]:
    rows: list[LedgerRow] = []
    seen_refs: set[tuple[str, str]] = set()
    for vendor, spec in vendors.items():
        query = backend.query_for(vendor, spec, since)
        ids = list(backend.search(query))
        print(f"[{vendor}] {len(ids)} messages matched")
        kept = 0
        for mid in ids:
            mail = backend.fetch(mid)
            body = html.unescape(mail.body)
            if not is_receipt(mail.subject, body, mail.sender):
                continue
            ref = extract_order_ref(mail.subject, body)
            key = (vendor, ref) if ref else (vendor, mail.message_id)
            if key in seen_refs:
                continue
            seen_refs.add(key)

            pdf_paths, pdf_blob = [], ""
            if save_pdfs and mail.attachments:
                vdir = out_dir / "receipts" / vendor
                vdir.mkdir(parents=True, exist_ok=True)
                for fname, data in mail.attachments:
                    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", fname)[:80]
                    p = vdir / f"{mail.date:%Y-%m-%d}_{mail.message_id[:10]}_{safe}"
                    p.write_bytes(data)
                    pdf_paths.append(str(p))
                    pdf_blob += "\n" + pdf_text(p)

            total, cur, conf, source = None, "", "low", "none"
            if pdf_blob.strip():
                total, cur, conf = extract_total(pdf_blob)
                source = "pdf" if total is not None else "none"
            if total is None:
                total, cur, conf = extract_total(body)
                source = "body" if total is not None else "none"

            rows.append(
                LedgerRow(
                    date=mail.date.strftime("%Y-%m-%d"),
                    vendor=vendor,
                    order_ref=ref,
                    item_summary=summarise_items(body, mail.subject),
                    currency=cur or "GBP",
                    total=total,
                    total_source=source,
                    confidence=conf,
                    subject=mail.subject[:160],
                    sender=mail.sender[:120],
                    message_id=mail.message_id,
                    pdf_paths=";".join(pdf_paths),
                )
            )
            kept += 1
        print(f"[{vendor}] kept {kept} receipt(s)")
    rows.sort(key=lambda r: (r.date, r.vendor))
    return rows


def write_csv(rows: list[LedgerRow], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r.csv_row())
    print(f"wrote {len(rows)} rows -> {path}")


def push_to_sheet(rows: list[LedgerRow], creds, spreadsheet_id: str, tab: str) -> None:
    import gspread

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(tab)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab, rows=max(100, len(rows) + 10), cols=len(CSV_FIELDS))
    values = [CSV_FIELDS] + [[r.csv_row()[f] for f in CSV_FIELDS] for r in rows]
    ws.update("A1", values)
    print(f"pushed {len(rows)} rows -> sheet {spreadsheet_id} / {tab}")


# --------------------------------------------------------------------------- #
# Self-test (no network) - exercises the parsers on real vendor layouts
# --------------------------------------------------------------------------- #
SELFTEST_CASES = [
    ("Reverb table", "| Subtotal | £1,250.00 |\n| Shipping | £35.00 |\n| Total | £1,285.00 |", 1285.00, "GBP"),
    ("Reverb GBP suffix", "| Delivery | £60.00 |\n| Total | £760.00GBP |", 760.00, "GBP"),
    ("Gear4music entity", "Sub Total VAT: &#163;77.58\nGrand Total: &#163;470.99", 470.99, "GBP"),
    ("Gear4music finance trap", "Grand Total: &#163;519.99\nMonthly Payments: &#163;18.87\nTotal Payments: &#163;679.32", 519.99, "GBP"),
    ("SX Pro", "Subtotal\n£199.00\nShipping\n£0.00\nOrder Total\n£199.00", 199.00, "GBP"),
    ("Avid", "Subtotal\n£174\nTax\n£34.8\nTotal:\n£208.8", 208.80, "GBP"),
    ("UA USD", "Subtotal $149.99\nTaxes $30.00\nTotal $179.99 USD", 179.99, "USD"),
    ("Bax comma decimal", "| Subtotal: | £ 464,00 |\n| Total (including £ 77,50 VAT) | £ 464,95 |", 464.95, "GBP"),
    ("Andertons", "| Subtotal: | £1,079.00 |\n| Delivery: | £7.99 |\n| Order Total: | £1,086.99 |", 1086.99, "GBP"),
    ("Thomann", "| Order total | GBP 755.00 |", 755.00, "GBP"),
    ("Plugin Boutique", "VAT: £19.37 TOTAL AMOUNT PAID: £116.24", 116.24, "GBP"),
    ("PayPal", "You paid £2500.00 GBP to Studioxchange Ltd", 2500.00, "GBP"),
]


def selftest() -> int:
    failures = 0
    for name, text, want, cur in SELFTEST_CASES:
        got, gcur, conf = extract_total(html.unescape(text))
        ok = got is not None and abs(got - want) < 0.005 and gcur == cur
        print(f"{'PASS' if ok else 'FAIL'}  {name:24s} -> {got} {gcur} ({conf})")
        failures += 0 if ok else 1
    noise = [("⚡ Bag a Geezer Butler signed head ⚡", "hello@info.reverb.com"),
             ("SX Pro: How did we do?", "feedbackrequest@feefo.com"),
             ("Your Transaction Failed", "webmail@spark.uaudio.com"),
             ("We're ready when you are – see what's waiting in your cart",
              "newsletter@news.native-instruments.com")]
    for s, sender in noise:
        ok = not is_receipt(s, "order", sender)
        print(f"{'PASS' if ok else 'FAIL'}  noise filter: {s[:40]}")
        failures += 0 if ok else 1
    keep = [("Your order W11257980 has been placed", "info@gear4music.com"),
            ("Order Confirmation", "noreply@sxpro.co.uk"),
            ("Invoice 90492882", "noreply.invoice.int@native-instruments.com"),
            ("Receipt for your payment to Studioxchange Ltd", "service@paypal.co.uk")]
    for s, sender in keep:
        ok = is_receipt(s, "", sender)
        print(f"{'PASS' if ok else 'FAIL'}  receipt filter: {s[:40]}")
        failures += 0 if ok else 1
    print("selftest:", "OK" if failures == 0 else f"{failures} failure(s)")
    return failures


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Harvest studio-gear receipts into a ledger CSV")
    ap.add_argument("--since", help="only mail after this date, YYYY-MM-DD")
    ap.add_argument("--out", default="studio_ledger.csv", help="CSV path (default studio_ledger.csv)")
    ap.add_argument("--out-dir", default=".", help="where receipts/ PDFs are stored")
    ap.add_argument("--vendor", action="append", help="limit to vendor key(s); repeatable")
    ap.add_argument("--no-pdf", action="store_true", help="skip attachment download")
    ap.add_argument("--sheet", help="Google Sheet ID to push the ledger into")
    ap.add_argument("--tab", default="Studio Ledger", help="worksheet tab name (default 'Studio Ledger')")
    ap.add_argument("--imap-host", help="use IMAP instead of Gmail API, e.g. imap.aol.com")
    ap.add_argument("--imap-user")
    ap.add_argument("--imap-folder", default="INBOX")
    ap.add_argument("--selftest", action="store_true", help="run parser checks and exit")
    ap.add_argument("--list-vendors", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if args.list_vendors:
        print("\n".join(VENDORS))
        return 0

    vendors = VENDORS
    if args.vendor:
        unknown = [v for v in args.vendor if v not in VENDORS]
        if unknown:
            sys.exit(f"unknown vendor(s): {unknown}. Use --list-vendors.")
        vendors = {k: VENDORS[k] for k in args.vendor}

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    creds = None
    if args.imap_host:
        pw = os.environ.get("RECEIPTS_IMAP_PASS")
        if not (args.imap_user and pw):
            sys.exit("--imap-user and RECEIPTS_IMAP_PASS are required for IMAP")
        backend = ImapBackend(args.imap_host, args.imap_user, pw, args.imap_folder)
    else:
        backend = GmailBackend(
            os.environ.get("RECEIPTS_CREDENTIALS", "credentials.json"),
            os.environ.get("RECEIPTS_TOKEN", "token.json"),
            want_sheets=bool(args.sheet),
        )
        creds = backend.creds

    rows = harvest(backend, vendors, args.since, out_dir, save_pdfs=not args.no_pdf)
    write_csv(rows, Path(args.out))

    if args.sheet:
        if creds is None:
            # IMAP run + sheet push still needs Google creds for Sheets only.
            g = GmailBackend(
                os.environ.get("RECEIPTS_CREDENTIALS", "credentials.json"),
                os.environ.get("RECEIPTS_TOKEN", "token.json"),
                want_sheets=True,
            )
            creds = g.creds
        push_to_sheet(rows, creds, args.sheet, args.tab)

    total_gbp = sum(r.total for r in rows if r.total is not None and r.currency == "GBP")
    print(f"GBP total across {len(rows)} receipts: £{total_gbp:,.2f}")
    print(json.dumps({"rows": len(rows), "gbp_total": round(total_gbp, 2)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
