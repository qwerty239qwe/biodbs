"""Gene ID translation functions."""

from typing import List, Dict, Union, Literal
import pandas as pd

from biodbs.fetch.biomart.funcs import biomart_convert_ids
from biodbs.fetch.KEGG.funcs import kegg_conv


def translate_gene_ids(
    ids: List[str],
    from_type: str,
    to_type: str,
    species: str = "human",
    database: Literal["biomart", "ensembl", "ncbi", "uniprot"] = "biomart",
    return_dict: bool = False,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene IDs between different identifier types.

    Args:
        ids: List of gene IDs to translate.
        from_type: Source ID type.
        to_type: Target ID type.
        species: Species name ("human", "mouse", "rat", etc.). Defaults to "human".
        database: Database to use for translation:
            - "biomart": Use BioMart/Ensembl query interface (default).
              Supports batch queries with many ID types.
            - "ensembl": Use Ensembl REST API (xrefs endpoint).
              Better for single ID lookups, returns more cross-references.
            - "ncbi": Use NCBI Datasets API.
              Best for NCBI Gene IDs (Entrez), RefSeq accessions, and symbols.
            - "uniprot": Use UniProt ID mapping API.
              Best for protein-centric translations (UniProt, PDB, RefSeq protein).
        return_dict: If True, return a dict mapping from_id -> to_id.
            If False (default), return a DataFrame.

    Supported ID types for NCBI:
        - symbol / gene_symbol: Gene symbol (e.g., "TP53")
        - entrez_id / gene_id: NCBI Gene ID (e.g., "7157")
        - refseq_accession: RefSeq accession (e.g., "NM_000546.6")
        - ensembl_gene_id: Ensembl gene ID (output only)
        - uniprot / swiss_prot: UniProt accession (output only)

    Supported ID types for BioMart:
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

    Supported ID types for Ensembl REST:
        - Input (from_type): Ensembl stable IDs (ENSG*, ENST*, ENSP*)
        - Output (to_type): Filter by external_db name (e.g., "HGNC", "EntrezGene",
          "Uniprot_gn", "RefSeq_mRNA", "RefSeq_peptide")

    Supported ID types for UniProt:
        - UniProtKB_AC-ID: UniProt accession (e.g., "P04637")
        - Gene_Name: Gene symbol (e.g., "TP53")
        - GeneID: NCBI Gene ID (e.g., "7157")
        - Ensembl: Ensembl gene ID
        - RefSeq_Protein: RefSeq protein ID
        - PDB: PDB structure ID

    Returns:
        Dict mapping source IDs to target IDs, or DataFrame with both columns.

    Example:
        >>> # Gene symbols to Ensembl IDs (using BioMart)
        >>> result = translate_gene_ids(
        ...     ["TP53", "BRCA1", "EGFR"],
        ...     from_type="external_gene_name",
        ...     to_type="ensembl_gene_id"
        ... )

        >>> # Ensembl IDs to HGNC (using Ensembl REST API)
        >>> result = translate_gene_ids(
        ...     ["ENSG00000141510", "ENSG00000012048"],
        ...     from_type="ensembl_gene_id",
        ...     to_type="HGNC",
        ...     database="ensembl"
        ... )
    """
    valid_databases = {"biomart", "ensembl", "ncbi", "uniprot"}
    if database not in valid_databases:
        raise ValueError(f"Unsupported database: {database}. Valid options: {valid_databases}")

    if database == "biomart":
        return _translate_via_biomart(ids, from_type, to_type, species, return_dict)
    elif database == "ensembl":
        return _translate_via_ensembl(ids, from_type, to_type, species, return_dict)
    elif database == "uniprot":
        return _translate_via_uniprot(ids, from_type, to_type, species, return_dict)
    else:  # ncbi
        return _translate_via_ncbi(ids, from_type, to_type, species, return_dict)


def _translate_via_biomart(
    ids: List[str],
    from_type: str,
    to_type: str,
    species: str,
    return_dict: bool,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene IDs using BioMart."""
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


def _translate_via_ensembl(
    ids: List[str],
    from_type: str,
    to_type: str,
    species: str,
    return_dict: bool,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene IDs using Ensembl REST API xrefs endpoint."""
    from biodbs.fetch.ensembl.funcs import ensembl_get_xrefs, ensembl_get_xrefs_symbol

    # Map common species names to Ensembl species names
    species_map = {
        "human": "homo_sapiens",
        "mouse": "mus_musculus",
        "rat": "rattus_norvegicus",
        "zebrafish": "danio_rerio",
        "fly": "drosophila_melanogaster",
        "worm": "caenorhabditis_elegans",
        "yeast": "saccharomyces_cerevisiae",
    }
    ensembl_species = species_map.get(species.lower(), species)

    results = []

    for id_val in ids:
        try:
            # Determine if input is an Ensembl ID or external symbol
            if id_val.startswith(("ENSG", "ENST", "ENSP", "ENSMUS", "ENSRNO")):
                # Input is Ensembl ID - get xrefs
                data = ensembl_get_xrefs(id_val, external_db=to_type if to_type else None)
                if data.results:
                    # Get the primary_id from the first matching xref
                    for xref in data.results:
                        if to_type is None or xref.get("dbname", "").upper() == to_type.upper():
                            results.append({
                                from_type: id_val,
                                to_type: xref.get("primary_id") or xref.get("display_id"),
                                "dbname": xref.get("dbname"),
                            })
                            break
                    else:
                        # No matching xref found
                        results.append({from_type: id_val, to_type: None})
                else:
                    results.append({from_type: id_val, to_type: None})
            else:
                # Input is external symbol - look up Ensembl ID
                data = ensembl_get_xrefs_symbol(ensembl_species, id_val)
                if data.results:
                    # Return the Ensembl ID
                    ensembl_id = data.results[0].get("id")
                    results.append({
                        from_type: id_val,
                        to_type: ensembl_id,
                        "type": data.results[0].get("type"),
                    })
                else:
                    results.append({from_type: id_val, to_type: None})
        except Exception:
            results.append({from_type: id_val, to_type: None})

    df = pd.DataFrame(results)

    if return_dict:
        if df.empty:
            return {}
        return dict(zip(df[from_type], df[to_type]))

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

    if ids:
        data = kegg_conv(target_db=to_db, source=ids)
    else:
        data = kegg_conv(target_db=to_db, source=from_db)

    return data.as_dataframe()


def _translate_via_ncbi(
    ids: List[str],
    from_type: str,
    to_type: str,
    species: str,
    return_dict: bool,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene IDs using NCBI Datasets API."""
    from biodbs.fetch.NCBI.funcs import ncbi_translate_gene_ids

    # Map common species names to NCBI taxon identifiers
    species_map = {
        "human": "human",
        "mouse": "mouse",
        "rat": "rat",
        "zebrafish": "zebrafish",
        "fly": "fruit fly",
        "worm": "nematode",
        "yeast": "baker's yeast",
    }
    taxon = species_map.get(species.lower(), species)

    return ncbi_translate_gene_ids(
        ids,
        from_type=from_type,
        to_type=to_type,
        taxon=taxon,
        return_dict=return_dict,
    )


def _translate_via_uniprot(
    ids: List[str],
    from_type: str,
    to_type: str,
    species: str,
    return_dict: bool,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene/protein IDs using UniProt ID mapping API."""
    from biodbs._funcs.translate.proteins import translate_protein_ids

    # Map common species names to NCBI taxonomy IDs
    species_taxids = {
        "human": 9606,
        "mouse": 10090,
        "rat": 10116,
        "zebrafish": 7955,
        "fly": 7227,
        "worm": 6239,
        "yeast": 559292,
    }
    organism = species_taxids.get(species.lower(), 9606)

    return translate_protein_ids(
        ids,
        from_type=from_type,
        to_type=to_type,
        organism=organism,
        return_dict=return_dict,
    )
