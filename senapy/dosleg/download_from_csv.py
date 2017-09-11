import csv, pprint, requests, json, time, sys

FILE = sys.argv[1] if len(sys.argv) > 1 else 'dossiers-legislatifs.csv'

# import chardet
# encoding = chardet.detect(open(FILE, 'rb').read())['encoding']

lines = [{k.lower().replace(' ' ,'_'): v for k,v in line.items()}
            for line in list(csv.DictReader(open(FILE), delimiter=';'))]

lines.sort(key=lambda line:int(line['date_initiale'].split('/')[-1])) # sort by year

for line in lines:
    year = int(line['date_initiale'].split('/')[-1])
    if year >= 2008:
        print(year)
        print(line['titre'])
        resp = requests.get(line['url_du_dossier'])
        line['html'] = resp.text
        open('tests/all_senat_dossiers/' + line['numéro_de_la_loi'] + '_' + line['titre'].lower().replace(' ', '_').replace('/','')[:100] + '.json', 'w') \
            .write(json.dumps(line, ensure_ascii=False, indent=2, sort_keys=True))
        #pprint.pprint(line)
        time.sleep(0.2)