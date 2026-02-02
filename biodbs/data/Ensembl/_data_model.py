"""Ensembl REST API data model with Pydantic validation.

Ensembl REST API structure:
    https://rest.ensembl.org/{endpoint}

Main endpoint categories:
    - Lookup: /lookup/id/:id, /lookup/symbol/:species/:symbol
    - Sequence: /sequence/id/:id, /sequence/region/:species/:region
    - Overlap: /overlap/id/:id, /overlap/region/:species/:region
    - Cross References: /xrefs/id/:id, /xrefs/symbol/:species/:symbol
    - Homology: /homology/id/:species/:id, /homology/symbol/:species/:symbol
    - Variation: /variation/:species/:id
    - VEP: /vep/:species/hgvs/:notation, /vep/:species/region/:region/:allele
    - Information: /info/assembly/:species, /info/species
    - Mapping: /map/:species/:asm_one/:region/:asm_two
    - Phenotype: /phenotype/gene/:species/:gene
    - Ontology: /ontology/id/:id
    - Gene Tree: /genetree/id/:id
"""

from enum import Enum
from pydantic import BaseModel, model_validator, ConfigDict, field_validator
from typing import Dict, Any, Optional, List, Union, Literal


class EnsemblEndpoint(str, Enum):
    """Available Ensembl REST API endpoint categories."""
    # Lookup
    lookup_id = "lookup/id"
    lookup_symbol = "lookup/symbol"
    # Sequence
    sequence_id = "sequence/id"
    sequence_region = "sequence/region"
    # Overlap
    overlap_id = "overlap/id"
    overlap_region = "overlap/region"
    overlap_translation = "overlap/translation"
    # Cross References
    xrefs_id = "xrefs/id"
    xrefs_symbol = "xrefs/symbol"
    xrefs_name = "xrefs/name"
    # Homology
    homology_id = "homology/id"
    homology_symbol = "homology/symbol"
    # Variation
    variation = "variation"
    variation_pmcid = "variation/pmcid"
    variation_pmid = "variation/pmid"
    # VEP
    vep_hgvs = "vep/hgvs"
    vep_id = "vep/id"
    vep_region = "vep/region"
    # Information
    info_analysis = "info/analysis"
    info_assembly = "info/assembly"
    info_biotypes = "info/biotypes"
    info_compara_methods = "info/compara/methods"
    info_compara_species_sets = "info/compara/species_sets"
    info_comparas = "info/comparas"
    info_data = "info/data"
    info_eg_version = "info/eg_version"
    info_external_dbs = "info/external_dbs"
    info_ping = "info/ping"
    info_rest = "info/rest"
    info_software = "info/software"
    info_species = "info/species"
    info_variation = "info/variation"
    info_variation_consequence_types = "info/variation/consequence_types"
    info_variation_populations = "info/variation/populations"
    info_variation_population_name = "info/variation/population_name"
    # Mapping
    map_assembly = "map"
    map_cdna = "map/cdna"
    map_cds = "map/cds"
    map_translation = "map/translation"
    # Phenotype
    phenotype_gene = "phenotype/gene"
    phenotype_region = "phenotype/region"
    phenotype_accession = "phenotype/accession"
    phenotype_term = "phenotype/term"
    # Ontology
    ontology_id = "ontology/id"
    ontology_name = "ontology/name"
    ontology_ancestors = "ontology/ancestors"
    ontology_descendants = "ontology/descendants"
    ontology_ancestors_chart = "ontology/ancestors/chart"
    # Gene Tree
    genetree_id = "genetree/id"
    genetree_member_id = "genetree/member/id"
    genetree_member_symbol = "genetree/member/symbol"
    # Archive
    archive_id = "archive/id"
    # Regulatory
    regulatory_species = "regulatory/species"
    # LD
    ld_pairwise = "ld"
    ld_region = "ld/region"


class EnsemblSequenceType(str, Enum):
    """Sequence types for sequence endpoints."""
    genomic = "genomic"
    cds = "cds"
    cdna = "cdna"
    protein = "protein"


class EnsemblMaskType(str, Enum):
    """Masking types for sequence endpoints."""
    hard = "hard"
    soft = "soft"


