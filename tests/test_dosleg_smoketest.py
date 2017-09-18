"""
Parse a sample of dosleg to smoke test the parser (no obvious errors)
"""
import os, random, json, sys

from senapy.dosleg.parser import parse

def test_dosleg_smoketest():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DIR = os.path.join(BASE_DIR, 'resources/recents_dosleg/')

    files = os.listdir(DIR)
    # random.shuffle(files)

    for file in files:
        path = os.path.join(DIR, file)
        print('## try', path)
        data = parse(open(path).read())
        # print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
        print()
        print('----')
