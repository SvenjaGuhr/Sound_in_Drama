#!/usr/bin/env python3

import csv
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def localname(tag: str) -> str:
    """Return the local name of an XML tag, stripping any namespace."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def build_parent_map(root):
    """Map each element to its parent."""
    return {child: parent for parent in root.iter() for child in parent}


def has_ancestor_with_localname(elem, names, parent_map):
    """Check whether elem has any ancestor whose local tag name is in names."""
    current = parent_map.get(elem)
    while current is not None:
        if localname(current.tag) in names:
            return True
        current = parent_map.get(current)
    return False


def count_stage_directions(xml_path: Path):
    """
    Count:
      - all <stage>
      - <stage> within <p> or <l>
      - <stage> outside <p>/<l>
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    parent_map = build_parent_map(root)

    stage_total = 0
    stage_within_speech = 0
    stage_outside_speech = 0

    for elem in root.iter():
        if localname(elem.tag) != "stage":
            continue

        stage_total += 1

        # "Within speech" = <stage> somewhere inside <p> or <l>
        if has_ancestor_with_localname(elem, {"p", "l"}, parent_map):
            stage_within_speech += 1
        else:
            stage_outside_speech += 1

    return {
        "filename": xml_path.name,
        "basename": (
            xml_path.name[:-4]
            if xml_path.name.endswith(".xml")
            else xml_path.stem
        ),
        "stage_total": stage_total,
        "stage_within_speech": stage_within_speech,
        "stage_outside_speech": stage_outside_speech,
    }


def parse_directory(input_dir: Path, output_csv: Path):
    xml_files = sorted(input_dir.glob("*.xml"))

    if not xml_files:
        raise FileNotFoundError(
            f"No .xml files found in directory: {input_dir}"
        )

    rows = []
    for xml_file in xml_files:
        try:
            rows.append(count_stage_directions(xml_file))
        except ET.ParseError as e:
            print(
                f"Skipping {xml_file.name}: XML parse error: {e}",
                file=sys.stderr,
            )

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "basename",
                "stage_total",
                "stage_within_speech",
                "stage_outside_speech",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python count_stage_directions.py <input_directory> <output_csv>",
            file=sys.stderr,
        )
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_csv = Path(sys.argv[2])

    if not input_dir.is_dir():
        print(f"Error: not a directory: {input_dir}", file=sys.stderr)
        sys.exit(1)

    parse_directory(input_dir, output_csv)
    print(f"Wrote results to {output_csv}")


if __name__ == "__main__":
    main()
