"""Protein ID translation functions using UniProt."""

from typing import List, Dict, Union
import pandas as pd

from biodbs.fetch.uniprot.funcs import (
    gene_to_uniprot,
    uniprot_to_gene,
    uniprot_map_ids,
)


def translate_protein_ids(
    ids: List[str],
    from_type: str,
    to_type: Union[str, List[str]],
    organism: int = 9606,
    return_dict: bool = False,
) -> Union[Dict[str, str], Dict[str, Dict[str, str]], "pd.DataFrame"]:
    """Translate protein/gene IDs using UniProt ID mapping service.

    This function provides comprehensive ID translation between various
    biological databases using the UniProt ID mapping API.

    Args:
        ids: List of IDs to translate.
        from_type: Source ID type. Common options:
            - "UniProtKB_AC-ID": UniProt accession (e.g., "P04637")
            - "Gene_Name": Gene name/symbol (e.g., "TP53")
            - "GeneID": NCBI Gene ID (e.g., "7157")
            - "Ensembl": Ensembl gene ID (e.g., "ENSG00000141510")
            - "RefSeq_Protein": RefSeq protein ID
            - "PDB": PDB structure ID
        to_type: Target ID type(s). Can be a single string or a list of strings.
            When a list is provided, multiple target IDs are returned.
            Common options:
            - "UniProtKB": UniProt entry (returns accession)
            - "UniProtKB_AC-ID": UniProt accession
            - "GeneID": NCBI Gene ID
            - "Ensembl": Ensembl gene ID
            - "Ensembl_Protein": Ensembl protein ID
            - "RefSeq_Protein": RefSeq protein ID
            - "PDB": PDB structure ID
            - "STRING": STRING database ID
            - "ChEMBL": ChEMBL target ID
        organism: NCBI taxonomy ID (default: 9606 for human).
            Only used for Gene_Name -> UniProt mapping.
        return_dict: If True, return dict mapping from_id -> to_id (or dict of to_ids
            when to_type is a list). If False, return DataFrame.

    Returns:
        When to_type is a string:
            Dict mapping source IDs to target IDs, or DataFrame with mapping.
        When to_type is a list:
            Dict mapping source IDs to dicts of {target_type: target_id}, or
            DataFrame with from column and one column per target type.

    Example:
        UniProt to NCBI Gene ID:

        ```python
        result = translate_protein_ids(
            ["P04637", "P00533"],
            from_type="UniProtKB_AC-ID",
            to_type="GeneID",
        )
        print(result)
        #      from     to
        # 0  P04637   7157
        # 1  P00533   1956
        ```

        Gene names to UniProt:

        ```python
        result = translate_protein_ids(
            ["TP53", "EGFR"],
            from_type="Gene_Name",
            to_type="UniProtKB",
        )
        print(result)
        #    from       to
        # 0  TP53  P04637
        # 1  EGFR  P00533
        ```

        Multiple target types:

        ```python
        result = translate_protein_ids(
            ["P04637", "P00533"],
            from_type="UniProtKB_AC-ID",
            to_type=["GeneID", "Ensembl", "Gene_Name"],
        )
        print(result)
        #      from  GeneID           Ensembl Gene_Name
        # 0  P04637    7157  ENSG00000141510      TP53
        # 1  P00533    1956  ENSG00000146648      EGFR
        ```
    """
    if not ids:
        return {} if return_dict else pd.DataFrame()

    # Handle multiple target types
    if isinstance(to_type, list):
        return _translate_protein_multiple_targets(ids, from_type, to_type, organism, return_dict)

    # Special case: Gene_Name to UniProt uses optimized search
    if from_type == "Gene_Name" and to_type in ("UniProtKB", "UniProtKB_AC-ID"):
        mapping = gene_to_uniprot(ids, organism=organism, reviewed_only=True)
        if return_dict:
            return mapping
        records = [{"from": k, "to": v} for k, v in mapping.items()]
        return pd.DataFrame(records)

    # Special case: UniProt to Gene_Name uses batch entry retrieval
    if from_type in ("UniProtKB", "UniProtKB_AC-ID") and to_type == "Gene_Name":
        mapping = uniprot_to_gene(ids)
        if return_dict:
            return mapping
        records = [{"from": k, "to": v} for k, v in mapping.items()]
        return pd.DataFrame(records)

    # Use UniProt ID mapping for other conversions
    mapping_result = uniprot_map_ids(ids, from_db=from_type, to_db=to_type)

    if return_dict:
        # Flatten to first result for each ID
        return {k: v[0] if v else None for k, v in mapping_result.items()}

    # Build DataFrame with all mappings
    records = []
    for from_id, to_ids in mapping_result.items():
        if to_ids:
            for to_id in to_ids:
                records.append({"from": from_id, "to": to_id})
        else:
            records.append({"from": from_id, "to": None})

    return pd.DataFrame(records)


def _translate_protein_multiple_targets(
    ids: List[str],
    from_type: str,
    to_types: List[str],
    organism: int,
    return_dict: bool,
) -> Union[Dict[str, Dict[str, str]], "pd.DataFrame"]:
    """Translate protein IDs to multiple target types."""
    # Collect results for each target type
    all_results: Dict[str, Dict[str, str]] = {id_val: {} for id_val in ids}

    for target_type in to_types:
        try:
            result = translate_protein_ids(
                ids, from_type, target_type, organism, return_dict=True
            )
            for from_id, to_id in result.items():
                if from_id in all_results:
                    all_results[from_id][target_type] = to_id
        except Exception:
            # If a target type fails, set None for all IDs
            for from_id in ids:
                if from_id in all_results:
                    all_results[from_id][target_type] = None

    if return_dict:
        return all_results

    # Convert to DataFrame
    records = []
    for from_id, targets in all_results.items():
        record = {"from": from_id}
        record.update(targets)
        records.append(record)

    return pd.DataFrame(records)


