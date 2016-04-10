# -*- coding: utf-8 -*-

import re

from urlparse import urlparse, parse_qs


class QuestionSummary(object):
    def __init__(self, url=None, legislature=None, question_type=None, title=None):
        self.url = url
        self.legislature = legislature
        self.question_type = question_type
        self.title = title

    def __repr__(self):
        return self.__dict__.__repr__()


    @classmethod
    def from_search_result(cls, url, title):
        params = parse_qs(urlparse(url).query)
        id = params['id'][0]

        legislature = re.findall(r'(\d+)', id)[0][:2]
        url = 'http://www.senat.fr/questions/base/20%s/%s.html' % (legislature, id)
        return QuestionSummary(url=url, legislature=legislature, question_type=params['_na'][0], title=title)


class QuestionSearchResult(object):
    def __init__(self, url=None, total_count=None, size=None, results=None):
        self.url = url
        self.total_count = total_count
        self.size = size
        self.results = results

    def __repr__(self):
        return self.__dict__.__repr__()