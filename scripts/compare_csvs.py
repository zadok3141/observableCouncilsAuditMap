"""Compare naturaljustice.csv against src/data/CouncilsAuditData2025.csv.

Produces:
  - compare_report.md  — human-readable diff
  - CouncilsAuditData2025.naturaljustice.csv — target updated with naturaljustice values
  - CouncilsAuditData2025.patch — unified diff to apply those updates

Rules applied to reduce noise:
  - naturaljustice.csv bytes: leading 0xff stripped; raw 0x19 treated as apostrophe.
  - Whitespace collapsed; dashes (-,–,—) unified for comparison.
  - Type/Opinion fields compared case-insensitively with a synonym table.
  - Empty naturaljustice value never overwrites a populated target value.
  - Target columns with no counterpart in naturaljustice.csv are preserved as-is
    (Latitude, Longitude, Description 8).
"""
import csv
import io
import re
from pathlib import Path

ROOT = Path("/home/arryn/projects/observableCouncilsAuditMap")
SRC_NJ = ROOT / "naturaljustice.csv"
SRC_TG = ROOT / "src/data/CouncilsAuditData2025.csv"
OUT_MD = ROOT / "compare_report.md"
OUT_CSV = ROOT / "CouncilsAuditData2025.naturaljustice.csv"
OUT_PATCH = ROOT / "CouncilsAuditData2025.patch"

NJ_INDEX_TO_TARGET = {
    0: "Council",
    2: "Financial year",
    3: "Opinion type",
    4: "Type 1", 5: "Nature 1", 6: "Description 1",
    7: "Type 2", 8: "Nature 2", 9: "Description 2",
    10: "Type 3", 11: "Nature 3", 12: "Description 3",
    13: "Type 4", 14: "Nature 4", 15: "Description 4",
    16: "Type 5", 17: "Nature 5", 18: "Description 5",
    19: "Type 6", 20: "Nature 6", 21: "Description 6",
    22: "Type 7", 23: "Description 7",
    24: "Type 8",
}

TYPE_SYNONYMS = {
    "qualified": "Qualified opinion",
    "qualified opinion": "Qualified opinion",
    "emphasis of matter": "Emphasis of matter paragraph",
    "emphasis of matter paragraph": "Emphasis of matter paragraph",
    "key audit matter": "Key audit matter",
    "other matter paragraph": "Other matter paragraph",
}

DASH_CLASS = re.compile(r"[\u2010-\u2015\u2212-]")
QUOTE_CLASS = re.compile(r"[\u2018\u2019\u201A\u201B\u2032\u0060']")
DQUOTE_CLASS = re.compile(r"[\u201C\u201D\u201E\u201F\u2033\"]")
# C0 controls except TAB/LF/CR (which are legitimate whitespace).
CONTROLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
ALNUM_ONLY = re.compile(r"[^a-z0-9]+")
WS = re.compile(r"\s+")


def scrub(value: str) -> str:
    """Remove control garbage and U+FFFD, leave printable text."""
    v = value.replace("\ufffd", "").replace("\u0019", "'")
    v = CONTROLS.sub("", v)
    return v


def canonical(value: str, column: str) -> str:
    """Canonical form used only for deciding 'are these equal?'"""
    if value is None:
        return ""
    v = scrub(value)
    v = DASH_CLASS.sub("-", v)
    v = QUOTE_CLASS.sub("'", v)
    v = DQUOTE_CLASS.sub('"', v)
    v = WS.sub(" ", v).strip()
    if column in ("Opinion type",) or column.startswith("Type "):
        return TYPE_SYNONYMS.get(v.lower(), v).lower()
    return v.lower()


def content_hash(value: str) -> str:
    """Ultra-aggressive equivalence: alphanumerics only, lowercase.

    Two values with the same content_hash likely differ only in punctuation,
    whitespace, dashes, quotes — i.e. text-extraction noise, not content."""
    return ALNUM_ONLY.sub("", scrub(value).lower())


def adopt(value: str, column: str) -> str:
    """Value to write into the updated CSV (cleaned but preserves original casing text)."""
    if value is None:
        return ""
    v = scrub(value)
    v = WS.sub(" ", v).strip()
    if column in ("Opinion type",) or column.startswith("Type "):
        mapped = TYPE_SYNONYMS.get(v.lower())
        if mapped:
            return mapped
    return v


def read_naturaljustice():
    with open(SRC_NJ, "rb") as f:
        raw = f.read()
    if raw[:1] == b"\xff":
        raw = raw[1:]
    text = raw.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    header = rows[0]
    parsed = []
    broken = []
    for idx, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            broken.append((idx, row))
            continue
        rec = {NJ_INDEX_TO_TARGET[i]: row[i] for i in NJ_INDEX_TO_TARGET}
        parsed.append(rec)
    return parsed, broken


