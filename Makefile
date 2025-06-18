mergeannotations: merge_annotations_into_tei.py annotations/ gdc-tei/
	python merge_annotations_into_tei.py --inputannotations annotations/ --inputtei manipulated_texts_generalized_approach/ --outputdir gdc-tei/enhanced/

creategenretable: create_genre_table.py gdc-tei/all/
	python create_genre_table.py --inputtei gdc-tei/all/ --outputfile ./genres.csv
