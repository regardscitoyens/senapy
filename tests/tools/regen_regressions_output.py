import json
import os
from os.path import join

from senapy.dosleg.parser import parse
from compare_thelawfactory_and_me import compare
from compare_with_anpy import compare as compare_anpy
from compare_with_legipy import compare as compare_legipy

from anpy.dossier_like_senapy import parse as parse_an
from anpy.utils import json_dumps

from lawfactory_utils.urls import enable_requests_cache

enable_requests_cache()

DIR = 'tests/resources/verified_dosleg/'

for file in os.listdir(DIR):
    path = DIR+file

    with open(path+'/input.html') as f:
        output = parse(f)
    with open(DIR+file+'/output.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, sort_keys=True)

    if True:  # enable this if you want to regen anpy.json
        if os.path.exists(join(path, 'anpy.json')):
            result = parse_an(output['url_dossier_assemblee'])[0]
            with open(DIR + file + '/anpy.json', 'w') as f:
                f.write(json_dumps(result, ensure_ascii=False, indent=4, sort_keys=True))

    if os.path.exists(join(path, 'lawfactory.json')):
        with open(join(path, 'lawfactory.json')) as f:
            proc = json.load(f)
        open(join(path, 'lawfactory_scores'), 'w').write('%d\n%d\n' % compare(proc, output, verbose=False))

    if os.path.exists(join(path, 'anpy.json')):
        with open(join(path, 'anpy.json')) as f:
            anpy = json.load(f)
        open(join(path, 'anpy_scores'), 'w').write('%s' % compare_anpy(anpy, output, verbose=False))

    if os.path.exists(join(path, 'legipy.json')):
        legipy = json.load(open(join(path, 'legipy.json')))
        open(join(path, 'legipy_scores'), 'w').write('%d\n%d\n' % compare_legipy(legipy, output, verbose=False))
