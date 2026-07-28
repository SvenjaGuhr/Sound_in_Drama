metadata.csv: gerdracor_api_metadata.csv stage_counts.csv genres.csv
	python create_paper_metadata_table.py

gerdracor_api_metadata.csv:
	curl -X 'GET' 'https://dracor.org/api/v1/corpora/ger/metadata/csv' -H 'accept: text/csv' > gerdracor_api_metadata.csv

stage_counts.csv: count_stage_directions.py ../gdc-tei/all
	python count_stage_directions.py ../gdc-tei/all/ stage_counts.csv

genres.csv: create_genre_table.py ../gdc-tei/all/
	python create_genre_table.py --inputtei ../gdc-tei/all/ --outputfile ./genres.csv
