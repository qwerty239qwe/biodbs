"""Convenience functions for BioMart/Ensembl data fetching."""

from typing import List, Optional, Union, Dict
from biodbs.fetch.biomart.biomart_fetcher import BioMart_Fetcher
from biodbs.data.BioMart import BioMartHost, BioMartDataset

# Module-level fetcher instance (lazy initialization)
_fetcher: Optional[BioMart_Fetcher] = None


def _get_fetcher(host: Optional[str] = None) -> BioMart_Fetcher:
    """Get or create the module-level fetcher instance."""
    global _fetcher
    if _fetcher is None or (host is not None and _fetcher.host != host):
        _fetcher = BioMart_Fetcher(host=host or BioMartHost.main)
    return _fetcher


def biomart_get_genes(
    ids: List[str],
    attributes: Optional[List[str]] = None,
    dataset: str = "hsapiens_gene_ensembl",
):
    """Get gene information by Ensembl gene IDs.

    Args:
        ids: List of Ensembl gene IDs (e.g., ["ENSG00000141510"]).
        attributes: Attributes to retrieve. Defaults to common gene attributes.
        dataset: Dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData with gene information.

    Example:
        >>> data = biomart_get_genes(["ENSG00000141510", "ENSG00000012048"])
        >>> df = data.as_dataframe()
        >>> print(df[["ensembl_gene_id", "external_gene_name"]])
    """
    return _get_fetcher().get_genes(ids, attributes, dataset)


def biomart_get_genes_by_name(
    names: List[str],
    attributes: Optional[List[str]] = None,
    dataset: str = "hsapiens_gene_ensembl",
):
    """Get gene information by gene names/symbols.

    Args:
        names: List of gene names (e.g., ["TP53", "BRCA1"]).
        attributes: Attributes to retrieve.
        dataset: Dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData with gene information.

    Example:
        >>> data = biomart_get_genes_by_name(["TP53", "BRCA1", "EGFR"])
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_genes_by_name(names, attributes, dataset)


def biomart_get_genes_by_region(
    chromosome: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    attributes: Optional[List[str]] = None,
    dataset: str = "hsapiens_gene_ensembl",
):
    """Get genes in a genomic region.

    Args:
        chromosome: Chromosome name (e.g., "17", "X").
        start: Start position (optional).
        end: End position (optional).
        attributes: Attributes to retrieve.
        dataset: Dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData with genes in the region.

    Example:
        >>> data = biomart_get_genes_by_region("17", 7661779, 7687550)  # TP53 region
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_genes_by_chromosome(
        chromosome, start, end, attributes, dataset
    )


def biomart_get_transcripts(
    gene_ids: List[str],
    attributes: Optional[List[str]] = None,
    dataset: str = "hsapiens_gene_ensembl",
):
    """Get transcript information for genes.

    Args:
        gene_ids: List of Ensembl gene IDs.
        attributes: Attributes to retrieve.
        dataset: Dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData with transcript information.

    Example:
        >>> data = biomart_get_transcripts(["ENSG00000141510"])
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_transcripts(gene_ids, attributes, dataset)


def biomart_get_go_annotations(
    gene_ids: List[str],
    dataset: str = "hsapiens_gene_ensembl",
):
    """Get Gene Ontology annotations for genes.

    Args:
        gene_ids: List of Ensembl gene IDs.
        dataset: Dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData with GO annotations.

    Example:
        >>> data = biomart_get_go_annotations(["ENSG00000141510"])
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_go_annotations(gene_ids, dataset)


def biomart_get_homologs(
    gene_ids: List[str],
    target_species: str = "mmusculus",
    dataset: str = "hsapiens_gene_ensembl",
):
    """Get homolog information for genes.

    Args:
        gene_ids: List of Ensembl gene IDs.
        target_species: Target species for homologs (e.g., "mmusculus").
        dataset: Dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData with homolog information.

    Example:
        >>> data = biomart_get_homologs(["ENSG00000141510"], target_species="mmusculus")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().get_homologs(gene_ids, target_species, dataset)


def biomart_convert_ids(
    ids: List[str],
    from_type: str = "ensembl_gene_id",
    to_type: str = "external_gene_name",
    dataset: str = "hsapiens_gene_ensembl",
):
    """Convert between different gene ID types.

    Common ID types:
    - ensembl_gene_id, ensembl_transcript_id, ensembl_peptide_id
    - external_gene_name, hgnc_symbol, hgnc_id
    - entrezgene_id, uniprot_gn_id
    - refseq_mrna, refseq_peptide

    Args:
        ids: List of IDs to convert.
        from_type: Source ID type (also used as filter).
        to_type: Target ID type.
        dataset: Dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData with ID mappings.

    Example:
        >>> data = biomart_convert_ids(["TP53", "BRCA1"], from_type="external_gene_name", to_type="ensembl_gene_id")
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().convert_ids(ids, from_type, to_type, dataset)


def biomart_query(
    dataset: str = "hsapiens_gene_ensembl",
    attributes: Optional[List[str]] = None,
    filters: Optional[Dict[str, Union[str, List[str]]]] = None,
):
    """Execute a custom BioMart query.

    Args:
        dataset: Dataset name.
        attributes: List of attributes to retrieve.
        filters: Dict of filter name to value(s).

    Returns:
        BioMartQueryData with query results.

    Example:
        >>> data = biomart_query(
        ...     dataset="hsapiens_gene_ensembl",
        ...     attributes=["ensembl_gene_id", "external_gene_name", "chromosome_name"],
        ...     filters={"chromosome_name": "22", "biotype": "protein_coding"}
        ... )
    """
    return _get_fetcher().query(dataset, attributes, filters)


def biomart_list_datasets(mart: str = "ENSEMBL_MART_ENSEMBL"):
    """List available datasets in a mart.

    Args:
        mart: Mart name. Defaults to the main Ensembl mart.

    Returns:
        BioMartDatasetsData with dataset information.

    Example:
        >>> data = biomart_list_datasets()
        >>> human = data.search(contain="sapiens")
    """
    return _get_fetcher().list_datasets(mart)


def biomart_list_attributes(dataset: str = "hsapiens_gene_ensembl", contain: Optional[str] = None):
    """List available attributes for a dataset.

    Args:
        dataset: Dataset name.
        contain: Filter attributes containing this string.

    Returns:
        DataFrame with attribute information.

    Example:
        >>> attrs = biomart_list_attributes("hsapiens_gene_ensembl", contain="gene")
    """
    return _get_fetcher().list_attributes(dataset, contain=contain)


def biomart_list_filters(dataset: str = "hsapiens_gene_ensembl", contain: Optional[str] = None):
    """List available filters for a dataset.

    Args:
        dataset: Dataset name.
        contain: Filter filters containing this string.

    Returns:
        DataFrame with filter information.

    Example:
        >>> filters = biomart_list_filters("hsapiens_gene_ensembl", contain="chromosome")
    """
    return _get_fetcher().list_filters(dataset, contain=contain)
