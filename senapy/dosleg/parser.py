import json
import sys
import re
from urllib.parse import urljoin, parse_qs, urlparse

import requests
import dateparser
from bs4 import BeautifulSoup, Comment

from lawfactory_utils.urls import pre_clean_url, clean_url, download, parse_national_assembly_url

re_clean_spaces = re.compile(r'\s+')
clean_spaces = lambda x: re_clean_spaces.sub(' ', x)


def format_date(date):
    parsed = dateparser.parse(date, languages=['fr'])
    return parsed.strftime("%Y-%m-%d")


def parse_table_concordance(url):
    html = download(url).text
    soup = BeautifulSoup(html, 'html5lib')

    old_to_adopted = {}
    confusing_entries = set()

    rows = soup.select('div[align="center"] > table tr') + soup.select('div[align="left"] > table tr')

    def normalize(entry):
        if entry.lower() in ('unique', '1'):
            return '1er'
        return entry

    def add(old, adopted):
        nonlocal old_to_adopted, confusing_entries
        if ' et ' in old:
            for el in old.split(' et '):
                add(el, adopted)
            return
        adopted, old = normalize(adopted), normalize(old)
        if adopted.lower() in ('id', 'idem'):  # id: Abbreviation of the Latin idem (“same”)
            adopted = old
        if adopted == '':
            adopted = 'supprimé'
        if 'suppr' in adopted.lower():
            adopted = adopted.lower()
        if old in old_to_adopted:
            print('## ERROR ###', 'DOUBLE ENTRY IN CONCORDANCE TABLE FOR', old, file=sys.stderr)
            confusing_entries.add(old)
        else:
            if 'suppr' not in adopted and adopted in old_to_adopted.values():
                print('## WARNING ###', 'MULTIPLE ARTICLES MERGED INTO ONE IN CONCORDANCE TABLE FOR', adopted, file=sys.stderr)
                adopted += ' (supprimé)'
            old_to_adopted[old] = adopted

    for line in rows:
        cells = [x.text.strip() for x in line.select('td')]
        old, adopted, *_ = cells
        if 'numérotation' in old.lower() or not old:
            continue
        add(old, adopted)

        # there can be two concordances per line
        # ex: https://www.senat.fr/dossier-legislatif/tc/tc_pjl08-155.html
        if len(cells) == 5:
            *_, old, adopted = cells
            add(old, adopted)

    for entry in confusing_entries:
        del old_to_adopted[entry]

    return old_to_adopted, list(confusing_entries)


def find_an_url(data):
    if not data['steps']:
        return
    an_text_url = [step['source_url'] for step in data['steps'] if step.get('source_url') and 'assemblee-nationale' in step.get('source_url')]
    for url in an_text_url:
        html = download(url).text
        soup = BeautifulSoup(html, 'lxml')
        btn = soup.select_one('#btn_dossier')
        if btn:
            a = btn.parent
            if a.attrs.get('href'):
                return clean_url(urljoin(url, a.attrs['href']))


def find_date(line, curr_stage=None):
    # find all dates and take the last one
    dates = [format_date(match.group(1)) for match in re.finditer(r"(\d\d? \w\w\w+ \d\d\d\d)", line)]
    if curr_stage == 'constitutionnalité' and len(dates) > 1:
        return sorted(dates)[-2]
    if dates:
        return sorted(dates)[-1]


def guess_senate_text_url(item_text, step, data):
    text_num_match = re.search(r'(\n|^)Texte( de la commission)?\s*n°\s*'
                               r'(?P<num>\d+)\s*'
                               r'(\(\s*20(?P<year>\d\d)\s*-\s*20\d\d\s*\))?',
                               item_text, re.I)
    if text_num_match:
        text_num = text_num_match.group('num')
        prefix = data['senat_id'].split('-')[0]
        if step.get('step') == 'hemicycle':
            prefix = prefix.replace(data.get('proposal_type').lower(), 'tas')

        # find text year in the item text
        text_year = text_num_match.group('year')
        # or guess it from the step date
        if not text_year:
            text_year = int(step["date"][2:4])
            step_month = int(step["date"][5:7])
            if step_month < 10:
                text_year -= 1

        prefix = '%s%02d' % (prefix[:-2], int(text_year))
        return 'https://www.senat.fr/leg/{}-{}.html'.format(prefix, text_num)


