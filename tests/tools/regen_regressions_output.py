import json, os

from senapy.dosleg.parser import parse

DIR = 'tests/resources/verified_dosleg/'

for file in os.listdir(DIR):
    result = parse(open(DIR+file+'/input.html'))
    json.dump(result, open(DIR+file+'/output.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)
