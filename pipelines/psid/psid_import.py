"""Import a PSID Data Center fixed-width ASCII extract described by a SAS setup file.

The SAS program defines column positions, labels, and formats. This script reads
those definitions (including the expected row, variable, and record-length counts
in the header comment) instead of hard-coding them, so it works for any PSID job.

Outputs (in --outdir):
  psid_family_wide.csv       Wide-format data (one row per family record)
  variable_dictionary.csv    Variable names, labels, SAS formats, 1-based column positions
  import_report.txt          Import checks and missingness summary

Example (job 366613: 718 variables, 33,440 records, record length 1,697):
  python psid_import.py --sas J366613.sas --data J366613.txt --outdir psid_output

Requirements: pandas
"""

from __future__ import annotations

import argparse
import csv
import re
import os
import sys
from pathlib import Path

import pandas as pd

DEFAULT_SAS = "J366613.sas"


def parse_sas_setup(sas_path: Path) -> tuple[list[dict], dict[str, int | None]]:
    """Extract INPUT positions, ATTRIB labels/formats, and header-comment totals."""
    text = sas_path.read_text(encoding="latin-1")

    # Header comment totals (N_OF_VARIABLES, N_OF_OBSERVATIONS, MAX_REC_LENGTH).
    def header_int(key: str) -> int | None:
        m = re.search(rf"{key}\s*:\s*([\d,]+)", text)
        return int(m.group(1).replace(",", "")) if m else None

    expected = {
        "variables": header_int("N_OF_VARIABLES"),
        "rows": header_int("N_OF_OBSERVATIONS"),
        "record_length": header_int("MAX_REC_LENGTH"),
    }

    # ATTRIB lines: NAME LABEL="..." FORMAT=F5. or F7.3
    labels: dict[str, str] = {}
    formats: dict[str, str] = {}
    for m in re.finditer(
        r'^\s*([A-Za-z_]\w*)\s+LABEL="([^"]*)"(?:\s+FORMAT=(\S+))?',
        text,
        flags=re.MULTILINE,
    ):
        labels[m.group(1)] = m.group(2).strip()
        formats[m.group(1)] = (m.group(3) or "").strip()

    # Search for INPUT only after the INFILE statement so that a label containing
    # the word "input" cannot be mistaken for the INPUT block.
    infile_match = re.search(r"\bINFILE\b", text, flags=re.IGNORECASE)
    search_from = infile_match.start() if infile_match else 0
    input_match = re.search(
        r"\bINPUT\s+(.*?);", text[search_from:], flags=re.DOTALL | re.IGNORECASE
    )
    if not input_match:
        raise ValueError(f"Could not find an INPUT block in {sas_path}.")

    variables: list[dict] = []
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s+(\d+)\s*-\s*(\d+)", input_match.group(1)):
        name, start, end = m.group(1), int(m.group(2)), int(m.group(3))
        if end < start:
            raise ValueError(f"Invalid column range for {name}: {start}-{end}")
        fmt = formats.get(name, "")
        dec = re.search(r"\.(\d+)$", fmt)
        variables.append(
            {
                "variable": name,
                "label": labels.get(name, ""),
                "format": fmt,
                "implied_decimals": int(dec.group(1)) if dec else 0,
                "start_col": start,
                "end_col": end,
                "width": end - start + 1,
            }
        )

    if not variables:
        raise ValueError(f"No fixed-width variable positions were parsed from {sas_path}.")

    names = [v["variable"] for v in variables]
    if len(names) != len(set(names)):
        raise ValueError("The SAS INPUT block contains duplicate variable names.")

    # Layout integrity: columns must be contiguous and non-overlapping.
    for prev, cur in zip(variables, variables[1:]):
        if cur["start_col"] != prev["end_col"] + 1:
            raise ValueError(
                f"Layout gap or overlap between {prev['variable']} "
                f"(ends {prev['end_col']}) and {cur['variable']} (starts {cur['start_col']})."
            )

    # Record length: prefer INFILE LRECL, fall back to the header comment.
    rec_match = re.search(r"\bLRECL\s*=\s*(\d+)", text, flags=re.IGNORECASE)
    if rec_match:
        expected["record_length"] = int(rec_match.group(1))

    last_col = variables[-1]["end_col"]
    if expected["record_length"] is not None and last_col != expected["record_length"]:
        raise ValueError(
            f"Last INPUT column {last_col} does not match record length {expected['record_length']}."
        )

    return variables, expected


