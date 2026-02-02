"""Gene ID translation functions."""

from typing import List, Dict, Union


def translate_gene_ids(
    ids: List[str],
    from_type: str,
    to_type: str,
    species: str = "human",
    return_dict: bool = False,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene IDs between different identifier types.

    Uses BioMart/Ensembl for gene ID conversion.

    Supported ID types:
        - ensembl_gene_id: Ensembl gene ID (e.g., "ENSG00000141510")
        - ensembl_transcript_id: Ensembl transcript ID
        - ensembl_peptide_id: Ensembl protein ID
        - external_gene_name: Gene symbol (e.g., "TP53")
        - hgnc_symbol: HGNC symbol
        - hgnc_id: HGNC ID (e.g., "HGNC:11998")
        - entrezgene_id: NCBI Entrez gene ID
        - uniprot_gn_id: UniProt gene name
        - refseq_mrna: RefSeq mRNA ID
        - refseq_peptide: RefSeq protein ID

    Args:
        ids: List of gene IDs to translate.
        from_type: Source ID type.
        to_type: Target ID type.
        species: Species name ("human", "mouse", "rat", etc.). Defaults to "human".
        return_dict: If True, return a dict mapping from_id -> to_id.
            If False (default), return a DataFrame.

    Returns:
        Dict mapping source IDs to target IDs, or DataFrame with both columns.

    Example:
        >>> # Gene symbols to Ensembl IDs
        >>> result = translate_gene_ids(
        ...     ["TP53", "BRCA1", "EGFR"],
        ...     from_type="external_gene_name",
        ...     to_type="ensembl_gene_id"
        ... )

        >>> # Ensembl IDs to Entrez IDs
        >>> mapping = translate_gene_ids(
        ...     ["ENSG00000141510"],
        ...     from_type="ensembl_gene_id",
        ...     to_type="entrezgene_id",
        ...     return_dict=True
        ... )
    """
    from biodbs.fetch.biomart.funcs import biomart_convert_ids

    # Map species names to BioMart dataset names
    species_datasets = {
        "human": "hsapiens_gene_ensembl",
        "mouse": "mmusculus_gene_ensembl",
        "rat": "rnorvegicus_gene_ensembl",
        "zebrafish": "drerio_gene_ensembl",
        "fly": "dmelanogaster_gene_ensembl",
        "worm": "celegans_gene_ensembl",
        "yeast": "scerevisiae_gene_ensembl",
    }
    dataset = species_datasets.get(species.lower(), f"{species}_gene_ensembl")

    data = biomart_convert_ids(ids, from_type=from_type, to_type=to_type, dataset=dataset)
    df = data.as_dataframe()

    if return_dict:
        # Create mapping dict, handling potential duplicates
        mapping = {}
        for _, row in df.iterrows():
            from_val = row.get(from_type)
            to_val = row.get(to_type)
            if from_val and to_val:
                mapping[from_val] = to_val
        return mapping

    return df


def translate_gene_ids_kegg(
    ids: List[str],
    from_db: str,
    to_db: str,
) -> "pd.DataFrame":
    """Translate gene IDs using KEGG database.

    Useful for converting between KEGG gene IDs and external databases.

    Supported databases:
        - KEGG organism codes: "hsa" (human), "mmu" (mouse), "rno" (rat), etc.
        - ncbi-geneid: NCBI Entrez Gene ID
        - ncbi-proteinid: NCBI Protein ID
        - uniprot: UniProt accession

    Args:
        ids: List of gene IDs to translate (e.g., ["hsa:7157", "hsa:672"]).
        from_db: Source database. Use KEGG entry IDs or external DB name.
        to_db: Target database name.

    Returns:
        DataFrame with source and target ID columns.

    Example:
        >>> # KEGG gene IDs to NCBI Entrez
        >>> result = translate_gene_ids_kegg(
        ...     ["hsa:7157", "hsa:672"],
        ...     from_db="hsa",
        ...     to_db="ncbi-geneid"
        ... )

        >>> # Convert entire organism's genes
        >>> result = translate_gene_ids_kegg([], from_db="hsa", to_db="uniprot")
    """
    from biodbs.fetch.KEGG.funcs import kegg_conv

    if ids:
        data = kegg_conv(target_db=to_db, source=ids)
    else:
        data = kegg_conv(target_db=to_db, source=from_db)

    return data.as_dataframe()
