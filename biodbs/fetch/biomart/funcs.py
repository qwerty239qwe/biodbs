"""Convenience functions for BioMart/Ensembl data fetching."""

from typing import List, Optional, Union, Dict
import pandas as pd
from biodbs.fetch.biomart.biomart_fetcher import BioMart_Fetcher
from biodbs.data.BioMart import BioMartHost
from biodbs.data.BioMart.data import BioMartQueryData, BioMartDatasetsData

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
) -> BioMartQueryData:
    """Get gene information by Ensembl gene IDs.

    Args:
        ids (List[str]): List of Ensembl gene IDs (e.g., ["ENSG00000141510"]).
        attributes (Optional[List[str]]): Attributes to retrieve. If None, uses common gene attributes.
        dataset (str): BioMart dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData containing gene information including
        gene ID, symbol, description, and coordinates.

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
) -> BioMartQueryData:
    """Get gene information by gene names/symbols.

    Args:
        names (List[str]): List of gene names/symbols (e.g., ["TP53", "BRCA1"]).
        attributes (Optional[List[str]]): Attributes to retrieve.
        dataset (str): BioMart dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData containing gene information.

    Example:
        >>> data = biomart_get_genes_by_name(["TP53", "BRCA1", "EGFR"])
        >>> df = data.as_dataframe()
        >>> print(df[["external_gene_name", "ensembl_gene_id"]].head())
    """
    return _get_fetcher().get_genes_by_name(names, attributes, dataset)


def biomart_get_genes_by_region(
    chromosome: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    attributes: Optional[List[str]] = None,
    dataset: str = "hsapiens_gene_ensembl",
) -> BioMartQueryData:
    """Get genes in a genomic region.

    Args:
        chromosome (str): Chromosome name (e.g., "17", "X").
        start (Optional[int]): Start position in base pairs.
        end (Optional[int]): End position in base pairs.
        attributes (Optional[List[str]]): Attributes to retrieve.
        dataset (str): BioMart dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData containing genes within the specified region.

    Example:
        >>> data = biomart_get_genes_by_region("17", 7661779, 7687550)  # TP53 region
        >>> df = data.as_dataframe()
        >>> print(df[["ensembl_gene_id", "external_gene_name"]].head())
    """
    return _get_fetcher().get_genes_by_chromosome(
        chromosome, start, end, attributes, dataset
    )


def biomart_get_transcripts(
    gene_ids: List[str],
    attributes: Optional[List[str]] = None,
    dataset: str = "hsapiens_gene_ensembl",
) -> BioMartQueryData:
    """Get transcript information for genes.

    Args:
        gene_ids (List[str]): List of Ensembl gene IDs.
        attributes (Optional[List[str]]): Attributes to retrieve.
        dataset (str): BioMart dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData containing transcript information
        including transcript ID, biotype, and coordinates.

    Example:
        >>> data = biomart_get_transcripts(["ENSG00000141510"])
        >>> df = data.as_dataframe()
        >>> print(df[["ensembl_gene_id", "ensembl_transcript_id", "transcript_biotype"]])
    """
    return _get_fetcher().get_transcripts(gene_ids, attributes, dataset)


def biomart_get_go_annotations(
    gene_ids: List[str],
    dataset: str = "hsapiens_gene_ensembl",
) -> BioMartQueryData:
    """Get Gene Ontology annotations for genes.

    Args:
        gene_ids (List[str]): List of Ensembl gene IDs.
        dataset (str): BioMart dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData containing GO annotations
        with GO term IDs, names, and evidence codes.

    Example:
        >>> data = biomart_get_go_annotations(["ENSG00000141510"])
        >>> df = data.as_dataframe()
        >>> print(df[["ensembl_gene_id", "go_id", "name_1006"]].head())
    """
    return _get_fetcher().get_go_annotations(gene_ids, dataset)


def biomart_get_homologs(
    gene_ids: List[str],
    target_species: str = "mmusculus",
    dataset: str = "hsapiens_gene_ensembl",
) -> BioMartQueryData:
    """Get homolog information for genes.

    Args:
        gene_ids (List[str]): List of Ensembl gene IDs.
        target_species (str): Target species for homologs (e.g., "mmusculus" for mouse).
        dataset (str): BioMart dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData containing homolog information
        with ortholog IDs and homology types.

    Example:
        >>> data = biomart_get_homologs(["ENSG00000141510"], target_species="mmusculus")
        >>> df = data.as_dataframe()
        >>> print(df[["ensembl_gene_id", "mmusculus_homolog_ensembl_gene"]].head())
    """
    return _get_fetcher().get_homologs(gene_ids, target_species, dataset)


def biomart_convert_ids(
    ids: List[str],
    from_type: str = "ensembl_gene_id",
    to_type: str = "external_gene_name",
    dataset: str = "hsapiens_gene_ensembl",
) -> BioMartQueryData:
    """Convert between different gene ID types.

    Supported ID types:
        - ensembl_gene_id, ensembl_transcript_id, ensembl_peptide_id
        - external_gene_name, hgnc_symbol, hgnc_id
        - entrezgene_id, uniprot_gn_id
        - refseq_mrna, refseq_peptide

    Args:
        ids (List[str]): List of IDs to convert.
        from_type (str): Source ID type (used as filter).
        to_type (str): Target ID type.
        dataset (str): BioMart dataset name. Defaults to human genes.

    Returns:
        BioMartQueryData containing ID mappings with
        both source and target ID columns.

    Example:
        >>> data = biomart_convert_ids(
        ...     ["TP53", "BRCA1"],
        ...     from_type="external_gene_name",
        ...     to_type="ensembl_gene_id"
        ... )
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().convert_ids(ids, from_type, to_type, dataset)