def read_target():
    # newline='' preserves embedded newlines in quoted fields; universal-newlines
    # decodes CRLF and bare LF row terminators identically.
    with open(SRC_TG, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    return rows, header


def main():
    nj_rows, nj_broken = read_naturaljustice()
    tg_rows, tg_header = read_target()

    nj_by_key = {r["Council"].strip(): r for r in nj_rows if r["Financial year"] == "2024/25"}

    common_cols = [c for c in NJ_INDEX_TO_TARGET.values()
                   if c in tg_header and c not in ("Council", "Financial year")]

    updated_rows = []
    diffs_per_council = {}
    for tg in tg_rows:
        council = tg["Council"].strip()
        nj = nj_by_key.get(council)
        new_row = dict(tg)
        diffs = []
        if nj:
            for col in common_cols:
                old = tg.get(col, "") or ""
                new = nj.get(col, "") or ""
                # Never overwrite a populated target value with an empty nj value.
                if new.strip() == "" and old.strip() != "":
                    continue
                if canonical(old, col) == canonical(new, col):
                    continue
                # Treat pure-typography differences (smart quotes, dashes,
                # PDF-extraction control chars) as non-changes — target wins.
                if content_hash(old) == content_hash(new):
                    continue
                adopted = adopt(new, col)
                diffs.append((col, old, adopted))
                new_row[col] = adopted
        updated_rows.append(new_row)
        if diffs:
            diffs_per_council[council] = diffs

    only_in_nj = sorted(set(nj_by_key) - {r["Council"].strip() for r in tg_rows})
    only_in_tg = sorted({r["Council"].strip() for r in tg_rows} - set(nj_by_key))

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=tg_header, quoting=csv.QUOTE_MINIMAL,
                            lineterminator="\r\n")
        w.writeheader()
        for row in updated_rows:
            w.writerow(row)

    # Structured field-level patch keyed on (Council, Field).
    patch_lines = [
        "# Field-level patch: naturaljustice.csv → src/data/CouncilsAuditData2025.csv",
        "# Format per block:",
        "#   COUNCIL: <Council name>",
        "#   FIELD:   <column name>",
        "#   -  <old value>",
        "#   +  <new value>",
        "#",
        "# To apply all of these, overwrite the target with the regenerated CSV:",
        "#   cp CouncilsAuditData2025.naturaljustice.csv src/data/CouncilsAuditData2025.csv",
        "",
    ]
    for council in sorted(diffs_per_council):
        for col, old, new in diffs_per_council[council]:
            patch_lines.append(f"COUNCIL: {council}")
            patch_lines.append(f"FIELD:   {col}")
            patch_lines.append(f"-  {old!r}")
            patch_lines.append(f"+  {new!r}")
            patch_lines.append("")
    with open(OUT_PATCH, "w", encoding="utf-8") as f:
        f.write("\n".join(patch_lines))

    lines = []
    lines.append("# naturaljustice.csv vs CouncilsAuditData2025.csv diff")
    lines.append("")
    lines.append(f"- Councils in naturaljustice (2024/25, parseable): {len(nj_by_key)}")
    lines.append(f"- Councils in target:                              {len(tg_rows)}")
    lines.append(f"- Councils with at least one differing field:      {len(diffs_per_council)}")
    lines.append(f"- Broken rows skipped in naturaljustice.csv:       {len(nj_broken)}")
    lines.append("")
    lines.append("## Scope and matching rules")
    lines.append("")
    lines.append("Matched on Council name, filtered to Financial year == 2024/25.")
    lines.append("Column map (naturaljustice → target):")
    lines.append("")
    lines.append("| naturaljustice | target |")
    lines.append("|---|---|")
    lines.append("| Type of audit report | Opinion type |")
    lines.append("| Type N (qualified/EoM/…) | Type N |")
    lines.append("| Nature of qualified opinion N / Nature of EoM N | Nature N |")
    lines.append("| Description N | Description N |")
    lines.append("| second 'Description 6' (header typo) | Description 7 |")
    lines.append("")
    lines.append("Differences below are only shown when they survive these normalisations:")
    lines.append("whitespace collapse, dashes unified to `-`, 0x19 → `'`, U+FFFD stripped,")
    lines.append("case-insensitive match on Type/Opinion fields, and the synonym table:")
    lines.append("")
    for k, v in TYPE_SYNONYMS.items():
        lines.append(f"  - `{k}` → `{v}`")
    lines.append("")
    lines.append("Empty naturaljustice values never overwrite populated target values.")
    lines.append("Target-only columns (preserved as-is): Latitude, Longitude, Description 8.")
    lines.append("naturaljustice-only column (ignored): Address.")
    lines.append("")

    if nj_broken:
        lines.append("## Broken rows in naturaljustice.csv (skipped — quote/escape errors)")
        lines.append("")
        for idx, row in nj_broken:
            snippet = (row[0] if row else "").strip()[:80]
            lines.append(f"- line {idx} (len={len(row)}): {snippet!r}")
        lines.append("")

    if only_in_nj:
        lines.append("## Councils in naturaljustice.csv but not in target")
        lines.append("")
        for c in only_in_nj:
            lines.append(f"- {c}")
        lines.append("")

    if only_in_tg:
        lines.append("## Councils in target but not in naturaljustice.csv (2024/25)")
        lines.append("")
        for c in only_in_tg:
            lines.append(f"- {c}")
        lines.append("")

    lines.append("## Per-council field differences")
    lines.append("")
    if not diffs_per_council:
        lines.append("_No material differences after normalisation._")
    else:
        def trim(s):
            s = (s or "").replace("\r", " ").replace("\n", " ⏎ ")
            return s if len(s) <= 240 else s[:240] + "…"
        for council in sorted(diffs_per_council):
            lines.append(f"### {council}")
            lines.append("")
            for col, old, new in diffs_per_council[council]:
                lines.append(f"- **{col}**")
                lines.append(f"  - target: `{trim(old)}`")
                lines.append(f"  - nj:     `{trim(new)}`")
            lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"Wrote {OUT_PATCH.relative_to(ROOT)}")
    print(f"Councils with differences: {len(diffs_per_council)}")


if __name__ == "__main__":
    main()
