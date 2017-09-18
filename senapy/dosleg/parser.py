import json, sys
from pprint import pprint as pp
from urllib.parse import urljoin, parse_qs, urlparse

import requests
import dateparser
from bs4 import BeautifulSoup


def log_error(error):
    print('## ERROR ###', error, file=sys.stderr)


def format_date(date):
    parsed = dateparser.parse(date, languages=['fr'])
    return parsed.strftime("%Y-%m-%d")


def parse(html, url_senat=None):
    data = {}

    # base_data = json.load(open(filename))
    soup = BeautifulSoup(html, 'lxml')

    # open('test.html', 'w').write(base_data['html'])
    # del base_data['html']
    # pp(base_data)

    data['short_title'] = soup.select('.title-dosleg')[0].text.strip()

    if not soup.select('.title .subtitle-01'):
        log_error('NO TITLE - MAYBE A REDIRECT ?')
        return

    data['long_title'] = soup.select('.title .subtitle-01')[0].text.strip()[:-2]
    data['long_title_descr'] = soup.find("meta", {"name":"Description"})['content']

    promulgee_line = None
    ordonnance_line = None
    acceleree_line = None
    for line in soup.select('.title .list-disc-03 li'):
        if ' parue ' in line.text:
            promulgee_line = line
        elif 'ordonnance' in line.text:
            ordonnance_line = line
        elif 'accélérée' in line.text:
            acceleree_line = line
        else:
            log_error('UNKNOWN SUBTITLE: %s' % line.text)
    if promulgee_line:
        data['end'] = format_date(promulgee_line.find('strong').text.split(' du ')[1].strip()) # promulgation
        data['end_jo'] = format_date(promulgee_line.text.split('JO n')[1].split(' du ')[1].split('(')[0].strip()) # inscription aux JO
        if promulgee_line.find('a'):
            data['url_jo'] = promulgee_line.find('a').attrs['href'].replace(';jsessionid=','')
            url_jo_params = parse_qs(urlparse(data['url_jo']).query)
            if 'cidTexte' in url_jo_params:
                data['legifrance_cidTexte'] = url_jo_params['cidTexte'][0]
        else:
            log_error('NO JO LINK')
    # TOPARSE: ordonnance_line

    data['urgence'] = acceleree_line is not None
    if url_senat:
        data['url_dossier_senat'] = url_senat
        data['senat_id'] = data['url_dossier_senat'].split('/')[-1].replace('.html', '')
    else:
        url_senat = 'http://www.senat.fr/'

    # TODO: selecteur foireux ?
    for link in soup.select('h4.title.title-06.link-type-02 a'):
        if 'Assemblée' in link.text:
            data['url_dossier_assemblee'] = link.attrs['href']
            data['assemblee_id'] = data['url_dossier_assemblee'].split('/')[-1].replace('.asp', '')
            data['assemblee_legislature'] = int(data['url_dossier_assemblee'].split('assemblee-nationale.fr/')[1].split('/')[0])

    data['steps'] = []
    steps_shortcuts = soup.select('.list-timeline li') # icons on top
    if not steps_shortcuts:
        log_error('VERY SPECIAL CASE - PAS DE NAVETTES NORMALES')
        return

    curr_institution = None
    curr_stage = None
    for item in soup.select('#box-timeline > div > div'):
        if 'timeline-' in item.attrs.get('id', ''):
            step = {}

            timeline_index = int(item.attrs['id'].split('-')[1]) - 1
            step_shortcut = steps_shortcuts[timeline_index]

            step['date'] = None
            if step_shortcut.select('em'):
                step['date'] = format_date(step_shortcut.select('em')[-1].text.strip())
            else:
                # TODO: date sometimes is not on the shortcut
                log_error('SHORCUT WITHOUT DATE')

            if timeline_index == 0:
                data['beginning'] = step['date']

            # TODO review this part
            step_step = step_shortcut.find('a').attrs['title'].split('|')[-1].split('-')[-1].lower().strip()
            if 'commission' in step_step:
                step_step = 'commission'
            elif 'séance' in step_step:
                step_step = 'hemicycle'

            # TODO: ca me parait bizarre cette histoire
            # stage = 1ere lecture|2nd lecture|CMP
            # institution = assemblee|senat|CMP|gouvernement
            # step = depot|commission|hemicycle
            if len(step_shortcut.select('em')) > 0:
                titre = step_shortcut.select('em')[0].text.lower().strip()
                if titre == 'loi' or 'promulgation' in titre:
                    curr_stage = 'promulgation'
                else:
                    curr_stage = step_shortcut.find('a').attrs['title'].split('|')[-1].split('-')[0].lower().strip()
                    if curr_stage == 'cmp':
                        curr_stage = 'CMP'
                img = step_shortcut.find('img').attrs['src']
                if 'picto_timeline_01_' in img:
                    curr_institution = 'assemblee'
                    step_step = 'depot'
                elif 'picto_timeline_02_' in img:
                    curr_institution = 'senat'
                    step_step = 'depot'
                elif 'picto_timeline_05_' in img:
                    curr_institution = 'CMP'

                    # there is no "depot" step for a CMP
                    continue
                elif 'picto_timeline_03_' in img:
                    step_step = 'commission'
                elif 'picto_timeline_04_' in img:
                    step_step = 'hemicycle'
                elif 'picto_timeline_07_' in img:
                    curr_institution = 'gouvernement'

                if curr_stage == 'c. constit.':
                    curr_institution = 'conseil constitutionnel'
                    curr_stage = 'constitutionnalité'
                    step_step = None
            step['institution'] = curr_institution
            step['stage'] = curr_stage
            if curr_stage not in ('constitutionnalité', 'promulgation'):
                step['step'] = step_step

            good_urls = []
            ## TROUVONS LES TEXTES
            for link in item.select('a'):
                line = link.parent
                if 'href' in link.attrs:
                    href = link.attrs['href']
                    nice_text = link.text.lower().strip()
                    # TODO: "Texte de la commission"
                    # TODO: assemblée "ppl, ppr, -a0" (a verif)
                    #
                    if (
                        ('/leg/' in href and '/' not in href.replace('/leg/', ''))
                        or nice_text in ('texte', 'texte de la commission', 'décision du conseil constitutionnel') \
                        or 'jo n°' in nice_text
                        ):

                        url = urljoin(url_senat, href)
                        line_text = line.text.lower()
                        institution = curr_institution
                        if 'par l\'assemblée' in line_text:
                            institution = 'assemblee'
                        elif 'par le sénat' in line_text:
                            institution = 'senat'
                        good_urls.append({
                            'url': url,
                            'institution': institution,
                        })
            if not good_urls:
                # sinon prendre une url d'un peu moins bonne qualité
                if 'source_url' not in step:
                    for link in item.select('.list-disc-02 a'):
                        if 'href' in link.attrs:
                            href = link.attrs['href']
                            nice_text = link.text.lower().strip()
                            if nice_text == 'rapport':
                                step['source_url'] = urljoin(url_senat, href)
                                break
                if 'source_url' not in step:
                    # TODO: NO TEXT LINK ! TAKE NUMERO AND DATE
                    log_error('ITEM WITHOUT URL TO TEXT - %s.%s.%s' % (step['institution'], step['stage'], step.get('step')))

            if good_urls:
                for url in good_urls:
                    clean_url = url['url'].replace(';jsessionid=', '') # cleaning
                    sub_step = {**step} # dubstep
                    sub_step['source_url'] = clean_url
                    sub_step['institution'] = url['institution']
                    data['steps'].append(sub_step)
            else:
                if 'source_url' in step:
                    step['source_url'] = step['source_url'].replace(';jsessionid=','')
                data['steps'].append(step)

            # TODO: if not both CMP.hemicycle.{senat|assemblee}, there's a problem
            if step.get('stage') == 'CMP' and step.get('step') == 'hemicycle' and (not good_urls or len(good_urls) != 2):
                log_error('CMP.hemicycle WITHOUT BOTH SENAT AND ASSEMBLEE')
                # todo: add empty missing step
                institutions_found = [url['institution'] for url in good_urls]
                if 'assemblee' not in institutions_found:
                    sub_step = {**step} # dubstep
                    sub_step['source_url'] = None
                    sub_step['institution'] = 'assemblee'
                    data['steps'].append(sub_step)

    return data


