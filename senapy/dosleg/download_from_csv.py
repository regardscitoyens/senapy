import csv, pprint, json, time, sys

import requests, slugify


# TODO: download CSV from http://data.senat.fr/data/dosleg/dossiers-legislatifs.csv
filename = sys.argv[1] if len(sys.argv) > 1 else 'dossiers-legislatifs.csv'

lines = [{k.lower().replace(' ' ,'_'): v for k,v in line.items()}
            for line in list(csv.DictReader(open(filename, encoding='ISO-8859-1'), delimiter=';'))]

dest = sys.argv[2] if len(sys.argv) > 2 else 'senat_dossiers/'

if not os.path.exists(dest):
    os.makedirs(dest)

lines.sort(key=lambda line:int(line['date_initiale'].split('/')[-1])) # sort by year

for line in lines:
    year = int(line['date_initiale'].split('/')[-1])
    if year >= 2008:
        print(year)
        print(line['titre'])
        resp = requests.get(line['url_du_dossier'])
        open(dest + slugify.slugify(line['url_du_dossier']), 'w').write(resp.text)
        #pprint.pprint(line)
        time.sleep(0.2)
