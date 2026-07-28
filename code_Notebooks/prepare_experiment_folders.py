"""
prepare_experiment_folders.py
─────────────────────────────
Creates folder structures for 5 cross-validation experiments comparing
sound annotation performance with varying amounts of prose training data.

Experiment overview (all use 3-fold CV; test set is always 4 drama plays):
  Exp 1 : 8 drama train
  Exp 2 : 8 drama train + 8  prose train
  Exp 3 : 8 drama train + 16 prose train
  Exp 4 : 8 drama train + 32 prose train
  Exp 5 : 8 drama train + 64 prose train

Output structure:
  <OUTPUT_DIR>/
    exp1_drama_only/
      fold1/  train/  test/
      fold2/  train/  test/
      fold3/  train/  test/
    exp2_drama_8prose/
      fold1/  train/  test/
      ...
    ...

Files are *copied* (not moved) into each fold's train/ and test/ sub-folders.
The drama test split is a strict 3-fold partition of the 12 plays (4 per fold),
so no play ever appears in both train and test within the same fold.
Prose files are sampled randomly but independently for each fold.

Usage:
    python prepare_experiment_folders.py

    Optionally edit the three path constants below before running.
"""

import os
import random
import shutil
from pathlib import Path

# ── CONFIGURE PATHS HERE ──────────────────────────────────────────────────────
DRAMA_SRC  = "/Users/sguhr/Downloads/Sound_in_Drama-main/20260413_cross-validation_64_prose_8_plays/12_plays"
PROSE_SRC  = "/Users/sguhr/Downloads/Sound_in_Drama-main/20260413_cross-validation_64_prose_8_plays/64_prosa_sound_annotated"
OUTPUT_DIR = "/Users/sguhr/Downloads/Sound_in_Drama-main/20260413_3_field_cross_validation_experiments"

RANDOM_SEED = 42   # set to None for a different random split each run
# ─────────────────────────────────────────────────────────────────────────────

# Experiment definitions: (name, n_prose_train)
EXPERIMENTS = [
    ("exp1_drama_only",    0),
    ("exp2_drama_8prose",  8),
    ("exp3_drama_16prose", 16),
    ("exp4_drama_32prose", 32),
    ("exp5_drama_64prose", 64),
]

N_FOLDS        = 3
N_TEST_DRAMA   = 4   # plays per fold test set  (3 × 4 = 12 total)
N_TRAIN_DRAMA  = 8   # plays per fold train set (12 - 4 = 8)


def collect_xml_files(folder: str) -> list[Path]:
    """Return sorted list of all .xml files in *folder*."""
    p = Path(folder)
    if not p.is_dir():
        raise FileNotFoundError(f"Source folder not found: {folder}")
    files = sorted(p.glob("*.xml"))
    if not files:
        raise ValueError(f"No .xml files found in: {folder}")
    return files


def make_drama_folds(drama_files: list[Path], rng: random.Random) -> list[dict]:
    """
    Partition the 12 drama files into 3 non-overlapping folds.
    Each fold gets exactly N_TEST_DRAMA test files and N_TRAIN_DRAMA train files.

    Returns a list of dicts: [{'train': [...], 'test': [...]}, ...]
    """
    shuffled = drama_files[:]
    rng.shuffle(shuffled)

    folds = []
    for i in range(N_FOLDS):
        test  = shuffled[i * N_TEST_DRAMA : (i + 1) * N_TEST_DRAMA]
        train = [f for f in shuffled if f not in set(test)]
        assert len(test)  == N_TEST_DRAMA,  f"Expected {N_TEST_DRAMA} test files, got {len(test)}"
        assert len(train) == N_TRAIN_DRAMA, f"Expected {N_TRAIN_DRAMA} train files, got {len(train)}"
        assert not set(test) & set(train),  "Test/train overlap detected!"
        folds.append({"train": train, "test": test})
    return folds


def copy_files(file_list: list[Path], dest_dir: Path) -> None:
    """Copy every file in *file_list* into *dest_dir*, creating it if needed."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for src in file_list:
        shutil.copy2(src, dest_dir / src.name)


def build_experiment(
    exp_name: str,
    n_prose: int,
    drama_folds: list[dict],
    prose_files: list[Path],
    output_root: Path,
    rng: random.Random,
) -> None:
    """
    Build the folder structure for one experiment across all folds.
    """
    if n_prose > len(prose_files):
        raise ValueError(
            f"{exp_name}: requested {n_prose} prose files but only "
            f"{len(prose_files)} are available."
        )

    exp_dir = output_root / exp_name
    print(f"\n{'─'*60}")
    print(f"  {exp_name}  (prose per fold: {n_prose})")
    print(f"{'─'*60}")

    for fold_idx, fold in enumerate(drama_folds, start=1):
        fold_dir   = exp_dir / f"fold{fold_idx}"
        train_dir  = fold_dir / "train"
        test_dir   = fold_dir / "test"

        # Drama files
        drama_train = fold["train"]
        drama_test  = fold["test"]

        # Prose files: sample fresh for each fold (independent draws)
        prose_sample = rng.sample(prose_files, n_prose) if n_prose > 0 else []

        # Copy everything
        copy_files(drama_train + prose_sample, train_dir)
        copy_files(drama_test,                 test_dir)

        print(f"  fold{fold_idx}/train : {len(drama_train)} drama + {len(prose_sample)} prose"
              f"  →  {len(drama_train) + len(prose_sample)} files")
        print(f"  fold{fold_idx}/test  : {len(drama_test)} drama files")

        # Sanity: no filename overlap between train and test
        train_names = {f.name for f in drama_train + prose_sample}
        test_names  = {f.name for f in drama_test}
        overlap = train_names & test_names
        if overlap:
            raise RuntimeError(
                f"Filename collision in {exp_name}/fold{fold_idx}: {overlap}"
            )


def main() -> None:
    rng = random.Random(RANDOM_SEED)

    print("Collecting source files …")
    drama_files = collect_xml_files(DRAMA_SRC)
    prose_files = collect_xml_files(PROSE_SRC)
    print(f"  Drama files : {len(drama_files)}")
    print(f"  Prose files : {len(prose_files)}")

    if len(drama_files) != 12:
        print(f"  ⚠  Expected 12 drama files, found {len(drama_files)}. "
              "Proceeding, but fold sizes may differ from the spec.")

    # Build the 3-fold drama split once; reused across all experiments
    drama_folds = make_drama_folds(drama_files, rng)

    print("\nDrama fold split (same across all experiments):")
    for i, fold in enumerate(drama_folds, 1):
        test_names = [f.name for f in fold["test"]]
        print(f"  fold{i} test : {test_names}")

    output_root = Path(OUTPUT_DIR)
    output_root.mkdir(parents=True, exist_ok=True)

    for exp_name, n_prose in EXPERIMENTS:
        build_experiment(
            exp_name, n_prose,
            drama_folds, prose_files,
            output_root, rng,
        )

    print(f"\n✓ All experiments written to: {output_root}\n")

    # Print a compact directory tree summary
    print("Output structure:")
    for exp_name, _ in EXPERIMENTS:
        exp_dir = output_root / exp_name
        for fold_idx in range(1, N_FOLDS + 1):
            for split in ("train", "test"):
                d = exp_dir / f"fold{fold_idx}" / split
                n = len(list(d.glob("*.xml"))) if d.exists() else 0
                print(f"  {exp_name}/fold{fold_idx}/{split}/  ({n} files)")


if __name__ == "__main__":
    main()
