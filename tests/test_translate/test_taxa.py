"""Offline checks for the translation facade over taxonomy mapping."""

from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

import biodbs
from biodbs import translate
from biodbs._funcs import translate as internal_translate
from biodbs.taxonomy import MAPPING_COLUMNS, TaxonomyMapper, load_taxdump
from biodbs.translate import translate_taxon_names


def test_taxonomic_translation_exports_share_one_implementation():
    for namespace in (biodbs, translate, internal_translate):
        assert namespace.translate_taxon_names is translate_taxon_names
        assert "translate_taxon_names" in namespace.__all__


def test_taxonomic_translation_matches_existing_mapper():
    taxdump = load_taxdump(Path(__file__).parents[1] / "test_taxonomy" / "fixtures")
    mapper = TaxonomyMapper(taxdump=taxdump)
    names = ["Escherichia coli", "Bacillus coli", "Not A Taxon", "Escherichia coli"]

    result = translate_taxon_names(iter(names), mapper=mapper, source="silva")

    pd.testing.assert_frame_equal(result, mapper.map_names(names, source="silva"))
    assert list(result.columns) == MAPPING_COLUMNS
    assert result["query"].tolist() == names
    assert result["hub_taxid"].iloc[[0, 1, 3]].tolist() == [562, 562, 562]
    assert pd.isna(result["hub_taxid"].iloc[2])
    assert result["canonical_name"].iloc[1] == "Escherichia coli"
    assert result["name_status"].tolist() == ["accepted", "synonym", "unmatched", "accepted"]


def test_taxonomic_translation_empty_input_keeps_mapping_schema():
    result = translate_taxon_names([], mapper=TaxonomyMapper())
    assert result.empty
    assert list(result.columns) == MAPPING_COLUMNS


def test_taxonomic_translation_uses_configured_fetcher():
    ncbi = Mock()
    ncbi.taxonomy_name_to_id.return_value = {"Bacteroides fragilis": 817}
    result = translate_taxon_names(
        ["Bacteroides fragilis"], mapper=TaxonomyMapper(ncbi_fetcher=ncbi)
    )
    assert result.loc[0, "hub_taxid"] == 817
    assert result.loc[0, "match_type"] == "ncbi"
    ncbi.taxonomy_name_to_id.assert_called_once_with(["Bacteroides fragilis"])


def test_taxonomic_translation_passes_gtdb_source_to_mapper():
    mapper = TaxonomyMapper(gtdb_crosswalk={"Escherichia coli": 562})
    result = translate_taxon_names(["Escherichia coli"], mapper=mapper, source="gtdb")
    assert result.loc[0, "hub_taxid"] == 562
    assert result.loc[0, "source"] == "gtdb"
    assert result.loc[0, "match_type"] == "gtdb-crosswalk"


def test_taxonomic_translation_propagates_fetcher_errors():
    ncbi = Mock()
    ncbi.taxonomy_name_to_id.side_effect = TimeoutError("NCBI unavailable")
    with pytest.raises(TimeoutError, match="NCBI unavailable"):
        translate_taxon_names(["Escherichia coli"], mapper=TaxonomyMapper(ncbi_fetcher=ncbi))


@pytest.mark.parametrize("names", ["Escherichia coli", b"Escherichia coli"])
def test_taxonomic_translation_rejects_scalar_strings(names):
    mapper = Mock(spec=TaxonomyMapper)
    with pytest.raises(TypeError, match="not a single string"):
        translate_taxon_names(names, mapper=mapper)
    mapper.map_names.assert_not_called()
