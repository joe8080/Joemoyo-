#!/usr/bin/env python3
"""Build a live portfolio tracker workbook: Dashboard + Prices + a tab per holding."""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation

OUT = "/tmp/claude-0/-home-user/de029611-12c7-500a-9a8b-f4dd5e8389f7/scratchpad/build/Portfolio_Tracker.xlsx"

# ---------------------------------------------------------------- source data
# Never Sell pie export, 4 Aug 2026 (supplied by user).
GBPUSD = 1.34499  # FMP forex quote GBPUSD, 4 Aug 2026

HOLDINGS = [
    # ticker, company, sleeve, invested GBP, current value GBP, shares
    ("AMZN", "Amazon.com, Inc.",        "Never Sell", 12204.39, 13618.02, 66.0103),
    ("MSFT", "Microsoft Corporation",   "Never Sell",  5800.47,  7250.23, 20.4311),
    ("UBER", "Uber Technologies, Inc.", "Never Sell",  5608.26,  5831.61, 109.6538),
]

# ------------------------------------------------------------------- styling
FONT = "Arial"
BLUE   = Font(name=FONT, size=10, color="0000FF")               # hardcoded input
BLACK  = Font(name=FONT, size=10)                               # formula
GREEN  = Font(name=FONT, size=10, color="008000")               # cross-sheet link
LABEL  = Font(name=FONT, size=10)
BOLD   = Font(name=FONT, size=10, bold=True)
TITLE  = Font(name=FONT, size=14, bold=True, color="FFFFFF")
SECT   = Font(name=FONT, size=11, bold=True, color="FFFFFF")
HEADF  = Font(name=FONT, size=10, bold=True, color="FFFFFF")
NOTE   = Font(name=FONT, size=9, italic=True, color="808080")

NAVY   = PatternFill("solid", fgColor="1F3864")
SLATE  = PatternFill("solid", fgColor="44546A")
YELLOW = PatternFill("solid", fgColor="FFFF00")   # fill me in
LGREY  = PatternFill("solid", fgColor="F2F2F2")
BANNER = PatternFill("solid", fgColor="D9E1F2")

THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

GBP  = '£#,##0.00;(£#,##0.00);"-"'
GBP0 = '£#,##0;(£#,##0);"-"'
USD  = '$#,##0.00;($#,##0.00);"-"'
PCT  = '0.0%;(0.0%);"-"'
PCT2 = '0.00%;(0.00%);"-"'
SHR  = '#,##0.0000;(#,##0.0000);"-"'
NUM  = '#,##0.00'
MULT = '0.0"x"'
DATE = 'dd/mm/yyyy'

wb = openpyxl.Workbook()


def style_cell(ws, coord, value=None, font=BLACK, fill=None, fmt=None,
               align=None, border=False, comment=None):
    c = ws[coord]
    if value is not None:
        c.value = value
    c.font = font
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    if align:
        c.alignment = Alignment(horizontal=align, vertical="center")
    if border:
        c.border = BOX
    if comment:
        c.comment = Comment(comment, "Portfolio Tracker")
    return c


def banner(ws, row, text, last_col="F", fill=NAVY, font=TITLE, height=22):
    ws.merge_cells(f"A{row}:{last_col}{row}")
    style_cell(ws, f"A{row}", text, font=font, fill=fill, align="left")
    for col in range(1, openpyxl.utils.column_index_from_string(last_col) + 1):
        ws.cell(row=row, column=col).fill = fill
    ws.row_dimensions[row].height = height


def section(ws, row, text, last_col="F"):
    banner(ws, row, text, last_col, fill=SLATE, font=SECT, height=18)


# =============================================================== 1. README
ws = wb.active
ws.title = "README"
ws.sheet_properties.tabColor = "1F3864"
ws.sheet_view.showGridLines = False
for col, w in zip("ABCDEF", [26, 62, 30, 14, 14, 14]):
    ws.column_dimensions[col].width = w

banner(ws, 1, "LIVE PORTFOLIO TRACKER  —  how to use this workbook")
r = 3
style_cell(ws, f"A{r}", "Built", font=BOLD)
style_cell(ws, f"B{r}", "4 August 2026, from your Never Sell pie export.", font=LABEL)
r += 1
style_cell(ws, f"A{r}", "Holdings in v1", font=BOLD)
style_cell(ws, f"B{r}", "AMZN, MSFT, UBER — one tab each. More sleeves get added as we refine.", font=LABEL)
r += 2

section(ws, r, "COLOUR LEGEND  —  what you may type into")
r += 1
legend = [
    ("Yellow fill, blue text", "TYPE HERE. These are your inputs: live prices, EPS, targets, rules.", YELLOW, BLUE),
    ("Blue text, no fill",     "Hardcoded input you can change (opening balances, fees).",           None,   BLUE),
    ("Black text",             "Formula. Do not overtype — it will break the calculation chain.",    None,   BLACK),
    ("Green text",             "Link pulling from another tab in this workbook.",                    None,   GREEN),
]
for name, desc, fill, font in legend:
    style_cell(ws, f"A{r}", name, font=font, fill=fill, border=True)
    style_cell(ws, f"B{r}", desc, font=LABEL, border=True)
    r += 1
r += 1

section(ws, r, "TAB GUIDE")
r += 1
tabs = [
    ("Dashboard",    "Whole-portfolio totals, every holding side by side, weights, and each sell signal."),
    ("Prices",       "The price engine. Update the live price cells here and the entire workbook moves."),
    ("AMZN / MSFT / UBER", "One tab per holding: position, valuation & EPS, sell discipline, dividends, trade history, thesis."),
    ("Transactions", "Master trade log. Every buy and sell goes here once. Shares and average cost are calculated from it — never typed."),
    ("Dividends",    "Dividend log. Feeds income figures on the holding tabs."),
    ("Sell_Rules",   "Your default sell rules in one place. Each holding tab inherits these and can override."),
]
for name, desc in tabs:
    style_cell(ws, f"A{r}", name, font=BOLD, border=True)
    style_cell(ws, f"B{r}", desc, font=LABEL, border=True)
    r += 1
r += 1

section(ws, r, "MAKING THE PRICES LIVE  —  three options, pick one")
r += 1
opts = [
    ("1. Stocks data type",
     "Microsoft 365. On Prices, select A7:A9, then Data > Stocks. Excel converts them to linked "
     "tickers. Then set D7 to  =A7.Price  and fill down. Refresh with Data > Refresh All."),
    ("2. STOCKHISTORY",
     "Microsoft 365. Put this in D7 (as a formula, not text):  "
     "=STOCKHISTORY(A7,TODAY()-5,TODAY(),0,0,1)  and take the last row. Recalculates on file open."),
    ("3. Manual / paste",
     "Works in every version of Excel, including web and Mac. Type or paste the price into D7:D9. "
     "Takes ten seconds and every number in the workbook updates."),
]
for name, desc in opts:
    style_cell(ws, f"A{r}", name, font=BOLD, border=True)
    style_cell(ws, f"B{r}", desc, font=LABEL, border=True)
    ws.row_dimensions[r].height = 42
    ws[f"B{r}"].alignment = Alignment(wrap_text=True, vertical="top")
    r += 1
