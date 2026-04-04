"""Shared test fixtures — realistic ClinVar esummary JSON shapes."""

# -------------------------------------------------------------------------
# Raw esummary doc dicts (the value under result.<uid>)
# -------------------------------------------------------------------------

TP53_DOC = {
    "uid": "12375",
    "obj_type": "single nucleotide variant",
    "accession": "VCV000012375",
    "accession_version": "VCV000012375.28",
    "title": "NM_000546.6(TP53):c.817C>T (p.Arg273Cys)",
    "genes": [
        {"symbol": "TP53", "geneid": "7157", "strand": "+", "source": "submitted"}
    ],
    "protein_change": "Arg273Cys",
    "rcvaccession": "RCV000013219|RCV000144296",
    "clinical_significance": {
        "description": "Pathogenic",
        "review_status": "reviewed by expert panel",
        "last_evaluated": "2019-05-01",
    },
    "trait_set": [
        {"trait_name": "Li-Fraumeni syndrome", "trait_type": "Disease"},
        {"trait_name": "Hereditary cancer-predisposing syndrome", "trait_type": "Disease"},
    ],
    "variation_set": [
        {
            "measure_set": {
                "variation_name": "NM_000546.6(TP53):c.817C>T",
                "variation_type": "single nucleotide variant",
            }
        }
    ],
    "assembly_set": [
        {
            "assembly_name": "GRCh38",
            "assembly_acc_ver": "GCF_000001405.40",
            "location": {
                "chr": "17",
                "asm_name": "GRCh38",
                "start": 7673781,
                "stop": 7673781,
            },
        },
        {
            "assembly_name": "GRCh37",
            "assembly_acc_ver": "GCF_000001405.25",
            "location": {
                "chr": "17",
                "asm_name": "GRCh37",
                "start": 7674220,
                "stop": 7674220,
            },
        },
    ],
}

BRCA1_DOC = {
    "uid": "65533",
    "obj_type": "single nucleotide variant",
    "accession": "VCV000065533",
    "accession_version": "VCV000065533.5",
    "title": "NM_007294.4(BRCA1):c.181T>G (p.Cys61Gly)",
    "genes": [
        {"symbol": "BRCA1", "geneid": "672", "strand": "+", "source": "submitted"}
    ],
    "protein_change": "Cys61Gly",
    "rcvaccession": "RCV000031124",
    "clinical_significance": {
        "description": "Pathogenic",
        "review_status": "criteria provided, multiple submitters, no conflicts",
        "last_evaluated": "2022-01-15",
    },
    "trait_set": [
        {"trait_name": "Hereditary breast and ovarian cancer syndrome", "trait_type": "Disease"}
    ],
    "variation_set": [
        {
            "measure_set": {
                "variation_name": "NM_007294.4(BRCA1):c.181T>G",
                "variation_type": "single nucleotide variant",
            }
        }
    ],
    "assembly_set": [
        {
            "assembly_name": "GRCh38",
            "location": {"chr": "17", "start": 43094347, "stop": 43094347},
        }
    ],
}

BENIGN_DOC = {
    "uid": "99999",
    "obj_type": "single nucleotide variant",
    "accession": "VCV000099999",
    "accession_version": "VCV000099999.1",
    "title": "NM_000546.6(TP53):c.100A>G (p.Thr34Ala)",
    "genes": [{"symbol": "TP53", "geneid": "7157", "strand": "+", "source": "submitted"}],
    "protein_change": "Thr34Ala",
    "rcvaccession": "RCV000888888",
    "clinical_significance": {
        "description": "Likely benign",
        "review_status": "criteria provided, single submitter",
        "last_evaluated": "2021-06-01",
    },
    "trait_set": [{"trait_name": "not provided", "trait_type": "Disease"}],
    "variation_set": [],
    "assembly_set": [],
}

MULTI_GENE_DOC = {
    "uid": "55555",
    "obj_type": "deletion",
    "accession": "VCV000055555",
    "accession_version": "VCV000055555.2",
    "title": "Deletion of BRCA1 and NBR1",
    "genes": [
        {"symbol": "BRCA1", "geneid": "672"},
        {"symbol": "NBR1", "geneid": "4077"},
    ],
    "protein_change": None,
    "rcvaccession": ["RCV000111111", "RCV000222222"],  # list form
    "clinical_significance": {
        "description": "Pathogenic/Likely pathogenic",
        "review_status": "criteria provided, multiple submitters, no conflicts",
        "last_evaluated": "2020-03-10",
    },
    "trait_set": [],
    "variation_set": [],
    "assembly_set": [
        {
            "assembly_name": "GRCh37",  # only GRCh37 available
            "location": {"chr": "17", "start": 41196312, "stop": 41277500},
        }
    ],
}

MINIMAL_DOC = {
    "uid": "1",
    "accession": "VCV000000001",
    "title": "Some variant",
}


# -------------------------------------------------------------------------
# Full esummary response wrappers
# -------------------------------------------------------------------------

def esummary_response(*docs: dict) -> dict:
    """Wrap doc dicts into a full esummary JSON structure."""
    uids = [d["uid"] for d in docs]
    result = {"uids": uids}
    for doc in docs:
        result[doc["uid"]] = doc
    return {"header": {"type": "esummary"}, "result": result}


def esearch_response(idlist: list, count: int = None) -> dict:
    """Build an esearch JSON response."""
    return {
        "esearchresult": {
            "count": str(count if count is not None else len(idlist)),
            "retmax": str(len(idlist)),
            "idlist": idlist,
            "translationset": [],
            "querytranslation": "",
        }
    }


def elink_response(pmids: list, variation_id: str = "12375") -> dict:
    """Build an elink JSON response."""
    return {
        "linksets": [
            {
                "dbfrom": "clinvar",
                "ids": [variation_id],
                "linksetdbs": [
                    {"dbto": "pubmed", "linkname": "clinvar_pubmed", "links": pmids}
                ],
            }
        ]
    }
