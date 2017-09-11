import os, random, json

from parser import parse

DIR = 'tests/all_senat_dossiers/'

files = os.listdir(DIR)
random.shuffle(files)

for file in files:
    print('## try', DIR + file)
    data = parse(DIR + file)
    # print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    print()
    print('----')