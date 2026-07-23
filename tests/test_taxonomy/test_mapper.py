import dataclasses

import pandas as pd

from biodbs.taxonomy import TaxonomyMapper, TaxonRecord, merge_on_hub, MAPPING_COLUMNS


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
