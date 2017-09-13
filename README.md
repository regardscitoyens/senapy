# senapy
A python client for http://senat.fr website

## Main goal
Retrieve painlessly json data from senat.fr

## Install :
```bash
pip install senapy
```

## Search services
 * **QuestionSearchService** to search for questions


## Dossiers Legislatifs

 - Parse one: `python tests/dosleg/parser.py URL_or_filepath`
 - Download all: `python tests/dosleg/download_from_csv.py dest_directory/`
 - Dowload recents: `python tests/dosleg/download_from_csv.py dest_directory/`
