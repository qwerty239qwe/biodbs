import pandas as pd
from biodbs.utils import get_rsp
import xml.etree.ElementTree as ET
from functools import reduce
import concurrent.futures
from functools import lru_cache


HOSTS = {"main": "www.ensembl.org",
         "apr2018": "apr2018.archive.ensembl.org",  # Ensembl version: 92.38 - used by HPA
         "may2015": "may2015.archive.ensembl.org",  # Ensembl version: GRCh38.p2
         "plants": "plants.ensembl.org",
         "fungi": "fungi.ensembl.org",
         "protist": "protist.ensembl.org",
         "metazoa": "metazoa.ensembl.org"}

DEFAULT_HOST = "http://" + HOSTS["main"] + "/biomart/martservice?"
DEFAULT_MART_NAME = "ENSEMBL_MART_ENSEMBL"
DEFAULT_DATASET_NAME = {"human": "hsapiens_gene_ensembl", "mouse": "mmusculus_gene_ensembl"}


def get_full_url_from_host(host_name):
    return "http://" + HOSTS[host_name] + "/biomart/martservice?"


def _rsp_to_df(rsp, columns):
    return pd.DataFrame([r.split("\t") for r in rsp.text.split("\n")], columns=columns)


def find_contained_rows(df, contain, cols, ignore_case=True):
    contain = contain.lower() if ignore_case else contain
    boolean_dfs = [df[col].apply(lambda x: "" if not isinstance(x, str) else
                                        x.lower() if ignore_case else x).str.match(f".*{contain}.*")
                   for col in cols]
    return df[reduce(lambda l, r: l | r, boolean_dfs)]


def find_matched_rows(df, pattern, cols):
    boolean_dfs = [df[col].str.match(pattern)
                   for col in cols]
    return df[reduce(lambda l, r: l | r, boolean_dfs)]


def xml_to_tabular(xml, tag=None, how="union"):
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


class Server:
    """
    A biomart server contains many mart
    """
    def __init__(self, host=DEFAULT_HOST):
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
            self._mart_df = xml_to_tabular(rsp.text)
        return self._mart_df


class Mart:
    """
    A mart contains many datasets
    """
    def __init__(self,
                 mart_name: str = DEFAULT_MART_NAME,
                 host: str = DEFAULT_HOST):
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
        df = _rsp_to_df(get_rsp(self.host, query), columns)[["dataset", "description",
                                                             "version", "virtual_schema"]].dropna(how="all")
        return df

    def list_datasets(self,
                      contain: str = None,
                      ignore_case: bool = True,
                      pattern: str = None):
        if not isinstance(self._datasets, pd.DataFrame):
            self._datasets = self._get_datasets()

        if contain:
            df = find_contained_rows(df=self._datasets,
                                     contain=contain,
                                     cols=["dataset", "description"],
                                     ignore_case=ignore_case)
        elif pattern:
            df = find_matched_rows(df=self._datasets,
                                   pattern=pattern,
                                   cols=["dataset", "description"])
        else:
            df = self._datasets
        return df


