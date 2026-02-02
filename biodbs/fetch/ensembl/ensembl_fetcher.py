"""Ensembl REST API fetcher following the standardized pattern."""

from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.Ensembl._data_model import (
    EnsemblModel,
    EnsemblEndpoint,
    EnsemblSequenceType,
    EnsemblFeatureType,
    EnsemblHomologyType,
)
from biodbs.data.Ensembl.data import EnsemblFetchedData, EnsemblDataManager
from typing import Dict, Any, List, Literal, Optional, Union
from pathlib import Path
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://rest.ensembl.org"


def _build_ensembl_url(params: Dict[str, Any]) -> str:
    """Build Ensembl REST API URL from validated parameters."""
    path = params.get("_path", "")
    return f"{BASE_URL}/{path}"


class EnsemblNameSpace(NameSpace):
    """Namespace that validates parameters via EnsemblModel."""

    def __init__(self):
        super().__init__(EnsemblModel)

    def validate(self, **kwargs):
        """Validate and compute derived fields (path, query params)."""
        is_valid, err_msg = super().validate(**kwargs)
        if is_valid:
            model = EnsemblModel(**kwargs)
            self._valid_params["_path"] = model.build_path()
            self._valid_params["_query_params"] = model.build_query_params()
            self._valid_params["_is_batch"] = model.is_batch_request()
            self._valid_params["_request_body"] = model.build_request_body()
        return is_valid, err_msg


class Ensembl_APIConfig(BaseAPIConfig):
    """API config for Ensembl REST API using a custom URL builder."""

    def __init__(self):
        super().__init__(url_builder=_build_ensembl_url)


