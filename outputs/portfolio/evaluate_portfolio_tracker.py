#!/usr/bin/env python3
"""Evaluate every formula with a pure-Python engine and report error cells.

Stands in for recalc.py: LibreOffice hangs in this sandbox even on a trivial file.
Rows are located by their label so the checks cannot drift as the layout changes.
"""
import re
import sys
import warnings

warnings.filterwarnings("ignore")
import formulas  # noqa: E402

PATH = "/tmp/claude-0/-home-user/de029611-12c7-500a-9a8b-f4dd5e8389f7/scratchpad/build/Portfolio_Tracker.xlsx"
ERRS = ("#NAME?", "#REF!", "#DIV/0!", "#VALUE!", "#NULL!", "#NUM!", "#N/A", "#ERROR!")
TICKERS = ("AMZN", "MSFT", "UBER")

import openpyxl  # noqa: E402
book = openpyxl.load_workbook(PATH)

# ---------------------------------------------------- banned-function screen
BANNED = re.compile(r"\b(XLOOKUP|XMATCH|SORT|FILTER|UNIQUE|SEQUENCE|TEXTJOIN|IFS"
                    r"|SWITCH|MAXIFS|MINIFS|STOCKHISTORY|LET|LAMBDA)\s*\(")
banned = []
for ws in book.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("="):
                for m in BANNED.finditer(c.value.upper()):
                    banned.append(f"{ws.title}!{c.coordinate} uses {m.group(1)}()")
print(f"[1] banned/spilling functions: {len(banned)}")
for b in banned:
    print("   ", b)

# label -> row, per sheet
def rowof(sheet, label):
    ws = book[sheet]
    for row in ws.iter_rows(min_col=1, max_col=1):
        if row[0].value == label:
            return row[0].row
    raise KeyError(f"{sheet}: no row labelled {label!r}")

print("\nloading and building the dependency graph ...")
xl = formulas.ExcelModel().loads(PATH).finish()
print("calculating ...")
sol = xl.calculate()
print("done\n")


def unwrap(v):
    try:
        while hasattr(v, "value"):
            v = v.value
        if hasattr(v, "tolist"):
            v = v.tolist()
        while isinstance(v, (list, tuple)) and len(v) == 1:
            v = v[0]
    except Exception:
        pass
    return v


vals, bad, n = {}, {}, 0
for key, val in sol.items():
    m = re.match(r"^'\[.*?\]([^']+)'!([A-Z]{1,3}\d+)$", key)
    if not m:
        continue
    v = unwrap(val)
    vals[(m.group(1).upper(), m.group(2))] = v
    n += 1
    if isinstance(v, str) and v.strip() in ERRS:
        bad.setdefault(v.strip(), []).append(f"{m.group(1)}!{m.group(2)}")

print(f"[2] cells evaluated: {n}")
if bad:
    print("    FORMULA ERRORS:")
    for e, locs in bad.items():
        print(f"      {e} x{len(locs)}: {', '.join(locs[:20])}")
else:
    print("    formula errors: 0")


def V(sheet, label):
    return vals.get((sheet.upper(), f"B{rowof(sheet, label)}"))


ok = not bad and not banned

# ------------------------------------------------------------- position block
print("\n[3] position and valuation")
print(f"    {'':6} {'shares':>10} {'invested':>10} {'avg':>8} {'price':>8} "
      f"{'value':>10} {'P/L':>9} {'wt':>6} {'fwd P/E':>8} {'PEG':>6}")
tot_mv = tot_inv = 0.0
for t in TICKERS:
    sh, inv = V(t, "Shares held"), V(t, "Total invested (GBP)")
    avg, px = V(t, "Average cost per share (GBP)"), V(t, "Price per share (GBP)")
    mv, pl = V(t, "Market value (GBP)"), V(t, "Unrealised P/L (GBP)")
    wt, pe = V(t, "% of portfolio"), V(t, "Forward P/E on Year 1 EPS")
    peg = V(t, "PEG (fwd P/E / EPS growth)")
    tot_mv += mv; tot_inv += inv
    print(f"    {t:6} {sh:10.4f} {inv:10.2f} {avg:8.2f} {px:8.2f} {mv:10.2f} "
          f"{pl:9.2f} {wt:6.1%} {pe:8.1f} {peg:6.2f}")
print(f"    {'TOTAL':6} {'':10} {tot_inv:10.2f} {'':8} {'':8} {tot_mv:10.2f} "
      f"{tot_mv-tot_inv:9.2f}")

# cost basis must still tie to the pie export exactly
EXPECT_INV = {"AMZN": 12204.39, "MSFT": 5800.47, "UBER": 5608.26}
for t, exp in EXPECT_INV.items():
    got = V(t, "Total invested (GBP)")
    if abs(got - exp) > 0.01:
        print(f"    !! {t} invested {got:.2f} != export {exp}")
        ok = False
