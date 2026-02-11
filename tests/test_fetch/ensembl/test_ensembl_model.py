"""Tests for biodbs.data.Ensembl._data_model — pure model tests, no API calls."""

import pytest
from pydantic import ValidationError

from biodbs.data.Ensembl._data_model import (
    EnsemblModel,
    EnsemblEndpoint,
    EnsemblSequenceType,
    EnsemblMaskType,
    EnsemblFeatureType,
    EnsemblHomologyType,
)


# =============================================================================
# validate_required_params
# =============================================================================

class TestValidateRequiredParams:
    """Test parameter validation for every endpoint category."""

    # -- Lookup ---------------------------------------------------------------
    def test_lookup_id_requires_id(self):
        with pytest.raises(ValidationError, match="id"):
            EnsemblModel(endpoint=EnsemblEndpoint.lookup_id)

    def test_lookup_id_with_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, id="ENSG00000141510")
        assert m.id == "ENSG00000141510"

    def test_lookup_id_with_ids(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, ids=["ENSG001", "ENSG002"])
        assert len(m.ids) == 2

    def test_lookup_symbol_requires_species_and_symbol(self):
        with pytest.raises(ValidationError, match="species.*symbol|symbol.*species"):
            EnsemblModel(endpoint=EnsemblEndpoint.lookup_symbol, species="human")
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.lookup_symbol, symbol="TP53")

    def test_lookup_symbol_ok(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_symbol, species="human", symbol="TP53")
        assert m.species == "human"

    # -- Sequence -------------------------------------------------------------
    def test_sequence_id_requires_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.sequence_id)

    def test_sequence_id_with_ids_batch(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.sequence_id, ids=["ENST001"])
        assert m.is_batch_request()

    def test_sequence_region_requires_species_and_region(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.sequence_region, species="human")

    def test_sequence_region_ok(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.sequence_region, species="human", region="X:1..100:1")
        assert m.region == "X:1..100:1"

    # -- Overlap --------------------------------------------------------------
    def test_overlap_id_requires_id_and_feature(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.overlap_id, feature="gene")
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.overlap_id, id="ENSG001")

    def test_overlap_id_ok(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.overlap_id, id="ENSG001", feature="gene")
        assert m.feature == "gene"

    def test_overlap_region_requires_species_region_feature(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.overlap_region, species="human", region="1:1-100")

    def test_overlap_region_ok(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.overlap_region,
            species="human", region="7:140424943-140624564", feature="gene",
        )
        assert m.species == "human"

    # -- Cross-references -----------------------------------------------------
    def test_xrefs_id_requires_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.xrefs_id)

    def test_xrefs_symbol_requires_species_and_symbol(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.xrefs_symbol, species="human")

    def test_xrefs_name_requires_species_and_name(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.xrefs_name, species="human")

    def test_xrefs_name_ok(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.xrefs_name, species="human", name="BRCA2")
        assert m.name == "BRCA2"

    # -- Homology -------------------------------------------------------------
    def test_homology_id_requires_species_and_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.homology_id, species="human")

    def test_homology_symbol_requires_species_and_symbol(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.homology_symbol, species="human")

    # -- Variation ------------------------------------------------------------
    def test_variation_requires_species_and_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.variation, id="rs56116432")

    def test_variation_ok(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.variation, species="human", id="rs56116432")
        assert m.id == "rs56116432"

    # -- VEP ------------------------------------------------------------------
    def test_vep_hgvs_requires_species_and_notation(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.vep_hgvs, species="human")

    def test_vep_hgvs_ok(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.vep_hgvs,
            species="human", hgvs_notation="ENST00000366667:c.803C>T",
        )
        assert m.hgvs_notation == "ENST00000366667:c.803C>T"

    def test_vep_id_requires_species_and_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.vep_id, species="human")

    def test_vep_region_requires_species_region_allele(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.vep_region, species="human", region="9:22125503-22125502:1")

    def test_vep_region_ok(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.vep_region,
            species="human", region="9:22125503-22125502:1", allele="C",
        )
        assert m.allele == "C"

    # -- Mapping --------------------------------------------------------------
    def test_map_assembly_requires_all_fields(self):
        with pytest.raises(ValidationError):
            EnsemblModel(
                endpoint=EnsemblEndpoint.map_assembly,
                species="human", asm_one="GRCh37", region="X:1..100:1",
            )

    def test_map_assembly_ok(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.map_assembly,
            species="human", asm_one="GRCh37", region="X:1..100:1", asm_two="GRCh38",
        )
        assert m.asm_two == "GRCh38"

    # -- Phenotype ------------------------------------------------------------
    def test_phenotype_gene_requires_species_and_gene(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.phenotype_gene, species="human")

    def test_phenotype_region_requires_species_and_region(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.phenotype_region, species="human")

    # -- Ontology -------------------------------------------------------------
    def test_ontology_id_requires_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.ontology_id)

    def test_ontology_ancestors_requires_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.ontology_ancestors)

    def test_ontology_descendants_requires_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.ontology_descendants)

    # -- Gene tree ------------------------------------------------------------
    def test_genetree_id_requires_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.genetree_id)

    def test_genetree_member_id_requires_species_and_id(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.genetree_member_id, species="human")

    def test_genetree_member_symbol_requires_species_and_symbol(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.genetree_member_symbol, species="human")

    # -- Info -----------------------------------------------------------------
    def test_info_assembly_requires_species(self):
        with pytest.raises(ValidationError):
            EnsemblModel(endpoint=EnsemblEndpoint.info_assembly)

    def test_info_species_no_requirements(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.info_species)
        assert m.endpoint == EnsemblEndpoint.info_species.value