def translate_gene_to_uniprot(
    gene_names: List[str],
    organism: int = 9606,
    reviewed_only: bool = True,
    return_dict: bool = True,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene names/symbols to UniProt accessions.

    This is a convenience function for the common use case of mapping
    gene symbols to their canonical UniProt protein accessions.

    Args:
        gene_names: List of gene names/symbols (e.g., ["TP53", "BRCA1"]).
        organism: NCBI taxonomy ID (default: 9606 for human).
        reviewed_only: Only return reviewed (Swiss-Prot) entries.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dict or DataFrame mapping gene names to UniProt accessions.

    Example:
        ```python
        mapping = translate_gene_to_uniprot(["TP53", "BRCA1", "EGFR"])
        print(mapping)
        # {'TP53': 'P04637', 'BRCA1': 'P38398', 'EGFR': 'P00533'}
        ```
    """
    mapping = gene_to_uniprot(
        gene_names, organism=organism, reviewed_only=reviewed_only
    )

    if return_dict:
        return mapping

    records = [{"gene_name": k, "uniprot_accession": v} for k, v in mapping.items()]
    return pd.DataFrame(records)


def translate_uniprot_to_gene(
    accessions: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate UniProt accessions to gene names/symbols.

    Args:
        accessions: List of UniProt accessions (e.g., ["P04637", "P00533"]).
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dict or DataFrame mapping UniProt accessions to gene names.

    Example:
        ```python
        mapping = translate_uniprot_to_gene(["P04637", "P00533"])
        print(mapping)
        # {'P04637': 'TP53', 'P00533': 'EGFR'}
        ```
    """
    mapping = uniprot_to_gene(accessions)

    if return_dict:
        return mapping

    records = [{"uniprot_accession": k, "gene_name": v} for k, v in mapping.items()]
    return pd.DataFrame(records)


def translate_uniprot_to_pdb(
    accessions: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, List[str]], "pd.DataFrame"]:
    """Translate UniProt accessions to PDB structure IDs.

    Note: One protein may have multiple PDB structures.

    Args:
        accessions: List of UniProt accessions.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dict mapping accessions to lists of PDB IDs, or DataFrame.

    Example:
        ```python
        result = translate_uniprot_to_pdb(["P04637"])
        print(result)
        # {'P04637': ['1A1U', '1AIE', '1C26', '1DT7', ...]}
        ```
    """
    mapping = uniprot_map_ids(accessions, from_db="UniProtKB_AC-ID", to_db="PDB")

    if return_dict:
        return mapping

    records = []
    for acc, pdb_ids in mapping.items():
        if pdb_ids:
            for pdb_id in pdb_ids:
                records.append({"uniprot_accession": acc, "pdb_id": pdb_id})
        else:
            records.append({"uniprot_accession": acc, "pdb_id": None})

    return pd.DataFrame(records)


def translate_uniprot_to_ensembl(
    accessions: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate UniProt accessions to Ensembl gene IDs.

    Args:
        accessions: List of UniProt accessions.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dict or DataFrame mapping UniProt accessions to Ensembl IDs.

    Example:
        ```python
        result = translate_uniprot_to_ensembl(["P04637", "P00533"])
        print(result)
        # {'P04637': 'ENSG00000141510', 'P00533': 'ENSG00000146648'}
        ```
    """
    mapping = uniprot_map_ids(accessions, from_db="UniProtKB_AC-ID", to_db="Ensembl")

    if return_dict:
        return {k: v[0] if v else None for k, v in mapping.items()}

    records = []
    for acc, ensembl_ids in mapping.items():
        ensembl_id = ensembl_ids[0] if ensembl_ids else None
        records.append({"uniprot_accession": acc, "ensembl_id": ensembl_id})

    return pd.DataFrame(records)


def translate_uniprot_to_refseq(
    accessions: List[str],
    return_dict: bool = True,
) -> Union[Dict[str, List[str]], "pd.DataFrame"]:
    """Translate UniProt accessions to RefSeq protein IDs.

    Args:
        accessions: List of UniProt accessions.
        return_dict: If True, return dict. If False, return DataFrame.

    Returns:
        Dict mapping accessions to lists of RefSeq IDs, or DataFrame.

    Example:
        ```python
        result = translate_uniprot_to_refseq(["P04637"])
        print(result)
        # {'P04637': ['NP_000537.3', 'NP_001119584.1', ...]}
        ```
    """
    mapping = uniprot_map_ids(
        accessions, from_db="UniProtKB_AC-ID", to_db="RefSeq_Protein"
    )

    if return_dict:
        return mapping

    records = []
    for acc, refseq_ids in mapping.items():
        if refseq_ids:
            for refseq_id in refseq_ids:
                records.append({"uniprot_accession": acc, "refseq_id": refseq_id})
        else:
            records.append({"uniprot_accession": acc, "refseq_id": None})

    return pd.DataFrame(records)