class Dataset:
    def __init__(self,
                 dataset_name: str = DEFAULT_DATASET_NAME["human"],
                 mart_name: str = DEFAULT_MART_NAME,
                 host: str = DEFAULT_HOST):
        self.host = host
        self.mart_name = mart_name
        self.dataset_name = dataset_name
        self._filters, self._attribs = self._get_config()

    def _get_filter_df(self, root_tree):
        filter_dfs = []
        for filter in root_tree.iter('FilterDescription'):
            filter_df = xml_to_tabular(filter, tag='Option').dropna(how="all")
            if filter_df.shape[0] == 0:
                continue
            filter_df = filter_df.rename(columns={"internalName": "name"})
            filter_dfs.append(filter_df)
        return pd.concat(filter_dfs, ignore_index=True)

    def _get_attr_df(self, root_tree):
        attr_dfs = []
        for i, page in enumerate(root_tree.iter('AttributePage')):
            df = xml_to_tabular(page, tag='AttributeDescription')
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
        query_attr = {"header": "0",
                      "virtualSchemaName": "default",
                      "formatter": "TSV",
                      "uniqueRows": "0",
                      "datasetConfigVersion": "0.6"}

        dataset_attr = {"name": self.dataset_name, "interface": "default"}
        query_node = self._add_element("Query", query_attr, None)
        dataset_node = self._add_element("Dataset", dataset_attr, root_node=query_node)
        if attribs:
            valid_attr_names = self._attribs["name"].to_list()
            attrib_attrs = [{"name": i} for i in attribs]
            assert all([dic["name"] in valid_attr_names for dic in attrib_attrs]), "Some attributes are not valid."
            attrib_nodes = self._add_element("Attribute", attrib_attrs, root_node=dataset_node)

        dfs = []
        if filter_dict:
            for k, v in filter_dict.items():
                max_len = 5000
                max_query = (max([len(vi) for vi in v]) + 2) * len(v) // max_len

                if not isinstance(v, list) or len(v) <= max_query:
                    filter_attrs = [{"name": k, "value": v if not isinstance(v, list) else ",".join(v)}]
                    dfs.append(self._append_filter_and_get_df(query_node,
                                                              dataset_node,
                                                              attribs,
                                                              filter_attrs))
                else:
                    filter_attrs_list = [[{"name": k, "value": ",".join(v[i_batch * max_query:
                                                                          (i_batch + 1) * max_query])}]
                                         for i_batch in range(1 + (len(v) // max_query))]
                    new_query_nodes = [self._add_element("Query", query_attr, None) for _ in filter_attrs_list]
                    new_dataset_nodes = [self._add_element("Dataset",
                                                           dataset_attr,
                                                           root_node=node) for node in new_query_nodes]
                    if attribs:
                        new_attr_nodes = [self._add_element("Attribute", attrib_attrs,
                                                            root_node=node) for node in new_dataset_nodes]
                    assert not any([len(f[0]["value"]) > max_len for f in filter_attrs_list]), \
                        [len(f[0]["value"]) for f in filter_attrs_list]

                    # for c_id, filter_attrs in enumerate(filter_attrs_list):
                    #     if len(filter_attrs[0]["value"]) == 0:
                    #         print("skip", c_id)
                    #         continue
                    #     result = self._append_filter_and_get_df(query_node=new_query_nodes[c_id],
                    #                                             dataset_node=new_dataset_nodes[c_id],
                    #                                             attribs=attribs,
                    #                                             filter_attrs=filter_attrs, chunk_id=c_id)
                    #     dfs.append(result)
                    print("Start multithreading process")
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        results = [executor.submit(self._append_filter_and_get_df,
                                                   query_node=new_query_nodes[c_id],
                                                   dataset_node=new_dataset_nodes[c_id],
                                                   attribs=attribs,
                                                   filter_attrs=filter_attrs,
                                                   chunk_id=c_id)
                                   for c_id, filter_attrs in enumerate(filter_attrs_list)
                                   if len(filter_attrs[0]["value"]) > 0]
                        for f in concurrent.futures.as_completed(results):
                            if f.result() is not None:
                                dfs.append(f.result())
        return pd.concat(dfs, axis=0, ignore_index=True).drop_duplicates()

    def _append_filter_and_get_df(self, query_node, dataset_node, attribs, filter_attrs, chunk_id=-1):
        valid_filter_names = self._filters["name"].to_list()
        assert all([dic["name"] in valid_filter_names for dic in filter_attrs]), "Some filters are not valid."
        filter_nodes = self._add_element('Filter', filter_attrs, root_node=dataset_node)
        try:
            rsp = get_rsp(self.host, query={"query": ET.tostring(query_node, encoding="unicode")})
            assert "Query ERROR" not in rsp.text
        except AssertionError:
            # sometimes biomart gives 500 error, but not always...
            patient = 10
            while patient != 0:
                rsp = get_rsp(self.host, query={"query": ET.tostring(query_node, encoding="unicode")}, safe_check=False)
                if rsp.status_code == 200:
                    break
                else:
                    patient -= 1
                    print("Still have patient..", patient)
            if patient == 0:
                raise ValueError("Out of patient")

        if not rsp.text == "":
            df = _rsp_to_df(rsp, columns=attribs)
            return df
        else:
            print("weird result occured")
            print(filter_attrs)
            return None

    def get_data_from_df(self, df, filter_cols):
        raise NotImplementedError

    def list_attributes(self,
                        contain: str = None,
                        pattern: str = None,
                        ignore_case: bool = True):
        df = self._attribs
        if contain:
            df = find_contained_rows(df=df,
                                     contain=contain,
                                     cols=["name", "displayName", "description"],
                                     ignore_case=ignore_case)
        elif pattern:
            df = find_matched_rows(df=df,
                                   pattern=pattern,
                                   cols=["name", "displayName", "description"])
        return df

    def list_filters(self,
                     contain: str = None,
                     pattern: str = None,
                     ignore_case: bool = True):
        df = self._filters
        if contain:
            df = find_contained_rows(df=df,
                                     contain=contain,
                                     cols=["name", 'displayName', "type", "description"],
                                     ignore_case=ignore_case)
        elif pattern:
            df = find_matched_rows(df=df,
                                   pattern=pattern,
                                   cols=["name", 'displayName', "type", "description"])
        return df