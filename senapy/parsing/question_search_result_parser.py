# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup

from ..model import QuestionSummary, QuestionSearchResult


def extract_total_count(soup):
    p = soup.find('p', class_='results-number-global')

    return int(re.findall('(\d+)\s*\n*questions', p.text)[0])


def parse_question_search_result(url, html_content):
    soup = BeautifulSoup(html_content, "html5lib")

    search_result = QuestionSearchResult(**{
        'url': url,
        'total_count': extract_total_count(soup)
    })

    rows = soup.find('div', class_='table table-01').find_all('tr')

    results = []

    for row in rows[1:]:
        row_url = 'http://www.senat.fr/' + row.find('a')['href']
        row_title = row.find('a').text.strip()
        results.append(QuestionSummary.from_search_result(row_url, row_title))

    search_result.results = results

    return search_result