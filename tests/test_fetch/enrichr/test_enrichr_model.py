"""Tests for biodbs.data.EnrichR._data_model module."""

import pytest
from pydantic import ValidationError

from biodbs.data.EnrichR._data_model import (
    EnrichRBase,
    EnrichRCategory,
    EnrichREndpoint,
    LibraryStatistics,
    CategoryInfo,
    EnrichRLibraryModel,
    EnrichRAddListModel,
    EnrichREnrichModel,
    EnrichRBackgroundModel,
    EnrichmentTerm,
    EnrichmentResult,
)


# =============================================================================
# Tests: Enums
# =============================================================================


class TestEnrichRBase:
    def test_human_url(self):
        assert EnrichRBase.HUMAN.value == "https://maayanlab.cloud/Enrichr"

    def test_mouse_same_as_human(self):
        assert EnrichRBase.MOUSE.value == EnrichRBase.HUMAN.value

    def test_fly_url(self):
        assert EnrichRBase.FLY.value == "https://maayanlab.cloud/FlyEnrichr"

    def test_yeast_url(self):
        assert EnrichRBase.YEAST.value == "https://maayanlab.cloud/YeastEnrichr"

    def test_worm_url(self):
        assert EnrichRBase.WORM.value == "https://maayanlab.cloud/WormEnrichr"

    def test_fish_url(self):
        assert EnrichRBase.FISH.value == "https://maayanlab.cloud/FishEnrichr"

    def test_speed_url(self):
        assert EnrichRBase.SPEED.value == "https://maayanlab.cloud/speedrichr"

    def test_is_str_enum(self):
        assert isinstance(EnrichRBase.HUMAN, str)
        assert EnrichRBase.HUMAN == "https://maayanlab.cloud/Enrichr"


class TestEnrichRCategory:
    def test_all_categories(self):
        assert EnrichRCategory.TRANSCRIPTION == 1
        assert EnrichRCategory.PATHWAYS == 2
        assert EnrichRCategory.ONTOLOGIES == 3
        assert EnrichRCategory.DISEASES_DRUGS == 4
        assert EnrichRCategory.CELL_TYPES == 5
        assert EnrichRCategory.MISC == 6
        assert EnrichRCategory.LEGACY == 7
        assert EnrichRCategory.CROWD == 8

    def test_is_int_enum(self):
        assert isinstance(EnrichRCategory.TRANSCRIPTION, int)


class TestEnrichREndpoint:
    def test_standard_endpoints(self):
        assert EnrichREndpoint.ADD_LIST == "addList"
        assert EnrichREndpoint.ENRICH == "enrich"
        assert EnrichREndpoint.EXPORT == "export"
        assert EnrichREndpoint.VIEW == "view"
        assert EnrichREndpoint.DATASET_STATISTICS == "datasetStatistics"
        assert EnrichREndpoint.GEN_MAP == "genemap"

    def test_speed_endpoints(self):
        assert EnrichREndpoint.SPEED_ADD_LIST == "api/addList"
        assert EnrichREndpoint.SPEED_ADD_BACKGROUND == "api/addbackground"
        assert EnrichREndpoint.SPEED_BACKGROUND_ENRICH == "api/backgroundenrich"

    def test_is_str_enum(self):
        assert isinstance(EnrichREndpoint.ADD_LIST, str)


# =============================================================================
# Tests: Simple Pydantic Models
# =============================================================================


class TestLibraryStatistics:
    def test_basic_creation(self):
        stats = LibraryStatistics(
            libraryName="KEGG_2021_Human",
            numTerms=320,
            geneCoverage=8000,
            genesPerTerm=25.0,
        )
        assert stats.libraryName == "KEGG_2021_Human"
        assert stats.numTerms == 320
        assert stats.geneCoverage == 8000
        assert stats.genesPerTerm == 25.0

    def test_defaults(self):
        stats = LibraryStatistics(
            libraryName="Test",
            numTerms=10,
            geneCoverage=100,
            genesPerTerm=5.0,
        )
        assert stats.link == ""
        assert stats.categoryId is None
        assert stats.appyter is None

    def test_all_fields(self):
        stats = LibraryStatistics(
            libraryName="GO_BP",
            numTerms=5000,
            geneCoverage=15000,
            genesPerTerm=30.0,
            link="http://geneontology.org",
            categoryId=3,
            appyter="some_appyter",
        )
        assert stats.link == "http://geneontology.org"
        assert stats.categoryId == 3
        assert stats.appyter == "some_appyter"


