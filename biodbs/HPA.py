from biodbs.utils import get_rsp, fetch_and_extract
import pandas as pd
import concurrent.futures
from typing import Tuple
from functools import partial
from tqdm import tqdm



DEFAULT_HOST = "http://www.proteinatlas.org/"
DOWNLOADABLE_DATA = ["normal_tissue",
                     "pathology",
                     "subcellular_location",
                     "rna_tissue_consensus",
                     "rna_tissue_hpa",
                     "rna_tissue_gtex",
                     "rna_tissue_fantom",
                     "rna_single_cell_type",
                     "rna_single_cell_type_tissue",
                     "rna_brain_gtex",
                     "rna_brain_fantom",
                     "rna_pig_brain_hpa",
                     "rna_pig_brain_sample_hpa",
                     "rna_mouse_brain_hpa",
                     "rna_mouse_brain_sample_hpa",
                     "rna_mouse_brain_allen",
                     "rna_blood_cell",
                     "rna_blood_cell_sample",
                     "rna_blood_cell_sample_tpm_m",
                     "rna_blood_cell_monaco",
                     "rna_blood_cell_schmiedel",
                     "rna_celline",
                     "rna_cancer_sample",
                     "transcript_rna_tissue",
                     "transcript_rna_celline",
                     "transcript_rna_pigbrain",
                     "transcript_rna_mousebrain"]


class HPAdb:
    def __init__(self, host=DEFAULT_HOST):
        self.host = host

    def list_proteins(self, ids = ["ENSG00000101473", "ENSG00000113552"]) -> Tuple[pd.DataFrame, list]:
        get_rsp_ = partial(get_rsp, safe_check=False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(tqdm(executor.map(get_rsp_, (self.host + p_id + ".json" for p_id in ids)), total=len(ids)))
        failed = [ids[i] for i, v in enumerate(results) if v.status_code != 200]
        successed = [r.json() for r in results if r.status_code == 200]
        return pd.DataFrame(successed), failed

    def download_HPA_data(self, options, saved_path):
        for opt in options:
            assert opt in DOWNLOADABLE_DATA, "{opt} is not valid, valid options: {valid}".format(opt=opt,
                                                                                                 valid=DOWNLOADABLE_DATA)
            fetch_and_extract(url="{host}/download/{opt}.tsv.zip".format(host=self.host, opt=opt), saved_path=saved_path)
            print("Data is downloaded and saved in ", saved_path)
