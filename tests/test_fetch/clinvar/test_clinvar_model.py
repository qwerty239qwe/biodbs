"""Tests for ClinVarVariant — data model parsing.

Pure unit tests, no network access.
"""

import pytest

from biodbs.data.ClinVar._data_model import ClinVarVariant
from tests.test_fetch.clinvar.fixtures import (
    TP53_DOC, BRCA1_DOC, BENIGN_DOC, MULTI_GENE_DOC, MINIMAL_DOC,
)


# =============================================================================
# from_esummary_dict — core fields
# =============================================================================

class TestFromEsummaryDict:
    def test_variation_id(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.variation_id == "12375"

    def test_accession(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.accession == "VCV000012375"
        assert v.accession_version == "VCV000012375.28"

    def test_title(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert "TP53" in v.title
        assert "Arg273Cys" in v.title

    def test_protein_change(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.protein_change == "Arg273Cys"

    def test_protein_change_none(self):
        v = ClinVarVariant.from_esummary_dict("55555", MULTI_GENE_DOC)
        assert v.protein_change is None


# =============================================================================
# from_esummary_dict — genes
# =============================================================================

class TestGenesParsing:
    def test_single_gene_symbol(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.gene_symbols == ["TP53"]
        assert v.gene_ids == ["7157"]

    def test_multi_gene(self):
        v = ClinVarVariant.from_esummary_dict("55555", MULTI_GENE_DOC)
        assert set(v.gene_symbols) == {"BRCA1", "NBR1"}
        assert set(v.gene_ids) == {"672", "4077"}

    def test_no_genes_in_minimal_doc(self):
        v = ClinVarVariant.from_esummary_dict("1", MINIMAL_DOC)
        assert v.gene_symbols == []
        assert v.gene_ids == []


# =============================================================================
# from_esummary_dict — clinical significance
# =============================================================================

class TestClinicalSignificance:
    def test_pathogenic(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.clinical_significance == "Pathogenic"

    def test_likely_benign(self):
        v = ClinVarVariant.from_esummary_dict("99999", BENIGN_DOC)
        assert v.clinical_significance == "Likely benign"

    def test_review_status(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.review_status == "reviewed by expert panel"

    def test_last_evaluated(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.last_evaluated == "2019-05-01"

    def test_missing_clinical_significance(self):
        v = ClinVarVariant.from_esummary_dict("1", MINIMAL_DOC)
        assert v.clinical_significance is None
        assert v.review_status is None
        assert v.last_evaluated is None


# =============================================================================
# from_esummary_dict — conditions / traits
# =============================================================================

class TestConditionsParsing:
    def test_multiple_conditions(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert "Li-Fraumeni syndrome" in v.conditions
        assert "Hereditary cancer-predisposing syndrome" in v.conditions

    def test_single_condition(self):
        v = ClinVarVariant.from_esummary_dict("65533", BRCA1_DOC)
        assert v.conditions == ["Hereditary breast and ovarian cancer syndrome"]

    def test_no_conditions(self):
        v = ClinVarVariant.from_esummary_dict("55555", MULTI_GENE_DOC)
        assert v.conditions == []


# =============================================================================
# from_esummary_dict — RCV accessions
# =============================================================================

class TestRCVParsing:
    def test_pipe_separated_string(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.rcv_accessions == ["RCV000013219", "RCV000144296"]

    def test_single_rcv_string(self):
        v = ClinVarVariant.from_esummary_dict("65533", BRCA1_DOC)
        assert v.rcv_accessions == ["RCV000031124"]

    def test_list_form(self):
        v = ClinVarVariant.from_esummary_dict("55555", MULTI_GENE_DOC)
        assert v.rcv_accessions == ["RCV000111111", "RCV000222222"]

    def test_empty_rcv(self):
        v = ClinVarVariant.from_esummary_dict("1", MINIMAL_DOC)
        assert v.rcv_accessions == []


# =============================================================================
# from_esummary_dict — variation type
# =============================================================================

class TestVariationTypeParsing:
    def test_from_measure_set(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.variation_type == "single nucleotide variant"

    def test_fallback_to_obj_type(self):
        # BENIGN_DOC has empty variation_set, falls back to obj_type
        v = ClinVarVariant.from_esummary_dict("99999", BENIGN_DOC)
        assert v.variation_type == "single nucleotide variant"

    def test_deletion_type(self):
        v = ClinVarVariant.from_esummary_dict("55555", MULTI_GENE_DOC)
        assert v.variation_type == "deletion"

    def test_no_type_in_minimal(self):
        v = ClinVarVariant.from_esummary_dict("1", MINIMAL_DOC)
        assert v.variation_type is None


# =============================================================================
# from_esummary_dict — genomic location
# =============================================================================

class TestAssemblyParsing:
    def test_prefers_grch38(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.assembly == "GRCh38"
        assert v.chromosome == "17"
        assert v.start == 7673781
        assert v.stop == 7673781

    def test_grch37_fallback(self):
        # MULTI_GENE_DOC only has GRCh37
        v = ClinVarVariant.from_esummary_dict("55555", MULTI_GENE_DOC)
        assert v.assembly == "GRCh37"
        assert v.chromosome == "17"
        assert v.start == 41196312
        assert v.stop == 41277500

    def test_no_assembly(self):
        v = ClinVarVariant.from_esummary_dict("1", MINIMAL_DOC)
        assert v.chromosome is None
        assert v.start is None
        assert v.stop is None
        assert v.assembly is None


# =============================================================================
# Properties
# =============================================================================

class TestProperties:
    def test_is_pathogenic_true(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.is_pathogenic is True

    def test_is_pathogenic_false_benign(self):
        v = ClinVarVariant.from_esummary_dict("99999", BENIGN_DOC)
        assert v.is_pathogenic is False

    def test_is_pathogenic_mixed(self):
        v = ClinVarVariant.from_esummary_dict("55555", MULTI_GENE_DOC)
        # "Pathogenic/Likely pathogenic" contains "pathogenic" but not "likely benign"
        assert v.is_pathogenic is True

    def test_primary_gene(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        assert v.primary_gene == "TP53"

    def test_primary_gene_none_when_no_genes(self):
        v = ClinVarVariant.from_esummary_dict("1", MINIMAL_DOC)
        assert v.primary_gene is None

    def test_repr_contains_accession(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        r = repr(v)
        assert "VCV000012375" in r
        assert "TP53" in r


# =============================================================================
# to_dict
# =============================================================================

class TestToDict:
    def test_returns_dict(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        d = v.to_dict()
        assert isinstance(d, dict)

    def test_contains_all_fields(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        d = v.to_dict()
        for field in ("variation_id", "accession", "title", "clinical_significance",
                      "gene_symbols", "conditions", "chromosome", "start", "stop"):
            assert field in d

    def test_values_match(self):
        v = ClinVarVariant.from_esummary_dict("12375", TP53_DOC)
        d = v.to_dict()
        assert d["variation_id"] == "12375"
        assert d["gene_symbols"] == ["TP53"]
        assert d["clinical_significance"] == "Pathogenic"