def parse(html, url_senat=None, logfile=sys.stderr):
    data = {}

    def log_error(error):
        print('## ERROR ###', error, file=logfile)

    soup = BeautifulSoup(html, 'html5lib')

    data['short_title'] = clean_spaces(soup.select_one('.title-dosleg').text.strip())

    if not soup.select('.title .subtitle-01'):
        log_error('NO TITLE - MAYBE A REDIRECT ?')
        return

    title_lines = soup.select_one('.title .subtitle-01').text.strip()
    data['long_title_descr'] = clean_spaces(title_lines.split('\n')[0][:-2])  # remove " :" at the end of the line
    data['long_title'] = clean_spaces(soup.find("meta", {"name": "Description"})['content'])

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
        data['law_name'] = clean_spaces(promulgee_line.find('strong').text.strip())  # promulgation
        data['end'] = format_date(promulgee_line.text.split('JO ')[-1].split('du ')[-1].split('(')[0].strip())  # inscription aux JO
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

    tableau_comparatif = soup.select_one('.button-tableau-comparatifs')
    if tableau_comparatif:
        data['tableau_comparatif_url'] = clean_url(urljoin(url_senat, tableau_comparatif.attrs['href']))

    # objet du texte (very basic)
    for div in soup.select('#main div.scroll'):
        if div.find('h3') and 'Objet du texte' in div.find('h3').text:
            data['objet_du_texte'] = div.text.replace('Objet du texte\n', '') \
                .replace("Lire le billet de l'Espace presse", '').strip()
            continue

    # TODO: selecteur foireux ?
    for link in soup.select('h4.title.title-06.link-type-02 a'):
        if 'Assemblée' in link.text:
            url_an = link.attrs['href']
            if 'documents/index-' not in url_an:
                data['url_dossier_assemblee'] = clean_url(url_an)
                legislature, data['assemblee_slug'] = parse_national_assembly_url(data['url_dossier_assemblee'])
                if legislature:
                    data['assemblee_legislature'] = legislature
                else:
                    log_error('NO LEGISLATURE IN AN LINK: ' + url_an)
                data['assemblee_id'] = '%d-%s' % (data.get('assemblee_legislature', ''), data['assemblee_slug'])
            else:
                log_error('INVALID URL AN: ' + url_an)

    data['steps'] = []
    steps_shortcuts = soup.select('.list-timeline li')  # icons on top
    if not steps_shortcuts:
        log_error('VERY SPECIAL CASE - PAS DE NAVETTES NORMALES')
        return

    themes_box = soup.select_one('#box-themes')
    if themes_box:
        data['themes'] = [x.text.strip() for x in themes_box.select('.theme')]

    for t in [
            'financement de la sécurité',
            'règlement des comptes',
            'règlement du budget',
            'approbation des comptes',
            'loi de finances rectificative',
            'loi de financement rectificative',
            'de loi constitutionnelle'
        ]:
        if t in data['long_title']:
            data['use_old_procedure'] = True
    if 'plfss' in data.get('senat_id', '') or 'pjlf' in data.get('senat_id', ''):
        data['use_old_procedure'] = True

    if 'pjl' in data.get('senat_id', '') or 'plfss' in data.get('senat_id', ''):
        data['proposal_type'] = 'PJL'
    elif 'ppl' in data.get('senat_id', ''):
        data['proposal_type'] = 'PPL'
    else:
        log_error('UNKNOWN PROPOSAL TYPE (PPL/PJL)')

    steps_contents = []
    for item in soup.select('#box-timeline > div div'):
        if 'timeline-' in item.attrs.get('id', ''):
            steps_contents.append(item)

    curr_institution = None
    curr_stage = None
    error_detection_last_date = None
    for timeline_index, step_shortcut in enumerate(steps_shortcuts):
        step = {}

        item = BeautifulSoup('', 'lxml') # no info block for steps in the futur
        if len(steps_contents) > timeline_index:
            item = steps_contents[timeline_index]

        section_title = item
        while section_title.previous_sibling and section_title.previous_sibling.name != 'h3':
            section_title = section_title.previous_sibling
        section_title = section_title.previous_sibling.text if section_title.previous_sibling else ''

        step['date'] = None
        if step_shortcut.select('em'):
            date_text = step_shortcut.select('em')[-1].text.strip()
            if '/' in date_text:
                step['date'] = format_date(date_text)
        if not step['date'] and item.text:
            # TODO: date sometimes is not on the shortcut
            log_error('SHORCUT WITHOUT DATE')

        if 'beginning' not in data and step['date']:
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
                # 'nouv. délib.' ex: http://www.senat.fr/dossier-legislatif/pjl02-182.html
                continue
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

        step['stage'] = curr_stage
        if curr_stage not in ('constitutionnalité', 'promulgation'):
            step['step'] = step_step

        # fill in for special case like http://www.senat.fr/dossier-legislatif/csm.html
        if curr_institution == 'congrès' and not curr_stage:
            step['stage'] = 'congrès'
        if curr_institution == 'congrès' and not step_step:
            step['step'] = 'congrès'
        # pass congrés if not hemicycle
        if step.get('step') == 'congrès': continue

        # add a legislature guess if missing
        if curr_institution == 'assemblee' and step['date']:
            if '2007-06-20' <= step['date'] <= '2012-06-19':
                data['assemblee_legislature'] = 13
            elif '2012-06-20' <= step['date'] <= '2017-06-20':
                data['assemblee_legislature'] = 14
            elif '2017-06-21' <= step['date'] <= '2022-06-20':
                data['assemblee_legislature'] = 15


        good_urls = []

        if 'Texte renvoyé en commission' in item.text:
            step['echec'] = 'renvoi en commission'
        elif item.text:
            # TROUVONS LES TEXTES
            for link in item.select('a'):
                line = link.parent

                if 'Lettre rectificative' in link.text:
                    continue

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
                        # if we detect a "texte de la commission" in an old procedure, it means it's probably not the old procedure
                        if data.get('use_old_procedure') and nice_text == 'texte de la commission' and step.get('stage') != 'CMP':
                            del data['use_old_procedure']

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

                        date = find_date(line_text, curr_stage)
                        if date:
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



        if not good_urls and item.text:
            # sinon prendre une url d'un peu moins bonne qualité

            if 'Texte retiré par' in item.text:
                # texte retiré means all the previous steps become useless except the depot
                data['steps'] = [step for step in data['steps'] if step.get('step') == 'depots']
                continue
            elif 'Texte rejeté par' in item.text:
                step['echec'] = "rejet"

            if 'source_url' not in step and not step.get('echec'):
                # trouver les numeros dans le texte
                if curr_institution == 'senat' and step.get('date'):
                    url = guess_senate_text_url(item.text, step, data)
                    if url:
                        step['source_url'] = url

                if 'source_url' not in step:
                    # prendre un rapport
                    for link in item.select('.list-disc-02 a'):
                        if 'href' in link.attrs:
                            href = link.attrs['href']
                            href = pre_clean_url(href)
                            nice_text = link.text.lower().strip()
                            if nice_text == 'rapport' or nice_text == 'rapport général':
                                step['source_url'] = urljoin(url_senat, href)
                                break

                if 'source_url' not in step and step.get('institution') == 'assemblee' and 'assemblee_legislature' in data:
                    legislature = data['assemblee_legislature']
                    text_num_match = re.search(r'(Texte|Rapport)\s*n°\s*(\d+)', item.text, re.I)
                    if text_num_match:
                        text_num = text_num_match.group(2)
                        url = None
                        if step.get('step') == 'commission':
                            url = 'http://www.assemblee-nationale.fr/{}/ta-commission/r{:04d}-a0.asp'
                        elif step.get('step') == 'depot':
                            if data.get('proposal_type') == 'PJL':
                                url = 'http://www.assemblee-nationale.fr/{}/projets/pl{:04d}.asp'
                            else:
                                url = 'http://www.assemblee-nationale.fr/{}/propositions/pion{:04d}.asp'
                        elif step.get('step') == 'hemicycle':
                            url = 'http://www.assemblee-nationale.fr/{}/ta/ta{:04d}.asp'

                        if url:
                            step['source_url'] = url.format(legislature, int(text_num))

            if 'source_url' not in step and not step.get('echec'):
                log_error('ITEM WITHOUT URL TO TEXT - %s.%s.%s' % (step['institution'], step.get('stage'), step.get('step')))

        # Decision Conseil Constitutionnel
        if curr_stage == 'constitutionnalité':
            # we try to find the decision in the paragraph or at the top of the dosleg
            decision_text = item.text
            if cc_line:
                decision_text += cc_line.text

            if 'partiellement conforme' in item.text:
                step['decision'] = 'partiellement conforme'
            elif 'se déclare incompétent' in item.text:
                step['decision'] = 'se déclare incompétent'
            elif 'non conforme' in item.text:
                step['decision'] = 'non conforme'
            elif 'conforme' in item.text:
                step['decision'] = 'conforme'
            else:
                log_error('WARNING: NO DECISION FOR CC')

        # look for Table de concordance
        if curr_stage == 'promulgation':
            for a in item.select('a'):
                if 'table de concordance' in a.text.lower():
                    table, errors = parse_table_concordance(clean_url(urljoin(url_senat, a.attrs['href'])))
                    data['table_concordance'] = table
                    if errors:
                        data['table_concordance_confusing_entries'] = errors

        # CMP commission has two urls: one for the Senate and one for the AN
        if step.get('stage') == 'CMP' and step.get('step') == 'commission':
            match = re.search(r"numéro de dépôt à l'Assemblée Nationale : (\d+)", clean_spaces(item.text))
            if match:
                text_num = int(match.group(1))
                step['cmp_commission_other_url'] = 'http://www.assemblee-nationale.fr/{}/ta-commission/r{:04d}-a0.asp'\
                                                        .format(data['assemblee_legislature'], text_num)

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

    # if there's not url for the AN dosleg, try to find it via the texts links
    if 'url_dossier_assemblee' not in data:
        an_url = find_an_url(data)
        if an_url:
            data['url_dossier_assemblee'] = an_url

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


# Examples

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
