import time
from biodbs.utils import get_rsp
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup as BS


DEFAULT_HOST = "https://maayanlab.cloud/Enrichr"
EXAMPLE_GS = [
    "PHF14", "RBM3", "MSL1", "PHF21A", "ARL10", "INSR", "JADE2",
    "P2RX7", "LINC00662", "CCDC101", "PPM1B", "KANSL1L", "CRYZL1",
    "ANAPC16", "TMCC1", "CDH8", "RBM11", "CNPY2", "HSPA1L", "CUL2",
    "PLBD2", "LARP7", "TECPR2", "ZNF302", "CUX1", "MOB2", "CYTH2",
    "SEC22C", "EIF4E3", "ROBO2", "ADAMTS9-AS2", "CXXC1", "LINC01314",
    "ATF7", "ATP5F1"
]


class Enrichr:
    def __init__(self, list_id_file_name=None, load_list_id=True, host = DEFAULT_HOST):
        self.host = host
        self.user_list_dic = []  # time: dict
        self.list_id_file_name = list_id_file_name
        if load_list_id:
            assert self.list_id_file_name is not None
            self._read_user_list_id()

    def _read_user_list_id(self):
        with open(Path(self.list_id_file_name), "r") as f:
            lines = f.readlines()[1:]
            for line in lines:
                user_list_id, short_id, time = line.split("\t")
                self.user_list_dic.append({'userListId': user_list_id, 'shortId': short_id, 'time': time})

    def _write_user_list_id(self, new_id):
        if not Path(self.list_id_file_name).exists():
            with open(Path(self.list_id_file_name), "w") as f:
                f.write("userListId\tshortId\trecordTime\n")

        with open(self.list_id_file_name, "a") as f:
            f.write(f"{new_id['userListId']}\t{new_id['shortId']}\t{new_id['time']}\n")

    def analyze_gene_set(self, genes, description):
        analysis_time = time.strftime("%Y-%m-%d, %H:%M:%S")
        response = get_rsp(self.host + "/addList",
                           method="post",
                           files={'list': (None, '\n'.join(genes)), 'description': (None, description)})
        data = response.json()
        data.update({"time": analysis_time})
        self.user_list_dic.append(data)
        # Save file
        if self.list_id_file_name is not None:
            self._write_user_list_id(data)

    def view_gene_set(self, user_list_id):
        response = get_rsp(self.host + "/view",
                           method="get",
                           query={"userListId": user_list_id})
        return response.json()

    def get_GSEA_result(self, user_list_id, library_name="KEGG_2015"):
        header = ["Rank", "Term name", "P-value", "Z-score",
                  "Combined score", "Overlapping genes", "Adjusted p-value",
                  "Old p-value", "Old adjusted p-value"]
        response = get_rsp(self.host + "/enrich",
                           method="get",
                           query={"userListId": user_list_id, "backgroundType": library_name})
        data = response.json()[library_name]
        df = pd.DataFrame(data)
        df.columns = header[: len(df.columns)]
        return df

    def find_gene_term(self, gene, json=True, setup=True):
        response = get_rsp(self.host + "/genemap",
                           method="get",
                           query={"json": json, "setup": setup, "gene": gene})
        return response.json() if json else response.text

    def get_library(self, name):
        response = get_rsp(self.host + "/geneSetLibrary",
                           method="get",
                           query={"mode": "text", "libraryName": name})
        data = response.text
        lines = data.split("\n")
        lines = [[c for c in row.split("\t") if c != ""] for row in lines]
        return {gdata[0]: gdata[1:] for gdata in lines}

    def get_libraries_table(self):
        columns = ["Gene-set Library", "Terms", "Gene Coverage", "Genes per Term"]
        try_times = 10
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(self.host + "/#stats")
            for _ in range(try_times):
                time.sleep(1.)
                page_content = page.content()
                soup = BS(page_content, 'html.parser')
                table = soup.find("table", id="stats").find("tbody")
                if table.text != "":
                    break
            browser.close()
        table_rows = table.find_all("tr")
        table_contents = [[c.text for c in tr.find_all("td") if c.text != ''] for tr in table_rows]
        return pd.DataFrame(table_contents, columns=columns)

