import json
import sys
import re
from urllib.parse import urljoin, parse_qs, urlparse

import requests
import dateparser
from bs4 import BeautifulSoup, Comment

from lawfactory_utils.urls import pre_clean_url, clean_url

def format_date(date):
    parsed = dateparser.parse(date, languages=['fr'])
    return parsed.strftime("%Y-%m-%d")


def parse(html, url_senat=None, logfile=sys.stderr):
    data = {}

    def log_error(error):
        print('## ERROR ###', error, file=logfile)

    # base_data = json.load(open(filename))
    soup = BeautifulSoup(html, 'lxml')

    # open('test.html', 'w').write(base_data['html'])
    # del base_data['html']
    # pp(base_data)

    data['short_title'] = soup.select_one('.title-dosleg').text.strip()

    if not soup.select('.title .subtitle-01'):
        log_error('NO TITLE - MAYBE A REDIRECT ?')
        return

    title_lines = soup.select_one('.title .subtitle-01').text.strip()
    data['long_title'] = title_lines.split('\n')[0][:-2]  # remove " :" at the end of the line
    data['long_title_descr'] = soup.find("meta", {"name": "Description"})['content']

    promulgee_line = None
    ordonnance_line = None
    acceleree_line = None
    cc_line = None
    for line in soup.select('.title .list-disc-03 li'):
        if ' parue ' in line.text:
            promulgee_line = line
        elif 'ordonnance' in line.text:
            ordonnance_line = line
        elif 'accélérée' in line.text or 'Urgence déclarée' in line.text:
            acceleree_line = line
        elif 'Décision du Conseil constitutionnel' in line.text:
            cc_line = line
        else:
            log_error('UNKNOWN SUBTITLE: %s' % line.text)
    if promulgee_line:
        data['end'] = format_date(promulgee_line.find('strong').text.split(' du ')[1].strip())  # promulgation
        data['end_jo'] = format_date(promulgee_line.text.split('JO ')[-1].split('du ')[-1].split('(')[0].strip())  # inscription aux JO
        if promulgee_line.find('a'):
            data['url_jo'] = clean_url(promulgee_line.find('a').attrs['href'])
            url_jo_params = parse_qs(urlparse(data['url_jo']).query)
            if 'cidTexte' in url_jo_params:
                data['legifrance_cidTexte'] = url_jo_params['cidTexte'][0]
        else:
            log_error('NO JO LINK')
    # TOPARSE: ordonnance_line
    # TOPARSE: CC decision

    data['urgence'] = acceleree_line is not None or 'procédure accélérée engagée par le' in title_lines
    if not url_senat:
        # the url is in a comment like "<!-- URL_SENAT=XXXX !-->" for downloaded pages
        comment = soup.find(text=lambda text: isinstance(text, Comment) and 'URL_SENAT' in text)
        if comment:
            url_senat = comment.split('=')[1].strip()
    if url_senat:
        data['url_dossier_senat'] = clean_url(url_senat)
        data['senat_id'] = data['url_dossier_senat'].split('/')[-1].replace('.html', '')
    else:
        url_senat = 'http://www.senat.fr/'

    # objet du texte (very basic)
    for div in soup.select('#main div.scroll'):
        if div.find('h3') and 'Objet du texte' in div.find('h3').text:
            data['objet_du_texte'] = div.text.replace('Objet du texte\n', '') \
                .replace("Lire le billet de l'Espace presse", '').strip()
            continue

    # TODO: selecteur foireux ?
    for link in soup.select('h4.title.title-06.link-type-02 a'):
        if 'Assemblée' in link.text:
            data['url_dossier_assemblee'] = link.attrs['href'].split('#')[0]
            data['assemblee_id'] = data['url_dossier_assemblee'].split('/')[-1].replace('.asp', '')
            legislature = data['url_dossier_assemblee'].split('.fr/')[1].split('/')[0]
            try:
                data['assemblee_legislature'] = int(legislature)
            except ValueError:  # strange link (old dosleg)
                log_error('NO LEGISLATURE IN AN LINK: ' + data['url_dossier_assemblee'])

    data['steps'] = []
    steps_shortcuts = soup.select('.list-timeline li')  # icons on top
    if not steps_shortcuts:
        log_error('VERY SPECIAL CASE - PAS DE NAVETTES NORMALES')
        return

    themes_box = soup.select_one('#box-themes')
    if themes_box:
        data['themes'] = [x.text.strip() for x in themes_box.select('.theme')]

        if 'Budget' in data['themes']:
            data['use_old_procedure'] = True

    if 'pjl' in data.get('senat_id', ''):
        data['proposal_type'] = 'PJL'
    elif 'ppl' in data.get('senat_id', ''):
        data['proposal_type'] = 'PPL'
    else:
        log_error('UNKNOWN PROPOSAL TYPE (PPL/PJL)')

    curr_institution = None
    curr_stage = None
    error_detection_last_date = None
    for item in soup.select('#box-timeline > div div'):
        if 'timeline-' in item.attrs.get('id', ''):
            step = {}

            timeline_index = int(item.attrs['id'].split('-')[1]) - 1
            step_shortcut = steps_shortcuts[timeline_index]

            section_title = item
            while section_title.previous_sibling and section_title.previous_sibling.name != 'h3':
                section_title = section_title.previous_sibling
            section_title = section_title.previous_sibling.text if section_title.previous_sibling else ''

            step['date'] = None
            if step_shortcut.select('em'):
                date_text = step_shortcut.select('em')[-1].text.strip()
                if '/' in date_text:
                    step['date'] = format_date(date_text)
            if not step['date']:
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
            # stage = 1ere lecture|2eme lecture|CMP
            # institution = assemblee|senat|CMP|gouvernement
            # step = depot|commission|hemicycle
            if step_shortcut.select_one('em'):
                titre = step_shortcut.select_one('em').text.lower().strip()
                if titre == 'loi' or 'promulgation' in titre:
                    curr_stage = 'promulgation'
                else:
                    curr_stage = step_shortcut.find('a').attrs['title'].split('|')[-1].split('-')[0].lower().strip()
                    if curr_stage == 'cmp':
                        curr_stage = 'CMP'

                # sometimes the lecture info is in the date, why not ?
                # ex: http://www.senat.fr/dossier-legislatif/a82831259.html
                if 'lecture' in date_text:
                    curr_stage = date_text

                img = step_shortcut.find('img').attrs['src']
                if 'picto_timeline_01_' in img:
                    curr_institution = 'assemblee'
                    step_step = 'depot'
                elif 'picto_timeline_02_' in img:
                    curr_institution = 'senat'
                    step_step = 'depot'
                elif 'picto_timeline_05_' in img:
                    curr_institution = 'CMP'
                    curr_stage = 'CMP'
                    # there is no "depot" step for a CMP
                    continue
                elif 'picto_timeline_03_' in img:
                    step_step = 'commission'
                elif 'picto_timeline_04_' in img:
                    step_step = 'hemicycle'
                elif 'picto_timeline_07_' in img:
                    curr_institution = 'gouvernement'
                elif 'picto_timeline_09_' in img:
                    # ex: http://www.senat.fr/dossier-legislatif/pjl02-182.html
                    curr_institution = 'nouv. délib.'
                elif 'picto_timeline_10_' in img:
                    curr_institution = 'congrès'

            if curr_stage == 'c. constit.':
                curr_institution = 'conseil constitutionnel'
                curr_stage = 'constitutionnalité'
                step_step = None

            # the picto can be the wrong one...also a depot step for a CMP doesn't makes sense
            # ex: http://www.senat.fr/dossier-legislatif/taan99-406.html
            if curr_stage == 'CMP' and step_step == 'depot':
                curr_institution = 'CMP'
                log_error('DEPOT STEP FOR A CMP')
                continue

            # no commissions for l. définitive
            if curr_stage == 'l. définitive' and step_step == 'commission':
                continue

            step['institution'] = curr_institution

            # standardize on 1ère lecture / 2ème lecture
            curr_stage = curr_stage.replace('eme', 'ème')

            if curr_institution != 'nouv. délib.':
                step['stage'] = curr_stage
                if curr_stage not in ('constitutionnalité', 'promulgation'):
                    step['step'] = step_step

            # fill in for special case like http://www.senat.fr/dossier-legislatif/csm.html
            if curr_institution == 'congrès' and not curr_stage:
                step['stage'] = 'congrès'
            if curr_institution == 'congrès' and not step_step:
                step['step'] = 'congrès'

            good_urls = []

            # nouv delib contains all the other steps, making it confusing
            # because there's no text for a nouv delib
            if curr_institution != 'nouv. délib.':

                if 'Texte renvoyé en commission' in item.text:
                    step['echec'] = 'renvoi en commission'
                else:
                    # TROUVONS LES TEXTES
                    for link in item.select('a'):
                        line = link.parent
                        if 'href' in link.attrs:
                            href = link.attrs['href']
                            nice_text = link.text.lower().strip()
                            # TODO: assemblée "ppl, ppr, -a0" (a verif)
                            if (
                                ('/leg/' in href and '/' not in href.replace('/leg/', '') and 'avis-ce' not in href)
                                or nice_text in ('texte', 'texte de la commission', 'décision du conseil constitutionnel')
                                or 'jo n°' in nice_text

                                # TODO: parse the whole block for date + url
                                # ex: http://www.senat.fr/dossier-legislatif/pjl08-641.html
                                or 'conseil-constitutionnel.fr/decision.' in href
                            ):

                                # motion for a referendum for example
                                # ex: http://www.senat.fr/dossier-legislatif/pjl12-349.html
                                if '/leg/motion' in href:
                                    continue
                                href = pre_clean_url(href)

                                url = urljoin(url_senat, href)
                                line_text = line.text.lower()
                                institution = curr_institution
                                if curr_stage != 'promulgation':  # TODO: be more specific, have a way to force the curr_instituion
                                    if 'par l\'assemblée' in line_text:
                                        institution = 'assemblee'
                                    elif 'par le sénat' in line_text:
                                        institution = 'senat'
                                    else:
                                        if curr_stage == 'CMP' and step_step == 'hemicycle' \
                                                and 'texte' in nice_text and not step.get('echec'):
                                            if 'assemblee-nationale.fr' in href:
                                                institution = 'assemblee'
                                            else:
                                                institution = 'senat'

                                # find all dates and take the last one
                                date = None
                                dates = [format_date(match.group(1)) for match in
                                    re.finditer(r"(\d\d? \w\w\w\w+ \d\d\d\d)", line_text)]
                                if dates:
                                    date = sorted(dates)[-1]
                                    if curr_stage == 'constitutionnalité' and len(dates) > 1:
                                        date = sorted(dates)[-2]

                                    if error_detection_last_date and dateparser.parse(error_detection_last_date) > dateparser.parse(date):
                                        # TODO: can be incorrect because of multi-depot
                                        log_error('DATE ORDER IS INCORRECT - last=%s - found=%s' % (error_detection_last_date, date))
                                    error_detection_last_date = date
                                if curr_stage == 'promulgation' and 'end' in data:
                                    date = data['end']

                                good_urls.append({
                                    'url': url,
                                    'institution': institution,
                                    'date': date,
                                })
                if not good_urls:
                    # sinon prendre une url d'un peu moins bonne qualité
                    if 'source_url' not in step:
                        for link in item.select('.list-disc-02 a'):
                            if 'href' in link.attrs:
                                href = link.attrs['href']
                                href = pre_clean_url(href)
                                nice_text = link.text.lower().strip()
                                if nice_text == 'rapport':
                                    step['source_url'] = urljoin(url_senat, href)
                                    break

                    if 'Texte retiré par' in item.text:
                        step['echec'] = "texte retiré"


                    if 'source_url' not in step and not step.get('echec'):
                        if step.get('institution') == 'assemblee' and 'assemblee_legislature' in data:
                            legislature = data.get('assemblee_legislature')
                            text_no_match = re.search(r'(Texte|Rapport)\s*n°\s*(\d+)', item.text, re.I)
                            if text_no_match:
                                text_no = text_no_match.group(2)
                                url = None
                                if step.get('step') == 'commission':
                                    url = 'http://www.assemblee-nationale.fr/{}/ta-commission/r{:04d}-a0.asp'
                                elif step.get('step') == 'depot':
                                    if step.get('proposal_type') == 'PJL':
                                        url = 'http://www.assemblee-nationale.fr/{}/projets/pl{:04d}.asp'
                                    else:
                                        url = 'http://www.assemblee-nationale.fr/{}/propositions/pion{:04d}.asp'
                                elif step.get('step') == 'hemicycle':
                                    url = 'http://www.assemblee-nationale.fr/{}/ta/ta{:04d}.asp'

                                if url:
                                    step['source_url'] = url.format(legislature, int(text_no))

                        if 'source_url' not in step:
                            log_error('ITEM WITHOUT URL TO TEXT - %s.%s.%s' % (step['institution'], step.get('stage'), step.get('step')))

            steps_to_add = []
            if good_urls:
                for url in good_urls:
                    sub_step = dict(**step)  # dubstep
                    sub_step['source_url'] = url['url']
                    sub_step['institution'] = url['institution']
                    if url['date']:
                        sub_step['date'] = url['date']
                    steps_to_add.append(sub_step)
            else:
                if 'source_url' in step:
                    step['source_url'] = step['source_url']
                steps_to_add.append(step)

            # remove CMP.CMP.hemicycle if it's a fail
            if step.get('stage') == 'CMP' and step.get('step') == 'hemicycle':
                if not good_urls:
                    last_step = data['steps'][-1]
                    if data['steps'][-1].get('stage') == 'CMP' and step.get('step') == 'hemicycle':
                        if 'désaccord' in section_title:
                            last_step['echec'] = 'echec'
                        else:
                            log_error('CMP.hemicycle with no links and no fail indicated')
                        continue
                elif len(good_urls) != 2:
                    log_error('CMP.hemicycle WITHOUT BOTH SENAT AND ASSEMBLEE')
                    # todo: add empty missing step
                    institutions_found = [url['institution'] for url in good_urls]
                    if 'assemblee' not in institutions_found:
                        sub_step = dict(**step)  # dubstep
                        sub_step['source_url'] = None
                        sub_step['institution'] = 'assemblee'
                        steps_to_add.append(sub_step)

            # clean urls
            for step in steps_to_add:
                url = step.get('source_url')
                if url:
                    step['source_url'] = clean_url(url)

            if len(steps_to_add) > 1:
                # multi-depot
                if step.get('step') == 'depot' and step.get('institution') == 'senat':
                    # put real text as last depot
                    steps_to_add = sorted(steps_to_add, key=lambda step: 1 if data.get('senat_id', '') in step.get('source_url', '') else 0)
                    # if we are in a later step, the others depot steps must go at the top
                    if len(data['steps']) > 0:
                        data['steps'] = steps_to_add[:-1] + data['steps']
                        steps_to_add = steps_to_add[-1:]
                # there can be multiple texts inside an hemicycle step, ok for CMP and multi-depots but not ok for other steps
                elif step.get('stage') != 'CMP':
                    log_error('MULTIPLE TEXTS BUT NOT CMP.hemicycle - %s.%s.%s' % (step['institution'], step.get('stage'), step.get('step')))
                    steps_to_add = [steps_to_add[-1]]

            data['steps'] += steps_to_add

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

# senat manque commision assemblee en CMP
# http://www.senat.fr/dossier-legislatif/pjl08-582.html

# http://www.assemblee-nationale.fr/13/cr-cafe/09-10/c0910061.asp => assemblee choper compte-rendus

# Echec en commission - "Résultat des travaux de la commission n° 732 (2012-2013) déposé le 9 juillet 2013"
