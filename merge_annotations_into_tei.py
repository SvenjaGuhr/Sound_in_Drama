#!/usr/bin/env python3

"""
Script to merge loudness annotations from CSV files into the
original GerDraCor TEI.
"""

import pandas as pd
import argparse
import glob
import os.path
import re


def parse_args() -> argparse.ArgumentParser:
    """
    Parse all arguments needed for the main function and its subprocesses.
    """

    handler = argparse.ArgumentParser(description=__doc__)
    handler.add_argument('--inputannotations', type=str, help='Location of annotation data')
    handler.add_argument('--inputtei', type=str, help='Location of annotation data')
    handler.add_argument('--outputdir', type=str, help='Directory for output')
    args = handler.parse_args()
    return args


def main() -> None:
    args = parse_args()

    # Import annotations
    annotations = {}
    annotations_path = args.inputannotations
    annotations_file_names = glob.glob(annotations_path + "/" + "*.csv")
    for file_name in annotations_file_names:
        annotations[os.path.basename(os.path.splitext(file_name)[0])] = pd.read_csv(file_name)

    # Import GDC TEI
    tei = {}
    tei_path = args.inputtei
    tei_file_names = glob.glob(tei_path + "/" + "*.xml")
    for file_name in tei_file_names:
        with open(file_name, "r") as f:
            tei_content = f.read()
            tei[os.path.basename(os.path.splitext(file_name)[0])] = tei_content

    # Merge annotations into TEI
    new_texts = {}
    for text in annotations:
        if text == "holz-ignorabimus":
            continue
        new_text = tei[text]
        print(text)
        for i, row in annotations[text].iterrows():
            stage_str_orig = row["stage"]
            #print(row["stage"])
            stage_str = re.sub(r"\s+", " ", stage_str_orig).replace(".", "\\.").replace(" ", '(?:\\s*?|\\s*?<pb n="\\d+?"/>\\s*?|\\s*und\\s*)').removeprefix(".*?").removeprefix('(?:\\s*?|\\s*?<pb n="\\d+?"/>\\s*?)').removesuffix(".*?").removesuffix('(?:\\s*?|\\s*?<pb n="\\d+?"/>\\s*?)')
            stage_regex = re.compile(stage_str)
            try:
                idx = re.search(stage_str, new_text, re.DOTALL).span()
                new_text = new_text[:idx[1]] + "</character_sound>" + new_text[idx[1]:]
                new_text = new_text[:idx[0]] + "<character_sound>" + new_text[idx[0]:]
            except AttributeError:
                raise AttributeError(f"'{stage_str_orig}' could not be found in {text}\nRegex: {stage_str}")
        new_texts[text] = new_text

    for text in new_texts:
        with open(f"{args.outputdir}/{text}.xml", "w") as f:
            f.write(new_texts[text])


if __name__ == "__main__":
    main()
