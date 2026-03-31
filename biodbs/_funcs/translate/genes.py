"""Gene ID translation functions."""

from typing import List, Dict, Union, Literal, TYPE_CHECKING
import pandas as pd

from biodbs.fetch.biomart.funcs import biomart_convert_ids
from biodbs.fetch.KEGG.funcs import kegg_conv
from biodbs._funcs.translate._id_types import GeneIDType, TranslationDatabase, resolve_id_type
from biodbs._funcs._species import Species, resolve_species

if TYPE_CHECKING:
    pass


def translate_gene_ids(
    ids: List[str],
    from_type: Union[GeneIDType, str],
    to_type: Union[GeneIDType, str, List[Union[GeneIDType, str]]],
    species: Union[Species, str, int] = Species.HUMAN,
    database: Union[TranslationDatabase, str] = TranslationDatabase.NCBI,
    return_dict: bool = False,
) -> Union[Dict[str, str], Dict[str, Dict[str, str]], "pd.DataFrame"]:
    """Translate gene IDs between different identifier types.

    Args:
        ids: List of gene IDs to translate.
        from_type: Source ID type.
        to_type: Target ID type(s). Can be a single string or a list of strings.
            When a list is provided, multiple target IDs are returned.
        species: Species to translate for.  Accepts a :class:`Species` member,
            a common name (``"human"``), a KEGG code (``"hsa"``), a
            scientific name, or an NCBI taxon ID (``9606``).
            Defaults to :attr:`Species.HUMAN`.
        database: Database backend for translation.  Accepts a
            :class:`TranslationDatabase` member or a plain string.
            Raw strings are matched case-insensitively for backwards compat.

            - :attr:`TranslationDatabase.NCBI` *(default)* — NCBI Datasets API.
              Most reliable; best for symbol ↔ Entrez ↔ Ensembl translations.
            - :attr:`TranslationDatabase.ENSEMBL` — Ensembl REST API (xrefs).
              Stable; natural when working with Ensembl IDs.
            - :attr:`TranslationDatabase.UNIPROT` — UniProt ID-mapping API.
              Best for protein-centric translations (UniProt, PDB, RefSeq protein).
            - :attr:`TranslationDatabase.BIOMART` — BioMart query interface.
              Widest ID-type coverage but less reliable than the other options.
        return_dict: If True, return a dict mapping from_id -> to_id (or dict of to_ids
            when to_type is a list). If False (default), return a DataFrame.

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
        When to_type is a string:
            Dict mapping source IDs to target IDs, or DataFrame with both columns.
        When to_type is a list:
            Dict mapping source IDs to dicts of {target_type: target_id}, or
            DataFrame with from_type column and one column per target type.

    Example:
        Gene symbols to Ensembl IDs using the universal enum:

        ```python
        from biodbs.translate import GeneIDType

        result = translate_gene_ids(
            ["TP53", "BRCA1", "EGFR"],
            from_type=GeneIDType.GENE_SYMBOL,
            to_type=GeneIDType.ENSEMBL_GENE_ID,
        )
        print(result)
        #   external_gene_name    ensembl_gene_id
        # 0               TP53  ENSG00000141510
        # 1              BRCA1  ENSG00000012048
        # 2               EGFR  ENSG00000146648
        ```

        Raw database-native strings still work (backwards compatible):

        ```python
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type="external_gene_name",   # BioMart native
            to_type="ensembl_gene_id",
        )
        ```

        Ensembl IDs to HGNC (using Ensembl REST API):

        ```python
        result = translate_gene_ids(
            ["ENSG00000141510", "ENSG00000012048"],
            from_type=GeneIDType.ENSEMBL_GENE_ID,
            to_type=GeneIDType.GENE_SYMBOL,
            database="ensembl",
        )
        ```

        Multiple target types (BioMart):

        ```python
        result = translate_gene_ids(
            ["TP53", "BRCA1"],
            from_type=GeneIDType.GENE_SYMBOL,
            to_type=[GeneIDType.ENSEMBL_GENE_ID, GeneIDType.ENTREZ_ID],
        )
        print(result)
        #   external_gene_name    ensembl_gene_id  entrezgene_id
        # 0               TP53  ENSG00000141510           7157
        # 1              BRCA1  ENSG00000012048            672
        ```
    """
    # Normalise database: accept TranslationDatabase member or plain string
    if isinstance(database, TranslationDatabase):
        database = database.value   # e.g. "ncbi"
    else:
        database = str(database).lower()
        try:
            database = TranslationDatabase(database).value
        except ValueError:
            valid = [m.value for m in TranslationDatabase]
            raise ValueError(
                f"Unsupported database: {database!r}. "
                f"Valid options: {valid}  "
                f"(or use TranslationDatabase enum)"
            )

    # Resolve species to a Species enum (accepts str common name, KEGG code,
    # scientific name, taxon ID int, or Species member)
    species_obj = resolve_species(species)

    # Resolve universal ID type aliases to database-native names
    from_type = resolve_id_type(from_type, database)

    # Handle multiple target types
    if isinstance(to_type, list):
        to_type = [resolve_id_type(t, database) for t in to_type]
        return _translate_multiple_targets(
            ids, from_type, to_type, species_obj.common_name, database, return_dict
        )

    to_type = resolve_id_type(to_type, database)

    # Use common name string for the backend helpers (they have their own
    # species → dataset/taxon mappings that accept common names)
    species_name = species_obj.common_name

    if database == "biomart":
        return _translate_via_biomart(ids, from_type, to_type, species_name, return_dict)
    elif database == "ensembl":
        return _translate_via_ensembl(ids, from_type, to_type, species_name, return_dict)
    elif database == "uniprot":
        return _translate_via_uniprot(ids, from_type, to_type, species_name, return_dict)
    else:  # ncbi
        return _translate_via_ncbi(ids, from_type, to_type, species_name, return_dict)


