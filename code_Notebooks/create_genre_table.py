#!/usr/bin/env python3

"""
Script to automatically extract genre allocations
from author's self ascriptions.
"""

import argparse
import glob
import os
import pandas as pd
from lxml import etree as ET


def parse_args() -> argparse.ArgumentParser:
    """
    Parse all arguments needed for the main function and its subprocesses.
    """

    handler = argparse.ArgumentParser(description=__doc__)
    handler.add_argument('--inputtei', type=str, help='Location of TEI data')
    handler.add_argument('--outputfile', type=str, help='Directory for output')
    args = handler.parse_args()
    return args


def strip_namespace(tree):
    """
    Strip XML namespaces to make processing easier.
    """
    for elem in tree.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    return tree


def main() -> None:
    """
    Main function
    """

    args = parse_args()

    tei = {}
    for file_name in glob.glob(args.inputtei + "/" + "*.xml"):
        with open(file_name, "rb") as f:
            tei_content = f.read()
            tei[os.path.basename(os.path.splitext(file_name)[0])] = tei_content

    rows = []
    for file_name in tei:
        print(f"Processing {file_name}")
        text = tei[file_name]
        root = ET.fromstring(text)
        # Remove namespaces
        for elem in root.getiterator():
            if not (
                isinstance(elem, ET._Comment)
                or isinstance(elem, ET._ProcessingInstruction)
            ):
                elem.tag = ET.QName(elem).localname
        ET.cleanup_namespaces(root)

        match = root.findall('.//title[@type="sub"]')

        genre = None
        if match != []:
            subtitle = match[0].text
            if "Tragikomödie" in subtitle or "Tragi-Komödie" in subtitle or "Tragische Komödie" in subtitle:
                genre = "Tragikomödie"
            elif "Komödie" in subtitle or "komödie" in subtitle:
                genre = "Komödie"
            elif "Tragödie" in subtitle or "tragödie" in subtitle:
                genre = "Tragödie"
            elif "Lustspiel" in subtitle or "lustspiel" in subtitle:
                genre = "Lustspiel"
            elif "Trauerspiel" in subtitle or "trauerspiel" in subtitle:
                genre = "Trauerspiel"
        else:
            subtitle = None

        row = {"filename": file_name+".xml", "genre_selfascription": subtitle, "genre": genre}
        rows.append(row)

    df = pd.DataFrame.from_dict(rows)
    df.to_csv(args.outputfile, index=False)


if __name__ == "__main__":
    main()
