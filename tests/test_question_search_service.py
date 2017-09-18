# -*- coding: utf-8 -*-

from senapy.service import QuestionSearchService


def test_service():
    service = QuestionSearchService()
    iterator = service.iter({'idNature': 'QG'})
    search_result = next(iterator)

    assert 21 == search_result.total_count
    assert 10 == len(search_result.results)