print("    cost basis ties to the pie export")

wsum = sum(V(t, "% of portfolio") for t in TICKERS)
if abs(wsum - 1.0) > 1e-6:
    print(f"    !! weights sum to {wsum}")
    ok = False
print(f"    weights sum to {wsum:.6f}")

# ------------------------------------------------------------ 3-year targets
print("\n[4] your 3-year price targets")
print(f"    {'':6} {'tgt P/E':>8} {'now $':>9} {'Y1 $':>9} {'Y2 $':>9} {'Y3 $':>9} "
      f"{'up Y3':>8} {'req p.a.':>9}  status")
for t in TICKERS:
    pe = V(t, "Your target P/E")
    now = V(t, "Live price (USD)")
    a = V(t, "Target price FY2027 (USD)")
    b = V(t, "Target price FY2028 (USD)")
    c = V(t, "Target price FY2029 (USD)")
    up, cg = V(t, "Upside to Year 3 target"), V(t, "Required annual return to Year 3")
    st = V(t, "TARGET STATUS")
    print(f"    {t:6} {pe:8.2f} {now:9.2f} {a:9.2f} {b:9.2f} {c:9.2f} "
          f"{up:8.1%} {cg:9.1%}  {st}")
    if not (a < b < c):
        print(f"    !! {t} targets not increasing across the three years")
        ok = False

# Year 1 target should land on the analyst consensus, by construction
print("\n[5] Year 1 target vs analyst consensus (should match by construction)")
est = book["Estimates"]
for i, t in enumerate(TICKERS):
    cons = est[f"L{5+i}"].value
    y1 = V(t, "Target price FY2027 (USD)")
    flag = "ok" if abs(y1 - cons) < 0.01 else "MISMATCH"
    if flag != "ok":
        ok = False
    print(f"    {t:6} target {y1:8.2f}   consensus {cons:8.2f}   {flag}")

# ------------------------------------------------------------------- signals
print("\n[6] sell signals")
for t in TICKERS:
    print(f"    {t:6} price {V(t,'Price per share (GBP)'):8.2f}  "
          f"stop {V(t,'Stop-loss price (GBP)'):7.2f}  "
          f"trim1 {V(t,'Trim 1 price (GBP)'):7.2f}  "
          f"trail {V(t,'Trailing stop price (GBP)'):7.2f}  -> {V(t,'SIGNAL')}")

# ------------------------------------------------------------------ dashboard
print("\n[7] dashboard and targets")
for lbl in ["Total invested (GBP)", "Current market value (GBP)", "Unrealised P/L (GBP)",
            "Unrealised P/L %", "Day change (GBP)", "Number of holdings",
            "Largest position", "Projected value at FY2029 (GBP)", "% of £1m goal today"]:
    v = vals.get(("DASHBOARD", f"B{rowof('Dashboard', lbl)}"))
    print(f"    {lbl:42} {v}")

print()
for lbl in ["Value today (GBP)", "Projected value FY2027 (GBP)", "Projected value FY2028 (GBP)",
            "Projected value FY2029 (GBP)", "Total gain to FY2029 (GBP)",
            "Portfolio return needed p.a."]:
    v = vals.get(("TARGETS", f"B{rowof('Targets', lbl)}"))
    print(f"    {lbl:42} {v}")

print()
for lbl in ["Target portfolio value (GBP)", "% of goal reached today", "Gap to goal (GBP)",
            "% of goal at FY2029", "Years to goal at that return, no new money",
            "Monthly contribution to hit goal by FY2029"]:
    v = vals.get(("TARGETS", f"B{rowof('Targets', lbl)}"))
    print(f"    {lbl:42} {v}")

# reconciliation
print("\n[8] reconciliation vs the pie export")
prc = book["Prices"]
rr = None
for row in prc.iter_rows(min_col=1, max_col=1):
    if row[0].value == "Ticker" and row[0].row > 10:
        rr = row[0].row + 1
for i, t in enumerate(TICKERS):
    exp = vals.get(("PRICES", f"B{rr+i}"))
    live = vals.get(("PRICES", f"C{rr+i}"))
    d = vals.get(("PRICES", f"D{rr+i}"))
    p = vals.get(("PRICES", f"E{rr+i}"))
    print(f"    {t:6} export {exp:10.2f}   workbook {live:10.2f}   diff {d:8.2f} ({p:6.2%})")

print("\n" + ("ALL CHECKS PASSED" if ok else "CHECKS FAILED"))
sys.exit(0 if ok else 1)
