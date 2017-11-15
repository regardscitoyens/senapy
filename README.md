# senapy
[![Build Status](https://travis-ci.org/regardscitoyens/senapy.svg?branch=master)](https://travis-ci.org/regardscitoyens/senapy)

A python client for [senat.fr](https://senat.fr) website.

## Main goal

Retrieve painlessly JSON data from [senat.fr](https://senat.fr).

## Requirements

Python 3

## Install:

- From pip: `pip3 install senapy`
- Locally: `pip3 install -r requirements.txt`

## Test:

- `pip3 install pytest`
- `pytest`

## Search services

 * **QuestionSearchService** to search for questions

## Dossiers Legislatifs

 - Parse one: `senapy-cli parse URL_or_filepath`
    - warning: for now the file must be in UTF-8
 - Get all the urls: `senapy-cli doslegs_urls`
 - Parse many: `cat urls | senapy-cli parse_many output_dir`