def _translate_multiple_targets(
    ids: List[str],
    from_type: str,
    to_types: List[str],
    species: str,
    database: str,
    return_dict: bool,
) -> Union[Dict[str, Dict[str, str]], "pd.DataFrame"]:
    """Translate gene IDs to multiple target types."""
    # Collect results for each target type
    all_results: Dict[str, Dict[str, str]] = {id_val: {} for id_val in ids}

    for target_type in to_types:
        try:
            result = translate_gene_ids(
                ids, from_type, target_type, species, database, return_dict=True
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
        record = {from_type: from_id}
        record.update(targets)
        records.append(record)

    return pd.DataFrame(records)


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


def _ensembl_xref_first(xrefs_data, db_name: str) -> str:
    """Return the first matching xref value from an EnsemblFetchedData result."""
    for xref in xrefs_data.results:
        if xref.get("dbname", "").upper() == db_name.upper():
            if db_name.upper() == "HGNC":
                # display_id = gene symbol ("TP53"), primary_id = accession ("HGNC:11998")
                return xref.get("display_id") or xref.get("primary_id")
            return xref.get("primary_id") or xref.get("display_id")
    return None


def _ensembl_lookup_parent(id_val: str, ensembl_lookup_fn) -> str:
    """Return the Parent Ensembl ID one level up (ENSP→ENST or ENST→ENSG)."""
    data = ensembl_lookup_fn(id_val)
    return data.results[0].get("Parent") if data.results else None


def _ensembl_gene_id_for(id_val: str, from_type: str, ensembl_lookup_fn) -> str:
    """Resolve any Ensembl stable ID to its parent gene ID (ENSG...)."""
    if from_type == "ensembl_gene_id":
        return id_val
    if from_type == "ensembl_transcript_id":
        return _ensembl_lookup_parent(id_val, ensembl_lookup_fn)
    if from_type == "ensembl_protein_id":
        transcript_id = _ensembl_lookup_parent(id_val, ensembl_lookup_fn)
        if transcript_id:
            return _ensembl_lookup_parent(transcript_id, ensembl_lookup_fn)
    return None


def _ensembl_gene_to_xref(gene_id: str, to_type: str, ensembl_get_xrefs_fn) -> str:
    """Get an external ID for an Ensembl gene ID via xrefs/id."""
    # to_type here is already the resolved external_db name from ENSEMBL_ID_MAP
    data = ensembl_get_xrefs_fn(gene_id, external_db=to_type)
    return _ensembl_xref_first(data, to_type)


def _translate_via_ensembl(
    ids: List[str],
    from_type: str,
    to_type: str,
    species: str,
    return_dict: bool,
) -> Union[Dict[str, str], "pd.DataFrame"]:
    """Translate gene IDs using Ensembl REST API.

    Handles three translation modes:

    1. **Ensembl-stable → external** (gene/transcript/protein ID → symbol, EntrezGene, UniProt, …):
       Uses ``xrefs/id`` on the gene ID.  Transcript and protein inputs are first
       resolved to their parent gene via ``lookup/id``, then xrefs are fetched on
       the gene.  Exceptions: transcript→RefSeq_mRNA and protein→RefSeq_peptide /
       UniProt are fetched directly on the respective stable ID.

    2. **Ensembl-stable → Ensembl-stable** (gene↔transcript↔protein hierarchy):
       Uses ``lookup/id?expand=1`` to navigate the gene → transcript → translation
       tree, preferring the canonical transcript where applicable.

    3. **External → Ensembl-stable** (symbol → Ensembl gene ID):
       Uses ``xrefs/symbol``.  This endpoint always returns Ensembl gene IDs; a
       warning is emitted if a non-gene Ensembl type was requested.
    """
    import warnings
    from biodbs.fetch.ensembl.funcs import (
        ensembl_get_xrefs,
        ensembl_get_xrefs_symbol,
        ensembl_lookup,
    )

    ensembl_species = (
        resolve_species(species).scientific_name.lower().replace(" ", "_")
    )

    ENSEMBL_STABLE = {"ensembl_gene_id", "ensembl_transcript_id", "ensembl_protein_id"}

    # External DB names that carry protein/transcript-level xrefs directly
    # (no need to chain through the gene for these)
    TRANSCRIPT_DIRECT_XREFS = {"RefSeq_mRNA"}
    PROTEIN_DIRECT_XREFS = {"RefSeq_peptide", "Uniprot/SWISSPROT"}

    # UniProt for proteins uses a different db name than for genes
    PROTEIN_UNIPROT_DB = "Uniprot/SWISSPROT"

    results: List[Dict] = []

    if from_type in ENSEMBL_STABLE:

        for id_val in ids:
            to_val = None
            try:
                # ── Ensembl → Ensembl (hierarchy navigation) ────────────────
                if to_type in ENSEMBL_STABLE:
                    if from_type == "ensembl_gene_id":
                        gene_data = ensembl_lookup(id_val, expand=True)
                        if gene_data.results:
                            transcripts = gene_data.results[0].get("Transcript", [])
                            canonical = next(
                                (t for t in transcripts if t.get("is_canonical")),
                                transcripts[0] if transcripts else None,
                            )
                            if canonical:
                                if to_type == "ensembl_transcript_id":
                                    to_val = canonical.get("id")
                                elif to_type == "ensembl_protein_id":
                                    trans = canonical.get("Translation")
                                    to_val = trans.get("id") if trans else None

                    elif from_type == "ensembl_transcript_id":
                        if to_type == "ensembl_gene_id":
                            to_val = _ensembl_lookup_parent(id_val, ensembl_lookup)
                        elif to_type == "ensembl_protein_id":
                            tx_data = ensembl_lookup(id_val, expand=True)
                            if tx_data.results:
                                trans = tx_data.results[0].get("Translation")
                                to_val = trans.get("id") if trans else None

                    elif from_type == "ensembl_protein_id":
                        if to_type == "ensembl_transcript_id":
                            to_val = _ensembl_lookup_parent(id_val, ensembl_lookup)
                        elif to_type == "ensembl_gene_id":
                            transcript_id = _ensembl_lookup_parent(id_val, ensembl_lookup)
                            if transcript_id:
                                to_val = _ensembl_lookup_parent(transcript_id, ensembl_lookup)

                # ── Ensembl → external ───────────────────────────────────────
                else:
                    if from_type == "ensembl_transcript_id" and to_type in TRANSCRIPT_DIRECT_XREFS:
                        # RefSeq_mRNA xrefs live on the transcript
                        xref_data = ensembl_get_xrefs(id_val, external_db=to_type)
                        to_val = _ensembl_xref_first(xref_data, to_type)

                    elif from_type == "ensembl_protein_id" and to_type in PROTEIN_DIRECT_XREFS:
                        # RefSeq_peptide / UniProt xrefs live on the protein
                        xref_data = ensembl_get_xrefs(id_val, external_db=to_type)
                        to_val = _ensembl_xref_first(xref_data, to_type)

                    elif from_type == "ensembl_protein_id" and to_type == "Uniprot_gn":
                        # Redirect: proteins use Uniprot/SWISSPROT, not Uniprot_gn
                        xref_data = ensembl_get_xrefs(id_val, external_db=PROTEIN_UNIPROT_DB)
                        to_val = _ensembl_xref_first(xref_data, PROTEIN_UNIPROT_DB)

                    else:
                        # General case: resolve to gene ID, then fetch gene-level xrefs
                        gene_id = _ensembl_gene_id_for(id_val, from_type, ensembl_lookup)
                        if gene_id:
                            xref_data = ensembl_get_xrefs(gene_id, external_db=to_type)
                            to_val = _ensembl_xref_first(xref_data, to_type)

            except Exception:
                pass

            results.append({from_type: id_val, to_type: to_val})

    else:
        # ── External → Ensembl stable ID ────────────────────────────────────
        # xrefs/symbol always returns Ensembl gene IDs regardless of to_type.
        if to_type not in ENSEMBL_STABLE:
            warnings.warn(
                f"Ensembl REST symbol lookup always returns Ensembl gene IDs; "
                f"cannot translate directly to {to_type!r}. "
                f"The result column will contain Ensembl gene IDs instead. "
                f"To get {to_type!r} output use database=TranslationDatabase.NCBI "
                f"or database=TranslationDatabase.UNIPROT.",
                UserWarning,
                stacklevel=3,
            )
        for id_val in ids:
            try:
                data = ensembl_get_xrefs_symbol(ensembl_species, id_val)
                ensembl_id = data.results[0].get("id") if data.results else None
                results.append({from_type: id_val, to_type: ensembl_id})
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
        KEGG gene IDs to NCBI Entrez:

        ```python
        result = translate_gene_ids_kegg(
            ["hsa:7157", "hsa:672"],
            from_db="hsa",
            to_db="ncbi-geneid",
        )
        print(result)
        #       source           target
        # 0  hsa:7157  ncbi-geneid:7157
        # 1   hsa:672   ncbi-geneid:672
        ```

        Convert entire organism's genes to UniProt:

        ```python
        result = translate_gene_ids_kegg([], from_db="hsa", to_db="uniprot")
        print(result.head())
        #       source              target
        # 0    hsa:1    up:P04217
        # 1    hsa:2    up:P01023
        # ...
        ```
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