class TestCategoryInfo:
    def test_basic_creation(self):
        info = CategoryInfo(name="Pathways", categoryId=2)
        assert info.name == "Pathways"
        assert info.categoryId == 2


# =============================================================================
# Tests: EnrichRLibraryModel
# =============================================================================


class TestEnrichRLibraryModel:
    def test_default_organism(self):
        model = EnrichRLibraryModel()
        assert model.organism == "human"

    @pytest.mark.parametrize("organism", ["human", "mouse", "fly", "yeast", "worm", "fish"])
    def test_valid_organisms(self, organism):
        model = EnrichRLibraryModel(organism=organism)
        assert model.organism == organism

    def test_invalid_organism_raises(self):
        with pytest.raises(ValidationError, match="Invalid organism"):
            EnrichRLibraryModel(organism="cat")

    def test_get_base_url_human(self):
        model = EnrichRLibraryModel(organism="human")
        assert model.get_base_url() == "https://maayanlab.cloud/Enrichr"

    def test_get_base_url_mouse(self):
        model = EnrichRLibraryModel(organism="mouse")
        assert model.get_base_url() == "https://maayanlab.cloud/Enrichr"

    def test_get_base_url_fly(self):
        model = EnrichRLibraryModel(organism="fly")
        assert model.get_base_url() == "https://maayanlab.cloud/FlyEnrichr"

    def test_get_base_url_yeast(self):
        model = EnrichRLibraryModel(organism="yeast")
        assert model.get_base_url() == "https://maayanlab.cloud/YeastEnrichr"

    def test_get_base_url_worm(self):
        model = EnrichRLibraryModel(organism="worm")
        assert model.get_base_url() == "https://maayanlab.cloud/WormEnrichr"

    def test_get_base_url_fish(self):
        model = EnrichRLibraryModel(organism="fish")
        assert model.get_base_url() == "https://maayanlab.cloud/FishEnrichr"


# =============================================================================
# Tests: EnrichRAddListModel
# =============================================================================


class TestEnrichRAddListModel:
    def test_basic_creation(self):
        model = EnrichRAddListModel(genes=["TP53", "BRCA1", "MDM2"])
        assert model.genes == ["TP53", "BRCA1", "MDM2"]
        assert model.description == "biodbs gene list"
        assert model.organism == "human"

    def test_custom_description(self):
        model = EnrichRAddListModel(genes=["TP53"], description="my custom list")
        assert model.description == "my custom list"

    def test_empty_genes_raises(self):
        with pytest.raises(ValidationError):
            EnrichRAddListModel(genes=[])

    def test_invalid_organism_raises(self):
        with pytest.raises(ValidationError, match="Invalid organism"):
            EnrichRAddListModel(genes=["TP53"], organism="dolphin")

    @pytest.mark.parametrize("organism", ["human", "mouse", "fly", "yeast", "worm", "fish"])
    def test_valid_organisms(self, organism):
        model = EnrichRAddListModel(genes=["TP53"], organism=organism)
        assert model.organism == organism

    def test_get_gene_string(self):
        model = EnrichRAddListModel(genes=["TP53", "BRCA1", "MDM2"])
        assert model.get_gene_string() == "TP53\nBRCA1\nMDM2"

    def test_get_gene_string_single_gene(self):
        model = EnrichRAddListModel(genes=["TP53"])
        assert model.get_gene_string() == "TP53"

    def test_get_base_url_human(self):
        model = EnrichRAddListModel(genes=["TP53"], organism="human")
        assert model.get_base_url() == "https://maayanlab.cloud/Enrichr"

    def test_get_base_url_fly(self):
        model = EnrichRAddListModel(genes=["gene1"], organism="fly")
        assert model.get_base_url() == "https://maayanlab.cloud/FlyEnrichr"

    def test_get_base_url_fish(self):
        model = EnrichRAddListModel(genes=["gene1"], organism="fish")
        assert model.get_base_url() == "https://maayanlab.cloud/FishEnrichr"


# =============================================================================
# Tests: EnrichREnrichModel
# =============================================================================


class TestEnrichREnrichModel:
    def test_basic_creation(self):
        model = EnrichREnrichModel(user_list_id=12345, gene_set_library="KEGG_2021_Human")
        assert model.user_list_id == 12345
        assert model.gene_set_library == "KEGG_2021_Human"
        assert model.organism == "human"

    def test_custom_organism(self):
        model = EnrichREnrichModel(
            user_list_id=99, gene_set_library="GO_BP", organism="fly"
        )
        assert model.organism == "fly"

    def test_get_base_url_human(self):
        model = EnrichREnrichModel(user_list_id=1, gene_set_library="lib")
        assert model.get_base_url() == "https://maayanlab.cloud/Enrichr"

    def test_get_base_url_yeast(self):
        model = EnrichREnrichModel(user_list_id=1, gene_set_library="lib", organism="yeast")
        assert model.get_base_url() == "https://maayanlab.cloud/YeastEnrichr"

    def test_get_base_url_worm(self):
        model = EnrichREnrichModel(user_list_id=1, gene_set_library="lib", organism="worm")
        assert model.get_base_url() == "https://maayanlab.cloud/WormEnrichr"


