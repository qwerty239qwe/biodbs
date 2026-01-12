from .api import QuickGOAPI, KeyWord
from biodbs.utils import get_rsp, save_image_from_rsp
import pandas as pd
import json


class SearchFetcher(QuickGOAPI):
    TERM_COLS = ["id", "isObsolete",
                 "name", "definition",
                 "synonyms", "aspect",
                 "usage", "ancestors",
                 "annotationGuidelines",
                 "blacklist", "children",
                 "comment", "credits",
                 "descendants", "goDiscussion", "history", "replacement"]

    def search(self, query, limit=600):
        query = {KeyWord.query.value: query,
                 KeyWord.limit.value: limit}
        result_dic = []
        result = self._get_one_result_page(query, 1, prefix="/search")
        result_dic.extend(result[KeyWord.results.value])
        print("Get " + str(result[KeyWord.number_of_hits.value]) + " results")
        if result[KeyWord.page_info.value] is not None:
            cur_page = result[KeyWord.page_info.value][KeyWord.current_page.value]
            total_page = result[KeyWord.page_info.value][KeyWord.total_page.value]
            for p in range(cur_page + 1, total_page + 1):
                result_dic.extend(self._get_one_result_page(query, p, prefix="/search")[KeyWord.results.value])
        return pd.DataFrame(result_dic)


class SlimFetcher(QuickGOAPI):
    def fetch_slim(self, slims_to_Ids, slims_from_Ids=None, relations=None):
        if relations is None:
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
            for p in range(cur_page + 1, total_page + 1):
                result_dic.extend(self._get_one_result_page(query, p, prefix="/slim")[KeyWord.results.value])
        return pd.DataFrame(result_dic)


class ChartFetcher(QuickGOAPI):
    def _get_chart_query(self, ids, base64=False, showKey=True, showIds=True,
                         termBoxWidth=None, termBoxHeight=None,
                         showSlimColours=False, showChildren=True, fontSize=None):
        query = {
            KeyWord.ids.value: ids,
            KeyWord.base64.value: base64,
            KeyWord.show_key.value: showKey,
            KeyWord.showIds.value: showIds,
            KeyWord.showSlimColours.value: showSlimColours,
            KeyWord.showChildren.value: showChildren
        }
        if fontSize is not None:
            query[KeyWord.fontSize.value] = fontSize
        if termBoxWidth is not None:
            query[KeyWord.termBoxWidth.value] = termBoxWidth
        if termBoxHeight is not None:
            query[KeyWord.termBoxHeight.value] = termBoxHeight
        return query

    def save_chart(self, ids, file_name, base64=False, showKey=True, showIds=True,
                   termBoxWidth=None, termBoxHeight=None,
                   showSlimColours=False, showChildren=True, fontSize=None):
        if isinstance(ids, list):
            ids = ",".join(ids)
        query = self._get_chart_query(ids, base64, showKey, showIds,
                                      termBoxWidth, termBoxHeight,
                                      showSlimColours, showChildren, fontSize)
        rsp = get_rsp(self.host + "/terms/{ids}/chart", query=query, headers=self.png_header, stream=True)
        save_image_from_rsp(rsp, file_name)
        return rsp

    def get_chart_coords(self, ids, base64=False, showKey=True, showIds=True,
                         termBoxWidth=None, termBoxHeight=None,
                         showSlimColours=False, showChildren=True, fontSize=None):
        if isinstance(ids, list):
            ids = ",".join(ids)
        query = self._get_chart_query(ids, base64, showKey, showIds,
                                      termBoxWidth, termBoxHeight,
                                      showSlimColours, showChildren, fontSize)
        rsp = get_rsp(self.host + f"/terms/{ids}/chart", query=query, headers=self.png_header, stream=True)
        return rsp.json()


class TermFetcher(QuickGOAPI):
    def fetch(self, ids=None, **show_kwargs):
        if "definition" not in show_kwargs:
            show_kwargs["definition"] = ["text"]
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
        return pd.DataFrame(result_dic)

    def get_graph_elements(self, start_ids, stop_ids=None, relations=None):
        query = {KeyWord.start_ids.value: ",".join(start_ids)}
        if stop_ids is not None:
            query[KeyWord.stop_ids.value] = ",".join(stop_ids)
        if relations is not None:
            query[KeyWord.relations.value] = ",".join(relations)

        rsp = get_rsp(self.host + "/terms/graph", query=query, headers=self.json_header)
        content = rsp.json()
        edges_df = pd.DataFrame(content[KeyWord.results.value][0][KeyWord.edges.value])
        vertices_df = pd.DataFrame(content[KeyWord.results.value][0][KeyWord.vertices.value])
        return edges_df, vertices_df

    def get_ancestors(self, ids, relations=None):
        if relations is None:
            relations = ["is_a", "part_of", "occurs_in", "regulates"]
        query = {KeyWord.relations.value: ",".join(relations)}
        rsp = get_rsp(self.host + f"/terms/{','.join(ids)}/ancestors", query=query, headers=self.json_header)
        return pd.DataFrame(rsp.json()[KeyWord.results.value])

    def get_children(self, ids):
        rsp = get_rsp(self.host + f"/terms/{','.join(ids)}/children", headers=self.json_header)
        return pd.DataFrame(rsp.json()[KeyWord.results.value])

    def get_complete(self, ids):
        raise NotImplementedError

    def get_constraints(self, ids):
        raise NotImplementedError

    def get_descendants(self, ids, relations):
        raise NotImplementedError


