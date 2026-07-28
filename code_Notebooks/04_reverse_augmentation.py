"""
reverse_augmentation.py
=======================

Reverse the stage direction augmentation and VALIDATE the result against the
ground-truth original play XML.

WHY VALIDATION MATTERS
----------------------
The augmentation inserts a verb ("Sagt"/"Sagen"), but the pipeline may also
introduce incidental whitespace and line-break changes to the TEI source
that a regex cannot reliably distinguish from the original encoding. Rather
than guess, this script removes the inserted verbs and then checks the
de-augmented text byte-for-byte against the original play. Any residual
difference is reported per file, so you know exactly which plays reverted
cleanly and which did not. This closes the text-reversibility gap: reversal
is verified, not assumed.

WHAT IT REMOVES
---------------
1. If the augmented file carries the <!--aug--> marker (written by
   augment_stage_directions.py), each marker and its immediately following
   "Sagt "/"Sagen " is deleted. This is exact and unambiguous.
2. If no marker is present (USE_MARKER was False, or the file came from an
   external augmentation), the script falls back to removing a leading
   "Sagt "/"Sagen " inside <stage> elements. This is best-effort and the
   validation step is then the real guarantee.

Sound annotation tags (<character_sound>, <ambient_sound>) are left in place
by default; the reversal concerns the TEXT layer. See --strip-sound if you
want an unannotated output to diff against a plain original.

VALIDATION
----------
For each augmented file, provide the matching original (unannotated) play.
The script strips sound tags from a copy of the reverted text and compares
it to the original. It reports one of:
    OK              de-augmented text == original (byte-for-byte)
    MISMATCH (n)    n character positions differ; first difference shown
    NO-ORIGINAL     no original file supplied for this play
Exit code is non-zero if any file MISMATCHed, so this can gate a release.

USAGE
-----
    # one file
    python reverse_augmentation.py aug.xml --original orig.xml > reverted.xml

    # batch: match by filename between two directories
    python reverse_augmentation.py --indir augmented/ \
        --origdir originals/ --outdir reverted/

    # validate only, write nothing
    python reverse_augmentation.py --indir augmented/ \
        --origdir originals/ --check-only
"""

import argparse
import os
import re
import sys

MARKER = "<!--aug-->"
_SOUND_TAG = re.compile(r"</?(character_sound|ambient_sound)>")


def strip_sound_tags(xml: str) -> str:
    return _SOUND_TAG.sub("", xml)


def reverse_xml(xml: str) -> str:
    """Remove inserted verbs. Prefer the exact marker path; fall back to a
    leading-verb removal inside <stage> when no marker is present."""
    if MARKER in xml:
        # remove "<!--aug-->Sagt " or "<!--aug-->Sagen " (verb + one space)
        return re.sub(re.escape(MARKER) + r"(?:Sagt|Sagen)\s", "", xml)

    # marker-free fallback: strip a leading Sagt/Sagen from stage text,
    # including the case where it sits just inside an opening inner tag.
    def fix_stage(m):
        s = m.group(0)
        return re.sub(
            r"(<stage>\s*(?:<[^>]+>\s*)*)(?:Sagt|Sagen)\s",
            r"\1",
            s,
        )

    return re.sub(r"<stage>.*?</stage>", fix_stage, xml, flags=re.S)


def validate(reverted_xml: str, original_xml: str):
    """Compare de-augmented text against the ground-truth original.
    Both sides have sound tags stripped so only the TEXT layer is compared.
    Returns (ok, n_diff, first_diff_index)."""
    a = strip_sound_tags(reverted_xml)
    b = strip_sound_tags(original_xml)
    if a == b:
        return True, 0, -1
    n = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                 min(len(a), len(b)))
    return False, n, first


def _report(name, reverted, original):
    if original is None:
        print(f"  {name:<45} NO-ORIGINAL")
        return True  # not a failure, just unvalidated
    ok, n, first = validate(reverted, original)
    if ok:
        print(f"  {name:<45} OK")
    else:
        a = strip_sound_tags(reverted)
        b = strip_sound_tags(original)
        print(f"  {name:<45} MISMATCH ({n} chars differ)")
        print(f"      reverted: {a[max(0,first-30):first+40]!r}")
        print(f"      original: {b[max(0,first-30):first+40]!r}")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Reverse and validate augmentation.")
    ap.add_argument("input", nargs="?", help="single augmented XML file")
    ap.add_argument("--original", help="ground-truth original for the single file")
    ap.add_argument("--indir", help="directory of augmented files")
    ap.add_argument("--origdir", help="directory of original (unannotated) files")
    ap.add_argument("--outdir", help="write reverted files here")
    ap.add_argument("--check-only", action="store_true",
                    help="validate but write no output")
    ap.add_argument("--strip-sound", action="store_true",
                    help="also strip sound tags from written output")
    args = ap.parse_args()

    all_ok = True

    if args.indir:
        if not args.check_only and not args.outdir:
            ap.error("--outdir is required unless --check-only")
        if args.outdir:
            os.makedirs(args.outdir, exist_ok=True)
        print("Reversal validation:")
        for fn in sorted(os.listdir(args.indir)):
            if not fn.endswith(".xml"):
                continue
            with open(os.path.join(args.indir, fn), encoding="utf-8") as f:
                aug = f.read()
            reverted = reverse_xml(aug)

            original = None
            if args.origdir:
                op = os.path.join(args.origdir, fn)
                if os.path.exists(op):
                    with open(op, encoding="utf-8") as f:
                        original = f.read()
            ok = _report(fn, reverted, original)
            all_ok = all_ok and ok

            if not args.check_only:
                out = strip_sound_tags(reverted) if args.strip_sound else reverted
                with open(os.path.join(args.outdir, fn), "w", encoding="utf-8") as f:
                    f.write(out)

    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            aug = f.read()
        reverted = reverse_xml(aug)
        if args.original:
            with open(args.original, encoding="utf-8") as f:
                original = f.read()
            ok = _report(os.path.basename(args.input), reverted, original)
            all_ok = all_ok and ok
        if not args.check_only:
            out = strip_sound_tags(reverted) if args.strip_sound else reverted
            sys.stdout.write(out)
    else:
        ap.print_help()
        return

    if not all_ok:
        sys.exit(1)   # gate a release: non-zero if any file failed validation


if __name__ == "__main__":
    main()
