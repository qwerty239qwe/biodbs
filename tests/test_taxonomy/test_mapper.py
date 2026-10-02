import dataclasses
from pathlib import Path

import pandas as pd
import pytest

from biodbs.taxonomy import TaxonomyMapper, TaxonRecord, merge_on_hub, MAPPING_COLUMNS, load_taxdump


class FakeTaxdump:
    def __init__(self, by_name, ranks=None, lineages=None):
        self._by_name = by_name
        self._ranks = ranks or {}
        self._lineages = lineages or {}

    def taxid_for_name(self, name):
        return self._by_name.get(name.lower())

    def rank(self, taxid):
        return self._ranks.get(taxid)

    def name(self, taxid):
        for n, t in self._by_name.items():
            if t == taxid:
                return n.title()
        return None

    def lineage(self, taxid):
        return self._lineages.get(taxid, [])


class FakeGBIF:
    def __init__(self, mapping):
        self._mapping = mapping  # name -> (canonical, status)

    def match_name(self, name, strict=False):
        from biodbs.data.GBIF import GBIFMatch
        canonical, status = self._mapping.get(name, (None, None))
        return GBIFMatch(
            query=name, canonical_name=canonical, status=status,
            match_type="EXACT" if canonical else "NONE",
            is_synonym=(status == "SYNONYM"),
        )


def test_resolve_uses_taxdump_then_gbif_for_canonical():
    taxdump = FakeTaxdump({"escherichia coli": 562}, ranks={562: "species"})
    gbif = FakeGBIF({"Escherichia coli": ("Escherichia coli", "ACCEPTED")})
    mapper = TaxonomyMapper(taxdump=taxdump, gbif_fetcher=gbif)

    record = mapper.resolve("Escherichia coli")

    assert record.hub_taxid == 562
    assert record.rank == "species"
    assert record.canonical_name == "Escherichia coli"
    assert record.name_status == "accepted"
    assert record.match_type == "taxdump"


def test_resolve_falls_back_to_ncbi_when_not_in_taxdump():
    class FakeNCBI:
        def taxonomy_name_to_id(self, names):
            return {"Bacteroides fragilis": 817}

    mapper = TaxonomyMapper(taxdump=FakeTaxdump({}), ncbi_fetcher=FakeNCBI(), use_gbif=False)

    record = mapper.resolve("Bacteroides fragilis")

    assert record.hub_taxid == 817
    assert record.match_type == "ncbi"
    assert record.name_status == "unmatched"  # no GBIF -> status unknown


def test_resolve_unmatched_name():
    mapper = TaxonomyMapper(taxdump=FakeTaxdump({}), use_gbif=False)
    record = mapper.resolve("Not A Taxon")
    assert record.hub_taxid is None
    assert record.match_type == "none"
    assert record.name_status == "unmatched"


def test_map_names_returns_dataframe_with_schema():
    taxdump = FakeTaxdump({"escherichia coli": 562}, ranks={562: "species"})
    mapper = TaxonomyMapper(taxdump=taxdump, use_gbif=False)

    df = mapper.map_names(["Escherichia coli", "Not A Taxon"])

    assert list(df.columns) == MAPPING_COLUMNS
    assert len(df) == 2
    row = df[df["query"] == "Escherichia coli"].iloc[0]
    assert row["hub_taxid"] == 562


def test_map_lineage_extracts_species_and_uses_gtdb_crosswalk():
    mapper = TaxonomyMapper(
        taxdump=FakeTaxdump({}),
        gtdb_crosswalk={"Escherichia coli": 562},
        use_gbif=False,
    )

    df = mapper.map_lineage(
        ["d__Bacteria;p__Pseudomonadota;...;s__Escherichia coli"], source="gtdb"
    )

    row = df.iloc[0]
    assert row["hub_taxid"] == 562
    assert row["match_type"] == "gtdb-crosswalk"
    assert row["source"] == "gtdb"


def test_mapping_columns_match_taxonrecord_field_order():
    assert MAPPING_COLUMNS == [f.name for f in dataclasses.fields(TaxonRecord)]


def test_resolve_precedence_across_sources():
    taxdump = FakeTaxdump({"escherichia coli": 111}, ranks={111: "species"})

    class FakeNCBI:
        def taxonomy_name_to_id(self, names):
            return {n: 222 for n in names}

    mapper = TaxonomyMapper(
        taxdump=taxdump,
        ncbi_fetcher=FakeNCBI(),
        gtdb_crosswalk={"Escherichia coli": 333},
        use_gbif=False,
    )

    # source="gtdb": crosswalk (333) beats taxdump and ncbi
    g = mapper.resolve("Escherichia coli", source="gtdb")
    assert g.hub_taxid == 333 and g.match_type == "gtdb-crosswalk"

    # source="name": taxdump (111) beats ncbi (222); crosswalk not consulted for non-gtdb source
    n = mapper.resolve("Escherichia coli", source="name")
    assert n.hub_taxid == 111 and n.match_type == "taxdump"


