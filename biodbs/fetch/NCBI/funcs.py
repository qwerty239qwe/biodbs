"""Convenience functions for NCBI Datasets API."""

from pathlib import Path
from typing import List, Dict, Union, Optional
import pandas as pd

from biodbs.fetch.NCBI.ncbi_fetcher import NCBI_Fetcher
from biodbs.data.NCBI.data import NCBIGeneFetchedData, NCBITaxonomyFetchedData


def ncbi_download_blast_database(
    name: str,
    dest: Union[str, Path],
    overwrite: bool = False,
) -> Path:
    """Download a preformatted NCBI BLAST database archive (MD5-verified).

    Example:
        >>> ncbi_download_blast_database("16S_ribosomal_RNA", "data/ncbi")
    """
    return NCBI_Fetcher().download_blast_database(name, dest, overwrite)


def ncbi_download_taxdump(
    dest: Union[str, Path],
    overwrite: bool = False,
) -> Path:
    """Download NCBI's ``new_taxdump`` taxonomy archive (MD5-verified)."""
    return NCBI_Fetcher().download_taxdump(dest, overwrite)


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


def _ensembl_ids_to_ncbi(ensembl_ids: List[str]) -> Dict[str, int]:
    """Convert Ensembl Gene IDs to NCBI Gene IDs via NCBI E-utilities esearch.

    Uses the ``[Ensembl Gene ID]`` search field which is indexed for
    every gene that has a cross-reference to Ensembl.

    Args:
        ensembl_ids: List of Ensembl stable gene IDs (e.g. "ENSG00000141510").

    Returns:
        Dict mapping each Ensembl ID to its NCBI Gene ID (skips failures).
    """
    import requests as req

    result: Dict[str, int] = {}
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    for eid in ensembl_ids:
        try:
            r = req.get(
                url,
                params={
                    "db": "gene",
                    "term": f"{eid}[Ensembl Gene ID]",
                    "retmode": "json",
                    "retmax": "1",
                },
                timeout=15,
            )
            r.raise_for_status()
            id_list = r.json().get("esearchresult", {}).get("idlist", [])
            if id_list:
                result[eid] = int(id_list[0])
        except Exception:
            pass
    return result


def _extract_to_val(gene, to_type: str):
    """Extract the target field value from a GeneReport."""
    if to_type in ("symbol", "gene_symbol"):
        return gene.symbol
    if to_type in ("entrez_id", "gene_id", "ncbi_gene_id"):
        return str(gene.gene_id)
    if to_type in ("ensembl_gene_id", "ensembl"):
        return gene.ensembl_gene_ids[0] if gene.ensembl_gene_ids else None
    if to_type in ("uniprot", "swiss_prot", "uniprot_id"):
        return gene.swiss_prot_accessions[0] if gene.swiss_prot_accessions else None
    if to_type in ("refseq_accession", "refseq_mrna", "refseq"):
        if gene.transcripts:
            # Prefer NM_ mRNA transcripts
            for t in gene.transcripts:
                if t.accession_version and t.accession_version.startswith("NM_"):
                    return t.accession_version
            return gene.transcripts[0].accession_version
        return None
    raise ValueError(f"Unsupported to_type: {to_type}")


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
        - symbol / gene_symbol: Gene symbol (e.g., "TP53")
        - entrez_id / gene_id: NCBI Gene ID (e.g., "7157")
        - ensembl_gene_id: Ensembl stable gene ID (e.g., "ENSG00000141510")
        - refseq_accession / refseq_mrna: RefSeq accession (e.g., "NM_000546.6")
        - uniprot / uniprot_id: UniProt / Swiss-Prot accession (output only)

    Args:
        ids: List of identifiers to translate.
        from_type: Source identifier type.
        to_type: Target identifier type.
        taxon: Taxonomy for symbol-based lookups.
        api_key: Optional NCBI API key.
        return_dict: If True, return dict mapping. If False, return DataFrame.

    Returns:
        Dictionary or DataFrame with translated identifiers.

    Example:
        >>> result = ncbi_translate_gene_ids(
        ...     ["TP53", "BRCA1"],
        ...     from_type="symbol",
        ...     to_type="entrez_id",
        ...     taxon="human",
        ... )
    """
    fetcher = NCBI_Fetcher(api_key=api_key)

    # Normalize type names
    from_type = from_type.lower().replace("-", "_")
    to_type = to_type.lower().replace("-", "_")

    # ── Ensembl Gene ID as from_type ─────────────────────────────────────────
    # The NCBI Datasets API has no direct Ensembl-input endpoint; we resolve
    # Ensembl → NCBI Gene ID first via the E-utilities esearch index.
    if from_type in ("ensembl_gene_id", "ensembl"):
        ensembl_to_ncbi = _ensembl_ids_to_ncbi(ids)
        ncbi_to_ensembl = {v: k for k, v in ensembl_to_ncbi.items()}
        int_ids = list(ensembl_to_ncbi.values())
        if not int_ids:
            empty = pd.DataFrame(columns=[from_type, to_type])
            return {} if return_dict else empty
        genes = fetcher.get_genes_by_id(int_ids)
        results = []
        for gene in genes.genes:
            from_val = ncbi_to_ensembl.get(gene.gene_id)
            if from_val is None:
                continue
            try:
                to_val = _extract_to_val(gene, to_type)
            except ValueError as e:
                raise e
            results.append({from_type: from_val, to_type: to_val})
        if return_dict:
            return {r[from_type]: r[to_type] for r in results if r[to_type]}
        return pd.DataFrame(results)

    # ── Standard paths ────────────────────────────────────────────────────────
    if from_type in ("symbol", "gene_symbol"):
        genes = fetcher.get_genes_by_symbol(ids, taxon=taxon)
    elif from_type in ("entrez_id", "gene_id", "ncbi_gene_id"):
        int_ids = [int(i) for i in ids]
        genes = fetcher.get_genes_by_id(int_ids)
    elif from_type in ("refseq_accession", "refseq_mrna", "refseq"):
        genes = fetcher.get_genes_by_accession(ids)
    else:
        raise ValueError(
            f"Unsupported from_type: {from_type!r}. "
            f"Supported: symbol, entrez_id, ensembl_gene_id, refseq_accession."
        )

    # Build result based on to_type
    results = []
    for gene in genes.genes:
        # Derive the from_val for this gene
        if from_type in ("symbol", "gene_symbol"):
            from_val = gene.symbol
        elif from_type in ("entrez_id", "gene_id", "ncbi_gene_id"):
            from_val = str(gene.gene_id)
        else:
            # refseq: match the query accession that led to this gene
            from_val = next(
                (
                    qid for qid in ids
                    if gene.transcripts and any(
                        t.accession_version and t.accession_version.startswith(qid.split(".")[0])
                        for t in gene.transcripts
                    )
                ),
                ids[0] if ids else None,  # fallback: first query id
            )

        try:
            to_val = _extract_to_val(gene, to_type)
        except ValueError as e:
            raise e

        if from_val:
            results.append({from_type: from_val, to_type: to_val})

    if return_dict:
        return {r[from_type]: r[to_type] for r in results if r[to_type]}

    return pd.DataFrame(results)
