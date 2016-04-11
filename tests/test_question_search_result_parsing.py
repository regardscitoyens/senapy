# -*- coding: utf-8 -*-

import codecs

from senapy.parsing.question_search_result_parser import parse_question_search_result


def test_parsing():
    html = codecs.open('tests/resources/question_search_result.html', encoding='iso-8859-1')
    url = 'http://www.senat.fr/basile/rechercheQuestion.do?off=30&rch=qa&de=20150403&au=20160403&dp=1+an&radio=dp&appr=text&aff=ar&tri=dd&afd=ppr&afd=ppl&afd=pjl&afd=cvn&_na=QG'
    search_result = parse_question_search_result(url, html)

    assert 330 == search_result.total_count
    assert 10 == len(search_result.results)
    assert 'http://www.senat.fr/questions/base/2016/qSEQ16030791G.html' == search_result.results[0].url
    assert u'Partenariat entre La Poste et l\'État : maisons de services au public' == search_result.results[0].title
    assert '16' == search_result.results[0].legislature
