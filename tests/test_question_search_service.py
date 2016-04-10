# -*- coding: utf-8 -*-

from senapy.service import QuestionSearchService


def test_service():
    service = QuestionSearchService()
    iterator = service.iter()
    search_result = iterator.next()

    assert 21 == search_result.total_count
    print search_result.results
    assert 10 == len(search_result.results)

