# senapy
[![Build Status](https://travis-ci.org/regardscitoyens/senapy.svg?branch=master)](https://travis-ci.org/regardscitoyens/senapy)
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

 - Parse one: `python senapy/dosleg/parser.py URL_or_filepath`
    - warning: for now the file must be in UTF-8
 - Download all: `python tests/dosleg/download_from_csv.py dest_directory/`
 - Dowload recents: `python tests/dosleg/download_from_csv.py dest_directory/`
