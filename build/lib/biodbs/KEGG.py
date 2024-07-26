from biodbs.utils import get_rsp, save_image_from_rsp
from enum import Enum
import pandas as pd
from functools import lru_cache


DEFAULT_HOST = "http://rest.kegg.jp"


class Database(Enum):
    # used_name : (DB name, abbrev, description)
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


ALIAS_NAME_DICT = {db.value[1]: db.name for db in Database}


def list_database():
    return pd.DataFrame({db.name: list(db.value)[:3]
                         for db in Database}, index=["DB name", "abbrev", "content"]).T


class KEGGdb:
    FIND_OPTIONS = ("formula", "exact_mass", "mol_weight", "nop")
    GET_OPTIONS = ("aaseq", "ntseq", "mol", "kcf", "image", "conf", "kgml", "json")
    CONV_GENE_EXTERNAL_DBS = ("ncbi-geneid", "ncbi-proteinid", "uniprot")
    CONV_CHEM_EXTERNAL_DBS = ("pubchem", "chebi")
    CONV_CHEM_INTERNAL_DBS = ("compound", "glycan", "drug")

    def __init__(self, host=DEFAULT_HOST):
        self.host = host

    @lru_cache()
    def get_info(self, database):
        if database in ALIAS_NAME_DICT:
            database = ALIAS_NAME_DICT[database]
        return get_rsp(self.host + "/info/" + database).text

    @lru_cache()
    def list_df(self, database):
        if database in ALIAS_NAME_DICT:
            database = ALIAS_NAME_DICT[database]
        rsp_txt = get_rsp(self.host + "/list/" + database).text
        rsp_lines = rsp_txt.split("\n")
        return pd.DataFrame([line.split("\t") for line in rsp_lines])

    @lru_cache()
    def list_organism(self,
                      contains: str = None,
                      query_tags: str = None  # ex: "A and B and C"
                      ):
        rsp_txt = get_rsp(self.host + "/list/organism").text
        rsp_lines = rsp_txt.split("\n")
        org_df = pd.DataFrame([line.split("\t") for line in rsp_lines],
                              columns=["ID", "abbrev", "full name", "tags"])
        if contains is not None:
            org_df = org_df[org_df["abbrev"].str.contains(contains) |
                            org_df["full name"].str.contains(contains) |
                            org_df["tags"].str.contains(contains)]
        if query_tags is not None:
            # TODO:
            org_df = org_df[org_df["tags"]]

        return org_df

    @lru_cache()
    def list_found_entries(self,
                           database,
                           query: str,
                           option: str = None):
        url = self.host + "/find/" + database + "/" + query

        if database in ("compound", "drug"):
            assert option in self.FIND_OPTIONS
            url += ("/" + option)

        rsp_txt = get_rsp(url).text
        rsp_lines = rsp_txt.split("\n")

        return pd.DataFrame([line.split("\t") for line in rsp_lines],
                            columns=["ID", option if option else "found_entries"])

    @lru_cache()
    def get_entries(self,
                    entries,
                    option=None):
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
    def list_converted_id(self,
                          target_db,
                          source_db=None,
                          entries=None):
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


