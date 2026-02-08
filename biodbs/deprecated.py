"""
Deprecated API implementations.

This module contains legacy implementations that are kept for backward compatibility
with the examples in README.md. New code should use the modern API in:
- biodbs.fetch.KEGG.kegg_fetcher.KEGG_Fetcher
- biodbs.fetch.QuickGO.quickgo_fetcher.QuickGO_Fetcher
- biodbs.fetch.FDA.fda_fetcher.FDA_Fetcher

These classes are deprecated and may be removed in a future version.
"""
import warnings
from biodbs.utils import get_rsp, save_image_from_rsp, async_get_resps, fetch_and_extract
from enum import Enum
from typing import List, Tuple
import pandas as pd
from functools import lru_cache, reduce, partial
import json
import asyncio
import xml.etree.ElementTree as ET
import concurrent.futures
from tqdm import tqdm


# =============================================================================
# KEGG (deprecated)
# =============================================================================

KEGG_DEFAULT_HOST = "http://rest.kegg.jp"


class KEGGDatabase(Enum):
    """KEGG database enum (deprecated)."""
    kegg = ("kegg", None, None)
    pathway = ("pathway", "path", "KEGG pathway maps")
    module = ("module", "md", "KEGG modules")
    ko = ("orthology", "ko", "KO functional orthologs")
    organism = ("organism", "org", None)
    brite = ("brite", "br", "BRITE functional hierarchies")
    genome = ("genome", "gn", "KEGG organisms")
    org = ("<org>", None, "Genes in KEGG organisms")
    genes = ("genes", None, None)
    vg = ("vg", "vg", "Genes in viruses category")
    ag = ("ag", "ag", "Genes in addendum category")
    compound = ("compound", "cpd", "Small molecules")
    glycan = ("glycan", "gl", "Glycans")
    reaction = ("reaction", "rn", "Biochemical reactions")
    rclass = ("rclass", "rc", "Reaction class")
    enzyme = ("enzyme", "ec", "Enzyme nomenclature")
    network = ("network", "ne", "Network elements")
    variant = ("variant", "hsa_var", "Human gene variants")
    disease = ("disease", "ds", "")
    drug = ("drug", "dr", "Drugs")
    dgroup = ("dgroup", "dr", "Drug groups")
    environ = ("environ", "ev", "Health-related substances")
    medicus = ("<medicus>", None, None)
    atc = ("ATC code", "atc", "ATC classification")
    jtc = ("Therapeutic category code", "jtc", "Therapeutic category in Japan")
    ndc = ("National Drug Code", "ndc", "Drug products in the USA")
    yj = ("YJ code", "yj", "Drug products in Japan")
    pubmed = ("pubmed", "pmid", "PubMed ID")
    ncbi_geneid = ("ncbi-geneid", None, "NCBI Gene ID")
    ncbi_proteinid = ("ncbi-proteinid", None, "NCBI Protein ID")
    uniprot = ("uniprot", "up", "Uniprot Accession")
    pubchem = ("pubchem", None, "PubChem SID")
    chebi = ("chebi", None, "ChEBI ID")


KEGG_ALIAS_NAME_DICT = {db.value[1]: db.name for db in KEGGDatabase}


def kegg_list_database():
    """List KEGG databases (deprecated).

    Use KEGG_Fetcher.get('info', database='kegg') instead.
    """
    warnings.warn(
        "kegg_list_database() is deprecated. Use KEGG_Fetcher from "
        "biodbs.fetch.KEGG.kegg_fetcher instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return pd.DataFrame({db.name: list(db.value)[:3]
                         for db in KEGGDatabase}, index=["DB name", "abbrev", "content"]).T


