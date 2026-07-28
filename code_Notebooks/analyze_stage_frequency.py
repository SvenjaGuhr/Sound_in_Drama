"""
Analyze TEI-encoded German plays:
- Count <stage> elements per play (frequency)
- Count words in <stage> elements via spaCy (verbosity)
- Count tokens in <p> and <l> elements using spaCy de_core_news_md
  -> only real word tokens (no punctuation, no whitespace) are counted
- Compute stage frequency and verbosity relative to pure text length
- Output a pandas DataFrame saved as CSV

Columns produced:
  stage_count          - number of <stage> elements
  stage_word_count     - total words inside all <stage> elements
  stage_avg_words      - mean words per stage direction
  word_count_l_p       - words in <l> and <p> elements (pure spoken/written text)
  stage_per_1k_words   - stage directions per 1,000 text words (frequency density)
  stage_words_per_1k   - stage direction words per 1,000 text words (verbosity density)

Requirements:
    pip install lxml pandas spacy
    python -m spacy download de_core_news_md
"""

import os
import pandas as pd
import spacy
from lxml import etree

# -- Configuration -------------------------------------------------------------
INPUT_DIR = "/Users/sguhr/Downloads/Sound_in_Drama-main/gdc-tei/all"
OUTPUT_CSV = "stage_frequency_results.csv"

# TEI namespace - present in every well-formed TEI file
TEI_NS = "http://www.tei-c.org/ns/1.0"
NS = {"tei": TEI_NS}

# -- Load spaCy model once (disable unused pipes for speed) --------------------
print("Loading spaCy model de_core_news_md ...")
nlp = spacy.load("de_core_news_md", disable=["ner", "parser", "morphologizer", "senter"])
# Increase max length to handle very long concatenated play texts
nlp.max_length = 5_000_000
print("Model loaded.\n")


# -- Helpers -------------------------------------------------------------------

def count_words_spacy(elements: list) -> int:
    """
    Concatenate text from a list of XML elements and count real word tokens
    using spaCy: excludes punctuation and pure-whitespace tokens.
    """
    combined_text = " ".join(
        "".join(el.itertext()) for el in elements
    ).strip()

    if not combined_text:
        return 0

    doc = nlp(combined_text)
    return sum(1 for token in doc if not token.is_punct and not token.is_space)


def count_stage_words_spacy(elements: list) -> tuple[int, float]:
    """
    Count total words across all <stage> elements and return
    (total_words, avg_words_per_stage).
    Each stage element is processed individually to compute the average.
    """
    if not elements:
        return 0, 0.0

    per_stage_counts = []
    for el in elements:
        text = "".join(el.itertext()).strip()
        if not text:
            per_stage_counts.append(0)
            continue
        doc = nlp(text)
        per_stage_counts.append(
            sum(1 for token in doc if not token.is_punct and not token.is_space)
        )

    total = sum(per_stage_counts)
    avg = total / len(per_stage_counts) if per_stage_counts else 0.0
    return total, round(avg, 4)


def extract_metadata(root) -> dict:
    """Pull title and author from teiHeader (best-effort)."""
    title_el = root.find(".//tei:titleStmt/tei:title[@type='main']", NS)
    title = title_el.text.strip() if title_el is not None and title_el.text else ""

    surname_el = root.find(".//tei:titleStmt/tei:author/tei:persName/tei:surname", NS)
    author = surname_el.text.strip() if surname_el is not None and surname_el.text else ""

    print_el = root.find(".//tei:listEvent/tei:event[@type='print']", NS)
    year = print_el.get("when", "") if print_el is not None else ""

    return {"title": title, "author": author, "year": year}


def analyze_file(filepath: str) -> dict | None:
    """Parse one TEI XML file and return a metrics dict, or None on error."""
    try:
        tree = etree.parse(filepath)
        root = tree.getroot()
    except etree.XMLSyntaxError as exc:
        print(f"  [PARSE ERROR] {filepath}: {exc}")
        return None

    filename = os.path.basename(filepath)

    # -- Stage elements --------------------------------------------------------
    stage_elements = root.findall(".//tei:stage", NS)
    if not stage_elements:
        stage_elements = root.findall(".//stage")
    stage_count = len(stage_elements)

    # -- Stage word count and average length -----------------------------------
    stage_word_count, stage_avg_words = count_stage_words_spacy(stage_elements)

    # -- Token count in <l> and <p> via spaCy (pure text) ---------------------
    line_elements = root.findall(".//tei:l", NS) or root.findall(".//l")
    para_elements = root.findall(".//tei:p", NS) or root.findall(".//p")
    word_count = count_words_spacy(line_elements + para_elements)

    # -- Relative metrics (per 1,000 text words) ------------------------------
    stage_per_1k_words = (
        round(stage_count / word_count * 1000, 4) if word_count > 0 else None
    )
    stage_words_per_1k = (
        round(stage_word_count / word_count * 1000, 4) if word_count > 0 else None
    )

    meta = extract_metadata(root)

    return {
        "filename":          filename,
        "author":            meta["author"],
        "title":             meta["title"],
        "year":              meta["year"],
        "stage_count":       stage_count,
        "stage_word_count":  stage_word_count,
        "stage_avg_words":   stage_avg_words,
        "word_count_l_p":    word_count,
        "stage_per_1k_words":  stage_per_1k_words,
        "stage_words_per_1k":  stage_words_per_1k,
    }


# -- Main ----------------------------------------------------------------------

def main():
    xml_files = sorted(
        f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".xml")
    )
    total = len(xml_files)
    print(f"Found {total} XML files in {INPUT_DIR}\n")

    records = []
    for i, fname in enumerate(xml_files, 1):
        fpath = os.path.join(INPUT_DIR, fname)
        print(f"[{i:3d}/{total}] {fname}", end=" ... ", flush=True)
        result = analyze_file(fpath)
        if result:
            records.append(result)
            print(
                f"stages={result['stage_count']}  "
                f"stage_words={result['stage_word_count']}  "
                f"avg={result['stage_avg_words']}  "
                f"text_words={result['word_count_l_p']}  "
                f"freq/1k={result['stage_per_1k_words']}  "
                f"verbosity/1k={result['stage_words_per_1k']}"
            )
        else:
            print("skipped")

    df = pd.DataFrame(records)

    # -- Save CSV --------------------------------------------------------------
    out_path = os.path.join(INPUT_DIR, OUTPUT_CSV)
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nDone. {len(records)} plays processed. CSV saved -> {out_path}")

    return df


if __name__ == "__main__":
    df = main()
