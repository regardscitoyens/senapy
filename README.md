# senapy
[![Build Status](https://travis-ci.org/regardscitoyens/senapy.svg?branch=master)](https://travis-ci.org/regardscitoyens/senapy)
A python client for http://senat.fr website

## Main goal
Retrieve painlessly json data from senat.fr

## Install :
```bash
pip install senapy (or "pip install -e ."" locally)
```

## Search services
 * **QuestionSearchService** to search for questions


## Dossiers Legislatifs

 - Parse one: `senapy-cli parse URL_or_filepath`
    - warning: for now the file must be in UTF-8
 - Get all the urls: `senapy-cli doslegs_urls`
 - Parse many: `cat urls | senapy-cli parse_many output_dir`
