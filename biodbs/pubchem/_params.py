import re


class PUBRESTNameSpace:
    xref_pattern = "|".join(["RegistryID", "RN", "PubMedID", "MMDBID", "ProteinGI", "NucleotideGI", "TaxonomyID",
                             "MIMID", "GeneID", "ProbeID", "PatentID"])
    fast_search = "fastformula|(fastidentity|fastsimilarity_2d|fastsimilarity_3d|fastsubstructure|fastsuperstructure)/" \
                  "(smiles|smarts|inchi|sdf|cid)"

    NAMESPACE = {"compound": ["cid", "name", "smiles", "inchi", "sdf", "inchikey", "formula",
                              r"(substructure|superstructure|similarity|identity)/(smiles|inchi|sdf|cid)",
                              "xref/{xref_pattern}".format(xref_pattern=xref_pattern),
                              "listkey",
                              fast_search],
                 "substance": ["sid", "sourceid/.*", "sourceall/.*", "name", "listkey",
                               "xref/{xref_pattern}".format(xref_pattern=xref_pattern)],
                 "assay": ["aid", "listkey",
                           "type/(all|confirmatory|doseresponse|onhold|panel|rnai|screening|summary|cellbased|"
                           "biochemical|invivo|invitro|activeconcentrationspecified)",
                           "sourceall/.*",
                           "target/(gi|proteinname|geneid|genesymbol|accession)",
                           "activity/.*"],
                 "bioassay": ["aid", "listkey",
                           "type/(all|confirmatory|doseresponse|onhold|panel|rnai|screening|summary|cellbased|"
                           "biochemical|invivo|invitro|activeconcentrationspecified)",
                           "sourceall/.*",
                           "target/(gi|proteinname|geneid|genesymbol|accession)",
                           "activity/.*"],
                 "gene": ["geneid", "genesymbol", "synonym"],
                 "protein": ["accession", "gi", "synonym"],
                 "pathway": ["pwacc"],
                 "taxonomy": ["taxid", "synonym"],
                 "cell": ["cellacc", "synonym"],
                 "others": [".*"]}

    def __init__(self, domain):
        self.name_space: list = self.NAMESPACE[domain]

    def match(self, to_test):
        return any([len(re.findall(ns, to_test)) > 0 for ns in self.name_space])


class PUBRESTOperation:
    properties = "property/.*"
    OPERATIONS = {"compound": [properties, "record", "synonyms", "sids", "cids", "aids",
                               "assaysummary", "classification", "description", "conformers", r"xrefs/.*"],
                  "substance": ["record", "synonyms", "sids", "cids", "aids",
                                "assaysummary", "classification", r"xrefs/.*", "description"],
                  "assay": ["record", "concise", "sids", "cids", "aids", "summary", "classification",
                            r"xrefs/.*", "description", "targets/(ProteinGI|ProteinName|GeneID|GeneSymbol)",
                            "doseresponse/sid"],
                  "bioassay": ["record", "concise", "sids", "cids", "aids", "summary", "classification",
                            r"xrefs/.*", "description", "targets/(ProteinGI|ProteinName|GeneID|GeneSymbol)",
                            "doseresponse/sid"],
                  "gene": ["summary", "aids", "concise", "pwaccs"],
                  "protein": ["summary", "aids", "concise", "pwaccs"],
                  "pathway": ["summary", "cids", "geneids", "accessions"],
                  "taxonomy": ["summary", "aids"],
                  "cell": ["summary", "aids"],
                  "others": [".*"]
                  }

    def __init__(self, domain):
        self.operations: list = self.OPERATIONS[domain]

    def match(self, to_test):
        return any([len(re.findall(op, to_test)) > 0 for op in self.operations])