"""Apply the field-level patch to src/data/CouncilsAuditData2025.csv.

Parses blocks of the form:
  COUNCIL: <name>
  FIELD:   <column>
  -  <python-repr old value>
  +  <python-repr new value>

For each block: verify the target row's current value matches the `-` value,
then replace with the `+` value. Preserves all other columns and row order.
"""
import codecs
import csv
import re
import sys
from pathlib import Path

ROOT = Path("/home/arryn/projects/observableCouncilsAuditMap")
PATCH = ROOT / "CouncilsAuditData2025.patch"
TARGET = ROOT / "src/data/CouncilsAuditData2025.csv"

BLOCK_RE = re.compile(
    r"^COUNCIL:\s*(?P<council>.+?)\n"
    r"FIELD:\s*(?P<field>.+?)\n"
    r"-\s+(?P<old>.+?)\n"
    r"\+\s+(?P<new>.+?)$",
    re.MULTILINE,
)


def unquote(s: str) -> str:
    """Undo Python-repr quoting: strip outer quotes, decode standard escapes."""
    s = s.strip()
    if len(s) < 2 or s[0] not in ("'", '"') or s[-1] != s[0]:
        raise ValueError(f"unquote: not a quoted string: {s[:40]!r}")
    quote = s[0]
    inner = s[1:-1]
    # Decode \n, \t, \\, \xNN, \uNNNN, and escaped same-quote char.
    decoded_bytes, _ = codecs.escape_decode(inner.encode("utf-8"))
    return decoded_bytes.decode("utf-8")


def parse_patch(text: str):
    blocks = []
    for m in BLOCK_RE.finditer(text):
        blocks.append({
            "council": m.group("council").strip(),
            "field": m.group("field").strip(),
            "old": unquote(m.group("old")),
            "new": unquote(m.group("new")),
        })
    return blocks


def main():
    blocks = parse_patch(PATCH.read_text(encoding="utf-8"))
    print(f"Parsed {len(blocks)} patch blocks")

    with open(TARGET, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)

    by_council = {r["Council"].strip(): r for r in rows}

    applied = 0
    mismatches = []
    missing = []
    for b in blocks:
        row = by_council.get(b["council"])
        if row is None:
            missing.append(b["council"])
            continue
        current = row.get(b["field"], "") or ""
        if current != b["old"]:
            mismatches.append((b["council"], b["field"], current, b["old"]))
            continue
        row[b["field"]] = b["new"]
        applied += 1

    if mismatches:
        print(f"\n{len(mismatches)} mismatches — current target value differs from patch '-' value:")
        for council, field, current, expected in mismatches:
            print(f"  {council} / {field}")
            print(f"    expected: {expected[:120]!r}")
            print(f"    current:  {current[:120]!r}")
    if missing:
        print(f"\n{len(missing)} councils not found in target: {missing}")

    if mismatches or missing:
        print("\nAborting: no changes written. Resolve mismatches first.")
        sys.exit(1)

    with open(TARGET, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, quoting=csv.QUOTE_MINIMAL,
                           lineterminator="\r\n")
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"\nApplied {applied} changes to {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