# =============================================================================
# Tests: EnrichRBackgroundModel
# =============================================================================


class TestEnrichRBackgroundModel:
    def test_basic_creation(self):
        model = EnrichRBackgroundModel(
            genes=["TP53", "BRCA1"],
            background=["TP53", "BRCA1", "MDM2", "CDK2"],
            gene_set_library="KEGG_2021_Human",
        )
        assert model.genes == ["TP53", "BRCA1"]
        assert model.background == ["TP53", "BRCA1", "MDM2", "CDK2"]
        assert model.gene_set_library == "KEGG_2021_Human"
        assert model.description == "biodbs gene list"

    def test_empty_genes_raises(self):
        with pytest.raises(ValidationError):
            EnrichRBackgroundModel(
                genes=[],
                background=["TP53"],
                gene_set_library="lib",
            )

    def test_empty_background_raises(self):
        with pytest.raises(ValidationError):
            EnrichRBackgroundModel(
                genes=["TP53"],
                background=[],
                gene_set_library="lib",
            )

    def test_get_gene_string(self):
        model = EnrichRBackgroundModel(
            genes=["TP53", "BRCA1"],
            background=["BG1"],
            gene_set_library="lib",
        )
        assert model.get_gene_string() == "TP53\nBRCA1"

    def test_get_background_string(self):
        model = EnrichRBackgroundModel(
            genes=["TP53"],
            background=["BG1", "BG2", "BG3"],
            gene_set_library="lib",
        )
        assert model.get_background_string() == "BG1\nBG2\nBG3"

    def test_custom_description(self):
        model = EnrichRBackgroundModel(
            genes=["TP53"],
            background=["BG1"],
            gene_set_library="lib",
            description="custom desc",
        )
        assert model.description == "custom desc"


# =============================================================================
# Tests: EnrichmentTerm
# =============================================================================


