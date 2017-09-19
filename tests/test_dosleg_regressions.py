"""
Test if the parser has regressions by comparing the output with verified output
"""
import os, random, json, difflib, sys
from os.path import join

from senapy.dosleg.parser import parse
from .tools.compare_thelawfactory_and_me import compare
from .tools.compare_with_anpy import compare as compare_anpy

def test_dosleg_regressions():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DIR = sys.argv[1] if len(sys.argv) > 1 \
        else join(BASE_DIR, 'resources/verified_dosleg/')

    for test_dir in os.listdir(DIR):
        path = join(DIR, test_dir)
        print('## try', path)

        data = parse(open(join(path, 'input.html')).read())
        output = json.load(open(join(path, 'output.json')))

        data_json = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        output_json = json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)

        if data_json != output_json:
            diff = difflib.unified_diff(data_json.split('\n'), output_json.split('\n'))
            for line in diff:
                print(line)
        assert data_json == output_json

        if os.path.exists(join(path, 'lawfactory.json')):
            proc = json.load(open(join(path, 'lawfactory.json')))
            score_ok, score_nok = compare(proc, output)
            last_score_ok, last_score_nok = [int(x) for x in open(join(path, 'lawfactory_scores')).read().split('\n') if x]
            assert score_ok == last_score_ok
            assert score_nok == last_score_nok

        if os.path.exists(join(path, 'anpy.json')):
            anpy = json.load(open(join(path, 'anpy.json')))
            score_ok, score_nok = compare_anpy(anpy, output)
            last_score_ok, last_score_nok = [int(x) for x in open(join(path, 'anpy_scores')).read().split('\n') if x]
            assert score_ok == last_score_ok
            assert score_nok == last_score_nok
