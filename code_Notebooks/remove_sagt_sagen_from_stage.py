"""
remove_sagt_sagen_from_stage.py
================================
Iterates over all TEI XML files in INPUT_DIR and removes the words
"sagt" and "sagen" (case-insensitive) when they appear as leading text
directly after any of these three opening patterns:

  1.  <stage>sagt …
  2.  <stage><character_sound>sagt …
  3.  <stage><ambient_sound>sagt …

Only the word itself is removed; surrounding whitespace is collapsed to
a single space so the rest of the element content is preserved intact.
Files are overwritten in place.

PATTERNS MATCHED (schematically):
  <stage>sagt,  <stage> sagt,  <stage>sagen,  <stage> sagen
  <stage><character_sound>sagt,  <stage><ambient_sound>sagen,  … etc.

Matching is case-insensitive. The word must be followed by a word
boundary (\\b) so "sagen" is not stripped from "sagend", "Ansage", etc.
"""

import os
import re

# ── Configuration ─────────────────────────────────────────────────────────────
INPUT_DIR = (
    "/Users/sguhr/Desktop/20250729_prediction_output/202508_GerDraCor_sound-pred_with_postprocessing_20260427"
)

# ── Regex ─────────────────────────────────────────────────────────────────────
#
# Matches one of the three opening patterns followed by optional whitespace
# and then the bare word "sagt" or "sagen" (word-boundary protected).
#
# Group 1  →  the opening tag sequence to keep
# Group 2  →  "sagt" or "sagen" to delete
# Group 3  →  whatever immediately follows (space / punctuation / next tag)
#
# The replacement keeps group 1 and group 3, dropping group 2 and any
# whitespace that directly surrounded it.

PATTERN = re.compile(
    r"""
    (                                       # Group 1: opening to keep
        <stage>                             #   bare <stage>
        (?:                                 #   optionally followed by
            \s*                             #     optional whitespace
            <(?:character_sound|ambient_sound)>  # a sound open tag
        )?
    )
    \s*                                     # optional whitespace before word
    (sagt|sagen)                            # Group 2: word to DELETE
    \b                                      # word boundary (not "sagend" etc.)
    \s*                                     # optional whitespace after word
    """,
    re.IGNORECASE | re.VERBOSE,
)


def clean_file(filepath: str) -> int:
    """Remove sagt/sagen after stage openings. Returns number of substitutions."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    cleaned, n = PATTERN.subn(r"\1", content)

    if n:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned)

    return n


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    xml_files = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".xml"))
    print(f"Found {len(xml_files)} XML files in {INPUT_DIR}\n")

    total = 0
    for fname in xml_files:
        path = os.path.join(INPUT_DIR, fname)
        n = clean_file(path)
        if n:
            print(f"  [cleaned {n:3d}] {fname}")
        total += n

    print(f"\nDone. {total} occurrences removed across {len(xml_files)} files.")


if __name__ == "__main__":
    main()
