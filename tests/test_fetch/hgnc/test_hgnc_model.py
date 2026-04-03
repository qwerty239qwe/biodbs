"""Tests for HGNCEntry and related model helpers.

Pure unit tests — no network access.
"""

import pytest

from biodbs.data.HGNC._data_model import (
    HGNCEntry,
    HGNC_SEARCHABLE_FIELDS,
    HGNC_STORED_FIELDS,
)


# ---------------------------------------------------------------------------
# Minimal / full API response dicts (mimic real HGNC API docs)
# ---------------------------------------------------------------------------

TP53_DICT = {
    "hgnc_id": "HGNC:11998",
    "symbol": "TP53",
    "name": "tumor protein p53",
    "status": "Approved",
    "location": "17p13.1",
    "locus_type": "gene with protein product",
    "locus_group": "protein-coding gene",
    "alias_symbol": ["p53", "LFS1"],
    "alias_name": ["tumor suppressor p53"],
    "prev_symbol": [],
    "prev_name": [],
    "gene_group": ["TP53 family"],
    "gene_group_id": [638],
    "date_approved_reserved": "1986-01-01",
    "date_modified": "2023-01-01",
    "ensembl_gene_id": "ENSG00000141510",
    "entrez_id": "7157",
    "uniprot_ids": ["P04637"],
    "refseq_accession": ["NM_000546"],
    "omim_id": ["191170"],
    "ccds_id": ["CCDS11118"],
    "pubmed_id": [6490712, 6336289],
    "vega_id": "OTTHUMG00000162125",
    "ucsc_id": "uc002gij.3",
    "cosmic": "TP53",
    "agr": "HGNC:11998",
    "uuid": "some-uuid",
}

MINIMAL_DICT = {
    "hgnc_id": "HGNC:9999",
    "symbol": "MYGENE",
}


# =============================================================================
# HGNCEntry.from_dict
# =============================================================================


class TestHGNCEntryFromDict:
    def test_full_record(self):
        entry = HGNCEntry.from_dict(TP53_DICT)
        assert entry.hgnc_id == "HGNC:11998"
        assert entry.symbol == "TP53"
        assert entry.name == "tumor protein p53"
        assert entry.ensembl_gene_id == "ENSG00000141510"
        assert entry.entrez_id == "7157"
        assert entry.uniprot_ids == ["P04637"]
        assert entry.refseq_accession == ["NM_000546"]
        assert entry.location == "17p13.1"
        assert entry.status == "Approved"

    def test_minimal_record(self):
        entry = HGNCEntry.from_dict(MINIMAL_DICT)
        assert entry.hgnc_id == "HGNC:9999"
        assert entry.symbol == "MYGENE"
        assert entry.name is None
        assert entry.ensembl_gene_id is None
        assert entry.alias_symbol == []

    def test_list_fields_are_lists(self):
        entry = HGNCEntry.from_dict(TP53_DICT)
        assert isinstance(entry.alias_symbol, list)
        assert isinstance(entry.uniprot_ids, list)
        assert isinstance(entry.refseq_accession, list)
        assert isinstance(entry.omim_id, list)
        assert isinstance(entry.pubmed_id, list)

    def test_scalar_in_list_field_wrapped(self):
        """If API ever returns a scalar instead of a list, wrap it."""
        d = {**MINIMAL_DICT, "uniprot_ids": "P04637"}
        entry = HGNCEntry.from_dict(d)
        assert entry.uniprot_ids == ["P04637"]

    def test_unknown_keys_ignored(self):
        d = {**TP53_DICT, "future_field_xyz": "value"}
        entry = HGNCEntry.from_dict(d)  # must not raise
        assert entry.symbol == "TP53"

    def test_empty_list_fields_default_to_empty_list(self):
        entry = HGNCEntry.from_dict(MINIMAL_DICT)
        assert entry.alias_symbol == []
        assert entry.prev_symbol == []
        assert entry.gene_group == []


# =============================================================================
# HGNCEntry.to_dict
# =============================================================================


class TestHGNCEntryToDict:
    def test_excludes_none_and_empty_lists(self):
        entry = HGNCEntry.from_dict(MINIMAL_DICT)
        d = entry.to_dict()
        assert "name" not in d
        assert "alias_symbol" not in d
        assert "ensembl_gene_id" not in d

    def test_includes_non_empty_fields(self):
        entry = HGNCEntry.from_dict(TP53_DICT)
        d = entry.to_dict()
        assert d["hgnc_id"] == "HGNC:11998"
        assert d["symbol"] == "TP53"
        assert d["uniprot_ids"] == ["P04637"]
        assert d["alias_symbol"] == ["p53", "LFS1"]

    def test_roundtrip(self):
        entry = HGNCEntry.from_dict(TP53_DICT)
        d = entry.to_dict()
        entry2 = HGNCEntry.from_dict(d)
        assert entry2.hgnc_id == entry.hgnc_id
        assert entry2.symbol == entry.symbol
        assert entry2.uniprot_ids == entry.uniprot_ids


# =============================================================================
# Field sets
# =============================================================================


class TestFieldSets:
    def test_core_searchable_fields_present(self):
        for field in ("symbol", "hgnc_id", "entrez_id", "ensembl_gene_id",
                      "uniprot_ids", "refseq_accession"):
            assert field in HGNC_SEARCHABLE_FIELDS

    def test_core_stored_fields_present(self):
        for field in ("symbol", "hgnc_id", "name", "status", "location",
                      "ensembl_gene_id", "entrez_id", "uniprot_ids",
                      "refseq_accession", "omim_id"):
            assert field in HGNC_STORED_FIELDS

    def test_stored_is_superset_of_searchable(self):
        # All searchable fields should exist in the stored set (mostly true;
        # a few curator-only fields are searchable but not stored, so we just
        # check the data-model fields)
        data_model_fields = set(HGNCEntry.__dataclass_fields__)
        for f in data_model_fields:
            if f in HGNC_SEARCHABLE_FIELDS:
                assert f in HGNC_STORED_FIELDS, f"{f!r} searchable but not stored"