def check_data_file(data_path: Path, expected_record_length: int | None) -> tuple[int, set[int]]:
    """Count records and collect observed line lengths without loading the file into RAM."""
    n_rows = 0
    lengths: set[int] = set()
    with data_path.open("rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            record = line.rstrip(b"\r\n")
            n_rows += 1
            lengths.add(len(record))
            if expected_record_length is not None and len(record) != expected_record_length:
                raise ValueError(
                    f"Record {line_number} has length {len(record)}; "
                    f"the SAS setup specifies {expected_record_length}."
                )
    return n_rows, lengths


def import_fixed_width(
    data_path: Path, variables: list[dict], output_path: Path
) -> tuple[int, pd.DataFrame]:
    """Slice records at SAS-defined positions and write a CSV."""
    names = [v["variable"] for v in variables]
    slices = [(v["start_col"] - 1, v["end_col"]) for v in variables]
    last_column = max(end for _, end in slices)
    missing_counts = [0] * len(names)
    rows_written = 0

    with data_path.open("r", encoding="ascii", newline="") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        writer = csv.writer(destination)
        writer.writerow(names)
        for line_number, line in enumerate(source, start=1):
            record = line.rstrip("\r\n")
            if len(record) < last_column:
                raise ValueError(
                    f"Record {line_number} has length {len(record)}, "
                    f"shorter than the last field ending at {last_column}."
                )
            values = [record[start:end].strip() for start, end in slices]
            for j, value in enumerate(values):
                if value == "":
                    missing_counts[j] += 1
            writer.writerow(values)
            rows_written += 1

    if rows_written == 0:
        raise ValueError("No records were imported from the data file.")

    missing_summary = pd.DataFrame(
        {
            "variable": names,
            "missing_count": missing_counts,
            "missing_share": [c / rows_written for c in missing_counts],
        }
    )
    return rows_written, missing_summary


def write_report(
    report_path: Path,
    sas_path: Path,
    data_path: Path,
    variables: list[dict],
    expected: dict[str, int | None],
    rows_found: int,
    line_lengths: set[int],
    rows_imported: int,
    missing_summary: pd.DataFrame,
) -> None:
    fmt = lambda x: f"{x:,}" if x is not None else "not specified"
    total_cells = rows_imported * len(variables)
    missing_cells = int(missing_summary["missing_count"].sum())
    lines = [
        "PSID fixed-width import report",
        "==============================",
        f"SAS setup file: {sas_path}",
        f"ASCII data file: {data_path}",
        f"Records counted in raw file: {rows_found:,}",
        f"Rows imported: {rows_imported:,}",
        f"Variables imported: {len(variables):,}",
        f"Observed raw record lengths: {', '.join(map(str, sorted(line_lengths)))}",
        f"Expected rows (SAS header): {fmt(expected['rows'])}",
        f"Expected variables (SAS header): {fmt(expected['variables'])}",
        f"Expected record length (SAS header/LRECL): {fmt(expected['record_length'])}",
        f"Total data cells: {total_cells:,}",
        f"Blank cells in raw fields: {missing_cells:,} ({missing_cells / total_cells:.2%})",
        "",
        "Variables with the highest missing shares:",
    ]
    top = missing_summary.sort_values("missing_share", ascending=False).head(20)
    lines.extend(
        f"  {r.variable}: {r.missing_count:,} missing ({r.missing_share:.1%})"
        for r in top.itertuples(index=False)
    )
    lines.extend(
        [
            "",
            "Notes:",
            "- Blank fields are written as empty CSV cells and load as missing in pandas.",
            "- Nonblank fields are preserved as trimmed numeric text, including negative values and literal decimal points.",
            "- Variables with a non-integer SAS format (see implied_decimals in the dictionary) carry a literal decimal point in the raw text.",
            "- The setup file has no value labels or missing-value recodes. Consult the PSID codebook before treating special codes (e.g., 0, 9, 99, 999) as ordinary values.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import a PSID fixed-width ASCII extract using its SAS setup file."
    )
    # PSID files live in <workspace>/data/psid (override with PSID_DIR)
    here = Path(os.environ.get("PSID_DIR") or Path(__file__).resolve().parents[2] / "data" / "psid")
    parser.add_argument("--sas", type=Path, default=here / DEFAULT_SAS, help=f"SAS setup file (default: {DEFAULT_SAS} in data/psid)")
    parser.add_argument("--data", type=Path, default=None, help="ASCII data file (default: SAS file stem + .txt)")
    parser.add_argument("--outdir", type=Path, default=here / "psid_output", help="Output directory (default: in data/psid)")
    args = parser.parse_args()

    if args.data is None:
        args.data = args.sas.with_suffix(".txt")
    if not args.sas.is_file():
        parser.error(f"SAS setup file not found: {args.sas}")
    if not args.data.is_file():
        parser.error(f"ASCII data file not found: {args.data}")

    args.outdir.mkdir(parents=True, exist_ok=True)
    wide_path = args.outdir / "psid_family_wide.csv"
    dictionary_path = args.outdir / "variable_dictionary.csv"
    report_path = args.outdir / "import_report.txt"

    try:
        variables, expected = parse_sas_setup(args.sas)
        rows_found, line_lengths = check_data_file(args.data, expected["record_length"])
        pd.DataFrame(variables).to_csv(dictionary_path, index=False)
        rows_imported, missing_summary = import_fixed_width(args.data, variables, wide_path)
        write_report(
            report_path, args.sas, args.data, variables, expected,
            rows_found, line_lengths, rows_imported, missing_summary,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Import completed.")
    print(f"Rows: {rows_imported:,}")
    print(f"Variables: {len(variables):,}")
    print(f"Wide CSV: {wide_path.resolve()}")
    print(f"Variable dictionary: {dictionary_path.resolve()}")
    print(f"Import report: {report_path.resolve()}")
    if expected["rows"] is not None and rows_imported != expected["rows"]:
        print(f"WARNING: SAS header says {expected['rows']:,} rows, but imported {rows_imported:,}.")
    if expected["variables"] is not None and len(variables) != expected["variables"]:
        print(f"WARNING: SAS header says {expected['variables']:,} variables, but parsed {len(variables):,}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())