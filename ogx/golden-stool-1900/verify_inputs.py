#!/usr/bin/env python3
"""Verify the Golden Stool build inputs on the box against manifest_inputs.json.

Run on the machine that holds /workspace/ogx-productions/golden-stool-1900:

    python3 verify_inputs.py manifest_inputs.json [--root /workspace/ogx-productions/golden-stool-1900]

Writes verify_report.md and verify_report.json next to the manifest and exits
non-zero if a required input is missing or its hash does not match. A locked
narration that fails its hash stops the build: do not record VO from it.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def resolve(root, rel):
    return rel if os.path.isabs(rel) else os.path.join(root, rel)


def check(item, root):
    path = resolve(root, item["path"])
    row = {"id": item["id"], "path": path, "version": item.get("version", ""),
           "required": item.get("required", False), "notes": []}
    if not os.path.isfile(path):
        row["status"] = "MISSING"
        return row
    actual = sha256(path)
    row["sha256"] = actual
    expected = item.get("sha256")
    prefix = item.get("sha256_prefix")
    if expected and expected != "record":
        row["status"] = "OK" if actual == expected else "HASH MISMATCH"
        if actual != expected:
            row["notes"].append(f"expected {expected}")
    elif prefix:
        row["status"] = "OK (prefix)" if actual.startswith(prefix) else "HASH MISMATCH"
        if not actual.startswith(prefix):
            row["notes"].append(f"expected prefix {prefix}")
    else:
        row["status"] = "RECORDED"
        row["notes"].append("no hash in hub; recorded now")

    if "expect_words" in item:
        with open(path, encoding="utf-8") as f:
            words = len(f.read().split())
        # Word-count method used by the crew is not recorded; hash is authoritative.
        row["notes"].append(f"{words} whitespace tokens (hub says {item['expect_words']} words)")
    if "expect_rows" in item:
        with open(path, newline="", encoding="utf-8") as f:
            rows = sum(1 for r in csv.reader(f) if any(c.strip() for c in r)) - 1
        flag = "" if rows == item["expect_rows"] else "  <-- CHECK"
        row["notes"].append(f"{rows} data rows (expected {item['expect_rows']}){flag}")
    if "expect_text" in item:
        with open(path, encoding="utf-8", errors="replace") as f:
            found = item["expect_text"] in f.read()
        row["notes"].append(f"'{item['expect_text']}' {'found' if found else 'NOT FOUND'}")
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--root")
    args = ap.parse_args()
    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)
    root = args.root or manifest["box_root"]
    rows = [check(item, root) for item in manifest["inputs"]]

    stale = [p for p in manifest.get("do_not_build_from", []) if os.path.exists(resolve(root, p))]
    bad = [r for r in rows if r["required"] and r["status"] in ("MISSING", "HASH MISMATCH")]
    narration = next(r for r in rows if r["id"] == "NARRATION")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out_dir = os.path.dirname(os.path.abspath(args.manifest))
    lines = [f"# Input verification — {manifest['episode']} — {stamp}", "",
             f"Root: `{root}`", "",
             "| ID | Status | Version | sha256 | Notes |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['status']} | {r['version']} | `{r.get('sha256', '-')}` | "
                     f"{'; '.join(r['notes'])} |")
    lines += ["", f"Obsolete files present (not used): {', '.join(stale) or 'none'}", "",
              f"**Narration lock:** {narration['status']}",
              f"**Result:** {'BLOCKED — ' + ', '.join(r['id'] for r in bad) if bad else 'PASS — build may proceed'}"]
    with open(os.path.join(out_dir, "verify_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out_dir, "verify_report.json"), "w", encoding="utf-8") as f:
        json.dump({"checked_at": stamp, "root": root, "rows": rows, "stale_present": stale,
                   "blocked_by": [r["id"] for r in bad]}, f, indent=2)
    print("\n".join(lines))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