class Ensembl_Fetcher(BaseDataFetcher):
    """Fetcher for Ensembl REST API.

    Ensembl REST API provides access to genomic data including:
    - Gene/transcript/protein lookup and information
    - Genomic and protein sequences
    - Feature overlap queries
    - Cross-references to external databases
    - Homology and comparative genomics
    - Variant data and VEP (Variant Effect Predictor)
    - Coordinate mapping between assemblies
    - Phenotype and ontology data

    Examples::

        fetcher = Ensembl_Fetcher()

        # Lookup a gene by Ensembl ID
        gene = fetcher.lookup("ENSG00000141510")
        print(gene.results[0]["display_name"])  # TP53

        # Get sequence for a transcript
        seq = fetcher.get_sequence("ENST00000269305", sequence_type="cds")

        # Find features overlapping a region
        features = fetcher.get_overlap_region(
            "human", "7:140424943-140624564",
            feature=["gene", "transcript"]
        )

        # Get homologs for a gene
        homologs = fetcher.get_homology("human", "ENSG00000141510")

        # Get variant consequences
        vep = fetcher.get_vep_hgvs("human", "ENST00000366667:c.803C>T")
    """

    def __init__(self, **data_manager_kws):
        super().__init__(Ensembl_APIConfig(), EnsemblNameSpace(), {})
        self._data_manager = (
            EnsemblDataManager(**data_manager_kws)
            if data_manager_kws
            else None
        )
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _make_request(
        self,
        url: str,
        query_params: Dict[str, Any],
        is_batch: bool = False,
        request_body: Optional[Dict] = None,
        content_type: str = "json",
    ) -> requests.Response:
        """Make HTTP request to Ensembl API."""
        headers = {}

        if content_type == "fasta":
            headers["Accept"] = "text/x-fasta"
        elif content_type == "text":
            headers["Accept"] = "text/plain"
        else:
            headers["Accept"] = "application/json"

        if is_batch and request_body:
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=request_body, params=query_params, headers=headers)
        else:
            response = requests.get(url, params=query_params, headers=headers)

        return response

    def get(
        self,
        endpoint: str,
        id: Optional[str] = None,
        ids: Optional[List[str]] = None,
        species: Optional[str] = None,
        symbol: Optional[str] = None,
        region: Optional[str] = None,
        gene: Optional[str] = None,
        name: Optional[str] = None,
        content_type: str = "json",
        **kwargs,
    ) -> EnsemblFetchedData:
        """Fetch data from Ensembl REST API.

        Args:
            endpoint: Ensembl endpoint (e.g., "lookup/id", "sequence/id").
            id: Ensembl stable ID for single lookups.
            ids: List of IDs for batch requests.
            species: Species name (e.g., "human", "homo_sapiens").
            symbol: Gene symbol for symbol-based lookups.
            region: Genomic region (e.g., "X:1000000..1000100:1").
            gene: Gene name or ID for phenotype endpoints.
            name: Name for name-based lookups.
            content_type: Response format ("json", "fasta", "text").
            **kwargs: Additional endpoint-specific parameters.

        Returns:
            EnsemblFetchedData with parsed results.
        """
        is_valid, err_msg = self._namespace.validate(
            endpoint=endpoint,
            id=id,
            ids=ids,
            species=species,
            symbol=symbol,
            region=region,
            gene=gene,
            name=name,
            **kwargs,
        )
        if not is_valid:
            raise ValueError(err_msg)

        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url
        query_params = self._namespace.valid_params.get("_query_params", {})
        is_batch = self._namespace.valid_params.get("_is_batch", False)
        request_body = self._namespace.valid_params.get("_request_body")

        response = self._make_request(
            url, query_params, is_batch, request_body, content_type
        )

        if response.status_code == 404:
            return EnsemblFetchedData({}, endpoint=endpoint)
        if response.status_code == 400:
            raise ValueError(f"Bad request: {response.text}")
        if response.status_code != 200:
            raise ConnectionError(
                f"Failed to fetch data from Ensembl API. "
                f"Status code: {response.status_code}, Message: {response.text}"
            )

        if content_type in ("fasta", "text"):
            return EnsemblFetchedData(
                response.text, endpoint=endpoint, content_type=content_type
            )

        return EnsemblFetchedData(response.json(), endpoint=endpoint)

    # =========================================================================
    # Lookup Methods
    # =========================================================================

    def lookup(
        self,
        id: str,
        species: Optional[str] = None,
        expand: bool = False,
        format: str = "full",
        db_type: str = "core",
        phenotypes: bool = False,
        utr: bool = False,
        mane: bool = False,
    ) -> EnsemblFetchedData:
        """Look up an Ensembl stable ID.

        Args:
            id: Ensembl stable ID (e.g., ENSG00000141510).
            species: Species name/alias (optional, auto-detected from ID).
            expand: Include connected features (transcripts, exons).
            format: Response format ("full" or "condensed").
            db_type: Database type ("core" or "otherfeatures").
            phenotypes: Include phenotypes (genes only).
            utr: Include UTR features (requires expand=True).
            mane: Include MANE features (requires expand=True).

        Returns:
            EnsemblFetchedData with gene/transcript/protein information.
        """
        return self.get(
            endpoint=EnsemblEndpoint.lookup_id,
            id=id,
            species=species,
            expand=expand,
            format=format,
            db_type=db_type,
            phenotypes=phenotypes,
            utr=utr,
            mane=mane,
        )

    def lookup_batch(
        self,
        ids: List[str],
        species: Optional[str] = None,
        expand: bool = False,
        format: str = "full",
        db_type: str = "core",
    ) -> EnsemblFetchedData:
        """Look up multiple Ensembl stable IDs in batch.

        Args:
            ids: List of Ensembl stable IDs (max 1000).
            species: Species name/alias.
            expand: Include connected features.
            format: Response format.
            db_type: Database type.

        Returns:
            EnsemblFetchedData with results for each ID.
        """
        return self.get(
            endpoint=EnsemblEndpoint.lookup_id,
            ids=ids,
            species=species,
            expand=expand,
            format=format,
            db_type=db_type,
        )

    def lookup_symbol(
        self,
        species: str,
        symbol: str,
        expand: bool = False,
        format: str = "full",
    ) -> EnsemblFetchedData:
        """Look up a gene by symbol.

        Args:
            species: Species name (e.g., "human", "mouse").
            symbol: Gene symbol (e.g., "BRCA2", "TP53").
            expand: Include connected features.
            format: Response format.

        Returns:
            EnsemblFetchedData with gene information.
        """
        return self.get(
            endpoint=EnsemblEndpoint.lookup_symbol,
            species=species,
            symbol=symbol,
            expand=expand,
            format=format,
        )

    # =========================================================================
    # Sequence Methods
    # =========================================================================

    def get_sequence(
        self,
        id: str,
        sequence_type: str = "genomic",
        species: Optional[str] = None,
        expand_5prime: Optional[int] = None,
        expand_3prime: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        mask: Optional[str] = None,
        mask_feature: bool = False,
        multiple_sequences: bool = False,
        format: str = "fasta",
    ) -> EnsemblFetchedData:
        """Get sequence for an Ensembl stable ID.

        Args:
            id: Ensembl stable ID (gene, transcript, exon, protein).
            sequence_type: Type of sequence ("genomic", "cds", "cdna", "protein").
            species: Species name (optional).
            expand_5prime: Extend upstream (genomic only).
            expand_3prime: Extend downstream (genomic only).
            start: Trim sequence start.
            end: Trim sequence end.
            mask: Mask repeats ("hard" or "soft", genomic only).
            mask_feature: Mask introns/UTRs.
            multiple_sequences: Return multiple sequences per ID.
            format: Output format ("fasta" or "json").

        Returns:
            EnsemblFetchedData with sequence data.
        """
        content_type = "fasta" if format == "fasta" else "json"
        return self.get(
            endpoint=EnsemblEndpoint.sequence_id,
            id=id,
            species=species,
            sequence_type=sequence_type,
            expand_5prime=expand_5prime,
            expand_3prime=expand_3prime,
            start=start,
            end=end,
            mask=mask,
            mask_feature=mask_feature,
            multiple_sequences=multiple_sequences,
            content_type=content_type,
        )

    def get_sequence_batch(
        self,
        ids: List[str],
        sequence_type: str = "genomic",
        species: Optional[str] = None,
        format: str = "fasta",
    ) -> EnsemblFetchedData:
        """Get sequences for multiple Ensembl IDs in batch.

        Args:
            ids: List of Ensembl stable IDs (max 50).
            sequence_type: Type of sequence.
            species: Species name.
            format: Output format.

        Returns:
            EnsemblFetchedData with sequences.
        """
        content_type = "fasta" if format == "fasta" else "json"
        return self.get(
            endpoint=EnsemblEndpoint.sequence_id,
            ids=ids,
            species=species,
            sequence_type=sequence_type,
            content_type=content_type,
        )

    def get_sequence_region(
        self,
        species: str,
        region: str,
        expand_5prime: Optional[int] = None,
        expand_3prime: Optional[int] = None,
        mask: Optional[str] = None,
        coord_system: Optional[str] = None,
        format: str = "fasta",
    ) -> EnsemblFetchedData:
        """Get genomic sequence for a region.

        Args:
            species: Species name (e.g., "human").
            region: Genomic region (e.g., "X:1000000..1000100:1").
            expand_5prime: Extend upstream.
            expand_3prime: Extend downstream.
            mask: Mask repeats ("hard" or "soft").
            coord_system: Coordinate system filter.
            format: Output format ("fasta" or "json").

        Returns:
            EnsemblFetchedData with sequence.
        """
        content_type = "fasta" if format == "fasta" else "json"
        return self.get(
            endpoint=EnsemblEndpoint.sequence_region,
            species=species,
            region=region,
            expand_5prime=expand_5prime,
            expand_3prime=expand_3prime,
            mask=mask,
            coord_system=coord_system,
            content_type=content_type,
        )

    # =========================================================================
    # Overlap Methods
    # =========================================================================

    def get_overlap_id(
        self,
        id: str,
        feature: Union[str, List[str]],
        species: Optional[str] = None,
        biotype: Optional[str] = None,
        logic_name: Optional[str] = None,
        db_type: str = "core",
    ) -> EnsemblFetchedData:
        """Get features overlapping an Ensembl ID.

        Args:
            id: Ensembl stable ID.
            feature: Feature type(s) to retrieve (gene, transcript, exon, etc.).
            species: Species name.
            biotype: Filter by biotype (e.g., "protein_coding").
            logic_name: Filter by analysis logic name.
            db_type: Database type.

        Returns:
            EnsemblFetchedData with overlapping features.
        """
        return self.get(
            endpoint=EnsemblEndpoint.overlap_id,
            id=id,
            feature=feature,
            species=species,
            biotype=biotype,
            logic_name=logic_name,
            db_type=db_type,
        )

    def get_overlap_region(
        self,
        species: str,
        region: str,
        feature: Union[str, List[str]],
        biotype: Optional[str] = None,
        logic_name: Optional[str] = None,
        so_term: Optional[str] = None,
        variant_set: Optional[str] = None,
        db_type: str = "core",
    ) -> EnsemblFetchedData:
        """Get features overlapping a genomic region.

        Args:
            species: Species name (e.g., "human").
            region: Genomic region (e.g., "7:140424943-140624564", max 5Mb).
            feature: Feature type(s) to retrieve.
            biotype: Filter by biotype.
            logic_name: Filter by analysis logic name.
            so_term: Sequence Ontology term filter.
            variant_set: Variant set restriction (e.g., "ClinVar").
            db_type: Database type.

        Returns:
            EnsemblFetchedData with overlapping features.
        """
        return self.get(
            endpoint=EnsemblEndpoint.overlap_region,
            species=species,
            region=region,
            feature=feature,
            biotype=biotype,
            logic_name=logic_name,
            so_term=so_term,
            variant_set=variant_set,
            db_type=db_type,
        )

    # =========================================================================
    # Cross Reference Methods
    # =========================================================================

    def get_xrefs(
        self,
        id: str,
        species: Optional[str] = None,
        external_db: Optional[str] = None,
        all_levels: bool = False,
        db_type: str = "core",
        object_type: Optional[str] = None,
    ) -> EnsemblFetchedData:
        """Get external cross-references for an Ensembl ID.

        Args:
            id: Ensembl stable ID.
            species: Species name.
            external_db: Filter by external database (e.g., "HGNC", "UniProt").
            all_levels: Find all linked features.
            db_type: Database type.
            object_type: Filter by feature type.

        Returns:
            EnsemblFetchedData with cross-references.
        """
        return self.get(
            endpoint=EnsemblEndpoint.xrefs_id,
            id=id,
            species=species,
            external_db=external_db,
            all_levels=all_levels,
            db_type=db_type,
            object_type=object_type,
        )

    def get_xrefs_symbol(
        self,
        species: str,
        symbol: str,
        external_db: Optional[str] = None,
        db_type: str = "core",
        object_type: Optional[str] = None,
    ) -> EnsemblFetchedData:
        """Look up Ensembl objects by external symbol.

        Args:
            species: Species name.
            symbol: External symbol (e.g., gene name "BRCA2").
            external_db: Filter by external database.
            db_type: Database type.
            object_type: Filter by feature type.

        Returns:
            EnsemblFetchedData with matching Ensembl objects.
        """
        return self.get(
            endpoint=EnsemblEndpoint.xrefs_symbol,
            species=species,
            symbol=symbol,
            external_db=external_db,
            db_type=db_type,
            object_type=object_type,
        )

    # =========================================================================
    # Homology Methods
    # =========================================================================

    def get_homology(
        self,
        species: str,
        id: str,
        homology_type: str = "all",
        target_species: Optional[str] = None,
        target_taxon: Optional[int] = None,
        aligned: bool = True,
        cigar_line: bool = True,
        sequence: str = "protein",
        compara: str = "vertebrates",
        format: str = "full",
    ) -> EnsemblFetchedData:
        """Get homology information for a gene.

        Args:
            species: Source species name.
            id: Ensembl gene ID.
            homology_type: Type of homology ("orthologues", "paralogues", "all").
            target_species: Filter by target species.
            target_taxon: Filter by target taxon ID.
            aligned: Include aligned sequences.
            cigar_line: Return sequence in CIGAR format.
            sequence: Sequence type ("none", "cdna", "protein").
            compara: Compara database name.
            format: Response format ("full" or "condensed").

        Returns:
            EnsemblFetchedData with homology data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.homology_id,
            species=species,
            id=id,
            homology_type=homology_type,
            target_species=target_species,
            target_taxon=target_taxon,
            aligned=aligned,
            cigar_line=cigar_line,
            sequence=sequence,
            compara=compara,
            format=format,
        )

    def get_homology_symbol(
        self,
        species: str,
        symbol: str,
        homology_type: str = "all",
        target_species: Optional[str] = None,
        sequence: str = "protein",
    ) -> EnsemblFetchedData:
        """Get homology information for a gene by symbol.

        Args:
            species: Source species name.
            symbol: Gene symbol.
            homology_type: Type of homology.
            target_species: Filter by target species.
            sequence: Sequence type.

        Returns:
            EnsemblFetchedData with homology data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.homology_symbol,
            species=species,
            symbol=symbol,
            homology_type=homology_type,
            target_species=target_species,
            sequence=sequence,
        )

    # =========================================================================
    # Variation Methods
    # =========================================================================

    def get_variation(
        self,
        species: str,
        id: str,
        genotypes: bool = False,
        pops: bool = False,
        population_genotypes: bool = False,
        phenotypes: bool = False,
        genotyping_chips: bool = False,
    ) -> EnsemblFetchedData:
        """Get variant information by rsID.

        Args:
            species: Species name.
            id: Variant ID (e.g., "rs56116432").
            genotypes: Include individual genotypes.
            pops: Include population allele frequencies.
            population_genotypes: Include population genotype frequencies.
            phenotypes: Include phenotypes.
            genotyping_chips: Include genotyping chip info.

        Returns:
            EnsemblFetchedData with variant data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.variation,
            species=species,
            id=id,
            genotypes=genotypes,
            pops=pops,
            population_genotypes=population_genotypes,
            phenotypes=phenotypes,
            genotyping_chips=genotyping_chips,
        )

    # =========================================================================
    # VEP (Variant Effect Predictor) Methods
    # =========================================================================

    def get_vep_hgvs(
        self,
        species: str,
        hgvs_notation: str,
        canonical: bool = False,
        domains: bool = False,
        hgvs: bool = False,
        numbers: bool = False,
        protein: bool = False,
        refseq: bool = False,
        variant_class: bool = False,
    ) -> EnsemblFetchedData:
        """Get variant consequences using HGVS notation.

        Args:
            species: Species name.
            hgvs_notation: HGVS notation (e.g., "ENST00000366667:c.803C>T").
            canonical: Only return canonical transcript.
            domains: Include protein domains.
            hgvs: Add HGVS nomenclature.
            numbers: Include exon/intron numbers.
            protein: Include protein position and amino acid changes.
            refseq: Include RefSeq transcripts.
            variant_class: Include variant class.

        Returns:
            EnsemblFetchedData with VEP results.
        """
        return self.get(
            endpoint=EnsemblEndpoint.vep_hgvs,
            species=species,
            hgvs_notation=hgvs_notation,
            canonical=canonical,
            domains=domains,
            hgvs=hgvs,
            numbers=numbers,
            protein=protein,
            refseq=refseq,
            variant_class=variant_class,
        )

    def get_vep_id(
        self,
        species: str,
        id: str,
        canonical: bool = False,
        domains: bool = False,
        hgvs: bool = False,
        numbers: bool = False,
        protein: bool = False,
    ) -> EnsemblFetchedData:
        """Get variant consequences using variant ID.

        Args:
            species: Species name.
            id: Variant ID (e.g., rsID).
            canonical: Only return canonical transcript.
            domains: Include protein domains.
            hgvs: Add HGVS nomenclature.
            numbers: Include exon/intron numbers.
            protein: Include protein position.

        Returns:
            EnsemblFetchedData with VEP results.
        """
        return self.get(
            endpoint=EnsemblEndpoint.vep_id,
            species=species,
            id=id,
            canonical=canonical,
            domains=domains,
            hgvs=hgvs,
            numbers=numbers,
            protein=protein,
        )

    def get_vep_region(
        self,
        species: str,
        region: str,
        allele: str,
        canonical: bool = False,
        domains: bool = False,
        hgvs: bool = False,
        numbers: bool = False,
        protein: bool = False,
    ) -> EnsemblFetchedData:
        """Get variant consequences using genomic coordinates.

        Args:
            species: Species name.
            region: Genomic region (e.g., "9:22125503-22125502:1").
            allele: Variant allele (e.g., "C", "DUP").
            canonical: Only return canonical transcript.
            domains: Include protein domains.
            hgvs: Add HGVS nomenclature.
            numbers: Include exon/intron numbers.
            protein: Include protein position.

        Returns:
            EnsemblFetchedData with VEP results.
        """
        return self.get(
            endpoint=EnsemblEndpoint.vep_region,
            species=species,
            region=region,
            allele=allele,
            canonical=canonical,
            domains=domains,
            hgvs=hgvs,
            numbers=numbers,
            protein=protein,
        )

    # =========================================================================
    # Mapping Methods
    # =========================================================================

    def map_assembly(
        self,
        species: str,
        asm_one: str,
        region: str,
        asm_two: str,
        coord_system: str = "chromosome",
        target_coord_system: str = "chromosome",
    ) -> EnsemblFetchedData:
        """Map coordinates between assemblies.

        Args:
            species: Species name.
            asm_one: Source assembly version (e.g., "GRCh37").
            region: Genomic region to map (e.g., "X:1000000..1000100:1").
            asm_two: Target assembly version (e.g., "GRCh38").
            coord_system: Input coordinate system.
            target_coord_system: Output coordinate system.

        Returns:
            EnsemblFetchedData with mapped coordinates.
        """
        return self.get(
            endpoint=EnsemblEndpoint.map_assembly,
            species=species,
            asm_one=asm_one,
            region=region,
            asm_two=asm_two,
            coord_system=coord_system,
            target_coord_system=target_coord_system,
        )

    # =========================================================================
    # Phenotype Methods
    # =========================================================================

    def get_phenotype_gene(
        self,
        species: str,
        gene: str,
        include_associated: bool = False,
        include_overlap: bool = False,
        include_pubmed_id: bool = False,
        include_review_status: bool = False,
        include_submitter: bool = False,
    ) -> EnsemblFetchedData:
        """Get phenotypes associated with a gene.

        Args:
            species: Species name.
            gene: Gene name or Ensembl ID.
            include_associated: Include phenotypes from associated variants.
            include_overlap: Include phenotypes from overlapping features.
            include_pubmed_id: Include PubMed IDs.
            include_review_status: Include review status.
            include_submitter: Include submitter names.

        Returns:
            EnsemblFetchedData with phenotype data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.phenotype_gene,
            species=species,
            gene=gene,
            include_associated=include_associated,
            include_overlap=include_overlap,
            include_pubmed_id=include_pubmed_id,
            include_review_status=include_review_status,
            include_submitter=include_submitter,
        )

    def get_phenotype_region(
        self,
        species: str,
        region: str,
        include_pubmed_id: bool = False,
        include_review_status: bool = False,
    ) -> EnsemblFetchedData:
        """Get phenotypes in a genomic region.

        Args:
            species: Species name.
            region: Genomic region.
            include_pubmed_id: Include PubMed IDs.
            include_review_status: Include review status.

        Returns:
            EnsemblFetchedData with phenotype data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.phenotype_region,
            species=species,
            region=region,
            include_pubmed_id=include_pubmed_id,
            include_review_status=include_review_status,
        )

    # =========================================================================
    # Ontology Methods
    # =========================================================================

    def get_ontology_term(
        self,
        id: str,
        relation: Optional[str] = None,
        simple: bool = False,
    ) -> EnsemblFetchedData:
        """Get ontology term information.

        Args:
            id: Ontology term ID (e.g., "GO:0005667").
            relation: Relationship types to include.
            simple: Don't fetch parent/child terms.

        Returns:
            EnsemblFetchedData with ontology term data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.ontology_id,
            id=id,
            relation=relation,
            simple=simple,
        )

    def get_ontology_ancestors(
        self,
        id: str,
        ontology: Optional[str] = None,
        zero_distance: bool = False,
    ) -> EnsemblFetchedData:
        """Get ancestor terms for an ontology term.

        Args:
            id: Ontology term ID.
            ontology: Filter by ontology.
            zero_distance: Include the term itself.

        Returns:
            EnsemblFetchedData with ancestor terms.
        """
        return self.get(
            endpoint=EnsemblEndpoint.ontology_ancestors,
            id=id,
            ontology=ontology,
            zero_distance=zero_distance,
        )

    def get_ontology_descendants(
        self,
        id: str,
        ontology: Optional[str] = None,
        zero_distance: bool = False,
        subset: Optional[str] = None,
    ) -> EnsemblFetchedData:
        """Get descendant terms for an ontology term.

        Args:
            id: Ontology term ID.
            ontology: Filter by ontology.
            zero_distance: Include the term itself.
            subset: Filter by subset.

        Returns:
            EnsemblFetchedData with descendant terms.
        """
        return self.get(
            endpoint=EnsemblEndpoint.ontology_descendants,
            id=id,
            ontology=ontology,
            zero_distance=zero_distance,
            subset=subset,
        )

    # =========================================================================
    # Gene Tree Methods
    # =========================================================================

    def get_genetree(
        self,
        id: str,
        aligned: bool = False,
        cigar_line: bool = False,
        sequence: str = "protein",
        nh_format: str = "simple",
        prune_species: Optional[str] = None,
        prune_taxon: Optional[int] = None,
        clusterset_id: Optional[str] = None,
        compara: str = "vertebrates",
    ) -> EnsemblFetchedData:
        """Get gene tree by tree ID.

        Args:
            id: Gene tree ID (e.g., "ENSGT00390000003602").
            aligned: Include aligned sequences.
            cigar_line: Return sequence in CIGAR format.
            sequence: Sequence type ("none", "cdna", "protein").
            nh_format: Newick format type.
            prune_species: Filter by species.
            prune_taxon: Filter by taxon ID.
            clusterset_id: Gene-tree resource name.
            compara: Compara database name.

        Returns:
            EnsemblFetchedData with gene tree data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.genetree_id,
            id=id,
            aligned=aligned,
            cigar_line=cigar_line,
            sequence=sequence,
            nh_format=nh_format,
            prune_species=prune_species,
            prune_taxon=prune_taxon,
            clusterset_id=clusterset_id,
            compara=compara,
        )

    def get_genetree_member(
        self,
        species: str,
        id: str,
        aligned: bool = False,
        sequence: str = "protein",
        compara: str = "vertebrates",
    ) -> EnsemblFetchedData:
        """Get gene tree containing a gene ID.

        Args:
            species: Species name.
            id: Ensembl gene ID.
            aligned: Include aligned sequences.
            sequence: Sequence type.
            compara: Compara database name.

        Returns:
            EnsemblFetchedData with gene tree data.
        """
        return self.get(
            endpoint=EnsemblEndpoint.genetree_member_id,
            species=species,
            id=id,
            aligned=aligned,
            sequence=sequence,
            compara=compara,
        )

    # =========================================================================
    # Information Methods
    # =========================================================================

    def get_assembly_info(
        self,
        species: str,
        bands: bool = False,
        synonyms: bool = False,
    ) -> EnsemblFetchedData:
        """Get assembly information for a species.

        Args:
            species: Species name.
            bands: Include karyotype band information.
            synonyms: Include known synonyms.

        Returns:
            EnsemblFetchedData with assembly information.
        """
        # Note: bands and synonyms are query params for this endpoint
        return self.get(
            endpoint=EnsemblEndpoint.info_assembly,
            species=species,
        )

    def get_species_info(
        self,
        division: Optional[str] = None,
        strain_collection: Optional[str] = None,
        hide_strain_info: bool = False,
    ) -> EnsemblFetchedData:
        """Get information about available species.

        Args:
            division: Filter by Ensembl division.
            strain_collection: Filter by strain collection.
            hide_strain_info: Hide strain information.

        Returns:
            EnsemblFetchedData with species information.
        """
        return self.get(
            endpoint=EnsemblEndpoint.info_species,
            division=division,
            strain_collection=strain_collection,
            hide_strain_info=hide_strain_info,
        )


if __name__ == "__main__":
    fetcher = Ensembl_Fetcher()

    # Test lookup
    print("=== Lookup TP53 ===")
    gene = fetcher.lookup("ENSG00000141510", expand=True)
    print(f"Gene: {gene.results[0].get('display_name')}")
    print(f"Biotype: {gene.results[0].get('biotype')}")

    # Test sequence
    print("\n=== Get CDS Sequence ===")
    seq = fetcher.get_sequence("ENST00000269305", sequence_type="cds")
    print(f"Sequence length: {len(seq.text)} characters")

    # Test xrefs
    print("\n=== Cross References ===")
    xrefs = fetcher.get_xrefs("ENSG00000141510", external_db="HGNC")
    print(f"Found {len(xrefs)} cross-references")

    # Test variation
    print("\n=== Variant Info ===")
    var = fetcher.get_variation("human", "rs56116432")
    print(f"Variant: {var.results[0].get('name', 'N/A')}")