def test_resolve_taxdump_only_marks_accepted_with_taxdump_canonical():
    taxdump = FakeTaxdump({"escherichia coli": 562}, ranks={562: "species"})
    mapper = TaxonomyMapper(taxdump=taxdump, use_gbif=False)

    r = mapper.resolve("Escherichia coli")

    assert r.match_type == "taxdump"
    assert r.name_status == "accepted"
    assert r.canonical_name == taxdump.name(562)


def test_map_lineage_sets_query_and_source_id_to_full_lineage():
    lineage = "d__Bacteria;p__Pseudomonadota;g__Escherichia;s__Escherichia coli"
    mapper = TaxonomyMapper(
        taxdump=FakeTaxdump({}),
        gtdb_crosswalk={"Escherichia coli": 562},
        use_gbif=False,
    )

    df = mapper.map_lineage([lineage], source="gtdb")

    row = df.iloc[0]
    assert row["query"] == lineage
    assert row["source_id"] == lineage
    assert row["hub_taxid"] == 562


def test_merge_on_hub_joins_two_mapping_tables():
    left = pd.DataFrame({"query": ["a"], "hub_taxid": [562], "source": ["silva"]})
    right = pd.DataFrame({"query": ["b"], "hub_taxid": [562], "source": ["gtdb"]})

    merged = merge_on_hub(left, right, suffixes=("_silva", "_gtdb"))

    assert len(merged) == 1
    assert merged.iloc[0]["hub_taxid"] == 562
    assert merged.iloc[0]["query_silva"] == "a"
    assert merged.iloc[0]["query_gtdb"] == "b"


@pytest.mark.parametrize("dtype", ["object", "float64", "Int64"])
@pytest.mark.parametrize("how", ["inner", "left", "right", "outer"])
def test_merge_on_hub_never_matches_missing_ids(dtype, how):
    missing = float("nan") if dtype == "float64" else pd.NA
    left = pd.DataFrame({
        "query": ["l562", "l817", "lu1", "lu2"],
        "hub_taxid": pd.Series([562, 817, missing, missing], dtype=dtype),
    })
    right = pd.DataFrame({
        "query": ["r562", "r9606", "ru1", "ru2"],
        "hub_taxid": pd.Series([562, 9606, missing, missing], dtype=dtype),
    })
    original_left, original_right = left.copy(), right.copy()

    result = merge_on_hub(left, right, how=how, suffixes=("_left", "_right"))

    pairs = {
        (None if pd.isna(a) else a, None if pd.isna(b) else b)
        for a, b in zip(result.query_left, result.query_right)
    }
    expected = {("l562", "r562")}
    if how in ("left", "outer"):
        expected |= {("l817", None), ("lu1", None), ("lu2", None)}
    if how in ("right", "outer"):
        expected |= {(None, "r9606"), (None, "ru1"), (None, "ru2")}
    assert pairs == expected
    assert len(result) == len(expected)
    assert str(result.hub_taxid.dtype) == dtype
    pd.testing.assert_frame_equal(left, original_left)
    pd.testing.assert_frame_equal(right, original_right)


@pytest.mark.parametrize("how", ["inner", "left", "right", "outer"])
@pytest.mark.parametrize("left_names,right_names", [
    ([], []), ([], ["unknown-r"]), (["unknown-l"], []),
    (["unknown-l"], ["unknown-r"]),
])
def test_merge_on_hub_empty_and_unresolved_tables(how, left_names, right_names):
    mapper = TaxonomyMapper(use_gbif=False)
    result = merge_on_hub(mapper.map_names(left_names), mapper.map_names(right_names), how=how)
    expected = (len(left_names) if how in ("left", "outer") else 0)
    expected += len(right_names) if how in ("right", "outer") else 0
    assert len(result) == expected
    assert result.hub_taxid.isna().all()


@pytest.mark.parametrize("name,status", [
    ("Escherichia coli", "accepted"),
    ("  ESCHERICHIA COLI  ", "accepted"),
    ("Bacillus coli", "synonym"),
    ("  BACILLUS COLI  ", "synonym"),
])
def test_offline_name_status_uses_scientific_name(name, status):
    taxdump = load_taxdump(Path(__file__).parent / "fixtures")
    record = TaxonomyMapper(taxdump=taxdump, use_gbif=False).resolve(name)
    assert record.hub_taxid == 562
    assert record.canonical_name == "Escherichia coli"
    assert record.name_status == status


def test_gbif_status_takes_precedence_over_offline_status():
    taxdump = load_taxdump(Path(__file__).parent / "fixtures")
    gbif = FakeGBIF({"Bacillus coli": ("GBIF accepted name", "ACCEPTED")})
    record = TaxonomyMapper(taxdump=taxdump, gbif_fetcher=gbif).resolve("Bacillus coli")
    assert record.canonical_name == "GBIF accepted name"
    assert record.name_status == "accepted"
