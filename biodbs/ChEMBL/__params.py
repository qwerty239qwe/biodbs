import re


class ChEMBLNameSpace:


    NAMESPACE = {
                 "activity": ["molecule_chembl_id","assay_chembl_id","target_chembl_id"],
                 "assay": ["target_chembl_id",],
                 "compound_record": [],
                 "drug": [],
                 "molecule": ["molecule_chembl_id",],
                 "mechanism":["molecule_chembl_id",],
                 "substance": [],
                 "protein_classification": [],
                 "cell_line": [],
                 "target": ["target_components_accession",],
                 "others": [".*"]}

    def __init__(self, domain):
        self.name_space: list = self.NAMESPACE[domain]

    def match(self, to_test):
        return any([len(re.findall(ns, to_test)) > 0 for ns in self.name_space])