# =============================================================================
# build_path
# =============================================================================

class TestBuildPath:
    """Test URL path construction for various endpoints."""

    def test_lookup_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, id="ENSG00000141510")
        assert m.build_path() == "lookup/id/ENSG00000141510"

    def test_lookup_symbol(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_symbol, species="human", symbol="TP53")
        assert m.build_path() == "lookup/symbol/human/TP53"

    def test_sequence_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.sequence_id, id="ENST00000269305")
        assert m.build_path() == "sequence/id/ENST00000269305"

    def test_sequence_region(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.sequence_region, species="human", region="X:1..100:1")
        assert m.build_path() == "sequence/region/human/X:1..100:1"

    def test_overlap_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.overlap_id, id="ENSG001", feature="gene")
        assert m.build_path() == "overlap/id/ENSG001"

    def test_overlap_region(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.overlap_region,
            species="human", region="7:140424943-140624564", feature="gene",
        )
        assert m.build_path() == "overlap/region/human/7:140424943-140624564"

    def test_xrefs_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.xrefs_id, id="ENSG001")
        assert m.build_path() == "xrefs/id/ENSG001"

    def test_xrefs_symbol(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.xrefs_symbol, species="human", symbol="BRCA2")
        assert m.build_path() == "xrefs/symbol/human/BRCA2"

    def test_homology_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.homology_id, species="human", id="ENSG001")
        assert m.build_path() == "homology/id/human/ENSG001"

    def test_homology_symbol(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.homology_symbol, species="human", symbol="TP53")
        assert m.build_path() == "homology/symbol/human/TP53"

    def test_variation(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.variation, species="human", id="rs56116432")
        assert m.build_path() == "variation/human/rs56116432"

    def test_vep_hgvs(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.vep_hgvs,
            species="human", hgvs_notation="ENST00000366667:c.803C>T",
        )
        assert m.build_path() == "vep/human/hgvs/ENST00000366667:c.803C>T"

    def test_vep_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.vep_id, species="human", id="rs56116432")
        assert m.build_path() == "vep/human/id/rs56116432"

    def test_vep_region(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.vep_region,
            species="human", region="9:22125503-22125502:1", allele="C",
        )
        assert m.build_path() == "vep/human/region/9:22125503-22125502:1/C"

    def test_map_assembly(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.map_assembly,
            species="human", asm_one="GRCh37", region="X:1..100:1", asm_two="GRCh38",
        )
        assert m.build_path() == "map/human/GRCh37/X:1..100:1/GRCh38"

    def test_phenotype_gene(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.phenotype_gene, species="human", gene="TP53")
        assert m.build_path() == "phenotype/gene/human/TP53"

    def test_phenotype_region(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.phenotype_region, species="human", region="7:140424943-140624564")
        assert m.build_path() == "phenotype/region/human/7:140424943-140624564"

    def test_ontology_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.ontology_id, id="GO:0005667")
        assert m.build_path() == "ontology/id/GO:0005667"

    def test_ontology_ancestors(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.ontology_ancestors, id="GO:0005667")
        assert m.build_path() == "ontology/ancestors/GO:0005667"

    def test_ontology_descendants(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.ontology_descendants, id="GO:0005667")
        assert m.build_path() == "ontology/descendants/GO:0005667"

    def test_genetree_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.genetree_id, id="ENSGT003900")
        assert m.build_path() == "genetree/id/ENSGT003900"

    def test_genetree_member_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.genetree_member_id, species="human", id="ENSG001")
        assert m.build_path() == "genetree/member/id/human/ENSG001"

    def test_genetree_member_symbol(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.genetree_member_symbol, species="human", symbol="BRCA2")
        assert m.build_path() == "genetree/member/symbol/human/BRCA2"

    def test_info_assembly(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.info_assembly, species="human")
        assert m.build_path() == "info/assembly/human"

    def test_info_species(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.info_species)
        assert m.build_path() == "info/species"