class TestEnrichmentTerm:
    def test_from_api_row_old_format(self):
        """Old format: [Rank, Term, P-val, Z-score, Combined, Genes, AdjP, OldP, OldAdjP]."""
        row = [1, "KEGG Pathway A", 0.001, -2.5, 15.0, ["GENE1", "GENE2"], 0.005, 0.002, 0.008]
        term = EnrichmentTerm.from_api_row(row)
        assert term.rank == 1
        assert term.term_name == "KEGG Pathway A"
        assert term.p_value == 0.001
        assert term.z_score == -2.5
        assert term.combined_score == 15.0
        assert term.overlapping_genes == ["GENE1", "GENE2"]
        assert term.adjusted_p_value == 0.005
        assert term.old_p_value == 0.002
        assert term.old_adjusted_p_value == 0.008

    def test_from_api_row_old_format_with_extra_cols(self):
        """Old format with more than 9 columns should still work."""
        row = [2, "Pathway B", 0.01, -1.0, 5.0, ["G1"], 0.05, 0.01, 0.06, "extra"]
        term = EnrichmentTerm.from_api_row(row)
        assert term.rank == 2
        assert term.term_name == "Pathway B"

    def test_from_api_row_newer_format(self):
        """Newer format: [Rank, Term, P-val, OddsRatio, Combined, Genes, AdjP]."""
        row = [1, "GO Term X", 0.005, 3.2, 20.0, ["ABC", "DEF", "GHI"], 0.02]
        term = EnrichmentTerm.from_api_row(row)
        assert term.rank == 1
        assert term.term_name == "GO Term X"
        assert term.p_value == 0.005
        assert term.odds_ratio == 3.2
        assert term.combined_score == 20.0
        assert term.overlapping_genes == ["ABC", "DEF", "GHI"]
        assert term.adjusted_p_value == 0.02
        assert term.z_score == 0.0  # Not provided in newer format

    def test_from_api_row_newer_format_8_cols(self):
        """8 columns is still < 9 so should use the newer format branch."""
        row = [3, "Term Z", 0.02, 1.5, 8.0, ["X1"], 0.1, "extra"]
        term = EnrichmentTerm.from_api_row(row)
        assert term.rank == 3
        assert term.term_name == "Term Z"
        assert term.odds_ratio == 1.5

    def test_from_api_row_too_few_columns(self):
        """Rows with fewer than 7 columns should raise ValueError."""
        row = [1, "Short", 0.01, -1.0, 5.0, ["G1"]]
        with pytest.raises(ValueError, match="Unexpected row format"):
            EnrichmentTerm.from_api_row(row)

    def test_from_api_row_very_short(self):
        row = [1, "Only two"]
        with pytest.raises(ValueError, match="Unexpected row format"):
            EnrichmentTerm.from_api_row(row)

    def test_from_api_row_empty_row(self):
        with pytest.raises(ValueError, match="Unexpected row format"):
            EnrichmentTerm.from_api_row([])

    def test_from_api_row_rank_fallback(self):
        """When row[0] is falsy, the rank parameter should be used."""
        row = [0, "Term", 0.01, -1.0, 5.0, ["G1"], 0.05, 0.01, 0.06]
        # row[0] is 0, which is falsy, so rank param (42) should be used
        term = EnrichmentTerm.from_api_row(row, rank=42)
        assert term.rank == 42

    def test_from_api_row_rank_from_row(self):
        """When row[0] is truthy, it should be used as rank."""
        row = [5, "Term", 0.01, -1.0, 5.0, ["G1"], 0.05, 0.01, 0.06]
        term = EnrichmentTerm.from_api_row(row, rank=99)
        assert term.rank == 5

    def test_from_api_row_falsy_values_old_format(self):
        """Test that falsy p-value, z-score, etc. get default values."""
        row = [None, "Term", None, None, None, None, None, None, None]
        term = EnrichmentTerm.from_api_row(row, rank=1)
        assert term.rank == 1
        assert term.p_value == 1.0
        assert term.z_score == 0.0
        assert term.combined_score == 0.0
        assert term.overlapping_genes == []
        assert term.adjusted_p_value == 1.0
        assert term.old_p_value is None
        assert term.old_adjusted_p_value is None

    def test_from_api_row_falsy_values_newer_format(self):
        """Test newer format with falsy values."""
        row = [None, "Term", None, None, None, None, None]
        term = EnrichmentTerm.from_api_row(row, rank=3)
        assert term.rank == 3
        assert term.p_value == 1.0
        assert term.odds_ratio is None
        assert term.combined_score == 0.0
        assert term.adjusted_p_value == 1.0

    def test_parse_genes_with_list(self):
        genes = EnrichmentTerm._parse_genes(["GENE1", "GENE2", "GENE3"])
        assert genes == ["GENE1", "GENE2", "GENE3"]

    def test_parse_genes_with_string(self):
        genes = EnrichmentTerm._parse_genes("GENE1;GENE2;GENE3")
        assert genes == ["GENE1", "GENE2", "GENE3"]

    def test_parse_genes_with_single_gene_string(self):
        genes = EnrichmentTerm._parse_genes("TP53")
        assert genes == ["TP53"]

    def test_parse_genes_with_none(self):
        genes = EnrichmentTerm._parse_genes(None)
        assert genes == []

    def test_parse_genes_with_empty_string(self):
        genes = EnrichmentTerm._parse_genes("")
        assert genes == []

    def test_parse_genes_with_empty_list(self):
        genes = EnrichmentTerm._parse_genes([])
        assert genes == []

    def test_parse_genes_with_unsupported_type(self):
        genes = EnrichmentTerm._parse_genes(12345)
        assert genes == []

    def test_direct_construction(self):
        term = EnrichmentTerm(
            rank=1,
            term_name="Test Term",
            p_value=0.01,
            z_score=-2.0,
            combined_score=10.0,
            overlapping_genes=["A", "B"],
            adjusted_p_value=0.05,
        )
        assert term.rank == 1
        assert term.term_name == "Test Term"
        assert term.old_p_value is None
        assert term.old_adjusted_p_value is None
        assert term.odds_ratio is None


# =============================================================================
# Tests: EnrichmentResult
# =============================================================================