r += 1
style_cell(ws, f"A{r}", "Note", font=BOLD)
style_cell(ws, f"B{r}",
           "A generated .xlsx cannot ship with prices already wired to a feed — Excel only trusts a live "
           "connection you enable yourself. Options 1 and 2 take one setup step each, then run themselves.",
           font=NOTE)
ws[f"B{r}"].alignment = Alignment(wrap_text=True, vertical="top")
ws.row_dimensions[r].height = 30
r += 2

section(ws, r, "ASSUMPTIONS AND SOURCES  —  read before trusting a number")
r += 1
assumptions = [
    ("Shares, invested, value", "Your Trading 212 Never Sell pie export, Never-sell-2026-08-04T11-15-05.211Z.csv."),
    ("Opening prices (USD)",    "Derived: your GBP value per share x GBP/USD 1.34499. Not a feed print — "
                                "replace with a live price on the Prices tab."),
    ("GBP/USD 1.34499",         "FMP forex quote GBPUSD, 4 August 2026."),
    ("EPS, forward EPS, analyst target",
                                "LEFT BLANK ON PURPOSE. I will not invent company financials. Fill from the "
                                "latest 10-Q or your broker's research tab — every valuation cell below them "
                                "lights up the moment you do."),
    ("52-week high / low",      "Blank. Fill on the Prices tab — the trailing stop depends on the 52w high."),
    ("Sell rules",              "Defaults on Sell_Rules are placeholders I chose, not advice. Set them to your own."),
    ("Fees",                    "Assumed zero on the opening rows. Add real fees per trade in Transactions column I."),
    ("Dividends",               "AMZN, MSFT and UBER: only MSFT currently pays one. Log actual payments in Dividends."),
]
for name, desc in assumptions:
    style_cell(ws, f"A{r}", name, font=BOLD, border=True)
    style_cell(ws, f"B{r}", desc, font=LABEL, border=True)
    ws[f"B{r}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 30 if len(desc) > 90 else 15
    r += 1
r += 1
style_cell(ws, f"A{r}", "Not financial advice. Figures are only as good as the inputs you keep current.", font=NOTE)


# =============================================================== 2. Sell_Rules
sr = wb.create_sheet("Sell_Rules")
sr.sheet_properties.tabColor = "C00000"
sr.sheet_view.showGridLines = False
for col, w in zip("ABCDEF", [38, 14, 62, 14, 14, 14]):
    sr.column_dimensions[col].width = w

banner(sr, 1, "DEFAULT SELL RULES  —  every holding tab inherits these")
SR = {}
r = 3
section(sr, r, "TRIGGER LEVELS")
r += 1
for col, head in zip("ABC", ["Rule", "Level", "What it means"]):
    style_cell(sr, f"{col}{r}", head, font=HEADF, fill=SLATE, border=True)
r += 1
rules = [
    ("take_profit", "Take-profit target (% above avg cost)", 0.50, "Full exit candidate. Price >= avg cost x 1.50."),
    ("trim1",       "Trim level 1 (% above avg cost)",       0.25, "First trim. Take some off the table, let the rest run."),
    ("trim2",       "Trim level 2 (% above avg cost)",       0.40, "Second trim, closer to the full target."),
    ("stop",        "Stop loss (% below avg cost)",          0.20, "Hard exit. Price <= avg cost x 0.80."),
    ("trail",       "Trailing stop (% below 52-week high)",  0.25, "Protects a run-up. Price <= 52w high x 0.75."),
]
for key, label, val, meaning in rules:
    style_cell(sr, f"A{r}", label, font=LABEL, border=True)
    style_cell(sr, f"B{r}", val, font=BLUE, fill=YELLOW, fmt=PCT, border=True, align="center")
    style_cell(sr, f"C{r}", meaning, font=LABEL, border=True)
    SR[key] = f"Sell_Rules!$B${r}"
    r += 1
r += 1
style_cell(sr, f"A{r}", "These are placeholders, not advice — set them to your own discipline.", font=NOTE)
r += 1
style_cell(sr, f"A{r}", "A holding tab can override any level: just type a number over the green link.", font=NOTE)
r += 2

section(sr, r, "SIGNAL PRIORITY  —  the order each holding tab tests")
r += 1
for i, txt in enumerate([
    "1.  No position  ->  NO POSITION",
    "2.  Manual sell price set and reached  ->  SELL - MANUAL TARGET",
    "3.  Price at or below stop loss  ->  SELL - STOP LOSS",
    "4.  Price at or above take-profit  ->  SELL - TARGET HIT",
    "5.  Price at or above trim 2  ->  TRIM 2",
    "6.  Price at or above trim 1  ->  TRIM 1",
    "7.  Price at or below trailing stop  ->  REVIEW - TRAILING STOP",
    "8.  Otherwise  ->  HOLD",
], start=0):
    style_cell(sr, f"A{r+i}", txt, font=LABEL)
r += 9
style_cell(sr, f"A{r}",
           "Stop loss is tested before take-profit so a crash is never masked by a stale target.", font=NOTE)


# =============================================================== 3. Prices
pr = wb.create_sheet("Prices")
pr.sheet_properties.tabColor = "00B050"
pr.sheet_view.showGridLines = False
widths = {"A": 11, "B": 26, "C": 10, "D": 14, "E": 13, "F": 12, "G": 11,
          "H": 13, "I": 13, "J": 13, "K": 12, "L": 13, "M": 11, "N": 11,
          "O": 15, "P": 12, "Q": 13}
for col, w in widths.items():
    pr.column_dimensions[col].width = w

banner(pr, 1, "PRICE ENGINE  —  update the yellow cells and the whole workbook moves", last_col="Q")
FX_ROW = 3
style_cell(pr, "A3", "GBP/USD rate", font=BOLD)
style_cell(pr, "B3", GBPUSD, font=BLUE, fill=YELLOW, fmt='0.00000', align="center",
           comment="Source: FMP forex quote GBPUSD, 4 Aug 2026.\nUpdate whenever you refresh prices.")
style_cell(pr, "C3", "<- every USD figure is converted at this rate", font=NOTE)
style_cell(pr, "A4", "Prices as at", font=BOLD)
style_cell(pr, "B4", "2026-08-04", font=BLUE, fill=YELLOW, align="center")
style_cell(pr, "C4", "<- stamp the date/time you last refreshed", font=NOTE)

PHEAD = 6
headers = [
    ("A", "Ticker"), ("B", "Company"), ("C", "Ccy"), ("D", "Live price"),
    ("E", "Prev close"), ("F", "Day chg"), ("G", "Day chg %"),
    ("H", "52w high"), ("I", "52w low"), ("J", "% off high"),
    ("K", "EPS TTM"), ("L", "EPS fwd"), ("M", "P/E TTM"), ("N", "Fwd P/E"),
    ("O", "Analyst target"), ("P", "Target upside"), ("Q", "Price (GBP)"),
]
for col, head in headers:
    style_cell(pr, f"{col}{PHEAD}", head, font=HEADF, fill=SLATE, border=True, align="center")
pr.row_dimensions[PHEAD].height = 26
pr.freeze_panes = f"A{PHEAD+1}"

PRICE_ROW = {}
r = PHEAD + 1
for tkr, name, sleeve, inv, val, shares in HOLDINGS:
    px_gbp = val / shares
    px_usd = px_gbp * GBPUSD
    PRICE_ROW[tkr] = r
    style_cell(pr, f"A{r}", tkr, font=BOLD, border=True, align="center")
    style_cell(pr, f"B{r}", name, font=LABEL, border=True)
    style_cell(pr, f"C{r}", "USD", font=BLUE, border=True, align="center")
    style_cell(pr, f"D{r}", round(px_usd, 4), font=BLUE, fill=YELLOW, fmt=USD, border=True,
               comment=(f"Derived, not a feed print: your GBP value per share "
                        f"({px_gbp:,.4f}) x GBP/USD {GBPUSD}.\n"
                        f"Source of the GBP value: Never Sell pie export, 4 Aug 2026.\n"
                        "Replace with a live price."))
    style_cell(pr, f"E{r}", None, font=BLUE, fill=YELLOW, fmt=USD, border=True,
               comment="Previous close, in USD. Leave blank if you do not track it.")
    style_cell(pr, f"F{r}", f'=IF(E{r}="","",D{r}-E{r})', font=BLACK, fmt=USD, border=True)
    style_cell(pr, f"G{r}", f'=IFERROR(F{r}/E{r},"")', font=BLACK, fmt=PCT2, border=True)
    style_cell(pr, f"H{r}", None, font=BLUE, fill=YELLOW, fmt=USD, border=True,
               comment="52-week high in USD. The trailing stop on the holding tab depends on this.")
    style_cell(pr, f"I{r}", None, font=BLUE, fill=YELLOW, fmt=USD, border=True,
               comment="52-week low in USD.")
    style_cell(pr, f"J{r}", f'=IFERROR(D{r}/H{r}-1,"")', font=BLACK, fmt=PCT, border=True)
    style_cell(pr, f"K{r}", None, font=BLUE, fill=YELLOW, fmt=USD, border=True,
               comment="Diluted EPS, trailing twelve months, USD.\nSource: latest 10-Q/10-K or your broker.\nLeft blank deliberately — I will not invent financials.")
    style_cell(pr, f"L{r}", None, font=BLUE, fill=YELLOW, fmt=USD, border=True,
               comment="Consensus EPS for the next full year, USD.\nSource: your broker's research tab.")
    style_cell(pr, f"M{r}", f'=IFERROR(D{r}/K{r},"")', font=BLACK, fmt=MULT, border=True)
    style_cell(pr, f"N{r}", f'=IFERROR(D{r}/L{r},"")', font=BLACK, fmt=MULT, border=True)
    style_cell(pr, f"O{r}", None, font=BLUE, fill=YELLOW, fmt=USD, border=True,
               comment="Consensus analyst price target, USD.")
    style_cell(pr, f"P{r}", f'=IFERROR(O{r}/D{r}-1,"")', font=BLACK, fmt=PCT, border=True)
    style_cell(pr, f"Q{r}", f'=IFERROR(IF(C{r}="USD",D{r}/$B${FX_ROW},D{r}),"")',
               font=BLACK, fmt=GBP, border=True)
    r += 1
PLAST = r - 1

pr.conditional_formatting.add(f"F{PHEAD+1}:G{PLAST}",
    CellIsRule(operator="lessThan", formula=["0"], font=Font(name=FONT, size=10, color="C00000")))
pr.conditional_formatting.add(f"F{PHEAD+1}:G{PLAST}",
    CellIsRule(operator="greaterThan", formula=["0"], font=Font(name=FONT, size=10, color="008000")))

r = PLAST + 2
style_cell(pr, f"A{r}", "Yellow = you fill in. Everything black is calculated.", font=NOTE)
r += 1
style_cell(pr, f"A{r}", "EPS, 52-week range and analyst target are blank by design — see README, Assumptions.", font=NOTE)
r += 1
style_cell(pr, f"A{r}", "To wire these to a live feed, see README > Making the prices live.", font=NOTE)


# =============================================================== 4. Transactions
tx = wb.create_sheet("Transactions")
tx.sheet_properties.tabColor = "7030A0"
tx.sheet_view.showGridLines = False
tx_widths = {"A": 12, "B": 10, "C": 9, "D": 13, "E": 15, "F": 10, "G": 15, "H": 14,
             "I": 11, "J": 14, "K": 13, "L": 13, "M": 15, "N": 15, "O": 16, "P": 15, "Q": 30}
for col, w in tx_widths.items():
    tx.column_dimensions[col].width = w

banner(tx, 1, "MASTER TRADE LOG  —  every buy and sell goes here once", last_col="Q")
style_cell(tx, "A2", "Shares held and average cost on every holding tab are calculated from this sheet. "
                     "Add new trades in the next empty row and keep the formulas in columns G to P.", font=NOTE)

THEAD = 3
tx_headers = [
    ("A", "Date", None), ("B", "Ticker", None), ("C", "Type", None),
    ("D", "Shares", None), ("E", "Price/share (native)", None), ("F", "FX (GBP/USD)", None),
    ("G", "Price/share (GBP)", "f"), ("H", "Gross (GBP)", "f"), ("I", "Fees (GBP)", None),
    ("J", "Net cash (GBP)", "f"), ("K", "Signed shares", "f"),
    ("L", "Shares before", "f"), ("M", "Cost basis before", "f"), ("N", "Avg cost before", "f"),
    ("O", "Cost basis impact", "f"), ("P", "Realised P/L (GBP)", "f"), ("Q", "Notes", None),
]
for col, head, _ in tx_headers:
    style_cell(tx, f"{col}{THEAD}", head, font=HEADF, fill=SLATE, border=True, align="center")
    tx[f"{col}{THEAD}"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
tx.row_dimensions[THEAD].height = 30
tx.freeze_panes = f"A{THEAD+1}"

TFIRST = THEAD + 1
TX_ROWS = 60          # room to grow
TLAST = TFIRST + TX_ROWS - 1

dv = DataValidation(type="list", formula1='"BUY,SELL"', allow_blank=True, showDropDown=False)
tx.add_data_validation(dv)
dv.add(f"C{TFIRST}:C{TLAST}")

seed = []
for tkr, name, sleeve, inv, val, shares in HOLDINGS:
    avg_gbp = inv / shares
    seed.append((tkr, shares, round(avg_gbp * GBPUSD, 6)))

for i, row in enumerate(range(TFIRST, TLAST + 1)):
    is_seed = i < len(seed)
    shade = LGREY if (i % 2 == 1) else None

    style_cell(tx, f"A{row}", "2026-08-04" if is_seed else None,
               font=BLUE, fill=shade, border=True, align="center")
    style_cell(tx, f"B{row}", seed[i][0] if is_seed else None,
               font=BLUE, fill=shade, border=True, align="center")
    style_cell(tx, f"C{row}", "BUY" if is_seed else None,
               font=BLUE, fill=shade, border=True, align="center")
    style_cell(tx, f"D{row}", seed[i][1] if is_seed else None,
               font=BLUE, fill=shade, fmt=SHR, border=True)
    style_cell(tx, f"E{row}", seed[i][2] if is_seed else None,
               font=BLUE, fill=shade, fmt=USD, border=True)
    style_cell(tx, f"F{row}", GBPUSD if is_seed else None,
               font=BLUE, fill=shade, fmt='0.00000', border=True)
    style_cell(tx, f"I{row}", 0 if is_seed else None,
               font=BLUE, fill=shade, fmt=GBP, border=True)
    style_cell(tx, f"Q{row}",
               "Opening position from Trading 212 Never Sell pie export, 4 Aug 2026. "
               "Replace with your real trade history when you have it." if is_seed else None,
               font=BLUE if is_seed else BLACK, fill=shade, border=True)

    blank = f'IF($B{row}="","",'
    style_cell(tx, f"G{row}", f'={blank}IFERROR($E{row}/$F{row},0))', font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(tx, f"H{row}", f'={blank}$D{row}*$G{row})', font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(tx, f"J{row}", f'={blank}IF($C{row}="BUY",$H{row}+$I{row},$H{row}-$I{row}))',
               font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(tx, f"K{row}", f'={blank}IF($C{row}="BUY",$D{row},-$D{row}))',
               font=BLACK, fill=shade, fmt=SHR, border=True)

    if row == TFIRST:
        prior_shares = "0"
        prior_cost = "0"
    else:
        prior_shares = f'SUMIFS($K${TFIRST}:$K{row-1},$B${TFIRST}:$B{row-1},$B{row})'
        prior_cost = f'SUMIFS($O${TFIRST}:$O{row-1},$B${TFIRST}:$B{row-1},$B{row})'
    style_cell(tx, f"L{row}", f'={blank}{prior_shares})', font=BLACK, fill=shade, fmt=SHR, border=True)
    style_cell(tx, f"M{row}", f'={blank}{prior_cost})', font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(tx, f"N{row}", f'={blank}IFERROR($M{row}/$L{row},0))', font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(tx, f"O{row}", f'={blank}IF($C{row}="BUY",$J{row},-$D{row}*$N{row}))',
               font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(tx, f"P{row}", f'={blank}IF($C{row}="SELL",$J{row}-$D{row}*$N{row},0))',
               font=BLACK, fill=shade, fmt=GBP, border=True)

tx[f"E{TFIRST}"].comment = Comment(
    "Derived so the opening row reproduces your export exactly:\n"
    "invested GBP / shares x GBP/USD 1.34499.\n"
    "Source: Never Sell pie export, 4 Aug 2026.", "Portfolio Tracker")

r = TLAST + 2
style_cell(tx, f"A{r}", "Average-cost accounting: a SELL is booked against the average cost of the shares held "
                        "before it, and the difference lands in Realised P/L.", font=NOTE)
r += 1
style_cell(tx, f"A{r}", "For a GBP-quoted holding (LGEN, BA, SHEL) put the price in pounds in column E and set FX to 1.", font=NOTE)
r += 1
style_cell(tx, f"A{r}", f"Need more than {TX_ROWS} trades? Copy the last row down — every formula is relative.", font=NOTE)


# =============================================================== 5. Dividends
dvs = wb.create_sheet("Dividends")
dvs.sheet_properties.tabColor = "BF8F00"
dvs.sheet_view.showGridLines = False
for col, w in zip("ABCDEFGHI", [12, 10, 16, 14, 11, 15, 17, 15, 34]):
    dvs.column_dimensions[col].width = w

banner(dvs, 1, "DIVIDEND LOG  —  feeds the income block on each holding tab", last_col="I")
style_cell(dvs, "A2", "Log each payment as it lands. Net GBP is what actually hit the account.", font=NOTE)

DHEAD = 3
for col, head in zip("ABCDEFGHI", ["Date", "Ticker", "Shares at pay date", "Gross (native)",
                                   "FX (GBP/USD)", "Gross (GBP)", "Withholding tax (GBP)",
                                   "Net (GBP)", "Notes"]):
    style_cell(dvs, f"{col}{DHEAD}", head, font=HEADF, fill=SLATE, border=True, align="center")
    dvs[f"{col}{DHEAD}"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
dvs.row_dimensions[DHEAD].height = 30
dvs.freeze_panes = f"A{DHEAD+1}"

DFIRST = DHEAD + 1
DLAST = DFIRST + 39
for i, row in enumerate(range(DFIRST, DLAST + 1)):
    shade = LGREY if (i % 2 == 1) else None
    for col, fmt in (("A", None), ("B", None), ("C", SHR), ("D", USD), ("E", '0.00000'), ("G", GBP)):
        style_cell(dvs, f"{col}{row}", None, font=BLUE, fill=shade, fmt=fmt, border=True)
    blank = f'IF($B{row}="","",'
    style_cell(dvs, f"F{row}", f'={blank}IFERROR($D{row}/$E{row},0))', font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(dvs, f"H{row}", f'={blank}$F{row}-$G{row})', font=BLACK, fill=shade, fmt=GBP, border=True)
    style_cell(dvs, f"I{row}", None, font=BLUE, fill=shade, border=True)

r = DLAST + 2
style_cell(dvs, f"A{r}", "US dividends in a UK ISA are normally taxed at 15% at source with a W-8BEN on file. "
                         "Put that amount in column G.", font=NOTE)
r += 1
style_cell(dvs, f"A{r}", "Of AMZN, MSFT and UBER, only MSFT currently pays a dividend.", font=NOTE)


# =============================================================== 6. Holding tabs
HOLDROW = {}   # ticker -> dict of named rows


# Bounded ranges. Full-column refs (Transactions!$K:$K) are correct but make
# LibreOffice/Excel evaluate a million rows per lookup, which stalls recalc.
def TXR(col):
    return f"Transactions!${col}${TFIRST}:${col}${TLAST}"


def DVR(col):
    return f"Dividends!${col}${DFIRST}:${col}${DLAST}"


# Holding tabs are written before the Dashboard, so the row holding total market
# value has to be known up front. Asserted against the real layout after build.
DASH_MV_ROW = 6

def build_holding(tkr, company, sleeve, invested, value, shares):
    sh = wb.create_sheet(tkr)
    sh.sheet_properties.tabColor = "2E75B6"
    sh.sheet_view.showGridLines = False
    for col, w in zip("ABCDEF", [36, 18, 58, 14, 14, 14]):
        sh.column_dimensions[col].width = w

    banner(sh, 1, f"{tkr}  —  {company}")
    R = {}
    r = 3

    def line(key, label, formula, font=BLACK, fmt=None, note=None, comment=None, fill=None):
        nonlocal r
        style_cell(sh, f"A{r}", label, font=LABEL, border=True)
        style_cell(sh, f"B{r}", formula, font=font, fmt=fmt, border=True,
                   align="right" if fmt else "center", comment=comment, fill=fill)
        if note:
            style_cell(sh, f"C{r}", note, font=NOTE)
        R[key] = r
        r += 1

    px_row = PRICE_ROW[tkr]

    # ---- 1. POSITION
    section(sh, r, "1.  POSITION"); r += 1
    line("ticker",  "Ticker", tkr, font=BOLD)
    line("company", "Company", company, font=LABEL)
    line("sleeve",  "Sleeve / pie", sleeve, font=BLUE, note="Trading 212 pie this sits in")
    line("ccy",     "Quote currency", f"=Prices!$C${px_row}", font=GREEN)
    line("shares",  "Shares held",
         f'=SUMIFS({TXR("K")},{TXR("B")},$B${R["ticker"]})',
         fmt=SHR, note="calculated from the Transactions log — never typed")
    line("invested", "Total invested (GBP)",
         f'=SUMIFS({TXR("O")},{TXR("B")},$B${R["ticker"]})', fmt=GBP)
    line("avgcost", "Average cost per share (GBP)",
         f'=IFERROR($B${R["invested"]}/$B${R["shares"]},0)', fmt=GBP)
    line("pxusd",   "Live price (USD)", f"=Prices!$D${px_row}", font=GREEN, fmt=USD,
         note="update on the Prices tab")
    line("fx",      "GBP/USD", f"=Prices!$B${FX_ROW}", font=GREEN, fmt='0.00000')
    line("pxgbp",   "Price per share (GBP)", f"=Prices!$Q${px_row}", font=GREEN, fmt=GBP)
    line("mv",      "Market value (GBP)", f'=$B${R["shares"]}*$B${R["pxgbp"]}', fmt=GBP)
    line("upl",     "Unrealised P/L (GBP)", f'=$B${R["mv"]}-$B${R["invested"]}', fmt=GBP)
    line("uplpct",  "Unrealised P/L %", f'=IFERROR($B${R["upl"]}/$B${R["invested"]},0)', fmt=PCT)
    line("daychg",  "Day change (GBP)",
         f'=IFERROR($B${R["shares"]}*Prices!$F${px_row}/$B${R["fx"]},0)', fmt=GBP,
         note="needs Prev close on the Prices tab")
    line("daypct",  "Day change %", f'=IFERROR(Prices!$G${px_row},0)', fmt=PCT2)
    line("weight",  "% of portfolio", None, fmt=PCT,
         note="share of total market value")   # formula set below, needs mv row
    line("rpl",     "Realised P/L (GBP)",
         f'=SUMIFS({TXR("P")},{TXR("B")},$B${R["ticker"]})', fmt=GBP)
    line("divrec",  "Dividends received (GBP)",
         f'=SUMIFS({DVR("H")},{DVR("B")},$B${R["ticker"]})', fmt=GBP)
    line("totret",  "Total return (GBP)",
         f'=$B${R["upl"]}+$B${R["rpl"]}+$B${R["divrec"]}', fmt=GBP)
    line("totretp", "Total return %",
         f'=IFERROR($B${R["totret"]}/$B${R["invested"]},0)', fmt=PCT)
    # weight needs the mv row, which `line` only assigns once it has run
    sh[f'B{R["weight"]}'] = f'=IFERROR($B${R["mv"]}/Dashboard!$B${DASH_MV_ROW},0)'
    r += 1

    # ---- 2. VALUATION & EPS
    section(sh, r, "2.  VALUATION AND EPS"); r += 1
    line("eps",     "EPS trailing 12m (USD)", f"=Prices!$K${px_row}", font=GREEN, fmt=USD,
         note="enter on the Prices tab — blank by design, I do not invent financials")
    line("epsfwd",  "EPS forward, next FY (USD)", f"=Prices!$L${px_row}", font=GREEN, fmt=USD,
         note="consensus, from your broker's research tab")
    line("epsgr",   "EPS growth, fwd vs TTM",
         f'=IFERROR($B${R["epsfwd"]}/$B${R["eps"]}-1,"")', fmt=PCT)
    line("pe",      "P/E trailing", f"=Prices!$M${px_row}", font=GREEN, fmt=MULT)
    line("fpe",     "P/E forward", f"=Prices!$N${px_row}", font=GREEN, fmt=MULT)
    line("peg",     "PEG (fwd P/E / growth)",
         f'=IFERROR($B${R["fpe"]}/($B${R["epsgr"]}*100),"")', fmt='0.00',
         note="under 1.0 is the classic cheap-for-its-growth marker")
    line("tgtpe",   "Target P/E you would pay", None, font=BLUE, fmt=MULT, fill=YELLOW,
         note="your multiple — this drives fair value below",
         comment="Type the multiple you think this business deserves, e.g. 28 for a quality compounder.")
    line("fvusd",   "Fair value (USD)",
         f'=IFERROR($B${R["tgtpe"]}*$B${R["epsfwd"]},"")', fmt=USD,
         note="target P/E x forward EPS")
    line("fvgbp",   "Fair value (GBP)",
         f'=IFERROR($B${R["fvusd"]}/$B${R["fx"]},"")', fmt=GBP)
    line("upside",  "Upside to fair value",
         f'=IFERROR($B${R["fvusd"]}/$B${R["pxusd"]}-1,"")', fmt=PCT)
    line("verdict", "Valuation verdict",
         f'=IF($B${R["upside"]}="","enter EPS and target P/E",'
         f'IF($B${R["upside"]}>=0.2,"UNDERVALUED",'
         f'IF($B${R["upside"]}<=-0.1,"OVERVALUED","FAIRLY VALUED")))', font=BOLD)
    line("antgt",   "Analyst price target (USD)", f"=Prices!$O${px_row}", font=GREEN, fmt=USD)
    line("anup",    "Upside to analyst target", f"=IFERROR(Prices!$P${px_row},\"\")", fmt=PCT)
    line("hi52",    "52-week high (USD)", f"=Prices!$H${px_row}", font=GREEN, fmt=USD)
    line("lo52",    "52-week low (USD)", f"=Prices!$I${px_row}", font=GREEN, fmt=USD)
    line("offhi",   "% below 52-week high", f"=IFERROR(Prices!$J${px_row},\"\")", fmt=PCT)
    r += 1

    # ---- 3. SELL DISCIPLINE
    section(sh, r, "3.  SELL DISCIPLINE  —  the exit plan, decided in advance"); r += 1
    line("tp",      "Take-profit target %", f"={SR['take_profit']}", font=GREEN, fmt=PCT,
         note="inherits Sell_Rules — type over it to override")
    line("tpp",     "Take-profit price (GBP)",
         f'=$B${R["avgcost"]}*(1+$B${R["tp"]})', fmt=GBP)
    line("t1",      "Trim level 1 %", f"={SR['trim1']}", font=GREEN, fmt=PCT)
    line("t1p",     "Trim 1 price (GBP)", f'=$B${R["avgcost"]}*(1+$B${R["t1"]})', fmt=GBP)
    line("t2",      "Trim level 2 %", f"={SR['trim2']}", font=GREEN, fmt=PCT)
    line("t2p",     "Trim 2 price (GBP)", f'=$B${R["avgcost"]}*(1+$B${R["t2"]})', fmt=GBP)
    line("sl",      "Stop loss %", f"={SR['stop']}", font=GREEN, fmt=PCT)
    line("slp",     "Stop-loss price (GBP)", f'=$B${R["avgcost"]}*(1-$B${R["sl"]})', fmt=GBP)
    line("tr",      "Trailing stop % off 52w high", f"={SR['trail']}", font=GREEN, fmt=PCT)
    line("trp",     "Trailing stop price (GBP)",
         f'=IFERROR($B${R["hi52"]}/$B${R["fx"]}*(1-$B${R["tr"]}),0)', fmt=GBP,
         note="0 until you enter the 52-week high on the Prices tab")
    line("manual",  "Manual sell price (GBP)", None, font=BLUE, fmt=GBP, fill=YELLOW,
         note="optional hard number that overrides everything above",
         comment="Leave blank to use the percentage rules. Set a price here and it takes priority.")

    signal = (
        f'=IF($B${R["shares"]}=0,"NO POSITION",'
        f'IF(AND($B${R["manual"]}>0,$B${R["pxgbp"]}>=$B${R["manual"]}),"SELL - MANUAL TARGET",'
        f'IF($B${R["pxgbp"]}<=$B${R["slp"]},"SELL - STOP LOSS",'
        f'IF($B${R["pxgbp"]}>=$B${R["tpp"]},"SELL - TARGET HIT",'
        f'IF($B${R["pxgbp"]}>=$B${R["t2p"]},"TRIM 2",'
        f'IF($B${R["pxgbp"]}>=$B${R["t1p"]},"TRIM 1",'
        f'IF(AND($B${R["trp"]}>0,$B${R["pxgbp"]}<=$B${R["trp"]}),"REVIEW - TRAILING STOP",'
        f'"HOLD")))))))'
    )
    style_cell(sh, f"A{r}", "SIGNAL", font=BOLD, fill=BANNER, border=True)
    style_cell(sh, f"B{r}", signal, font=Font(name=FONT, size=12, bold=True),
               fill=BANNER, border=True, align="center")
    style_cell(sh, f"C{r}", "recalculated the moment the price changes", font=NOTE)
    sh.row_dimensions[r].height = 22
    R["signal"] = r
    r += 1

    line("selval",  "Value if sold today (GBP)", f'=$B${R["mv"]}', fmt=GBP)
    line("selfee",  "Estimated selling costs (GBP)", 0, font=BLUE, fmt=GBP, fill=YELLOW,
         note="FX charge / commission — Trading 212 FX fee is 0.15% of the trade",
         comment="Assumed 0. Trading 212 charges a 0.15% FX conversion fee on USD sales.")
    line("selnet",  "Net proceeds if sold (GBP)", f'=$B${R["selval"]}-$B${R["selfee"]}', fmt=GBP)
    line("sellock", "Gain locked in if sold (GBP)",
         f'=$B${R["selnet"]}-$B${R["invested"]}', fmt=GBP)
    line("sellockp", "Gain locked in %",
         f'=IFERROR($B${R["sellock"]}/$B${R["invested"]},0)', fmt=PCT)
    r += 1

    # ---- 4. DIVIDENDS
    section(sh, r, "4.  DIVIDEND INCOME"); r += 1
    line("dps",   "Annual dividend per share (USD)", None, font=BLUE, fmt=USD, fill=YELLOW,
         note="0 if it does not pay one",
         comment="Declared annual dividend per share in USD.\nSource: company investor relations page.")
    line("dyield", "Dividend yield on price",
         f'=IFERROR($B${R["dps"]}/$B${R["pxusd"]},0)', fmt=PCT2)
    line("dyoc",   "Yield on your cost",
         f'=IFERROR($B${R["dps"]}/$B${R["fx"]}/$B${R["avgcost"]},0)', fmt=PCT2,
         note="the number that actually matters once you are in profit")
    line("dinc",   "Estimated annual income (GBP)",
         f'=IFERROR($B${R["shares"]}*$B${R["dps"]}/$B${R["fx"]},0)', fmt=GBP)
    line("dgot",   "Dividends received to date (GBP)", f'=$B${R["divrec"]}', fmt=GBP)
    r += 1

    # ---- 5. TRADE HISTORY
    section(sh, r, "5.  TRADE HISTORY  —  summarised from the Transactions log"); r += 1
    t = f'{TXR("B")},$B${R["ticker"]}'
    line("ntrades", "Number of trades",
         f'=COUNTIFS({TXR("B")},$B${R["ticker"]})', fmt='#,##0')
    line("bought", "Shares bought",
         f'=SUMIFS({TXR("D")},{t},{TXR("C")},"BUY")', fmt=SHR)
    line("sold",   "Shares sold",
         f'=SUMIFS({TXR("D")},{t},{TXR("C")},"SELL")', fmt=SHR)
    line("cashin", "Total cash invested (GBP)",
         f'=SUMIFS({TXR("J")},{t},{TXR("C")},"BUY")', fmt=GBP)
    line("cashout", "Total cash from sales (GBP)",
         f'=SUMIFS({TXR("J")},{t},{TXR("C")},"SELL")', fmt=GBP)
    line("feespaid", "Total fees paid (GBP)",
         f'=SUMIFS({TXR("I")},{t})', fmt=GBP)
    r += 1

    # ---- 6. THESIS
    section(sh, r, "6.  THESIS AND NOTES"); r += 1
    prompts = [
        ("Why I own it", "the one-line reason — if you cannot write it, you should not hold it"),
        ("What would make me sell", "name the broken thing, not a price"),
        ("Key risk", ""),
        ("Next catalyst / earnings date", ""),
        ("Last reviewed", ""),
    ]
    for label, hint in prompts:
        style_cell(sh, f"A{r}", label, font=LABEL, border=True)
        style_cell(sh, f"B{r}", None, font=BLUE, fill=YELLOW, border=True)
        sh.merge_cells(f"B{r}:C{r}")
        style_cell(sh, f"C{r}", None, fill=YELLOW, border=True)
        if hint:
            style_cell(sh, f"D{r}", hint, font=NOTE)
        r += 1

    # conditional formatting
    green_f = Font(name=FONT, size=10, color="008000")
    red_f = Font(name=FONT, size=10, color="C00000")
    for key in ("upl", "uplpct", "totret", "totretp", "rpl", "daychg", "daypct",
                "sellock", "sellockp"):
        rr = R[key]
        sh.conditional_formatting.add(f"B{rr}",
            CellIsRule(operator="lessThan", formula=["0"], font=red_f))
        sh.conditional_formatting.add(f"B{rr}",
            CellIsRule(operator="greaterThan", formula=["0"], font=green_f))

    sig = f'B{R["signal"]}'
    sh.conditional_formatting.add(sig, FormulaRule(
        formula=[f'ISNUMBER(SEARCH("SELL",{sig}))'],
        fill=PatternFill("solid", fgColor="FFC7CE"),
        font=Font(name=FONT, size=12, bold=True, color="9C0006")))
    sh.conditional_formatting.add(sig, FormulaRule(
        formula=[f'ISNUMBER(SEARCH("TRIM",{sig}))'],
        fill=PatternFill("solid", fgColor="FFEB9C"),
        font=Font(name=FONT, size=12, bold=True, color="9C6500")))
    sh.conditional_formatting.add(sig, FormulaRule(
        formula=[f'ISNUMBER(SEARCH("REVIEW",{sig}))'],
        fill=PatternFill("solid", fgColor="FFEB9C"),
        font=Font(name=FONT, size=12, bold=True, color="9C6500")))
    sh.conditional_formatting.add(sig, FormulaRule(
        formula=[f'EXACT({sig},"HOLD")'],
        fill=PatternFill("solid", fgColor="C6EFCE"),
        font=Font(name=FONT, size=12, bold=True, color="006100")))

    vd = f'B{R["verdict"]}'
    sh.conditional_formatting.add(vd, FormulaRule(
        formula=[f'EXACT({vd},"UNDERVALUED")'], font=Font(name=FONT, size=10, bold=True, color="006100")))
    sh.conditional_formatting.add(vd, FormulaRule(
        formula=[f'EXACT({vd},"OVERVALUED")'], font=Font(name=FONT, size=10, bold=True, color="9C0006")))

    HOLDROW[tkr] = R
    return R


for h in HOLDINGS:
    build_holding(*h)


# =============================================================== 7. Dashboard
db = wb.create_sheet("Dashboard", 0)
db.sheet_properties.tabColor = "FF0000"
db.sheet_view.showGridLines = False
db_widths = {"A": 30, "B": 17, "C": 26, "D": 14, "E": 14, "F": 15, "G": 15,
             "H": 15, "I": 12, "J": 11, "K": 13, "L": 24}
for col, w in db_widths.items():
    db.column_dimensions[col].width = w

banner(db, 1, "PORTFOLIO DASHBOARD", last_col="L")
style_cell(db, "A2", "Prices as at", font=BOLD)
style_cell(db, "B2", f"=Prices!$B${4}", font=GREEN, align="center")
style_cell(db, "C2", "update on the Prices tab", font=NOTE)

r = 4
section(db, r, "PORTFOLIO SUMMARY", last_col="L")
r += 1
SUMROW = {}
summary = [
    ("invested", "Total invested (GBP)", GBP0),
    ("mv",       "Current market value (GBP)", GBP0),
    ("upl",      "Unrealised P/L (GBP)", GBP0),
    ("uplpct",   "Unrealised P/L %", PCT),
    ("rpl",      "Realised P/L (GBP)", GBP0),
    ("div",      "Dividends received (GBP)", GBP0),
    ("totret",   "Total return (GBP)", GBP0),
    ("totretp",  "Total return %", PCT),
    ("daychg",   "Day change (GBP)", GBP0),
    ("daypct",   "Day change %", PCT2),
    ("nhold",    "Number of holdings", '#,##0'),
    ("biggest",  "Largest position", None),
]
for key, label, fmt in summary:
    style_cell(db, f"A{r}", label, font=BOLD, fill=LGREY, border=True)
    style_cell(db, f"B{r}", None, font=BLACK, fmt=fmt, border=True, align="right")
    SUMROW[key] = r
    r += 1

r += 1
section(db, r, "HOLDINGS", last_col="L")
r += 1
HHEAD = r
hcols = ["Ticker", "Company", "Sleeve", "Shares", "Avg cost (GBP)", "Price (GBP)",
         "Invested (GBP)", "Market value (GBP)", "Unreal. P/L (GBP)", "P/L %",
         "Weight", "Signal"]
for i, head in enumerate(hcols):
    col = get_column_letter(i + 1)
    style_cell(db, f"{col}{HHEAD}", head, font=HEADF, fill=SLATE, border=True, align="center")
    db[f"{col}{HHEAD}"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
db.row_dimensions[HHEAD].height = 30
db.freeze_panes = f"A{HHEAD+1}"

r = HHEAD + 1
HFIRST = r
for tkr, company, sleeve, inv, val, shares in HOLDINGS:
    R = HOLDROW[tkr]
    cells = [
        ("A", f"='{tkr}'!$B${R['ticker']}", None, BOLD, "center"),
        ("B", f"='{tkr}'!$B${R['company']}", None, GREEN, None),
        ("C", f"='{tkr}'!$B${R['sleeve']}", None, GREEN, "center"),
        ("D", f"='{tkr}'!$B${R['shares']}", SHR, GREEN, None),
        ("E", f"='{tkr}'!$B${R['avgcost']}", GBP, GREEN, None),
        ("F", f"='{tkr}'!$B${R['pxgbp']}", GBP, GREEN, None),
        ("G", f"='{tkr}'!$B${R['invested']}", GBP, GREEN, None),
        ("H", f"='{tkr}'!$B${R['mv']}", GBP, GREEN, None),
        ("I", f"='{tkr}'!$B${R['upl']}", GBP, GREEN, None),
        ("J", f"='{tkr}'!$B${R['uplpct']}", PCT, GREEN, None),
        ("K", f"='{tkr}'!$B${R['weight']}", PCT, GREEN, None),
        ("L", f"='{tkr}'!$B${R['signal']}", None, BOLD, "center"),
    ]
    for col, formula, fmt, font, align in cells:
        style_cell(db, f"{col}{r}", formula, font=font, fmt=fmt, border=True,
                   align=align or "right")
    r += 1
HLAST = r - 1

# total row
style_cell(db, f"A{r}", "TOTAL", font=BOLD, fill=BANNER, border=True)
for col in "BCDEF":
    style_cell(db, f"{col}{r}", None, fill=BANNER, border=True)
for col, fmt in (("G", GBP), ("H", GBP), ("I", GBP)):
    style_cell(db, f"{col}{r}", f"=SUM({col}{HFIRST}:{col}{HLAST})",
               font=BOLD, fill=BANNER, fmt=fmt, border=True, align="right")
style_cell(db, f"J{r}", f"=IFERROR(I{r}/G{r},0)", font=BOLD, fill=BANNER, fmt=PCT,
           border=True, align="right")
style_cell(db, f"K{r}", f"=SUM(K{HFIRST}:K{HLAST})", font=BOLD, fill=BANNER, fmt=PCT,
           border=True, align="right")
style_cell(db, f"L{r}", None, fill=BANNER, border=True)
TOTROW = r
r += 2

style_cell(db, f"A{r}", "Green figures are pulled live from the holding tabs. Change nothing here — "
                        "edit the holding tab or the Prices tab.", font=NOTE)
r += 1
style_cell(db, f"A{r}", "Weight is each position as a share of current market value, not of invested capital.", font=NOTE)

# summary formulas
db[f"B{SUMROW['invested']}"] = f"=G{TOTROW}"
db[f"B{SUMROW['mv']}"] = f"=H{TOTROW}"
db[f"B{SUMROW['upl']}"] = f"=I{TOTROW}"
db[f"B{SUMROW['uplpct']}"] = f"=IFERROR(B{SUMROW['upl']}/B{SUMROW['invested']},0)"
db[f"B{SUMROW['rpl']}"] = f"=SUM({TXR('P')})"
db[f"B{SUMROW['div']}"] = f"=SUM({DVR('H')})"
db[f"B{SUMROW['totret']}"] = (f"=B{SUMROW['upl']}+B{SUMROW['rpl']}+B{SUMROW['div']}")
db[f"B{SUMROW['totretp']}"] = f"=IFERROR(B{SUMROW['totret']}/B{SUMROW['invested']},0)"
db[f"B{SUMROW['daychg']}"] = "=" + "+".join(
    [f"'{t}'!$B${HOLDROW[t]['daychg']}" for t, *_ in HOLDINGS])
db[f"B{SUMROW['daypct']}"] = (f"=IFERROR(B{SUMROW['daychg']}/(B{SUMROW['mv']}-B{SUMROW['daychg']}),0)")
db[f"B{SUMROW['nhold']}"] = f'=COUNTIF(A{HFIRST}:A{HLAST},"?*")'
db[f"B{SUMROW['biggest']}"] = (
    f'=IFERROR(INDEX(A{HFIRST}:A{HLAST},MATCH(MAX(H{HFIRST}:H{HLAST}),H{HFIRST}:H{HLAST},0)),"")')

green_f = Font(name=FONT, size=10, color="008000")
red_f = Font(name=FONT, size=10, color="C00000")
for key in ("upl", "uplpct", "rpl", "totret", "totretp", "daychg", "daypct"):
    cc = f"B{SUMROW[key]}"
    db.conditional_formatting.add(cc, CellIsRule(operator="lessThan", formula=["0"], font=red_f))
    db.conditional_formatting.add(cc, CellIsRule(operator="greaterThan", formula=["0"], font=green_f))
db.conditional_formatting.add(f"I{HFIRST}:J{HLAST}",
    CellIsRule(operator="lessThan", formula=["0"], font=red_f))
db.conditional_formatting.add(f"I{HFIRST}:J{HLAST}",
    CellIsRule(operator="greaterThan", formula=["0"], font=green_f))
db.conditional_formatting.add(f"L{HFIRST}:L{HLAST}", FormulaRule(
    formula=[f'ISNUMBER(SEARCH("SELL",$L{HFIRST}))'],
    fill=PatternFill("solid", fgColor="FFC7CE"), font=Font(name=FONT, size=10, bold=True, color="9C0006")))
db.conditional_formatting.add(f"L{HFIRST}:L{HLAST}", FormulaRule(
    formula=[f'ISNUMBER(SEARCH("TRIM",$L{HFIRST}))'],
    fill=PatternFill("solid", fgColor="FFEB9C"), font=Font(name=FONT, size=10, bold=True, color="9C6500")))
db.conditional_formatting.add(f"L{HFIRST}:L{HLAST}", FormulaRule(
    formula=[f'EXACT($L{HFIRST},"HOLD")'],
    fill=PatternFill("solid", fgColor="C6EFCE"), font=Font(name=FONT, size=10, bold=True, color="006100")))
# data bar on weight
db.conditional_formatting.add(f"K{HFIRST}:K{HLAST}",
    openpyxl.formatting.rule.DataBarRule(start_type="num", start_value=0,
                                         end_type="num", end_value=1, color="638EC6"))

assert SUMROW["mv"] == DASH_MV_ROW, (
    f"holding tabs point weight at Dashboard!B{DASH_MV_ROW}, but market value "
    f"landed on row {SUMROW['mv']}")

# tab order
order = ["Dashboard", "README", "Prices"] + [h[0] for h in HOLDINGS] + \
        ["Transactions", "Dividends", "Sell_Rules"]
wb._sheets = [wb[name] for name in order]
wb.active = 0

# openpyxl writes formulas with no cached results. This tells Excel to compute
# the whole workbook the first time it is opened, so no cell shows blank.
wb.calculation.fullCalcOnLoad = True

wb.save(OUT)
print("written:", OUT)
print("sheets:", wb.sheetnames)