# =============================================================================
# build_query_params
# =============================================================================

class TestBuildQueryParams:
    """Test query parameter generation."""

    def test_empty_params(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.info_species)
        assert m.build_query_params() == {}

    def test_sequence_type(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.sequence_id, id="ENST001", sequence_type="cds")
        params = m.build_query_params()
        assert params["type"] == "cds"

    def test_mask_and_mask_feature(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.sequence_id, id="ENST001",
            mask="soft", mask_feature=True,
        )
        params = m.build_query_params()
        assert params["mask"] == "soft"
        assert params["mask_feature"] == 1

    def test_expand_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.sequence_id, id="ENST001",
            expand_5prime=100, expand_3prime=200,
        )
        params = m.build_query_params()
        assert params["expand_5prime"] == 100
        assert params["expand_3prime"] == 200

    def test_start_end(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.sequence_id, id="ENST001", start=10, end=50)
        params = m.build_query_params()
        assert params["start"] == 10
        assert params["end"] == 50

    def test_multiple_sequences(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.sequence_id, id="ENST001", multiple_sequences=True)
        params = m.build_query_params()
        assert params["multiple_sequences"] == 1

    def test_feature_single(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.overlap_id, id="ENSG001", feature="gene")
        params = m.build_query_params()
        assert params["feature"] == "gene"

    def test_feature_list(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.overlap_id, id="ENSG001",
            feature=["gene", "transcript"],
        )
        params = m.build_query_params()
        assert isinstance(params["feature"], list)
        assert "gene" in params["feature"]

    def test_lookup_expand_format(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, id="ENSG001", expand=True, format="condensed")
        params = m.build_query_params()
        assert params["expand"] == 1
        assert params["format"] == "condensed"

    def test_phenotypes_utr_mane(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.lookup_id, id="ENSG001",
            phenotypes=True, utr=False, mane=True,
        )
        params = m.build_query_params()
        assert params["phenotypes"] == 1
        assert params["utr"] == 0
        assert params["mane"] == 1

    def test_homology_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.homology_id, species="human", id="ENSG001",
            homology_type="orthologues", target_species="mouse",
            target_taxon=10090, aligned=True, cigar_line=False,
            sequence="protein", compara="vertebrates",
        )
        params = m.build_query_params()
        assert params["type"] == "orthologues"
        assert params["target_species"] == "mouse"
        assert params["target_taxon"] == 10090
        assert params["aligned"] == 1
        assert params["cigar_line"] == 0
        assert params["sequence"] == "protein"
        assert params["compara"] == "vertebrates"

    def test_variation_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.variation, species="human", id="rs001",
            genotypes=True, pops=False,
            population_genotypes=True, genotyping_chips=False,
        )
        params = m.build_query_params()
        assert params["genotypes"] == 1
        assert params["pops"] == 0
        assert params["population_genotypes"] == 1
        assert params["genotyping_chips"] == 0

    def test_vep_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.vep_hgvs, species="human",
            hgvs_notation="X:c.1A>G",
            canonical=True, domains=False, hgvs=True,
            numbers=True, protein=False, refseq=True, variant_class=True,
        )
        params = m.build_query_params()
        assert params["canonical"] == 1
        assert params["domains"] == 0
        assert params["hgvs"] == 1
        assert params["refseq"] == 1
        assert params["variant_class"] == 1

    def test_mapping_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.map_assembly,
            species="human", asm_one="GRCh37", region="X:1..100:1", asm_two="GRCh38",
            coord_system="chromosome", target_coord_system="chromosome",
        )
        params = m.build_query_params()
        assert params["coord_system"] == "chromosome"
        assert params["target_coord_system"] == "chromosome"

    def test_phenotype_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.phenotype_gene, species="human", gene="TP53",
            include_associated=True, include_overlap=False,
            include_pubmed_id=True, include_review_status=False,
            include_submitter=True,
        )
        params = m.build_query_params()
        assert params["include_associated"] == 1
        assert params["include_overlap"] == 0
        assert params["include_pubmed_id"] == 1

    def test_ontology_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.ontology_id, id="GO:0005667",
            relation="is_a", simple=True,
        )
        params = m.build_query_params()
        assert params["relation"] == "is_a"
        assert params["simple"] == 1

    def test_ontology_zero_distance_and_subset(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.ontology_descendants, id="GO:0005667",
            zero_distance=True, ontology="GO", subset="goslim_generic",
        )
        params = m.build_query_params()
        assert params["zero_distance"] == 1
        assert params["ontology"] == "GO"
        assert params["subset"] == "goslim_generic"

    def test_genetree_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.genetree_id, id="ENSGT003900",
            nh_format="simple", prune_species="human", prune_taxon=9606,
            clusterset_id="default",
        )
        params = m.build_query_params()
        assert params["nh_format"] == "simple"
        assert params["prune_species"] == "human"
        assert params["prune_taxon"] == 9606
        assert params["clusterset_id"] == "default"

    def test_xref_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.xrefs_id, id="ENSG001",
            external_db="HGNC", all_levels=True, db_type="core", object_type="Gene",
        )
        params = m.build_query_params()
        assert params["external_db"] == "HGNC"
        assert params["all_levels"] == 1
        assert params["db_type"] == "core"
        assert params["object_type"] == "Gene"

    def test_info_params(self):
        m = EnsemblModel(
            endpoint=EnsemblEndpoint.info_species,
            division="EnsemblVertebrates", hide_strain_info=True,
            strain_collection="mouse",
        )
        params = m.build_query_params()
        assert params["division"] == "EnsemblVertebrates"
        assert params["hide_strain_info"] == 1
        assert params["strain_collection"] == "mouse"

    def test_species_in_query_for_lookup_id(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, id="ENSG001", species="human")
        params = m.build_query_params()
        assert params["species"] == "human"


# =============================================================================
# is_batch_request & build_request_body
# =============================================================================

class TestBatchRequest:
    def test_single_id_not_batch(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, id="ENSG001")
        assert m.is_batch_request() is False
        assert m.build_request_body() is None

    def test_ids_is_batch(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, ids=["ENSG001", "ENSG002"])
        assert m.is_batch_request() is True
        body = m.build_request_body()
        assert body == {"ids": ["ENSG001", "ENSG002"]}

    def test_empty_ids_not_batch(self):
        m = EnsemblModel(endpoint=EnsemblEndpoint.lookup_id, id="ENSG001", ids=[])
        assert m.is_batch_request() is False
