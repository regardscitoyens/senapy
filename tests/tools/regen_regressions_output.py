import json, os
from os.path import join

from senapy.dosleg.parser import parse
from compare_thelawfactory_and_me import compare
from compare_with_anpy import compare as compare_anpy
from compare_with_legipy import compare as compare_legipy

DIR = 'tests/resources/verified_dosleg/'

for file in os.listdir(DIR):
    path = DIR+file
    output = parse(open(path+'/input.html'))
    json.dump(output, open(DIR+file+'/output.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)

    if os.path.exists(join(path, 'lawfactory.json')):
        proc = json.load(open(join(path, 'lawfactory.json')))
        open(join(path, 'lawfactory_scores'), 'w').write('%d\n%d\n' % compare(proc, output))

    if os.path.exists(join(path, 'anpy.json')):
        anpy = json.load(open(join(path, 'anpy.json')))
        open(join(path, 'anpy_scores'), 'w').write('%d\n%d\n' % compare_anpy(anpy, output))

    if os.path.exists(join(path, 'legipy.json')):
        legipy = json.load(open(join(path, 'legipy.json')))
        open(join(path, 'legipy_scores'), 'w').write('%d\n%d\n' % compare_legipy(legipy, output))