class EnsemblFeatureType(str, Enum):
    """Feature types for overlap endpoints."""
    gene = "gene"
    transcript = "transcript"
    cds = "cds"
    exon = "exon"
    repeat = "repeat"
    simple = "simple"
    misc = "misc"
    variation = "variation"
    somatic_variation = "somatic_variation"
    structural_variation = "structural_variation"
    somatic_structural_variation = "somatic_structural_variation"
    constrained = "constrained"
    regulatory = "regulatory"
    motif = "motif"
    mane = "mane"
    band = "band"


class EnsemblHomologyType(str, Enum):
    """Homology types for homology endpoints."""
    orthologues = "orthologues"
    paralogues = "paralogues"
    projections = "projections"
    all = "all"


class EnsemblModel(BaseModel):
    """Pydantic model for Ensembl REST API request validation.

    This model validates parameters and builds the URL path and query params
    for all Ensembl REST API endpoints.
    """
    model_config = ConfigDict(use_enum_values=True)

    endpoint: EnsemblEndpoint
    # Common identifiers
    id: Optional[str] = None
    ids: Optional[List[str]] = None  # For batch requests
    species: Optional[str] = None
    symbol: Optional[str] = None
    region: Optional[str] = None
    gene: Optional[str] = None
    name: Optional[str] = None
    # Sequence parameters
    sequence_type: Optional[EnsemblSequenceType] = None
    mask: Optional[EnsemblMaskType] = None
    mask_feature: Optional[bool] = None
    expand_5prime: Optional[int] = None
    expand_3prime: Optional[int] = None
    start: Optional[int] = None
    end: Optional[int] = None
    multiple_sequences: Optional[bool] = None
    # Overlap parameters
    feature: Optional[Union[EnsemblFeatureType, List[EnsemblFeatureType]]] = None
    biotype: Optional[str] = None
    logic_name: Optional[str] = None
    so_term: Optional[str] = None
    variant_set: Optional[str] = None
    # Lookup parameters
    expand: Optional[bool] = None
    format: Optional[str] = None  # 'full' or 'condensed'
    phenotypes: Optional[bool] = None
    utr: Optional[bool] = None
    mane: Optional[bool] = None
    # Homology parameters
    homology_type: Optional[EnsemblHomologyType] = None
    target_species: Optional[str] = None
    target_taxon: Optional[int] = None
    aligned: Optional[bool] = None
    cigar_line: Optional[bool] = None
    sequence: Optional[str] = None  # 'none', 'cdna', 'protein'
    compara: Optional[str] = None
    # Variation parameters
    genotypes: Optional[bool] = None
    pops: Optional[bool] = None
    population_genotypes: Optional[bool] = None
    genotyping_chips: Optional[bool] = None
    # VEP parameters
    hgvs_notation: Optional[str] = None
    allele: Optional[str] = None
    canonical: Optional[bool] = None
    domains: Optional[bool] = None
    hgvs: Optional[bool] = None
    numbers: Optional[bool] = None
    protein: Optional[bool] = None
    refseq: Optional[bool] = None
    transcript_id: Optional[str] = None
    variant_class: Optional[bool] = None
    vcf_string: Optional[bool] = None
    # Mapping parameters
    asm_one: Optional[str] = None
    asm_two: Optional[str] = None
    coord_system: Optional[str] = None
    target_coord_system: Optional[str] = None
    # Phenotype parameters
    include_associated: Optional[bool] = None
    include_overlap: Optional[bool] = None
    include_pubmed_id: Optional[bool] = None
    include_review_status: Optional[bool] = None
    include_submitter: Optional[bool] = None
    non_specified: Optional[bool] = None
    trait: Optional[bool] = None
    tumour: Optional[bool] = None
    # Ontology parameters
    relation: Optional[str] = None
    simple: Optional[bool] = None
    zero_distance: Optional[bool] = None
    ontology: Optional[str] = None
    subset: Optional[str] = None
    # Gene tree parameters
    nh_format: Optional[str] = None
    prune_species: Optional[str] = None
    prune_taxon: Optional[int] = None
    clusterset_id: Optional[str] = None
    # Cross-reference parameters
    external_db: Optional[str] = None
    all_levels: Optional[bool] = None
    db_type: Optional[str] = None
    object_type: Optional[str] = None
    # Info parameters
    division: Optional[str] = None
    hide_strain_info: Optional[bool] = None
    strain_collection: Optional[str] = None
    # LD parameters
    d_prime: Optional[float] = None
    r2: Optional[float] = None
    population_name: Optional[str] = None
    window_size: Optional[int] = None
    # Archive parameters
    version: Optional[int] = None

    @model_validator(mode="after")
    def validate_required_params(self):
        """Validate required parameters based on endpoint."""
        endpoint = self.endpoint

        # Lookup endpoints
        if endpoint == EnsemblEndpoint.lookup_id.value:
            if not self.id and not self.ids:
                raise ValueError("lookup/id requires 'id' or 'ids'")
        elif endpoint == EnsemblEndpoint.lookup_symbol.value:
            if not self.species or not self.symbol:
                raise ValueError("lookup/symbol requires 'species' and 'symbol'")

        # Sequence endpoints
        elif endpoint == EnsemblEndpoint.sequence_id.value:
            if not self.id and not self.ids:
                raise ValueError("sequence/id requires 'id' or 'ids'")
        elif endpoint == EnsemblEndpoint.sequence_region.value:
            if not self.species or not self.region:
                raise ValueError("sequence/region requires 'species' and 'region'")

        # Overlap endpoints
        elif endpoint == EnsemblEndpoint.overlap_id.value:
            if not self.id:
                raise ValueError("overlap/id requires 'id'")
            if not self.feature:
                raise ValueError("overlap/id requires 'feature'")
        elif endpoint == EnsemblEndpoint.overlap_region.value:
            if not self.species or not self.region:
                raise ValueError("overlap/region requires 'species' and 'region'")
            if not self.feature:
                raise ValueError("overlap/region requires 'feature'")

        # Cross-reference endpoints
        elif endpoint == EnsemblEndpoint.xrefs_id.value:
            if not self.id:
                raise ValueError("xrefs/id requires 'id'")
        elif endpoint == EnsemblEndpoint.xrefs_symbol.value:
            if not self.species or not self.symbol:
                raise ValueError("xrefs/symbol requires 'species' and 'symbol'")
        elif endpoint == EnsemblEndpoint.xrefs_name.value:
            if not self.species or not self.name:
                raise ValueError("xrefs/name requires 'species' and 'name'")

        # Homology endpoints
        elif endpoint == EnsemblEndpoint.homology_id.value:
            if not self.species or not self.id:
                raise ValueError("homology/id requires 'species' and 'id'")
        elif endpoint == EnsemblEndpoint.homology_symbol.value:
            if not self.species or not self.symbol:
                raise ValueError("homology/symbol requires 'species' and 'symbol'")

        # Variation endpoint
        elif endpoint == EnsemblEndpoint.variation.value:
            if not self.species or not self.id:
                raise ValueError("variation requires 'species' and 'id'")

        # VEP endpoints
        elif endpoint == EnsemblEndpoint.vep_hgvs.value:
            if not self.species or not self.hgvs_notation:
                raise ValueError("vep/hgvs requires 'species' and 'hgvs_notation'")
        elif endpoint == EnsemblEndpoint.vep_id.value:
            if not self.species or not self.id:
                raise ValueError("vep/id requires 'species' and 'id'")
        elif endpoint == EnsemblEndpoint.vep_region.value:
            if not self.species or not self.region or not self.allele:
                raise ValueError("vep/region requires 'species', 'region', and 'allele'")

        # Mapping endpoint
        elif endpoint == EnsemblEndpoint.map_assembly.value:
            if not self.species or not self.asm_one or not self.region or not self.asm_two:
                raise ValueError("map requires 'species', 'asm_one', 'region', and 'asm_two'")

        # Phenotype endpoint
        elif endpoint == EnsemblEndpoint.phenotype_gene.value:
            if not self.species or not self.gene:
                raise ValueError("phenotype/gene requires 'species' and 'gene'")
        elif endpoint == EnsemblEndpoint.phenotype_region.value:
            if not self.species or not self.region:
                raise ValueError("phenotype/region requires 'species' and 'region'")

        # Ontology endpoints
        elif endpoint == EnsemblEndpoint.ontology_id.value:
            if not self.id:
                raise ValueError("ontology/id requires 'id'")
        elif endpoint == EnsemblEndpoint.ontology_ancestors.value:
            if not self.id:
                raise ValueError("ontology/ancestors requires 'id'")
        elif endpoint == EnsemblEndpoint.ontology_descendants.value:
            if not self.id:
                raise ValueError("ontology/descendants requires 'id'")

        # Gene tree endpoints
        elif endpoint == EnsemblEndpoint.genetree_id.value:
            if not self.id:
                raise ValueError("genetree/id requires 'id'")
        elif endpoint == EnsemblEndpoint.genetree_member_id.value:
            if not self.species or not self.id:
                raise ValueError("genetree/member/id requires 'species' and 'id'")
        elif endpoint == EnsemblEndpoint.genetree_member_symbol.value:
            if not self.species or not self.symbol:
                raise ValueError("genetree/member/symbol requires 'species' and 'symbol'")

        # Info assembly
        elif endpoint == EnsemblEndpoint.info_assembly.value:
            if not self.species:
                raise ValueError("info/assembly requires 'species'")

        return self

    def build_path(self) -> str:
        """Build the URL path component."""
        endpoint = self.endpoint
        parts = [endpoint]

        # Build path based on endpoint type
        if endpoint == EnsemblEndpoint.lookup_id.value:
            if self.id:
                parts.append(self.id)
        elif endpoint == EnsemblEndpoint.lookup_symbol.value:
            parts = [endpoint, self.species, self.symbol]

        elif endpoint == EnsemblEndpoint.sequence_id.value:
            if self.id:
                parts.append(self.id)
        elif endpoint == EnsemblEndpoint.sequence_region.value:
            parts = [endpoint, self.species, self.region]

        elif endpoint == EnsemblEndpoint.overlap_id.value:
            parts.append(self.id)
        elif endpoint == EnsemblEndpoint.overlap_region.value:
            parts = [endpoint, self.species, self.region]
        elif endpoint == EnsemblEndpoint.overlap_translation.value:
            parts.append(self.id)

        elif endpoint == EnsemblEndpoint.xrefs_id.value:
            parts.append(self.id)
        elif endpoint == EnsemblEndpoint.xrefs_symbol.value:
            parts = [endpoint, self.species, self.symbol]
        elif endpoint == EnsemblEndpoint.xrefs_name.value:
            parts = [endpoint, self.species, self.name]

        elif endpoint == EnsemblEndpoint.homology_id.value:
            parts = [endpoint, self.species, self.id]
        elif endpoint == EnsemblEndpoint.homology_symbol.value:
            parts = [endpoint, self.species, self.symbol]

        elif endpoint == EnsemblEndpoint.variation.value:
            parts = [endpoint, self.species, self.id]
        elif endpoint == EnsemblEndpoint.variation_pmcid.value:
            parts = [endpoint, self.species, self.id]
        elif endpoint == EnsemblEndpoint.variation_pmid.value:
            parts = [endpoint, self.species, self.id]

        elif endpoint == EnsemblEndpoint.vep_hgvs.value:
            parts = ["vep", self.species, "hgvs", self.hgvs_notation]
        elif endpoint == EnsemblEndpoint.vep_id.value:
            parts = ["vep", self.species, "id", self.id]
        elif endpoint == EnsemblEndpoint.vep_region.value:
            parts = ["vep", self.species, "region", self.region, self.allele]

        elif endpoint == EnsemblEndpoint.map_assembly.value:
            parts = ["map", self.species, self.asm_one, self.region, self.asm_two]
        elif endpoint == EnsemblEndpoint.map_cdna.value:
            parts = [endpoint, self.id, self.region]
        elif endpoint == EnsemblEndpoint.map_cds.value:
            parts = [endpoint, self.id, self.region]
        elif endpoint == EnsemblEndpoint.map_translation.value:
            parts = [endpoint, self.id, self.region]

        elif endpoint == EnsemblEndpoint.phenotype_gene.value:
            parts = [endpoint, self.species, self.gene]
        elif endpoint == EnsemblEndpoint.phenotype_region.value:
            parts = [endpoint, self.species, self.region]
        elif endpoint == EnsemblEndpoint.phenotype_accession.value:
            parts = [endpoint, self.species, self.id]
        elif endpoint == EnsemblEndpoint.phenotype_term.value:
            parts = [endpoint, self.species, self.name]

        elif endpoint == EnsemblEndpoint.ontology_id.value:
            parts.append(self.id)
        elif endpoint == EnsemblEndpoint.ontology_name.value:
            parts.append(self.name)
        elif endpoint == EnsemblEndpoint.ontology_ancestors.value:
            parts.append(self.id)
        elif endpoint == EnsemblEndpoint.ontology_descendants.value:
            parts.append(self.id)
        elif endpoint == EnsemblEndpoint.ontology_ancestors_chart.value:
            parts.append(self.id)

        elif endpoint == EnsemblEndpoint.genetree_id.value:
            parts.append(self.id)
        elif endpoint == EnsemblEndpoint.genetree_member_id.value:
            parts = [endpoint, self.species, self.id]
        elif endpoint == EnsemblEndpoint.genetree_member_symbol.value:
            parts = [endpoint, self.species, self.symbol]

        elif endpoint == EnsemblEndpoint.archive_id.value:
            if self.id:
                parts.append(self.id)

        elif endpoint == EnsemblEndpoint.info_assembly.value:
            parts.append(self.species)

        elif endpoint == EnsemblEndpoint.regulatory_species.value:
            parts.append(self.species)

        elif endpoint == EnsemblEndpoint.ld_pairwise.value:
            parts = ["ld", self.species, "pairwise", self.id]
        elif endpoint == EnsemblEndpoint.ld_region.value:
            parts = [endpoint, self.species, self.region]

        return "/".join(str(p) for p in parts if p)

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for the request."""
        params = {}

        # Sequence parameters
        if self.sequence_type:
            params["type"] = self.sequence_type
        if self.mask:
            params["mask"] = self.mask
        if self.mask_feature is not None:
            params["mask_feature"] = 1 if self.mask_feature else 0
        if self.expand_5prime is not None:
            params["expand_5prime"] = self.expand_5prime
        if self.expand_3prime is not None:
            params["expand_3prime"] = self.expand_3prime
        if self.start is not None:
            params["start"] = self.start
        if self.end is not None:
            params["end"] = self.end
        if self.multiple_sequences is not None:
            params["multiple_sequences"] = 1 if self.multiple_sequences else 0

        # Overlap parameters
        if self.feature:
            if isinstance(self.feature, list):
                params["feature"] = ";feature=".join(
                    f.value if hasattr(f, "value") else f for f in self.feature
                )
            else:
                feat = self.feature.value if hasattr(self.feature, "value") else self.feature
                params["feature"] = feat
        if self.biotype:
            params["biotype"] = self.biotype
        if self.logic_name:
            params["logic_name"] = self.logic_name
        if self.so_term:
            params["so_term"] = self.so_term
        if self.variant_set:
            params["variant_set"] = self.variant_set

        # Lookup parameters
        if self.expand is not None:
            params["expand"] = 1 if self.expand else 0
        if self.format:
            params["format"] = self.format
        if self.phenotypes is not None:
            params["phenotypes"] = 1 if self.phenotypes else 0
        if self.utr is not None:
            params["utr"] = 1 if self.utr else 0
        if self.mane is not None:
            params["mane"] = 1 if self.mane else 0

        # Homology parameters
        if self.homology_type:
            params["type"] = self.homology_type
        if self.target_species:
            params["target_species"] = self.target_species
        if self.target_taxon:
            params["target_taxon"] = self.target_taxon
        if self.aligned is not None:
            params["aligned"] = 1 if self.aligned else 0
        if self.cigar_line is not None:
            params["cigar_line"] = 1 if self.cigar_line else 0
        if self.sequence:
            params["sequence"] = self.sequence
        if self.compara:
            params["compara"] = self.compara

        # Variation parameters
        if self.genotypes is not None:
            params["genotypes"] = 1 if self.genotypes else 0
        if self.pops is not None:
            params["pops"] = 1 if self.pops else 0
        if self.population_genotypes is not None:
            params["population_genotypes"] = 1 if self.population_genotypes else 0
        if self.genotyping_chips is not None:
            params["genotyping_chips"] = 1 if self.genotyping_chips else 0

        # VEP parameters
        if self.canonical is not None:
            params["canonical"] = 1 if self.canonical else 0
        if self.domains is not None:
            params["domains"] = 1 if self.domains else 0
        if self.hgvs is not None:
            params["hgvs"] = 1 if self.hgvs else 0
        if self.numbers is not None:
            params["numbers"] = 1 if self.numbers else 0
        if self.protein is not None:
            params["protein"] = 1 if self.protein else 0
        if self.refseq is not None:
            params["refseq"] = 1 if self.refseq else 0
        if self.transcript_id:
            params["transcript_id"] = self.transcript_id
        if self.variant_class is not None:
            params["variant_class"] = 1 if self.variant_class else 0
        if self.vcf_string is not None:
            params["vcf_string"] = 1 if self.vcf_string else 0

        # Mapping parameters
        if self.coord_system:
            params["coord_system"] = self.coord_system
        if self.target_coord_system:
            params["target_coord_system"] = self.target_coord_system

        # Phenotype parameters
        if self.include_associated is not None:
            params["include_associated"] = 1 if self.include_associated else 0
        if self.include_overlap is not None:
            params["include_overlap"] = 1 if self.include_overlap else 0
        if self.include_pubmed_id is not None:
            params["include_pubmed_id"] = 1 if self.include_pubmed_id else 0
        if self.include_review_status is not None:
            params["include_review_status"] = 1 if self.include_review_status else 0
        if self.include_submitter is not None:
            params["include_submitter"] = 1 if self.include_submitter else 0
        if self.non_specified is not None:
            params["non_specified"] = 1 if self.non_specified else 0
        if self.trait is not None:
            params["trait"] = 1 if self.trait else 0
        if self.tumour is not None:
            params["tumour"] = 1 if self.tumour else 0

        # Ontology parameters
        if self.relation:
            params["relation"] = self.relation
        if self.simple is not None:
            params["simple"] = 1 if self.simple else 0
        if self.zero_distance is not None:
            params["zero_distance"] = 1 if self.zero_distance else 0
        if self.ontology:
            params["ontology"] = self.ontology
        if self.subset:
            params["subset"] = self.subset

        # Gene tree parameters
        if self.nh_format:
            params["nh_format"] = self.nh_format
        if self.prune_species:
            params["prune_species"] = self.prune_species
        if self.prune_taxon:
            params["prune_taxon"] = self.prune_taxon
        if self.clusterset_id:
            params["clusterset_id"] = self.clusterset_id

        # Cross-reference parameters
        if self.external_db:
            params["external_db"] = self.external_db
        if self.all_levels is not None:
            params["all_levels"] = 1 if self.all_levels else 0
        if self.db_type:
            params["db_type"] = self.db_type
        if self.object_type:
            params["object_type"] = self.object_type

        # Info parameters
        if self.division:
            params["division"] = self.division
        if self.hide_strain_info is not None:
            params["hide_strain_info"] = 1 if self.hide_strain_info else 0
        if self.strain_collection:
            params["strain_collection"] = self.strain_collection

        # LD parameters
        if self.d_prime is not None:
            params["d_prime"] = self.d_prime
        if self.r2 is not None:
            params["r2"] = self.r2
        if self.population_name:
            params["population_name"] = self.population_name
        if self.window_size is not None:
            params["window_size"] = self.window_size

        # Archive parameters
        if self.version is not None:
            params["version"] = self.version

        # Species for endpoints that need it in query
        if self.species and self.endpoint in [
            EnsemblEndpoint.lookup_id.value,
            EnsemblEndpoint.sequence_id.value,
            EnsemblEndpoint.overlap_id.value,
            EnsemblEndpoint.xrefs_id.value,
        ]:
            params["species"] = self.species

        return params

    def is_batch_request(self) -> bool:
        """Check if this is a batch (POST) request."""
        return self.ids is not None and len(self.ids) > 0

    def build_request_body(self) -> Optional[Dict[str, Any]]:
        """Build request body for POST requests."""
        if self.ids:
            return {"ids": self.ids}
        return None