if __name__ == '__main__':
    url = sys.argv[1]
    if url.startswith('http'):
        html = requests.get(url).text
        data = parse(html, url)
    else:
        html = open(url).read()
        data = parse(html)
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


# TOPARSE
# Lire le billet de l'Espace presse
# Objet du texte
# RSS
# Dossier d'information
# Themes
# Cette page a été générée le 14 juillet 2017


# D�cision du CC
# Décision du Conseil constitutionnel n° 2016-741 DC du 8 décembre 2016 (non conforme)

# http://www.senat.fr/dossier-legislatif/pjl09-344.html => multiple text, do as multiple "depot" steps
# => or "extra_text" and sort to have the main text as the last "depot" step
# http://www.senat.fr/dossier-legislatif/pjl11-592.html
# https://www.lafabriquedelaloi.fr/articles.html?loi=pjl12-688

# http://www.senat.fr/dossier-legislatif/pjl11-720.html
# texte retiré

# TODO: ECHEC = PAS DE TEXTE
# ex: http://www.senat.fr/dossier-legislatif/ppl09-422.html
# caduc = step

# Dossier d'information - http://www.senat.fr/dossier-legislatif/pjl10-438.html

# Comptes rendus des réunions des commissions
# Compte rendu intégral des débats


# 3eme lecture
# http://www.senat.fr/dossier-legislatif/pjl08-460.html

# senat manque commision assemblee en CMP
# http://www.senat.fr/dossier-legislatif/pjl08-582.html

# todo: order CMP hemicycle senat->assemblee

# http://www.assemblee-nationale.fr/13/cr-cafe/09-10/c0910061.asp => assemblee choper compte-rendus
