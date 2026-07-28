#!/usr/bin/env python3

"""
Script to merge metadata information and bring it into the correct
format for the paper.
"""

import pandas as pd
import numpy as np


def main():
    gerdracor_api_metadata = pd.read_csv("gerdracor_api_metadata.csv")
    stage_direction_counts = pd.read_csv("stage_counts.csv")
    genre_metadata = pd.read_csv("genres.csv")

    metadata = gerdracor_api_metadata.merge(
        stage_direction_counts, left_on="name", right_on="basename"
    ).merge(genre_metadata, on=["filename", "basename"])

    # When a play has more p than l elements, it is counted as
    # being written in prose, otherwise in verse
    metadata["verse"] = np.where(
        metadata["numOfL"] > metadata["numOfP"], "Yes", "No"
    )
    print(metadata.columns)

    # Select plays
    selected_plays = [
        "ayrer-fassnachtspil-wie-einem-weib-jhr-eygener-mann",
        "neuber-die-beschuetzte-schauspielkunst",
        "lessing-emilia-galotti",
        "schiller-die-raeuber",
        "guenderode-udohla",
        "chezy-der-neue-narziss",
        "ebner-eschenbach-die-veilchen",
        "dohm-ein-schuss-ins-schwarze",
        "dovsky-mona-lisa",
        "borchert-draussen-vor-der-tuer",
        "sachs-eulenspiegel-mit-dem-blauen-hosentuch",
        "wedekind-fruehlings-erwachen",
    ]
    metadata_paper = metadata.loc[metadata["basename"].isin(selected_plays)]

    # Select columns
    columns_to_keep = [
        "firstAuthor",
        "yearNormalized",
        "title",
        "genre",
        "verse",
        "numOfActs",
        "numOfScenes",
        "numOfSpeakers",
        "stage_total",
        "stage_within_speech",
        "stage_outside_speech",
    ]
    metadata_paper = metadata_paper[columns_to_keep]

    # Rename columns
    metadata_paper = metadata_paper.rename(
        columns={
            "firstAuthor": "Author",
            "yearNormalized": "Publication Year",
            "title": "Title",
            "genre": "Genre",
            "verse": "in Verse",
            "numOfActs": "Number of Acts",
            "numOfScenes": "Number of Scenes",
            "numOfSpeakers": "Number of Speakers",
            "stage_total": "Number of Stage Directions",
            "stage_within_speech": "Number of Stage Directions within Character Speech",
            "stage_outside_speech": "Number of Stage Directions outside Character Speech",
        }
    )

    print(
        metadata_paper.to_latex(
            index=False,
            na_rep="--",
            column_format="lrp{4cm}llp{1.5cm}p{1.5cm}p{2cm}p{2cm}p{2cm}p{2cm}",
        )
    )
    metadata_paper.to_csv("metadata.csv", index=False)


if __name__ == "__main__":
    main()