class TestEnrichmentResult:
    @pytest.fixture
    def sample_terms(self):
        return [
            EnrichmentTerm(
                rank=1,
                term_name="Highly Significant",
                p_value=0.001,
                z_score=-3.0,
                combined_score=25.0,
                overlapping_genes=["TP53", "BRCA1"],
                adjusted_p_value=0.005,
            ),
            EnrichmentTerm(
                rank=2,
                term_name="Moderately Significant",
                p_value=0.01,
                z_score=-2.0,
                combined_score=15.0,
                overlapping_genes=["MDM2"],
                adjusted_p_value=0.04,
            ),
            EnrichmentTerm(
                rank=3,
                term_name="Borderline",
                p_value=0.04,
                z_score=-1.0,
                combined_score=5.0,
                overlapping_genes=["CDK2"],
                adjusted_p_value=0.08,
            ),
            EnrichmentTerm(
                rank=4,
                term_name="Not Significant",
                p_value=0.2,
                z_score=-0.5,
                combined_score=1.0,
                overlapping_genes=[],
                adjusted_p_value=0.5,
            ),
        ]

    @pytest.fixture
    def result(self, sample_terms):
        return EnrichmentResult(library_name="KEGG_2021_Human", terms=sample_terms)

    def test_basic_creation(self, result):
        assert result.library_name == "KEGG_2021_Human"
        assert len(result.terms) == 4

    def test_empty_terms(self):
        result = EnrichmentResult(library_name="Empty", terms=[])
        assert len(result.terms) == 0

    def test_default_terms(self):
        result = EnrichmentResult(library_name="NoTerms")
        assert result.terms == []

    def test_significant_terms_adjusted_default(self, result):
        """Default: filters by adjusted_p_value < 0.05."""
        sig = result.significant_terms()
        assert len(sig) == 2
        names = [t.term_name for t in sig]
        assert "Highly Significant" in names
        assert "Moderately Significant" in names
        assert "Borderline" not in names
        assert "Not Significant" not in names

    def test_significant_terms_custom_threshold(self, result):
        """Custom threshold for adjusted p-value."""
        sig = result.significant_terms(p_threshold=0.1)
        assert len(sig) == 3
        names = [t.term_name for t in sig]
        assert "Borderline" in names

    def test_significant_terms_strict_threshold(self, result):
        sig = result.significant_terms(p_threshold=0.001)
        assert len(sig) == 0

    def test_significant_terms_raw_pvalue(self, result):
        """use_adjusted=False: filters by raw p_value < threshold."""
        sig = result.significant_terms(use_adjusted=False)
        assert len(sig) == 3  # p_value < 0.05: 0.001, 0.01, 0.04
        names = [t.term_name for t in sig]
        assert "Highly Significant" in names
        assert "Moderately Significant" in names
        assert "Borderline" in names
        assert "Not Significant" not in names

    def test_significant_terms_raw_pvalue_strict(self, result):
        sig = result.significant_terms(p_threshold=0.005, use_adjusted=False)
        assert len(sig) == 1
        assert sig[0].term_name == "Highly Significant"

    def test_significant_terms_empty_result(self):
        result = EnrichmentResult(library_name="Empty", terms=[])
        sig = result.significant_terms()
        assert sig == []

    def test_top_terms_default(self, result):
        """top_terms returns sorted by combined_score descending."""
        top = result.top_terms()
        assert len(top) == 4  # default n=10, but only 4 terms
        assert top[0].combined_score == 25.0
        assert top[1].combined_score == 15.0
        assert top[2].combined_score == 5.0
        assert top[3].combined_score == 1.0

    def test_top_terms_limited(self, result):
        top = result.top_terms(n=2)
        assert len(top) == 2
        assert top[0].term_name == "Highly Significant"
        assert top[1].term_name == "Moderately Significant"

    def test_top_terms_more_than_available(self, result):
        top = result.top_terms(n=100)
        assert len(top) == 4

    def test_top_terms_one(self, result):
        top = result.top_terms(n=1)
        assert len(top) == 1
        assert top[0].combined_score == 25.0

    def test_top_terms_empty_result(self):
        result = EnrichmentResult(library_name="Empty", terms=[])
        top = result.top_terms()
        assert top == []

    def test_top_terms_preserves_order(self):
        """Ensure top_terms sorts correctly even if terms are not pre-sorted."""
        terms = [
            EnrichmentTerm(
                rank=1, term_name="Low", p_value=0.1, z_score=-0.5,
                combined_score=2.0, adjusted_p_value=0.3,
            ),
            EnrichmentTerm(
                rank=2, term_name="High", p_value=0.001, z_score=-3.0,
                combined_score=50.0, adjusted_p_value=0.01,
            ),
            EnrichmentTerm(
                rank=3, term_name="Mid", p_value=0.01, z_score=-1.5,
                combined_score=10.0, adjusted_p_value=0.05,
            ),
        ]
        result = EnrichmentResult(library_name="Test", terms=terms)
        top = result.top_terms(n=3)
        assert top[0].term_name == "High"
        assert top[1].term_name == "Mid"
        assert top[2].term_name == "Low"
