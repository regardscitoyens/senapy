# -*- coding: utf-8 -*-
from __future__ import division

import requests

from .parsing.question_search_result_parser import parse_question_search_result

__all__ = ['QuestionSearchService']


class QuestionSearchService(object):
    def __init__(self):
        self.search_url = "http://www.senat.fr/basile/rechercheQuestion.do"
        self.size = 10
        self.default_params = {
            'off': 0,
            'rch': 'qa',
            'de': '20150101',
            'au': '20150201',
            'dp': '1 an',
            'radio': 'deau',
            'appr': 'text',
            'aff': 'ar',
            'tri': 'dd',
            '_na': 'QG',
            'afd': 'ppr',
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

        for start in range(1, search_results.total_count, self.size):
            params['off'] = start * 10
            yield self.get(params)