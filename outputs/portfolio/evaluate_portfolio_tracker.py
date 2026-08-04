#!/usr/bin/env python3
"""Evaluate every formula with a pure-Python engine and report error values.

Stands in for recalc.py, which cannot run here — LibreOffice hangs in this
sandbox even on a trivial file.
"""
import re
import sys
import warnings

warnings.filterwarnings("ignore")
import formulas  # noqa: E402

PATH = "/tmp/claude-0/-home-user/de029611-12c7-500a-9a8b-f4dd5e8389f7/scratchpad/build/Portfolio_Tracker.xlsx"

ERRS = ("#NAME?", "#REF!", "#DIV/0!", "#VALUE!", "#NULL!", "#NUM!", "#N/A")

print("loading and building the dependency graph ...")
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


bad = {}
cells = 0
values = {}
for key, val in sol.items():
    m = re.match(r"^'\[.*?\]([^']+)'!([A-Z]{1,3}\d+)$", key)
    if not m:
        continue
    sheet, coord = m.group(1), m.group(2)
    v = unwrap(val)
    cells += 1
    values[(sheet.upper(), coord)] = v
    if isinstance(v, str) and v.strip() in ERRS:
        bad.setdefault(v.strip(), []).append(f"{sheet}!{coord}")

print(f"cells evaluated: {cells}")
if bad:
    print("\nFORMULA ERRORS FOUND:")
    for err, locs in bad.items():
        print(f"  {err}  x{len(locs)}: {', '.join(locs[:15])}")
    sys.exit(1)
print("formula errors: 0\n")


def get(sheet, coord):
    return values.get((sheet.upper(), coord))


print("computed values pulled straight out of the evaluated workbook")
print("-" * 74)
rows = [("AMZN", 13618.02, 1413.63), ("MSFT", 7250.23, None), ("UBER", 5831.61, 223.35)]
print(f"{'tab':6} {'shares':>11} {'invested':>11} {'avg cost':>10} {'mkt value':>11} "
      f"{'P/L':>10} {'weight':>8}  signal")
ok = True
for tab, exp_mv, _ in rows:
    shares = get(tab, "B8")
    inv = get(tab, "B9")
    avg = get(tab, "B10")
    mv = get(tab, "B14")
    pl = get(tab, "B15")
    wt = get(tab, "B19")
    sig = get(tab, "B55")
    try:
        print(f"{tab:6} {shares:11.4f} {inv:11.2f} {avg:10.4f} {mv:11.2f} "
              f"{pl:10.2f} {wt:8.2%}  {sig}")
    except Exception:
        print(f"{tab:6} shares={shares} inv={inv} avg={avg} mv={mv} pl={pl} wt={wt} sig={sig}")
    if not isinstance(mv, (int, float)) or abs(mv - exp_mv) > 0.01:
        print(f"   !! {tab} market value {mv} != export {exp_mv}")
        ok = False

print("-" * 74)
print(f"{'Dashboard':22} invested {get('Dashboard','B5')}")
print(f"{'':22} value    {get('Dashboard','B6')}")
print(f"{'':22} P/L      {get('Dashboard','B7')}   ({get('Dashboard','B8')})")
print(f"{'':22} total rt {get('Dashboard','B11')}")
print(f"{'':22} holdings {get('Dashboard','B15')}  largest {get('Dashboard','B16')}")

wsum = sum(get(t, "B19") for t, _, _ in rows if isinstance(get(t, "B19"), (int, float)))
print(f"\nweights sum to {wsum:.6f} (must be 1.0)")
if abs(wsum - 1.0) > 1e-6:
    print("   !! weights do not sum to 100%")
    ok = False

sys.exit(0 if ok else 1)