def biomart_query(
    dataset: str = "hsapiens_gene_ensembl",
    attributes: Optional[List[str]] = None,
    filters: Optional[Dict[str, Union[str, List[str]]]] = None,
) -> BioMartQueryData:
    """Execute a custom BioMart query.

    Args:
        dataset (str): BioMart dataset name.
        attributes (Optional[List[str]]): List of attributes to retrieve.
        filters (Optional[Dict[str, Union[str, List[str]]]]): Dict of filter name to value(s).

    Returns:
        BioMartQueryData containing query results.

    Example:
        >>> data = biomart_query(
        ...     dataset="hsapiens_gene_ensembl",
        ...     attributes=["ensembl_gene_id", "external_gene_name", "chromosome_name"],
        ...     filters={"chromosome_name": "22", "biotype": "protein_coding"}
        ... )
        >>> df = data.as_dataframe()
    """
    return _get_fetcher().query(dataset, attributes, filters)


def biomart_list_datasets(mart: str = "ENSEMBL_MART_ENSEMBL") -> BioMartDatasetsData:
    """List available datasets in a BioMart mart.

    Args:
        mart (str): Mart name. Defaults to the main Ensembl mart.

    Returns:
        BioMartDatasetsData containing available datasets
        with names, descriptions, and versions.

    Example:
        >>> data = biomart_list_datasets()
        >>> human = data.search(contain="sapiens")
        >>> print(human)
    """
    return _get_fetcher().list_datasets(mart)


def biomart_list_attributes(
    dataset: str = "hsapiens_gene_ensembl",
    contain: Optional[str] = None,
) -> pd.DataFrame:
    """List available attributes for a BioMart dataset.

    Args:
        dataset (str): BioMart dataset name.
        contain (Optional[str]): If provided, filter to attributes containing this string.

    Returns:
        DataFrame containing attribute names, descriptions, and pages.

    Example:
        >>> attrs = biomart_list_attributes("hsapiens_gene_ensembl", contain="gene")
        >>> print(attrs.head())
    """
    return _get_fetcher().list_attributes(dataset, contain=contain)


def biomart_list_filters(
    dataset: str = "hsapiens_gene_ensembl",
    contain: Optional[str] = None,
) -> pd.DataFrame:
    """List available filters for a BioMart dataset.

    Args:
        dataset (str): BioMart dataset name.
        contain (Optional[str]): If provided, filter to filters containing this string.

    Returns:
        DataFrame containing filter names, descriptions, and types.

    Example:
        >>> filters = biomart_list_filters("hsapiens_gene_ensembl", contain="chromosome")
        >>> print(filters.head())
    """
    return _get_fetcher().list_filters(dataset, contain=contain)