class KEGGdb:
    """KEGG database client (deprecated).

    Use KEGG_Fetcher from biodbs.fetch.KEGG.kegg_fetcher instead.
    """
    FIND_OPTIONS = ("formula", "exact_mass", "mol_weight", "nop")
    GET_OPTIONS = ("aaseq", "ntseq", "mol", "kcf", "image", "conf", "kgml", "json")
    CONV_GENE_EXTERNAL_DBS = ("ncbi-geneid", "ncbi-proteinid", "uniprot")
    CONV_CHEM_EXTERNAL_DBS = ("pubchem", "chebi")
    CONV_CHEM_INTERNAL_DBS = ("compound", "glycan", "drug")

    def __init__(self, host=KEGG_DEFAULT_HOST):
        warnings.warn(
            "KEGGdb is deprecated. Use KEGG_Fetcher from "
            "biodbs.fetch.KEGG.kegg_fetcher instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.host = host

    @lru_cache()
    def get_info(self, database):
        if database in KEGG_ALIAS_NAME_DICT:
            database = KEGG_ALIAS_NAME_DICT[database]
        return get_rsp(self.host + "/info/" + database).text

    @lru_cache()
    def list_df(self, database):
        if database in KEGG_ALIAS_NAME_DICT:
            database = KEGG_ALIAS_NAME_DICT[database]
        rsp_txt = get_rsp(self.host + "/list/" + database).text
        rsp_lines = rsp_txt.split("\n")
        return pd.DataFrame([line.split("\t") for line in rsp_lines])

    @lru_cache()
    def list_organism(self, contains: str = None, query_tags: str = None):
        rsp_txt = get_rsp(self.host + "/list/organism").text
        rsp_lines = rsp_txt.split("\n")
        org_df = pd.DataFrame([line.split("\t") for line in rsp_lines],
                              columns=["ID", "abbrev", "full name", "tags"])
        if contains is not None:
            org_df = org_df[org_df["abbrev"].str.contains(contains) |
                            org_df["full name"].str.contains(contains) |
                            org_df["tags"].str.contains(contains)]
        if query_tags is not None:
            org_df = org_df[org_df["tags"]]

        return org_df

    @lru_cache()
    def list_found_entries(self, database, query: str, option: str = None):
        url = self.host + "/find/" + database + "/" + query
        if database in ("compound", "drug"):
            assert option in self.FIND_OPTIONS
            url += ("/" + option)
        rsp_txt = get_rsp(url).text
        rsp_lines = rsp_txt.split("\n")
        return pd.DataFrame([line.split("\t") for line in rsp_lines],
                            columns=["ID", option if option else "found_entries"])

    @lru_cache()
    def get_entries(self, entries, option=None):
        url = self.host + "/get/" + entries
        if option:
            assert option in self.GET_OPTIONS
            assert option != "image", "image file cannot be converted to text, use save_image() instead"
            url += ("/" + option)
        return get_rsp(url).text

    def save_image(self, entries, file_name):
        url = self.host + "/get/" + entries + "/image"
        rsp = get_rsp(url)
        save_image_from_rsp(rsp, file_name)

    @staticmethod
    def _add_entries(url, entries):
        if isinstance(entries, list):
            entries = "+".join(entries)
        if entries is not None:
            url += ("/" + entries)
        return url

    @lru_cache()
    def list_converted_id(self, target_db, source_db=None, entries=None):
        url = self.host + "/conv/" + target_db
        if source_db is not None:
            url += ("/" + source_db)
        url = self._add_entries(url, entries)
        print(url)
        rsp_txt = get_rsp(url).text
        rsp_lines = rsp_txt.split("\n")
        return pd.DataFrame([line.split("\t") for line in rsp_lines],
                            columns=[target_db, source_db if source_db else "entry(s)"])

    @lru_cache()
    def list_entry_link(self, target_db, source_db=None, entries=None):
        url = self.host + "/link/" + target_db
        if source_db:
            url += ("/" + source_db)
        else:
            url = self._add_entries(url, entries)
        print(url)
        rsp_txt = get_rsp(url).text
        rsp_lines = rsp_txt.split("\n")
        return pd.DataFrame([line.split("\t") for line in rsp_lines],
                            columns=[target_db, source_db if source_db else "entry(s)"])

    @lru_cache()
    def list_ddi(self, entries):
        url = self.host + "/ddi"
        url = self._add_entries(url, entries)
        rsp_txt = get_rsp(url).text
        rsp_lines = rsp_txt.split("\n")
        return pd.DataFrame([line.split("\t") for line in rsp_lines],
                            columns=["Drug 1", "Drug 2", "Interaction", "Classification"])


# =============================================================================
# QuickGO (deprecated)
# =============================================================================

QUICKGO_DEFAULT_HOST = "https://www.ebi.ac.uk/QuickGO/services"


class QuickGOKeyWord(Enum):
    """QuickGO keywords (deprecated)."""
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


def _get_union_keys_in_dics(dics: list) -> list:
    keys = [set(dic.keys()) for dic in dics]
    return list(reduce(set.union, keys))


class QuickGOdb:
    """QuickGO database client (deprecated).

    Use QuickGO_Fetcher from biodbs.fetch.QuickGO.quickgo_fetcher instead.
    """
    TERM_COLS = ["id", "isObsolete", "name", "definition", "synonyms", "aspect",
                 "usage", "ancestors", "annotationGuidelines", "blacklist",
                 "children", "comment", "credits", "descendants", "goDiscussion",
                 "history", "replacement"]

    def __init__(self, host=QUICKGO_DEFAULT_HOST):
        warnings.warn(
            "QuickGOdb is deprecated. Use QuickGO_Fetcher from "
            "biodbs.fetch.QuickGO.quickgo_fetcher instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.host = host + "/ontology/go"
        self.json_header = {"Accept": "application/json"}
        self.png_header = {"Accept": "image/png"}

    @lru_cache()
    def get_about(self):
        rsp = get_rsp(self.host + "/about", headers=self.json_header)
        return rsp.text

    def _get_one_result_page(self, query, page, prefix) -> dict:
        query_and_page = {QuickGOKeyWord.page.value: page} if page is not None else {}
        query_and_page.update(query)
        rsp = get_rsp(self.host + prefix, query=query_and_page, headers=self.json_header)
        result = rsp.json()
        return result

    def _get_all_result_pages(self, queries, pages, prefix):
        if pages is not None:
            queries_and_pages = [{QuickGOKeyWord.page.value: page} for page in pages]
        else:
            queries_and_pages = [{} for _ in queries]
        if queries is not None:
            for q, qp in zip(queries, queries_and_pages):
                qp.update(q)
        resps = asyncio.run(async_get_resps(
            self.host + prefix,
            queries=queries_and_pages,
            kwarg_list=[{"headers": self.json_header} for _ in queries_and_pages]
        ))
        return resps

    @lru_cache()
    def list_search_result(self, query):
        query = {QuickGOKeyWord.query.value: query, QuickGOKeyWord.limit.value: 600}
        result_dic = []
        result = self._get_one_result_page(query, 1, prefix="/search")
        result_dic.extend(result[QuickGOKeyWord.results.value])
        print("Get " + str(result[QuickGOKeyWord.number_of_hits.value]) + " results")
        if result[QuickGOKeyWord.page_info.value] is not None:
            cur_page = result[QuickGOKeyWord.page_info.value][QuickGOKeyWord.current_page.value]
            total_page = result[QuickGOKeyWord.page_info.value][QuickGOKeyWord.total_page.value]
            for p in range(cur_page + 1, total_page + 1):
                result_dic.extend(
                    self._get_one_result_page(query, p, prefix="/search")[QuickGOKeyWord.results.value]
                )
        return pd.DataFrame(result_dic)

    def list_slim(self, slims_to_Ids, slims_from_Ids=None, relations="default"):
        if relations == "default":
            relations = "is_a,part_of,occurs_in,regulates"
        elif isinstance(relations, list):
            relations = ",".join(relations)
        query = {
            QuickGOKeyWord.slims_to_Ids.value: slims_to_Ids,
            QuickGOKeyWord.slims_from_Ids.value: slims_from_Ids,
            QuickGOKeyWord.relations.value: relations
        }
        result_dic = []
        result = self._get_one_result_page(query, None, prefix="/slim")
        result_dic.extend(result[QuickGOKeyWord.results.value])
        print("Get " + str(result[QuickGOKeyWord.number_of_hits.value]) + " results")
        if result[QuickGOKeyWord.page_info.value] is not None:
            cur_page = result[QuickGOKeyWord.page_info.value][QuickGOKeyWord.current_page.value]
            total_page = result[QuickGOKeyWord.page_info.value][QuickGOKeyWord.total_page.value]
            for p in range(cur_page + 1, total_page + 1):
                result_dic.extend(
                    self._get_one_result_page(query, p, prefix="/slim")[QuickGOKeyWord.results.value]
                )
        return pd.DataFrame(result_dic)

    def _get_chart_query(self, ids, base64: bool = False, showKey: bool = True,
                         showIds: bool = True, termBoxWidth: int = None,
                         termBoxHeight: int = None, showSlimColours: bool = False,
                         showChildren: bool = True, fontSize: int = None):
        query = {
            QuickGOKeyWord.ids.value: ids,
            QuickGOKeyWord.base64.value: base64,
            QuickGOKeyWord.show_key.value: showKey,
            QuickGOKeyWord.showIds.value: showIds,
            QuickGOKeyWord.showSlimColours.value: showSlimColours,
            QuickGOKeyWord.showChildren.value: showChildren
        }
        if fontSize is not None:
            query.update({QuickGOKeyWord.fontSize.value: fontSize})
        if termBoxWidth is not None:
            query.update({QuickGOKeyWord.termBoxWidth.value: termBoxWidth})
        if termBoxHeight is not None:
            query.update({QuickGOKeyWord.termBoxHeight.value: termBoxHeight})
        return query

    def save_chart(self, ids, file_name: str, base64: bool = False,
                   showKey: bool = True, showIds: bool = True,
                   termBoxWidth: int = None, termBoxHeight: int = None,
                   showSlimColours: bool = False, showChildren: bool = True,
                   fontSize: int = None):
        if isinstance(ids, list):
            ids = ",".join(ids)
        query = self._get_chart_query(ids, base64, showKey, showIds, termBoxWidth,
                                      termBoxHeight, showSlimColours, showChildren, fontSize)
        rsp = get_rsp(self.host + "/terms/{ids}/chart", query=query,
                      headers=self.png_header, stream=True)
        save_image_from_rsp(rsp, file_name)
        return rsp

    def list_chart_coords(self, ids, file_name: str, base64: bool = False,
                          showKey: bool = True, showIds: bool = True,
                          termBoxWidth: int = None, termBoxHeight: int = None,
                          showSlimColours: bool = False, showChildren: bool = True,
                          fontSize: int = None):
        if isinstance(ids, list):
            ids = ",".join(ids)
        query = self._get_chart_query(ids, base64, showKey, showIds, termBoxWidth,
                                      termBoxHeight, showSlimColours, showChildren, fontSize)
        rsp = get_rsp(self.host + f"/terms/{ids}/chart", query=query,
                      headers=self.png_header, stream=True)
        return rsp.json()

    def list_term(self, ids: list = None, **show_kwargs):
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
        result_dic.extend(result[QuickGOKeyWord.results.value])
        print("Get " + str(result[QuickGOKeyWord.number_of_hits.value]) + " results")
        if result[QuickGOKeyWord.page_info.value] is not None:
            cur_page = result[QuickGOKeyWord.page_info.value][QuickGOKeyWord.current_page.value]
            total_page = result[QuickGOKeyWord.page_info.value][QuickGOKeyWord.total_page.value]
            pages = [p for p in range(cur_page + 1, total_page + 1)]
            page_results = self._get_all_result_pages(queries=None, pages=pages, prefix="/terms")
            for r in page_results:
                result_dic.extend(r[QuickGOKeyWord.results.value])
        return pd.DataFrame(result_dic)

    def list_term_graph_elements(self, start_ids: List[str], stop_ids: List[str] = None,
                                 relations: List[str] = None):
        query = {QuickGOKeyWord.start_ids.value: ",".join(start_ids)}
        if stop_ids is not None:
            query.update({QuickGOKeyWord.stop_ids.value: ",".join(stop_ids)})
        if relations is not None:
            query.update({QuickGOKeyWord.relations.value: ",".join(relations)})
        rsp = get_rsp(self.host + "/terms/graph", query=query, headers=self.json_header)
        content = rsp.json()
        edges_df = pd.DataFrame(content[QuickGOKeyWord.results.value][0][QuickGOKeyWord.edges.value])
        vertices_df = pd.DataFrame(content[QuickGOKeyWord.results.value][0][QuickGOKeyWord.vertices.value])
        return edges_df, vertices_df

    def list_term_ancestors(self, ids, relations=None):
        if relations is None:
            relations = ["is_a", "part_of", "occurs_in", "regulates"]
        query = {QuickGOKeyWord.relations.value: ",".join(relations)}
        rsp = get_rsp(self.host + f"/terms/{','.join(ids)}/ancestors",
                      query=query, headers=self.json_header)
        return pd.DataFrame(rsp.json()[QuickGOKeyWord.results.value])

    def list_term_children(self, ids):
        rsp = get_rsp(self.host + f"/terms/{','.join(ids)}/children", headers=self.json_header)
        return pd.DataFrame(rsp.json()[QuickGOKeyWord.results.value])

    def list_term_complete(self, ids):
        raise NotImplementedError

    def list_term_constraints(self, ids):
        raise NotImplementedError

    def list_term_descendants(self, ids, relations):
        raise NotImplementedError


# =============================================================================
# HPA (deprecated)
# =============================================================================

HPA_DEFAULT_HOST = "http://www.proteinatlas.org/"
HPA_DOWNLOADABLE_DATA = [
    "normal_tissue", "pathology", "subcellular_location", "rna_tissue_consensus",
    "rna_tissue_hpa", "rna_tissue_gtex", "rna_tissue_fantom", "rna_single_cell_type",
    "rna_single_cell_type_tissue", "rna_brain_gtex", "rna_brain_fantom",
    "rna_pig_brain_hpa", "rna_pig_brain_sample_hpa", "rna_mouse_brain_hpa",
    "rna_mouse_brain_sample_hpa", "rna_mouse_brain_allen", "rna_blood_cell",
    "rna_blood_cell_sample", "rna_blood_cell_sample_tpm_m", "rna_blood_cell_monaco",
    "rna_blood_cell_schmiedel", "rna_celline", "rna_cancer_sample",
    "transcript_rna_tissue", "transcript_rna_celline", "transcript_rna_pigbrain",
    "transcript_rna_mousebrain"
]


class HPAdb:
    """Human Protein Atlas database client (deprecated)."""

    def __init__(self, host=HPA_DEFAULT_HOST):
        warnings.warn(
            "HPAdb is deprecated and may be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        self.host = host

    def list_proteins(self, ids=["ENSG00000101473", "ENSG00000113552"]) -> Tuple[pd.DataFrame, list]:
        get_rsp_ = partial(get_rsp, safe_check=False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(tqdm(
                executor.map(get_rsp_, (self.host + p_id + ".json" for p_id in ids)),
                total=len(ids)
            ))
        failed = [ids[i] for i, v in enumerate(results) if v.status_code != 200]
        successed = [r.json() for r in results if r.status_code == 200]
        return pd.DataFrame(successed), failed

    def download_HPA_data(self, options, saved_path):
        for opt in options:
            assert opt in HPA_DOWNLOADABLE_DATA, \
                f"{opt} is not valid, valid options: {HPA_DOWNLOADABLE_DATA}"
            fetch_and_extract(
                url=f"{self.host}/download/{opt}.tsv.zip",
                saved_path=saved_path
            )
            print("Data is downloaded and saved in ", saved_path)


# =============================================================================
# BioMart (deprecated)
# =============================================================================

BIOMART_HOSTS = {
    "main": "www.ensembl.org",
    "apr2018": "apr2018.archive.ensembl.org",
    "may2015": "may2015.archive.ensembl.org",
    "plants": "plants.ensembl.org",
    "fungi": "fungi.ensembl.org",
    "protist": "protist.ensembl.org",
    "metazoa": "metazoa.ensembl.org"
}

BIOMART_DEFAULT_HOST = "http://" + BIOMART_HOSTS["main"] + "/biomart/martservice?"
BIOMART_DEFAULT_MART_NAME = "ENSEMBL_MART_ENSEMBL"
BIOMART_DEFAULT_DATASET_NAME = {"human": "hsapiens_gene_ensembl", "mouse": "mmusculus_gene_ensembl"}


def biomart_get_full_url_from_host(host_name):
    return "http://" + BIOMART_HOSTS[host_name] + "/biomart/martservice?"


def _biomart_rsp_to_df(rsp, columns):
    return pd.DataFrame([r.split("\t") for r in rsp.text.split("\n")], columns=columns)


def _biomart_find_contained_rows(df, contain, cols, ignore_case=True):
    contain = contain.lower() if ignore_case else contain
    boolean_dfs = [
        df[col].apply(lambda x: "" if not isinstance(x, str) else
                      x.lower() if ignore_case else x).str.match(f".*{contain}.*")
        for col in cols
    ]
    return df[reduce(lambda l, r: l | r, boolean_dfs)]


def _biomart_find_matched_rows(df, pattern, cols):
    boolean_dfs = [df[col].str.match(pattern) for col in cols]
    return df[reduce(lambda l, r: l | r, boolean_dfs)]


def _biomart_xml_to_tabular(xml, tag=None, how="union"):
    tree = ET.fromstring(xml) if not isinstance(xml, ET.Element) else xml
    child_keys = [set(ch.attrib.keys()) for ch in tree.iter(tag)]
    if len(child_keys) == 0:
        return pd.DataFrame({})
    to_gets = reduce(getattr(set, how), child_keys)
    data = {key: [] for key in to_gets}
    for ch in tree.iter(tag):
        for k, v in data.items():
            v.append(ch.attrib.get(k))
    return pd.DataFrame(data).dropna(how="all")


class BioMartServer:
    """BioMart server client (deprecated)."""

    def __init__(self, host=BIOMART_DEFAULT_HOST):
        warnings.warn(
            "BioMartServer is deprecated and may be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        self.host = host
        self._mart_df = None

    @property
    def marts(self):
        if not isinstance(self._mart_df, pd.DataFrame):
            _ = self.list_marts()
        return self._mart_df["name"].to_list()

    def list_marts(self):
        if not isinstance(self._mart_df, pd.DataFrame):
            rsp = get_rsp(self.host, query={"type": "registry"})
            self._mart_df = _biomart_xml_to_tabular(rsp.text)
        return self._mart_df


class BioMartMart:
    """BioMart mart client (deprecated)."""

    def __init__(self, mart_name: str = BIOMART_DEFAULT_MART_NAME,
                 host: str = BIOMART_DEFAULT_HOST):
        warnings.warn(
            "BioMartMart is deprecated and may be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        self.host = host
        self.mart_name = mart_name
        self._datasets = None

    @property
    def datasets(self):
        if not isinstance(self._datasets, pd.DataFrame):
            self._datasets = self._get_datasets()
        return self._datasets["dataset"]

    def _get_datasets(self):
        query = {"type": "datasets", "mart": self.mart_name}
        columns = ["col_0", "dataset", "description", "col_1",
                   "version", "col_2", "col_3", "virtual_schema", "col_5"]
        df = _biomart_rsp_to_df(get_rsp(self.host, query), columns)[
            ["dataset", "description", "version", "virtual_schema"]
        ].dropna(how="all")
        return df

    def list_datasets(self, contain: str = None, ignore_case: bool = True, pattern: str = None):
        if not isinstance(self._datasets, pd.DataFrame):
            self._datasets = self._get_datasets()

        if contain:
            df = _biomart_find_contained_rows(
                df=self._datasets, contain=contain,
                cols=["dataset", "description"], ignore_case=ignore_case
            )
        elif pattern:
            df = _biomart_find_matched_rows(
                df=self._datasets, pattern=pattern, cols=["dataset", "description"]
            )
        else:
            df = self._datasets
        return df


class BioMartDataset:
    """BioMart dataset client (deprecated)."""

    def __init__(self, dataset_name: str = BIOMART_DEFAULT_DATASET_NAME["human"],
                 mart_name: str = BIOMART_DEFAULT_MART_NAME,
                 host: str = BIOMART_DEFAULT_HOST):
        warnings.warn(
            "BioMartDataset is deprecated and may be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        self.host = host
        self.mart_name = mart_name
        self.dataset_name = dataset_name
        self._filters, self._attribs = self._get_config()

    def _get_filter_df(self, root_tree):
        filter_dfs = []
        for filter in root_tree.iter('FilterDescription'):
            filter_df = _biomart_xml_to_tabular(filter, tag='Option').dropna(how="all")
            if filter_df.shape[0] == 0:
                continue
            filter_df = filter_df.rename(columns={"internalName": "name"})
            filter_dfs.append(filter_df)
        return pd.concat(filter_dfs, ignore_index=True)

    def _get_attr_df(self, root_tree):
        attr_dfs = []
        for i, page in enumerate(root_tree.iter('AttributePage')):
            df = _biomart_xml_to_tabular(page, tag='AttributeDescription')
            df["pageName"], df["outFormats"] = page.get("internalName"), page.get("outFormats")
            df = df.rename(columns={"internalName": "name"})
            attr_dfs.append(df)
        return pd.concat(attr_dfs, ignore_index=True)

    def _get_config(self):
        query = {"type": "configuration", "dataset": self.dataset_name}
        rsp = get_rsp(self.host, query)
        tree = ET.fromstring(rsp.text)
        return self._get_filter_df(tree), self._get_attr_df(tree)

    def _add_one_element(self, name, attr_dic, root_node=None):
        if isinstance(root_node, ET.Element):
            node = ET.SubElement(root_node, name)
        else:
            node = ET.Element(name)
        for lab, val in attr_dic.items():
            node.set(lab, val)
        return node

    def _add_element(self, name, attrs, root_node=None):
        if isinstance(attrs, dict):
            node = self._add_one_element(name, attrs, root_node=root_node)
        elif isinstance(attrs, list):
            node = [self._add_one_element(name, attr, root_node=root_node) for attr in attrs]
        else:
            raise ValueError("attrs should be a list of dict or a dict")
        return node

    def get_data(self, attribs, unique_rows=False, **filter_dict):
        query_attr = {
            "header": "0", "virtualSchemaName": "default", "formatter": "TSV",
            "uniqueRows": "0", "datasetConfigVersion": "0.6"
        }
        dataset_attr = {"name": self.dataset_name, "interface": "default"}
        query_node = self._add_element("Query", query_attr, None)
        dataset_node = self._add_element("Dataset", dataset_attr, root_node=query_node)

        if attribs:
            valid_attr_names = self._attribs["name"].to_list()
            attrib_attrs = [{"name": i} for i in attribs]
            assert all([dic["name"] in valid_attr_names for dic in attrib_attrs]), \
                "Some attributes are not valid."
            attrib_nodes = self._add_element("Attribute", attrib_attrs, root_node=dataset_node)

        dfs = []
        if filter_dict:
            for k, v in filter_dict.items():
                max_len = 5000
                max_query = (max([len(vi) for vi in v]) + 2) * len(v) // max_len

                if not isinstance(v, list) or len(v) <= max_query:
                    filter_attrs = [{"name": k, "value": v if not isinstance(v, list) else ",".join(v)}]
                    dfs.append(self._append_filter_and_get_df(
                        query_node, dataset_node, attribs, filter_attrs
                    ))
                else:
                    filter_attrs_list = [
                        [{"name": k, "value": ",".join(v[i_batch * max_query:(i_batch + 1) * max_query])}]
                        for i_batch in range(1 + (len(v) // max_query))
                    ]
                    new_query_nodes = [self._add_element("Query", query_attr, None) for _ in filter_attrs_list]
                    new_dataset_nodes = [
                        self._add_element("Dataset", dataset_attr, root_node=node)
                        for node in new_query_nodes
                    ]
                    if attribs:
                        new_attr_nodes = [
                            self._add_element("Attribute", attrib_attrs, root_node=node)
                            for node in new_dataset_nodes
                        ]
                    assert not any([len(f[0]["value"]) > max_len for f in filter_attrs_list]), \
                        [len(f[0]["value"]) for f in filter_attrs_list]

                    print("Start multithreading process")
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        results = [
                            executor.submit(
                                self._append_filter_and_get_df,
                                query_node=new_query_nodes[c_id],
                                dataset_node=new_dataset_nodes[c_id],
                                attribs=attribs,
                                filter_attrs=filter_attrs,
                                chunk_id=c_id
                            )
                            for c_id, filter_attrs in enumerate(filter_attrs_list)
                            if len(filter_attrs[0]["value"]) > 0
                        ]
                        for f in concurrent.futures.as_completed(results):
                            if f.result() is not None:
                                dfs.append(f.result())
        return pd.concat(dfs, axis=0, ignore_index=True).drop_duplicates()

    def _append_filter_and_get_df(self, query_node, dataset_node, attribs, filter_attrs, chunk_id=-1):
        valid_filter_names = self._filters["name"].to_list()
        assert all([dic["name"] in valid_filter_names for dic in filter_attrs]), \
            "Some filters are not valid."
        filter_nodes = self._add_element('Filter', filter_attrs, root_node=dataset_node)
        try:
            rsp = get_rsp(self.host, query={"query": ET.tostring(query_node, encoding="unicode")})
            assert "Query ERROR" not in rsp.text
        except AssertionError:
            patient = 10
            while patient != 0:
                rsp = get_rsp(
                    self.host,
                    query={"query": ET.tostring(query_node, encoding="unicode")},
                    safe_check=False
                )
                if rsp.status_code == 200:
                    break
                else:
                    patient -= 1
                    print("Still have patient..", patient)
            if patient == 0:
                raise ValueError("Out of patient")

        if not rsp.text == "":
            df = _biomart_rsp_to_df(rsp, columns=attribs)
            return df
        else:
            print("weird result occured")
            print(filter_attrs)
            return None

    def get_data_from_df(self, df, filter_cols):
        raise NotImplementedError

    def list_attributes(self, contain: str = None, pattern: str = None, ignore_case: bool = True):
        df = self._attribs
        if contain:
            df = _biomart_find_contained_rows(
                df=df, contain=contain,
                cols=["name", "displayName", "description"],
                ignore_case=ignore_case
            )
        elif pattern:
            df = _biomart_find_matched_rows(
                df=df, pattern=pattern,
                cols=["name", "displayName", "description"]
            )
        return df

    def list_filters(self, contain: str = None, pattern: str = None, ignore_case: bool = True):
        df = self._filters
        if contain:
            df = _biomart_find_contained_rows(
                df=df, contain=contain,
                cols=["name", 'displayName', "type", "description"],
                ignore_case=ignore_case
            )
        elif pattern:
            df = _biomart_find_matched_rows(
                df=df, pattern=pattern,
                cols=["name", 'displayName', "type", "description"]
            )
        return df
