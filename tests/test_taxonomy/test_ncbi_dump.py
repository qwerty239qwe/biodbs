from pathlib import Path

from biodbs._funcs.taxonomy.ncbi_dump import load_taxdump

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_taxdump_names_ranks_parents():
    tax = load_taxdump(FIXTURES)
    assert tax.name(562) == "Escherichia coli"
    assert tax.rank(562) == "species"
    assert tax.parent(562) == 561
    assert tax.name(2) == "Bacteria"


def test_taxid_for_name_scientific_and_synonym_case_insensitive():
    tax = load_taxdump(FIXTURES)
    assert tax.taxid_for_name("Escherichia coli") == 562
    assert tax.taxid_for_name("escherichia coli") == 562
    assert tax.taxid_for_name("Bacillus coli") == 562  # synonym
    assert tax.taxid_for_name("no such organism") is None


def test_merged_ids_resolve():
    tax = load_taxdump(FIXTURES)
    assert tax.resolve(999999) == 562
    assert tax.resolve(562) == 562


def test_lineage_root_to_leaf():
    tax = load_taxdump(FIXTURES)
    lineage = tax.lineage(562)
    assert lineage[0] == ("no rank", "root")
    assert lineage[-1] == ("species", "Escherichia coli")
    names = [name for _, name in lineage]
    assert "Bacteria" in names and "Escherichia" in names
