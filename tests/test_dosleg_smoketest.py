"""
Parse a sample of dosleg to smoke test the parser (no obvious errors)
"""
import os

from senapy.dosleg.parser import parse

from lawfactory_utils.urls import enable_requests_cache


def test_dosleg_smoketest():
    enable_requests_cache()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DIR = os.path.join(BASE_DIR, 'resources/recents_dosleg/')

    files = os.listdir(DIR)

    for file in files:
        path = os.path.join(DIR, file)
        print('## try', path)
        parse(open(path).read())
