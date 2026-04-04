"""Tests for biodbs._funcs.analysis.gmt — load_gmt, save_gmt, fetch_gmt.

All tests are pure unit tests with no real network access.
"""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biodbs._funcs.analysis.gmt import load_gmt, save_gmt, fetch_gmt, _fetch_enrichr_gmt
from biodbs._funcs.analysis.ora import Pathway, ora


# =============================================================================
# Helpers
# =============================================================================


def _make_gmt_text(*rows):
    """Build a raw GMT string from (id, name, *genes) tuples."""
    return "\n".join("\t".join(row) for row in rows) + "\n"


def _write_gmt(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


# =============================================================================
# load_gmt
# =============================================================================


class TestLoadGmt:
    def test_basic_load(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            _make_gmt_text(
                ("PATHWAY_A", "Pathway A description", "TP53", "BRCA1", "BRCA2"),
                ("PATHWAY_B", "Pathway B description", "MYC", "EGFR"),
            ),
        )
        result = load_gmt(gmt_file)
        assert len(result) == 2
        assert "PATHWAY_A" in result
        assert "PATHWAY_B" in result

    def test_pathway_fields(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            _make_gmt_text(("hsa04110", "Cell cycle", "CDK1", "CDK2", "TP53")),
        )
        result = load_gmt(gmt_file, database="KEGG", species="Homo sapiens")
        p = result["hsa04110"]
        assert isinstance(p, Pathway)
        assert p.id == "hsa04110"
        assert p.name == "Cell cycle"
        assert p.genes == frozenset({"CDK1", "CDK2", "TP53"})
        assert p.database == "KEGG"
        assert p.species == "Homo sapiens"

    def test_na_description_falls_back_to_id(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            _make_gmt_text(("SET1", "na", "G1", "G2")),
        )
        result = load_gmt(gmt_file)
        assert result["SET1"].name == "SET1"

    def test_empty_description_falls_back_to_id(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            "SET1\t\tG1\tG2\n",
        )
        result = load_gmt(gmt_file)
        assert result["SET1"].name == "SET1"

    def test_skips_empty_lines(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            "\n".join([
                "PATHWAY_A\tDesc A\tG1\tG2",
                "",
                "PATHWAY_B\tDesc B\tG3\tG4",
                "",
            ]),
        )
        result = load_gmt(gmt_file)
        assert len(result) == 2

    def test_skips_lines_with_fewer_than_3_columns(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            "PATHWAY_A\tDesc\n"        # only 2 columns — no genes
            "PATHWAY_B\tDesc\tG1\n",   # valid
        )
        result = load_gmt(gmt_file)
        assert len(result) == 1
        assert "PATHWAY_B" in result

    def test_strips_whitespace_from_genes(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            "SET1\tDesc\t  TP53  \t  BRCA1  \n",
        )
        result = load_gmt(gmt_file)
        assert "TP53" in result["SET1"].genes
        assert "BRCA1" in result["SET1"].genes
        assert "  TP53  " not in result["SET1"].genes

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_gmt(tmp_path / "nonexistent.gmt")

    def test_accepts_string_path(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "test.gmt",
            _make_gmt_text(("S1", "desc", "G1", "G2")),
        )
        result = load_gmt(str(gmt_file))
        assert "S1" in result

    def test_large_file(self, tmp_path):
        rows = [f"PATH{i}\tDescription {i}\t" + "\t".join(f"G{j}" for j in range(20))
                for i in range(500)]
        (tmp_path / "big.gmt").write_text("\n".join(rows), encoding="utf-8")
        result = load_gmt(tmp_path / "big.gmt")
        assert len(result) == 500


# =============================================================================
# save_gmt
# =============================================================================


class TestSaveGmt:
    def test_roundtrip_pathway_objects(self, tmp_path):
        original = {
            "P1": Pathway(id="P1", name="Pathway One",
                          genes=frozenset({"A", "B", "C"}), database="test"),
            "P2": Pathway(id="P2", name="Pathway Two",
                          genes=frozenset({"D", "E"}), database="test"),
        }
        out = tmp_path / "out.gmt"
        save_gmt(original, out)
        reloaded = load_gmt(out)

        assert set(reloaded.keys()) == {"P1", "P2"}
        assert reloaded["P1"].genes == frozenset({"A", "B", "C"})
        assert reloaded["P1"].name == "Pathway One"

    def test_roundtrip_tuple_format(self, tmp_path):
        gene_sets = {
            "S1": ("Set One", {"X", "Y", "Z"}),
        }
        out = tmp_path / "out.gmt"
        save_gmt(gene_sets, out)
        reloaded = load_gmt(out)
        assert reloaded["S1"].genes == frozenset({"X", "Y", "Z"})
        assert reloaded["S1"].name == "Set One"

    def test_returns_resolved_path(self, tmp_path):
        gene_sets = {"S1": Pathway(id="S1", name="S", genes=frozenset({"G1"}), database="t")}
        result = save_gmt(gene_sets, tmp_path / "out.gmt")
        assert isinstance(result, Path)
        assert result.exists()

    def test_creates_parent_directories(self, tmp_path):
        out = tmp_path / "deep" / "nested" / "out.gmt"
        gene_sets = {"S1": Pathway(id="S1", name="S", genes=frozenset({"G1"}), database="t")}
        save_gmt(gene_sets, out)
        assert out.exists()

    def test_genes_are_sorted(self, tmp_path):
        gene_sets = {
            "S1": Pathway(id="S1", name="S",
                          genes=frozenset({"ZZZ", "AAA", "MMM"}), database="t"),
        }
        out = tmp_path / "out.gmt"
        save_gmt(gene_sets, out)
        line = out.read_text().strip()
        parts = line.split("\t")
        genes = parts[2:]
        assert genes == sorted(genes)

    def test_pathway_name_fallback_to_id(self, tmp_path):
        gene_sets = {
            "MY_ID": Pathway(id="MY_ID", name="",
                             genes=frozenset({"G1"}), database="t"),
        }
        out = tmp_path / "out.gmt"
        save_gmt(gene_sets, out)
        line = out.read_text().strip()
        parts = line.split("\t")
        assert parts[1] == "MY_ID"

    def test_empty_gene_sets(self, tmp_path):
        out = tmp_path / "empty.gmt"
        save_gmt({}, out)
        assert out.read_text() == ""


# =============================================================================
# ora() with GMT path
# =============================================================================


class TestOraWithGmtPath:
    def test_accepts_path_object(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "sets.gmt",
            _make_gmt_text(
                ("P1", "Pathway 1", "G1", "G2", "G3", "G4", "G5"),
                ("P2", "Pathway 2", "G6", "G7", "G8"),
            ),
        )
        result = ora(["G1", "G2", "G3"], gmt_file, min_overlap=1)
        assert len(result) > 0

    def test_accepts_string_path(self, tmp_path):
        gmt_file = _write_gmt(
            tmp_path / "sets.gmt",
            _make_gmt_text(("P1", "Pathway 1", "G1", "G2", "G3")),
        )
        result = ora(["G1", "G2", "G3"], str(gmt_file), min_overlap=1)
        assert len(result) > 0

    def test_dict_input_still_works(self, tmp_path):
        gene_sets = {
            "P1": Pathway(id="P1", name="Pathway 1",
                          genes=frozenset({"G1", "G2", "G3"}), database="test"),
        }
        result = ora(["G1", "G2", "G3"], gene_sets, min_overlap=1)
        assert len(result) > 0

    def test_missing_gmt_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ora(["G1"], tmp_path / "missing.gmt", min_overlap=1)


# =============================================================================
# _fetch_enrichr_gmt (mocked HTTP)
# =============================================================================


class TestFetchEnrichrGmt:
    GMT_TEXT = textwrap.dedent("""\
        HALLMARK_APOPTOSIS\tna\tTP53\tBAX\tBCL2\tCASP3
        HALLMARK_CELL_CYCLE\tCell Cycle Description\tCDK1\tCDK2\tCCNB1
    """)

    def _mock_response(self, text, status_code=200):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = text
        return resp

    @patch("biodbs.fetch._rate_limit.request_with_retry")
    @patch("biodbs.exceptions.raise_for_status")
    def test_returns_pathway_dict(self, mock_raise, mock_request):
        mock_request.return_value = self._mock_response(self.GMT_TEXT)
        result = _fetch_enrichr_gmt("MSigDB_Hallmark_2020")
        assert len(result) == 2
        assert "HALLMARK_APOPTOSIS" in result
        assert "HALLMARK_CELL_CYCLE" in result

    @patch("biodbs.fetch._rate_limit.request_with_retry")
    @patch("biodbs.exceptions.raise_for_status")
    def test_pathway_fields(self, mock_raise, mock_request):
        mock_request.return_value = self._mock_response(self.GMT_TEXT)
        result = _fetch_enrichr_gmt("MSigDB_Hallmark_2020")

        apoptosis = result["HALLMARK_APOPTOSIS"]
        assert isinstance(apoptosis, Pathway)
        assert apoptosis.id == "HALLMARK_APOPTOSIS"
        # "na" description → falls back to term name
        assert apoptosis.name == "HALLMARK_APOPTOSIS"
        assert "TP53" in apoptosis.genes
        assert apoptosis.database == "EnrichR:MSigDB_Hallmark_2020"

        cell_cycle = result["HALLMARK_CELL_CYCLE"]
        assert cell_cycle.name == "Cell Cycle Description"

    @patch("biodbs.fetch._rate_limit.request_with_retry")
    @patch("biodbs.exceptions.raise_for_status")
    def test_skips_malformed_lines(self, mock_raise, mock_request):
        text = "VALID\tDesc\tG1\tG2\n" "INVALID\n"
        mock_request.return_value = self._mock_response(text)
        result = _fetch_enrichr_gmt("TestLib")
        assert len(result) == 1
        assert "VALID" in result

    @patch("biodbs.fetch._rate_limit.request_with_retry")
    @patch("biodbs.exceptions.raise_for_status")
    def test_empty_response(self, mock_raise, mock_request):
        mock_request.return_value = self._mock_response("")
        result = _fetch_enrichr_gmt("EmptyLib")
        assert result == {}


# =============================================================================
# fetch_gmt — dispatch and save_at
# =============================================================================


class TestFetchGmt:
    def _make_pathways(self, n=3):
        return {
            f"P{i}": Pathway(
                id=f"P{i}", name=f"Pathway {i}",
                genes=frozenset({f"G{j}" for j in range(5)}),
                database="test",
            )
            for i in range(n)
        }

    def test_unknown_database_raises(self):
        with pytest.raises(ValueError, match="Unknown database"):
            fetch_gmt("hsa", database="notadb")

    @patch("biodbs._funcs.analysis.gmt._fetch_enrichr_gmt")
    def test_enrichr_dispatch(self, mock_fetch):
        mock_fetch.return_value = self._make_pathways()
        result = fetch_gmt("KEGG_2021_Human", database="enrichr")
        mock_fetch.assert_called_once_with("KEGG_2021_Human")
        assert len(result) == 3

    @patch("biodbs._funcs.analysis.gmt._fetch_enrichr_gmt")
    def test_msigdb_alias_dispatches_to_enrichr(self, mock_fetch):
        mock_fetch.return_value = self._make_pathways()
        fetch_gmt("MSigDB_Hallmark_2020", database="msigdb")
        mock_fetch.assert_called_once_with("MSigDB_Hallmark_2020")

    @patch("biodbs._funcs.analysis.gmt._fetch_enrichr_gmt")
    def test_save_at_writes_file(self, mock_fetch, tmp_path):
        mock_fetch.return_value = self._make_pathways()
        out = tmp_path / "out.gmt"
        fetch_gmt("TestLib", database="enrichr", save_at=str(out))
        assert out.exists()
        lines = out.read_text().splitlines()
        assert len(lines) == 3

    @patch("biodbs._funcs.analysis.gmt._fetch_enrichr_gmt")
    def test_save_at_name_template(self, mock_fetch, tmp_path):
        mock_fetch.return_value = self._make_pathways()
        template = str(tmp_path / "{name}.gmt")
        fetch_gmt("MyLib", database="enrichr", save_at=template)
        assert (tmp_path / "MyLib.gmt").exists()

    @patch("biodbs._funcs.analysis.gmt._fetch_enrichr_gmt")
    def test_save_at_none_does_not_write(self, mock_fetch, tmp_path):
        mock_fetch.return_value = self._make_pathways()
        fetch_gmt("TestLib", database="enrichr", save_at=None)
        assert not any(tmp_path.iterdir())

    @patch("biodbs._funcs.analysis.gmt._fetch_enrichr_gmt")
    def test_database_case_insensitive(self, mock_fetch):
        mock_fetch.return_value = {}
        fetch_gmt("Lib", database="ENRICHR")
        mock_fetch.assert_called_once()

    def test_database_aliases_coverage(self):
        """All expected aliases are present in _DB_ALIASES and map to the right db."""
        from biodbs._funcs.analysis.gmt import _DB_ALIASES

        assert _DB_ALIASES["gene ontology"] == "go"
        assert _DB_ALIASES["go"] == "go"
        assert _DB_ALIASES["kegg"] == "kegg"
        assert _DB_ALIASES["reactome"] == "reactome"
        assert _DB_ALIASES["enrichr"] == "enrichr"
        assert _DB_ALIASES["msigdb"] == "enrichr"
