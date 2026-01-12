from biodbs.utils import get_rsp, async_get_resps
from .enum import KeyWord
from functools import lru_cache
import pandas as pd


DEFAULT_HOST = "https://www.ebi.ac.uk/QuickGO/services"


class QuickGOAPI:
    def __init__(self, host=DEFAULT_HOST):
        self.host = host + "/ontology/go"
        self.json_header = {"Accept": "application/json"}
        self.png_header = {"Accept": "image/png"}

    @lru_cache()
    def get_about(self):
        rsp = get_rsp(self.host + "/about", headers=self.json_header)
        return rsp.text

    def _get_one_result_page(self, query, page, prefix):
        query_and_page = {KeyWord.page.value: page} if page is not None else {}
        query_and_page.update(query)
        rsp = get_rsp(self.host + prefix, query=query_and_page, headers=self.json_header)
        return rsp.json()

    def _get_all_result_pages(self, queries, pages, prefix):
        if pages is not None:
            queries_and_pages = [{KeyWord.page.value: page} for page in pages]
        else:
            queries_and_pages = [{} for _ in queries]
        if queries is not None:
            for q, qp in zip(queries, queries_and_pages):
                qp.update(q)
        resps = async_get_resps(self.host + prefix,
                                queries=queries_and_pages,
                                kwarg_list=[{"headers": self.json_header} for _ in queries_and_pages])
        return resps
