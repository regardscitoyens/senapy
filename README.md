# senapy
[![Build Status](https://travis-ci.org/regardscitoyens/senapy.svg?branch=master)](https://travis-ci.org/regardscitoyens/senapy)

A python client for [senat.fr](https://senat.fr) website.

## Main goal

Retrieve painlessly JSON data from [senat.fr](https://senat.fr).

## Requirements

Python 3

## Install:

- from pip: `pip3 install senapy`
- locally: `pip3 install -e .`

## Test:

- `pip3 install pytest`
- `pytest`

## Dossiers Legislatifs

 - Parse one: `senapy-cli parse URL_or_filepath`
    - example: `senapy-cli parse pjl16-537` (instead of the URL, you can just give the ID)
    - warning: for now the file must be in UTF-8
 - Get all the urls: `senapy-cli doslegs_urls`
 - Parse many: `cat urls | senapy-cli parse_many output_dir`

## Search services

 * **QuestionSearchService** to search for questions

