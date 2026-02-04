"""Convenience functions for NCBI Datasets API."""

from typing import List, Dict, Union, Optional
import pandas as pd

from biodbs.fetch.NCBI.ncbi_fetcher import NCBI_Fetcher
from biodbs.data.NCBI.data import NCBIGeneFetchedData, NCBITaxonomyFetchedData


def ncbi_get_gene(
    identifiers: List[Union[int, str]],
    taxon: Union[int, str] = "human",
    api_key: Optional[str] = None,
) -> NCBIGeneFetchedData:
    """Get gene information from NCBI by gene IDs or symbols.

    This is a convenience function that wraps the NCBI_Fetcher.

    Args:
        identifiers: List of NCBI Gene IDs (integers) or gene symbols (strings).
        taxon: Taxonomy ID or name (used for symbol lookups).
        api_key: Optional NCBI API key for higher rate limits.

    Returns:
        NCBIGeneFetchedData containing gene reports.

    Examples:
        >>> # By gene IDs
        >>> genes = ncbi_get_gene([7157, 672])
        >>> print(genes.as_dataframe())

        >>> # By symbols
        >>> genes = ncbi_get_gene(["TP53", "BRCA1"], taxon="human")
        >>> print(genes.get_gene_ids())
    """
    fetcher = NCBI_Fetcher(api_key=api_key)
    return fetcher.get_gene_info(identifiers, taxon=taxon)


def ncbi_symbol_to_id(
    symbols: List[str],
    taxon: Union[int, str] = "human",
    api_key: Optional[str] = None,
    return_dict: bool = True,
) -> Union[Dict[str, int], "pd.DataFrame"]:
    """Convert gene symbols to NCBI Gene IDs.

    Args:
        symbols: List of gene symbols.
        taxon: Taxonomy ID or name.
        api_key: Optional NCBI API key.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary mapping symbols to gene IDs, or DataFrame.

    Example:
        >>> mapping = ncbi_symbol_to_id(["TP53", "BRCA1", "EGFR"])
        >>> print(mapping)
        {'TP53': 7157, 'BRCA1': 672, 'EGFR': 1956}
    """
    fetcher = NCBI_Fetcher(api_key=api_key)
    genes = fetcher.get_genes_by_symbol(symbols, taxon=taxon)

    if return_dict:
        return genes.to_id_mapping()

    # Return as DataFrame
    mapping = genes.to_id_mapping()
    records = [{"symbol": sym, "gene_id": gid} for sym, gid in mapping.items()]
    return pd.DataFrame(records)


def ncbi_id_to_symbol(
    gene_ids: List[int],
    api_key: Optional[str] = None,
    return_dict: bool = True,
) -> Union[Dict[int, str], "pd.DataFrame"]:
    """Convert NCBI Gene IDs to gene symbols.

    Args:
        gene_ids: List of NCBI Gene IDs.
        api_key: Optional NCBI API key.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dictionary mapping gene IDs to symbols, or DataFrame.

    Example:
        >>> mapping = ncbi_id_to_symbol([7157, 672, 1956])
        >>> print(mapping)
        {7157: 'TP53', 672: 'BRCA1', 1956: 'EGFR'}
    """
    fetcher = NCBI_Fetcher(api_key=api_key)
    genes = fetcher.get_genes_by_id(gene_ids)

    if return_dict:
        return genes.to_symbol_mapping()

    # Return as DataFrame
    mapping = genes.to_symbol_mapping()
    records = [{"gene_id": gid, "symbol": sym} for gid, sym in mapping.items()]
    return pd.DataFrame(records)


def ncbi_get_taxonomy(
    taxons: List[Union[int, str]],
    api_key: Optional[str] = None,
) -> NCBITaxonomyFetchedData:
    """Get taxonomy information from NCBI.

    Args:
        taxons: List of taxonomy IDs or names.
        api_key: Optional NCBI API key.

    Returns:
        NCBITaxonomyFetchedData containing taxonomy reports.

    Example:
        >>> tax = ncbi_get_taxonomy([9606, 10090])
        >>> print(tax.as_dataframe())
    """
    fetcher = NCBI_Fetcher(api_key=api_key)
    return fetcher.get_taxonomy(taxons)


def ncbi_translate_gene_ids(
    ids: List[str],
    from_type: str,
    to_type: str,
    taxon: Union[int, str] = "human",
    api_key: Optional[str] = None,
    return_dict: bool = False,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene identifiers using NCBI.

    Supports translation between:
        - symbol: Gene symbol (e.g., "TP53")
        - entrez_id / gene_id: NCBI Gene ID (e.g., 7157)
        - refseq_accession: RefSeq accession (e.g., "NM_000546.6")

    Args:
        ids: List of identifiers to translate.
        from_type: Source identifier type.
        to_type: Target identifier type.
        taxon: Taxonomy for the genes.
        api_key: Optional NCBI API key.
        return_dict: If True, return dict mapping. If False, return DataFrame.

    Returns:
        Dictionary or DataFrame with translated identifiers.

    Example:
        >>> # Symbol to Gene ID
        >>> result = ncbi_translate_gene_ids(
        ...     ["TP53", "BRCA1"],
        ...     from_type="symbol",
        ...     to_type="entrez_id",
        ...     taxon="human"
        ... )
    """
    fetcher = NCBI_Fetcher(api_key=api_key)

    # Normalize type names
    from_type = from_type.lower().replace("-", "_")
    to_type = to_type.lower().replace("-", "_")

    # Handle different translation paths
    if from_type in ("symbol", "gene_symbol"):
        genes = fetcher.get_genes_by_symbol(ids, taxon=taxon)
    elif from_type in ("entrez_id", "gene_id", "ncbi_gene_id"):
        int_ids = [int(i) for i in ids]
        genes = fetcher.get_genes_by_id(int_ids)
    elif from_type in ("refseq_accession", "refseq"):
        genes = fetcher.get_genes_by_accession(ids)
    else:
        raise ValueError(f"Unsupported from_type: {from_type}")

    # Build result based on to_type
    results = []
    for gene in genes.genes:
        from_val = None
        to_val = None

        # Get from value
        if from_type in ("symbol", "gene_symbol"):
            from_val = gene.symbol
        elif from_type in ("entrez_id", "gene_id", "ncbi_gene_id"):
            from_val = str(gene.gene_id)
        elif from_type in ("refseq_accession", "refseq"):
            # Attempt to get from query
            for qid in ids:
                # Match by checking transcripts or just use first match
                from_val = qid
                break

        # Get to value
        if to_type in ("symbol", "gene_symbol"):
            to_val = gene.symbol
        elif to_type in ("entrez_id", "gene_id", "ncbi_gene_id"):
            to_val = str(gene.gene_id)
        elif to_type in ("ensembl_gene_id", "ensembl"):
            if gene.ensembl_gene_ids:
                to_val = gene.ensembl_gene_ids[0]
        elif to_type in ("uniprot", "swiss_prot"):
            if gene.swiss_prot_accessions:
                to_val = gene.swiss_prot_accessions[0]
        else:
            raise ValueError(f"Unsupported to_type: {to_type}")

        if from_val:
            results.append({from_type: from_val, to_type: to_val})

    if return_dict:
        return {r[from_type]: r[to_type] for r in results if r[to_type]}

    return pd.DataFrame(results)
