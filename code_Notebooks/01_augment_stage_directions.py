"""
augment_stage_directions.py
===========================

Stage direction augmentation heuristic for GerDraCor sound annotation,
as described in Guhr, Pagel & Reiter, "What Does Drama Sound Like?",
subsection 3.1.

WHAT IT DOES
------------
For each <stage> element that is elliptical (begins lowercase and contains
no finite verb), prepend the speech verb "Sagt" (singular speaker) or
"Sagen" (plural speaker), turning the elliptical direction into a
syntactically complete verbal phrase resembling the prose training examples.

The speaker count is read from the enclosing <sp who="..."> element:
more than one whitespace-separated id in `who` -> plural -> "Sagen".

SCOPE AND HONESTY NOTE
----------------------
This script performs the AUTOMATIC heuristic step only. In the manual
annotation workflow, an annotator subsequently PRUNED insertions that did
not correspond to a realized speech act (e.g. stage actions such as
"aufspringend"). The gold TRAINING files therefore reflect
heuristic-then-corrected text, whereas this script reflects the heuristic's
raw proposals. Applied to unlabeled plays for corpus-wide prediction there
is no correction pass, so the output over-inserts relative to the manually
corrected training data. Document this asymmetry; do not present the script
as an exact reproduction of the gold files.

MARKER
------
Each inserted verb is preceded by the comment <!--aug-->. This lets the
companion reversal script remove exactly what was added, with no guessing,
and lets the reversal's validation step confirm the de-augmented text is
byte-for-byte identical to the original. Set USE_MARKER = False to omit it
(then reversal must rely on text alignment alone).

USAGE
-----
    python augment_stage_directions.py input.xml > input.augmented.xml
    python augment_stage_directions.py --indir plays/ --outdir plays_augmented/

REQUIRES
--------
    pip install spacy
    python -m spacy download de_core_news_sm
"""

import argparse
import os
import re
import sys

import spacy

_NLP = spacy.load("de_core_news_sm", disable=["ner", "lemmatizer"])

USE_MARKER = True
MARKER = "<!--aug-->"


def has_finite_verb(text: str) -> bool:
    """True if text contains a finite verb (VerbForm=Fin)."""
    for tok in _NLP(text):
        if tok.pos_ in ("VERB", "AUX") and "Fin" in tok.morph.get("VerbForm"):
            return True
    return False


def is_elliptical(inner_text: str) -> bool:
    """
    Augmentation candidate: begins with a lowercase letter and lacks a
    finite verb. Capitalization is the conservative filter from the paper:
    syntactically complete directions tend to begin uppercase.
    """
    stripped = inner_text.strip()
    if not stripped:
        return False
    first_alpha = next((c for c in stripped if c.isalpha()), "")
    if not first_alpha or not first_alpha.islower():
        return False
    return not has_finite_verb(stripped)


def speaker_is_plural(who_attr: str) -> bool:
    ids = [w for w in who_attr.replace("#", "").split() if w]
    return len(ids) > 1


def _augment_stage(stage_xml: str, plural: bool) -> str:
    """Insert the verb before the first text character of the stage
    direction, after "<stage>" and any immediately following opening tag.
    Idempotent: an already-augmented direction begins with the inserted
    verb and no longer passes is_elliptical."""
    inner = re.sub(r"<[^>]+>", "", stage_xml[len("<stage>"):-len("</stage>")])
    if not is_elliptical(inner):
        return stage_xml

    verb = "Sagen" if plural else "Sagt"
    insertion = f"{MARKER if USE_MARKER else ''}{verb} "

    body = stage_xml[len("<stage>"):-len("</stage>")]
    m = re.match(r"^(\s*(?:<[^>]+>\s*)*)", body)   # leading ws + opening tags
    prefix = m.group(1)
    rest = body[len(prefix):]
    return f"<stage>{prefix}{insertion}{rest}</stage>"


def augment_xml(xml: str) -> str:
    """Augment every <stage>, using the enclosing <sp> for speaker count.
    Stage directions outside any <sp> default to singular."""

    def process_sp(match):
        sp = match.group(0)
        who = re.search(r'who="([^"]*)"', sp)
        plural = speaker_is_plural(who.group(1)) if who else False
        return re.sub(r"<stage>.*?</stage>",
                      lambda sm: _augment_stage(sm.group(0), plural),
                      sp, flags=re.S)

    xml = re.sub(r"<sp\b[^>]*>.*?</sp>", process_sp, xml, flags=re.S)
    # remaining <stage> outside <sp>: singular default (idempotent re-run)
    xml = re.sub(r"<stage>.*?</stage>",
                 lambda sm: _augment_stage(sm.group(0), False),
                 xml, flags=re.S)
    return xml


def main():
    ap = argparse.ArgumentParser(description="Augment GerDraCor stage directions.")
    ap.add_argument("input", nargs="?", help="single input XML file")
    ap.add_argument("--indir", help="input directory of .xml files")
    ap.add_argument("--outdir", help="output directory (used with --indir)")
    args = ap.parse_args()

    if args.indir:
        if not args.outdir:
            ap.error("--outdir is required with --indir")
        os.makedirs(args.outdir, exist_ok=True)
        for fn in sorted(os.listdir(args.indir)):
            if not fn.endswith(".xml"):
                continue
            with open(os.path.join(args.indir, fn), encoding="utf-8") as f:
                out = augment_xml(f.read())
            with open(os.path.join(args.outdir, fn), "w", encoding="utf-8") as f:
                f.write(out)
            print(f"augmented {fn}", file=sys.stderr)
    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            sys.stdout.write(augment_xml(f.read()))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
