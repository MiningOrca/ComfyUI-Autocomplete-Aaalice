#!/usr/bin/env python3
"""Convert a Rule34.xxx tag dump to Aaalice's native CSV format.

The output is ``tag,category,count,alias`` and defaults to a pt20-style
minimum post count. The converter accepts the common Rule34/Gelbooru schema
(``type,count,name,...``) and the normalized equivalents
(``category_id,post_count,tag_name,...``).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "rule34_tags.csv"
VALID_CATEGORIES = {0, 1, 2, 3, 4, 5, 6}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create data/rule34_tags.csv for ComfyUI-Autocomplete-Aaalice."
    )
    parser.add_argument("input", type=Path, help="Rule34 tags CSV to convert.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=20,
        help="Minimum Rule34 post count to keep (default: 20, i.e. pt20).",
    )
    return parser.parse_args()


def first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return ""


def convert(source: Path, destination: Path, min_count: int) -> tuple[int, int]:
    if min_count < 0:
        raise ValueError("--min-count must be >= 0")

    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Input CSV not found: {source}")

    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    skipped = 0

    with source.open("r", encoding="utf-8-sig", newline="") as source_file,             destination.open("w", encoding="utf-8", newline="") as output_file:
        reader = csv.DictReader(source_file)
        if not reader.fieldnames:
            raise ValueError("Source CSV has no header")

        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(("tag", "category", "count", "alias"))

        for row in reader:
            tag = first_value(row, "name", "tag_name", "tag").strip()
            try:
                count = int(first_value(row, "count", "post_count") or 0)
                category = int(first_value(row, "type", "category_id", "category") or -1)
            except ValueError:
                skipped += 1
                continue

            if not tag or count < min_count:
                skipped += 1
                continue

            # Rule34/Gelbooru category IDs:
            # 0 general, 1 artist, 2 invalid/unused, 3 copyright,
            # 4 character, 5 meta, 6 deprecated.
            if category not in VALID_CATEGORIES:
                category = -1

            writer.writerow((tag, category, count, ""))
            kept += 1

    return kept, skipped


def main() -> int:
    args = parse_args()
    kept, skipped = convert(args.input, args.output, args.min_count)
    print(f"Wrote {kept:,} tags to {args.output.expanduser().resolve()}")
    print(f"Skipped {skipped:,} rows (count < {args.min_count}, invalid, or empty)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
