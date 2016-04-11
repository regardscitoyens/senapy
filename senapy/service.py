# -*- coding: utf-8 -*-
from __future__ import division

import requests

from .parsing.question_search_result_parser import parse_question_search_result

__all__ = ['QuestionSearchService']


class QuestionSearchService(object):
    """Search for questions and build an iterator to iterate over all questions

    Search is parametrized by the following dict params :
        :param off: offset
        :param rch: ?
        :param aff:
            "ar": avec réponse
            "sr": sans réponse
            "ens": tout
        :param radio: date params
            "dp": depuis
            "deau": de YYYYMMDD au YYYYMMDD

        :param du: YYYYMMDD
        :param au: YYYYMMDD
        :param appr: text search in given field
            "titre": in title
        :param idNature: question teyp
            "QE": question écrite
            "QOSD": question orale sans débat
            "QOAD": question orale avec débat
            "QOAE": question orale avec débat et portant sur un sujet européen
            "QAG": question d'actualité au Gouvernement
            "QC": question crible thématique
    """
    def __init__(self):
        self.search_url = "http://www.senat.fr/basile/rechercheQuestion.do"
        self.size = 10
        self.default_params = {
            'off': 0,
            'rch': 'qa',
            'de': '20150101',
            'au': '20150201',
            'radio': 'deau',
            'aff': 'ens',
            'tri': 'dd',
            'afd': 'ppr',
            'idNature': ''
        }

    def get(self, params):
        content = requests.get(self.search_url, params=params).content
        return parse_question_search_result(self.search_url, content)

    def total_count(self, _params=None):
        params = self.default_params.copy()

        if _params:
            params.update(_params)

        return self.get(params).total_count

    def iter(self, _params=None):
        params = self.default_params.copy()

        if _params:
            params.update(_params)

        search_results = self.get(params)

        yield search_results

        for offset in range(self.size, search_results.total_count, self.size):
            params['off'] = offset
            yield self.get(params)