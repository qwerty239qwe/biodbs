from biodbs.utils import get_rsp, save_image_from_rsp, async_get_resps
from enum import Enum
from typing import List, Union
import pandas as pd
from functools import lru_cache, reduce
import json
import asyncio


DEFAULT_HOST = "https://www.ebi.ac.uk/QuickGO/services"


class KeyWord(Enum):
    query = "query"
    limit = "limit"
    page = "page"
    page_info = "pageInfo"
    number_of_hits = "numberOfHits"
    results = "results"
    current_page = "current"
    total_page = "total"
    ids = "ids"
    base64 = "base64"
    show_key = "showKey"
    showIds = "showIds"
    termBoxWidth = "termBoxWidth"
    termBoxHeight = "termBoxHeight"
    showSlimColours = "showSlimColours"
    showChildren = "showChildren"
    fontSize = "fontSize"
    slims_to_Ids = "slimsToIds"
    slims_from_Ids = "slimsFromIds"
    relations = "relations"
    start_ids = "startIds"
    stop_ids = "stopIds"
    edges = "edges"
    vertices = "vertices"


def get_union_keys_in_dics(dics: list) -> list:
    keys = [set(dic.keys()) for dic in dics]
    return list(reduce(set.union, keys))


class QuickGOdb:
    TERM_COLS = ["id", "isObsolete",
                 "name", "definition",
                 "synonyms", "aspect",
                 "usage", "ancestors",
                 "annotationGuidelines",
                 "blacklist", "children",
                 "comment", "credits",
                 "descendants", "goDiscussion", "history", "replacement"]

    def __init__(self, host = DEFAULT_HOST):
        self.host = host + "/ontology/go"
        self.json_header = {"Accept": "application/json"}
        self.png_header = {"Accept": "image/png"}

    @lru_cache()
    def get_about(self):
        rsp = get_rsp(self.host + "/about", headers=self.json_header)
        return rsp.text

    def _get_one_result_page(self, query, page, prefix) -> dict:
        query_and_page = {KeyWord.page.value: page} if page is not None else {}
        query_and_page.update(query)
        rsp = get_rsp(self.host + prefix, query=query_and_page, headers=self.json_header)
        result = rsp.json()
        return result

    def _get_all_result_pages(self, queries, pages, prefix):
        if pages is not None:
            queries_and_pages = [{KeyWord.page.value: page} for page in pages]
        else:
            queries_and_pages = [{} for _ in queries]
        if queries is not None:
            for q, qp in zip(queries, queries_and_pages):
                qp.update(q)
        resps = asyncio.run(async_get_resps(self.host + prefix,
                                            queries=queries_and_pages,
                                            kwarg_list=[{"headers": self.json_header} for _ in queries_and_pages]))
        return resps

    @lru_cache()
    def list_search_result(self, query):
        query = {KeyWord.query.value: query,
                 KeyWord.limit.value: 600}
        result_dic = []
        # first_query
        result = self._get_one_result_page(query, 1, prefix="/search")
        result_dic.extend(result[KeyWord.results.value])
        print("Get " + str(result[KeyWord.number_of_hits.value]) + " results")
        if result[KeyWord.page_info.value] is not None:
            cur_page = result[KeyWord.page_info.value][KeyWord.current_page.value]
            total_page = result[KeyWord.page_info.value][KeyWord.total_page.value]
            for p in range(cur_page+1, total_page+1):
                result_dic.extend(self._get_one_result_page(query, p, prefix="/search")[KeyWord.results.value])

        return pd.DataFrame(result_dic)

    def list_slim(self,
                  slims_to_Ids,
                  slims_from_Ids = None,
                  relations = "default"):
        if relations == "default":
            relations = "is_a,part_of,occurs_in,regulates"
        elif isinstance(relations, list):
            relations = ",".join(relations)
        query = {KeyWord.slims_to_Ids.value: slims_to_Ids,
                 KeyWord.slims_from_Ids.value: slims_from_Ids,
                 KeyWord.relations.value: relations}

        result_dic = []
        result = self._get_one_result_page(query, None, prefix="/slim")
        result_dic.extend(result[KeyWord.results.value])
        print("Get " + str(result[KeyWord.number_of_hits.value]) + " results")
        if result[KeyWord.page_info.value] is not None:
            cur_page = result[KeyWord.page_info.value][KeyWord.current_page.value]
            total_page = result[KeyWord.page_info.value][KeyWord.total_page.value]
            for p in range(cur_page+1, total_page+1):
                result_dic.extend(self._get_one_result_page(query, p, prefix="/slim")[KeyWord.results.value])

        return pd.DataFrame(result_dic)

    def _get_chart_query(self,
                         ids,
                         base64: bool = False,
                         showKey: bool = True,
                         showIds: bool = True,
                         termBoxWidth: int = None,
                         termBoxHeight: int = None,
                         showSlimColours: bool = False,
                         showChildren: bool = True,
                         fontSize: int = None
                         ):
        query = {
            KeyWord.ids.value: ids,
            KeyWord.base64.value: base64,
            KeyWord.show_key.value: showKey,
            KeyWord.showIds.value: showIds,
            KeyWord.showSlimColours.value: showSlimColours,
            KeyWord.showChildren.value: showChildren
        }
        if fontSize is not None:
            query.update({KeyWord.fontSize.value: fontSize})
        if termBoxWidth is not None:
            query.update({KeyWord.termBoxWidth.value: termBoxWidth, })
        if termBoxHeight is not None:
            query.update({KeyWord.termBoxHeight.value: termBoxHeight, })
        return query


    def save_chart(self,
                   ids,
                   file_name: str,
                   base64: bool = False,
                   showKey: bool = True,
                   showIds: bool = True,
                   termBoxWidth: int = None,
                   termBoxHeight: int = None,
                   showSlimColours: bool = False,
                   showChildren: bool = True,
                   fontSize: int = None
                   ):
        if isinstance(ids, list):
            ids = ",".join(ids)
        query = self._get_chart_query(ids,
                                      base64,
                                      showKey,
                                      showIds,
                                      termBoxWidth,
                                      termBoxHeight,
                                      showSlimColours,
                                      showChildren,
                                      fontSize)
        rsp = get_rsp(self.host + "/terms/{ids}/chart", query=query, headers=self.png_header, stream=True)
        save_image_from_rsp(rsp, file_name)
        return rsp

    def list_chart_coords(self,
                          ids,
                          file_name: str,
                          base64: bool = False,
                          showKey: bool = True,
                          showIds: bool = True,
                          termBoxWidth: int = None,
                          termBoxHeight: int = None,
                          showSlimColours: bool = False,
                          showChildren: bool = True,
                          fontSize: int = None
                          ):
        if isinstance(ids, list):
            ids = ",".join(ids)
        query = self._get_chart_query(ids,
                                      base64,
                                      showKey,
                                      showIds,
                                      termBoxWidth,
                                      termBoxHeight,
                                      showSlimColours,
                                      showChildren,
                                      fontSize)
        rsp = get_rsp(self.host + f"/terms/{ids}/chart", query=query, headers=self.png_header, stream=True)
        return rsp.json()

    def list_term(self,
                  ids: list = None,  # if none, list all
                  **show_kwargs):
        if "definition" not in show_kwargs:
            show_kwargs["definition"] = ["text"]  # xref
        if "synonyms" not in show_kwargs:
            show_kwargs["synonyms"] = ["name", "type"]
        if "children" not in show_kwargs:
            show_kwargs["children"] = ["id", "relation"]

        result_dic = []
        if ids is not None:
            if isinstance(ids, list):
                ids = ",".join(ids)
            rsp = get_rsp(self.host + "/terms/" + ids, headers=self.json_header)
            result = json.loads(rsp.text)
        else:
            result = self._get_one_result_page(query={}, page=1, prefix="/terms")
        result_dic.extend(result[KeyWord.results.value])
        print("Get " + str(result[KeyWord.number_of_hits.value]) + " results")
        if result[KeyWord.page_info.value] is not None:
            cur_page = result[KeyWord.page_info.value][KeyWord.current_page.value]
            total_page = result[KeyWord.page_info.value][KeyWord.total_page.value]
            pages = [p for p in range(cur_page + 1, total_page + 1)]
            page_results = self._get_all_result_pages(queries=None, pages=pages, prefix="/terms")
            for r in page_results:
                result_dic.extend(r[KeyWord.results.value])

        # get_union_keys_in_dics
        return pd.DataFrame(result_dic)

    def list_term_graph_elements(self,
                                 start_ids: List[str],
                                 stop_ids: List[str] = None,
                                 relations: List[str] = None):
        query = {
            KeyWord.start_ids.value: ",".join(start_ids)
        }
        if stop_ids is not None:
            query.update({KeyWord.stop_ids.value: ",".join(stop_ids)})

        if relations is not None:
            query.update({KeyWord.relations.value: ",".join(relations)})

        rsp = get_rsp(self.host + "/terms/graph", query=query, headers=self.json_header)
        content = rsp.json()
        edges_df = pd.DataFrame(content[KeyWord.results.value][0][KeyWord.edges.value])
        vertices_df = pd.DataFrame(content[KeyWord.results.value][0][KeyWord.vertices.value])
        return edges_df, vertices_df

    def list_term_ancestors(self,
                            ids,
                            relations=None):
        if relations is None:
            relations = ["is_a", "part_of", "occurs_in", "regulates"]
        query = {
            KeyWord.relations.value: ",".join(relations)
        }
        rsp = get_rsp(self.host + f"/terms/{','.join(ids)}/ancestors", query=query, headers=self.json_header)
        return pd.DataFrame(rsp.json()[KeyWord.results.value])

    def list_term_children(self, ids):
        rsp = get_rsp(self.host + f"/terms/{','.join(ids)}/children", headers=self.json_header)
        return pd.DataFrame(rsp.json()[KeyWord.results.value])

    def list_term_complete(self, ids):
        NotImplemented

    def list_term_constraints(self, ids):
        NotImplemented

    def list_term_descendants(self, ids, relations):
        NotImplemented

