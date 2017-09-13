"""
Test if the parser has regressions by comparing the output with verified output
"""

import os, random, json, difflib, sys

from senapy.dosleg.parser import parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR = sys.argv[1] if len(sys.argv) > 1 \
    else os.path.join(BASE_DIR, 'resources/verified_dosleg/')

for test_dir in os.listdir(DIR):
    path = DIR + test_dir
    print('## try', path)

    data = parse(path + '/input.json')
    output = json.load(open(path + '/output.json'))

    data_json = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    output_json = json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)

    if data_json != output_json:
        print('different !')
        diff = difflib.unified_diff(data_json.split('\n'), output_json.split('\n'))
        for line in diff:
            print(line)
    else:
        print('success')
    print('----')