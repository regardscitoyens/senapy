# senapy
[![Build Status](https://travis-ci.org/regardscitoyens/senapy.svg?branch=master)](https://travis-ci.org/regardscitoyens/senapy) [![Coverage Status](https://coveralls.io/repos/github/regardscitoyens/senapy/badge.svg?branch=master)](https://coveralls.io/github/regardscitoyens/senapy?branch=master)

A python client for [senat.fr](https://senat.fr) website.

## Main goal

Retrieve painlessly JSON data from [senat.fr](https://senat.fr).

## Requirements

Python 3

## Install:

- from pip: `pip3 install senapy`
- locally: `pip3 install -e .`

## Dossiers Legislatifs

 - Parse one: `senapy-cli parse URL_or_filepath`
    - example: `senapy-cli parse pjl16-537` (instead of the URL, you can just give the ID)
    - warning: for now the file must be in UTF-8
 - Get all the urls: `senapy-cli doslegs_urls`
 - Parse many: `cat urls | senapy-cli parse_many output_dir`

## Search services

 * **QuestionSearchService** to search for questions

## Tests:

- `pip3 install pytest`
- `pytest`
- If you modify the output, there's an utility to make the tests reflect that: `python tests/tools/regen_regressions_output.py`
