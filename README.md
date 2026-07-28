# Sound in Drama

Repository for the paper **"What Does Drama Sound Like? Sound Analysis of GerDraCor."**

Guhr, Svenja / Pagel, Janis / Reiter, Nils (2026). "What Does Drama Sound Like? Sound Analysis of GerDraCor." In: *Journal of Computational Literary Studies* 5 (2).

An earlier version was presented at the Second Workshop on Computational Drama Analysis at the DraCor Summit (Berlin, 3 September 2025). The workshop preprint is available in the conference reader, doi: [10.5281/zenodo.16814034](https://doi.org/10.5281/zenodo.16814034). Workshop slides are [here](https://github.com/SvenjaGuhr/Sound_in_Drama/blob/main/20250903_Sound_in_GerDraCor.pdf).

A page with interactive supplementary visualizations is available [here](https://svenjaguhr.github.io/sound-in-drama). The static figures in the article correspond to the interactive versions, which allow hovering over individual data points to inspect play titles, years, and genre information.

<img width="2732" height="1003" alt="Sound_in_GerDraCor_Method" src="https://github.com/user-attachments/assets/5c4567f8-35e1-4fd8-abd5-2b31d6c3d4c5" />

## Overview

The project adapts a sound-event annotation and recognition method developed for German-language prose (Guhr 2026) to dramatic texts, using the German Drama Corpus ([GerDraCor](https://dracor.org/ger), Fischer et al. 2019). Twelve plays were manually annotated for character and ambient sound events. A pretrained German BERT model was fine-tuned in a series of 3-fold cross-validation experiments, and the resulting model was applied to the wider corpus to study how sound representation varies across periods, literary movements, and authors.

A rule-based **stage direction augmentation** heuristic sits at the center of the method: elliptical stage directions (for example a bare manner adverbial such as *sehr ruhig*) are completed with an inserted speech verb (*sagt* / *sagen*) so that their sound indications resemble the prose training examples. The augmentation is applied before both annotation and prediction, and is reversed after prediction.

## Installation

Requires **Python 3.10 or newer**.

```bash
pip install -r requirements.txt
python -m spacy download de_core_news_sm
python -m spacy download de_core_news_md
```

The two spaCy German models are not on PyPI and must be installed with the two `spacy download` commands above. `de_core_news_sm` is used for the augmentation heuristic and post-processing; `de_core_news_md` is used for the stage-direction frequency analysis.

## Pipeline

The numbered files run in order. Preprocessing and text-manipulation utilities are called by these steps.

| Step | File | Purpose |
|---|---|---|
| 1 | `01_augment_stage_directions.py` | Insert *sagt* / *sagen* into elliptical stage directions (the augmentation heuristic). |
| 2 | `02_postprocessing.ipynb` | Clean the model's raw prediction output (merge fragmented spans, remove structural false positives). |
| 3 | `03_evaluation.ipynb` | Compute token-level, span-detection, span-classification, E-F1, and Gamma agreement scores. |
| 4 | `04_reverse_augmentation.py` | Remove the inserted verbs and validate the de-augmented text against the original play. |
| 5 | `05_Sound_in_Drama_Analysis.ipynb` | Sound Event Density (SED) analysis across periods, movements, and authors. |

### Supporting scripts

- `20250727_drama_preprocessing.py` — strip page breaks, emphasis, and inline line breaks from the TEI before annotation.
- `20250730_predicted_xml-file_cleaning.py` — additional post-processing of predicted XML (merging and de-duplicating adjacent sound tags).
- `remove_false_positive_sounds.py` — delete sound tags whose text matches a known false-positive phrase list.
- `remove_sagt_sagen_from_stage.py` — remove inserted *sagt* / *sagen* directly following a `<stage>` opening.
- `merge_annotations_into_tei.py` — merge annotations from CSV back into the original GerDraCor TEI.
- `create_genre_table.py` — extract genre labels from play self-ascriptions in the TEI subtitle.
- `analyze_stage_frequency.py` — count stage directions and their length relative to spoken text (stage direction density).
- `prepare_experiment_folders.py` — build the 3-fold cross-validation folder structure (Exp. 0'–4').
- `sound_stage_correlation.ipynb`, `stage_direction_analysis.ipynb` — correlation of SED with stage direction density and other play-level measures.

## Cross-validation experiments

The twelve annotated plays are rotated across three folds (four held out per fold), with the fold split fixed across all configurations. Prose texts from Guhr (2026) are added in increasing amounts to a constant set of eight augmented plays:

| Configuration | Drama (augmented) | Prose |
|---|---|---|
| Exp. 0' | 8 | 0 |
| Exp. 2' | 8 | 8 |
| Exp. 3' | 8 | 16 |
| Exp. 4' | 8 | 32 |
| Exp. 1' | 8 | 64 |

Unprimed configurations (Exp. 0, Exp. 1) use the original, non-augmented plays. See the paper for details and results.

## Repository structure

```
Sound_in_Drama/
├── 01_augment_stage_directions.py
├── 02_postprocessing.ipynb
├── 03_evaluation.ipynb
├── 04_reverse_augmentation.py
├── 05_Sound_in_Drama_Analysis.ipynb
├── requirements.txt
├── data/
│   └── *.xml                  (sound-annotated plays)
│   
└── output/                    (created automatically)
```

## Data availability

The GerDraCor source corpus is available from [DraCor](https://github.com/dracor-org/gerdracor). Note that the sound-annotated corpus released here is not byte-identical to the GerDraCor source: the augmentation step alters whitespace and line breaks in the TEI in ways that cannot be reliably reversed, so those changes are retained. Comparisons within the corpus remain valid, since every play was processed identically.

## Citation

```bibtex
@article{guhr2026drama,
  author  = {Guhr, Svenja and Pagel, Janis and Reiter, Nils},
  title   = {What Does Drama Sound Like? Sound Analysis of GerDraCor},
  journal = {Journal of Computational Literary Studies},
  volume  = {5},
  number  = {2},
  year    = {2026}
}
```
