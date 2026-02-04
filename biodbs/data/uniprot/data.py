"""UniProt fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from biodbs.data.uniprot._data_model import UniProtEntry
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class UniProtFetchedData(BaseFetchedData):
    """Fetched data from UniProt API.

    Contains protein entry data including:
        - Accession, entry name, protein name
        - Gene names, organism information
        - Sequence and features
        - Cross-references to other databases

    Attributes:
        entries: List of UniProtEntry objects.
        total_count: Total number of entries.
    """

    def __init__(
        self,
        content: Union[dict, list],
        query_ids: Optional[List[str]] = None,
    ):
        """Initialize UniProtFetchedData.

        Args:
            content: Raw API response.
            query_ids: Original query identifiers.
        """
        super().__init__(content)
        self.query_ids = query_ids or []

        # Parse response
        if isinstance(content, dict):
            # Search response with results array
            if "results" in content:
                self.entries = [self._parse_entry(e) for e in content.get("results", [])]
                self.entries = [e for e in self.entries if e is not None]
            # Single entry response
            elif "primaryAccession" in content:
                entry = self._parse_entry(content)
                self.entries = [entry] if entry else []
            else:
                self.entries = []
            self.total_count = len(self.entries)
        elif isinstance(content, list):
            self.entries = [e for e in (self._parse_entry(d) for d in content) if e]
            self.total_count = len(self.entries)
        else:
            self.entries = []
            self.total_count = 0

    def _parse_entry(self, data: Dict) -> Optional[UniProtEntry]:
        """Parse UniProt entry data."""
        try:
            return UniProtEntry(**data)
        except Exception:
            return None

    def __len__(self) -> int:
        return len(self.entries)

    def __iadd__(self, other: "UniProtFetchedData") -> "UniProtFetchedData":
        """Concatenate results from another UniProtFetchedData."""
        self.entries.extend(other.entries)
        self.total_count += other.total_count
        return self

    @property
    def results(self) -> List[UniProtEntry]:
        """Get entry results."""
        return self.entries

    def get_accessions(self) -> List[str]:
        """Get list of accessions."""
        return [e.primaryAccession for e in self.entries]

    def get_entry_names(self) -> List[str]:
        """Get list of entry names."""
        return [e.uniProtkbId for e in self.entries if e.uniProtkbId]

    def get_protein_names(self) -> List[str]:
        """Get list of protein names."""
        return [e.protein_name for e in self.entries if e.protein_name]

    def get_gene_names(self) -> List[str]:
        """Get list of primary gene names."""
        return [e.gene_name for e in self.entries if e.gene_name]

    def get_entry(self, accession: str) -> Optional[UniProtEntry]:
        """Get a specific entry by accession.

        Args:
            accession: UniProt accession.

        Returns:
            UniProtEntry or None.
        """
        for e in self.entries:
            if e.primaryAccession == accession:
                return e
            if e.secondaryAccessions and accession in e.secondaryAccessions:
                return e
        return None

    def get_entry_by_gene(self, gene_name: str) -> Optional[UniProtEntry]:
        """Get entry by gene name (case-insensitive).

        Args:
            gene_name: Gene name to search.

        Returns:
            First matching UniProtEntry or None.
        """
        gene_lower = gene_name.lower()
        for e in self.entries:
            for name in e.gene_names:
                if name.lower() == gene_lower:
                    return e
        return None

    def filter_reviewed(self) -> "UniProtFetchedData":
        """Filter to reviewed (Swiss-Prot) entries only.

        Returns:
            New UniProtFetchedData with filtered entries.
        """
        filtered = [e for e in self.entries if e.is_reviewed]
        result = UniProtFetchedData.__new__(UniProtFetchedData)
        result._content = self._content
        result.query_ids = self.query_ids
        result.entries = filtered
        result.total_count = len(filtered)
        return result

    def filter_by_organism(self, tax_id: int) -> "UniProtFetchedData":
        """Filter entries by organism taxonomy ID.

        Args:
            tax_id: NCBI taxonomy ID.

        Returns:
            New UniProtFetchedData with filtered entries.
        """
        filtered = [e for e in self.entries if e.tax_id == tax_id]
        result = UniProtFetchedData.__new__(UniProtFetchedData)
        result._content = self._content
        result.query_ids = self.query_ids
        result.entries = filtered
        result.total_count = len(filtered)
        return result

    def to_accession_mapping(self) -> Dict[str, str]:
        """Create mapping from gene name to accession.

        Returns:
            Dictionary mapping gene names to accessions.
        """
        mapping = {}
        for e in self.entries:
            if e.gene_name:
                mapping[e.gene_name] = e.primaryAccession
        return mapping

    def to_gene_mapping(self) -> Dict[str, str]:
        """Create mapping from accession to gene name.

        Returns:
            Dictionary mapping accessions to gene names.
        """
        return {e.primaryAccession: e.gene_name for e in self.entries if e.gene_name}

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return entries as list of dicts.

        Args:
            columns: Columns to include. None means all standard columns.

        Returns:
            List of dictionaries.
        """
        results = []
        for entry in self.entries:
            record = {
                "accession": entry.primaryAccession,
                "entry_name": entry.uniProtkbId,
                "protein_name": entry.protein_name,
                "gene_name": entry.gene_name,
                "gene_names": ", ".join(entry.gene_names) if entry.gene_names else None,
                "organism": entry.organism_name,
                "tax_id": entry.tax_id,
                "sequence_length": entry.sequence_length,
                "is_reviewed": entry.is_reviewed,
                "function": entry.get_function(),
                "subcellular_location": entry.get_subcellular_location(),
                "pdb_ids": ", ".join(entry.pdb_ids) if entry.pdb_ids else None,
                "ensembl_gene_id": entry.ensembl_gene_id,
                "entrez_gene_id": entry.entrez_gene_id,
            }
            if columns:
                record = {k: v for k, v in record.items() if k in columns}
            results.append(record)
        return results

    def as_dataframe(
        self,
        columns: Optional[List[str]] = None,
        engine: Literal["pandas", "polars"] = "pandas",
        flatten: bool = False,
    ):
        """Convert results to a DataFrame.

        Args:
            columns: Columns to include. None means all columns.
            engine: "pandas" or "polars".
            flatten: If True, flatten nested dictionaries.

        Returns:
            DataFrame with entry data.
        """
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def show_columns(self) -> List[str]:
        """Return list of available column names."""
        return [
            "accession", "entry_name", "protein_name", "gene_name", "gene_names",
            "organism", "tax_id", "sequence_length", "is_reviewed",
            "function", "subcellular_location", "pdb_ids",
            "ensembl_gene_id", "entrez_gene_id",
        ]

    def get_sequences(self) -> Dict[str, str]:
        """Get accession to sequence mapping.

        Returns:
            Dictionary mapping accessions to amino acid sequences.
        """
        return {
            e.primaryAccession: e.sequence.value
            for e in self.entries
            if e.sequence and e.sequence.value
        }

    def to_fasta(self) -> str:
        """Convert entries to FASTA format.

        Returns:
            FASTA formatted string.
        """
        lines = []
        for e in self.entries:
            if e.sequence and e.sequence.value:
                header = f">{e.uniProtkbId}|{e.primaryAccession}"
                if e.protein_name:
                    header += f" {e.protein_name}"
                if e.organism_name:
                    header += f" OS={e.organism_name}"
                lines.append(header)
                # Wrap sequence at 60 characters
                seq = e.sequence.value
                for i in range(0, len(seq), 60):
                    lines.append(seq[i:i+60])
        return "\n".join(lines)

    def summary(self) -> str:
        """Get a text summary of the results."""
        lines = [
            "UniProt Results",
            "=" * 40,
            f"Query IDs: {len(self.query_ids)}",
            f"Entries found: {len(self.entries)}",
        ]

        reviewed = sum(1 for e in self.entries if e.is_reviewed)
        lines.append(f"Reviewed (Swiss-Prot): {reviewed}")
        lines.append(f"Unreviewed (TrEMBL): {len(self.entries) - reviewed}")

        if self.entries:
            lines.append("\nTop 5 entries:")
            for e in self.entries[:5]:
                name = e.protein_name or "N/A"
                if len(name) > 40:
                    name = name[:40] + "..."
                lines.append(f"  {e.primaryAccession}: {e.gene_name or 'N/A'} - {name}")

        return "\n".join(lines)


class UniProtSearchResult(UniProtFetchedData):
    """Search result from UniProt with pagination info."""

    def __init__(
        self,
        content: Dict,
        query: Optional[str] = None,
        next_cursor: Optional[str] = None,
    ):
        """Initialize UniProtSearchResult.

        Args:
            content: Raw search response.
            query: Original search query.
            next_cursor: Cursor for next page.
        """
        super().__init__(content)
        self.query = query
        self.next_cursor = next_cursor

    @property
    def has_next(self) -> bool:
        """Check if there are more results."""
        return self.next_cursor is not None


class UniProtDataManager(BaseDBManager):
    """Data manager for UniProt data."""

    def __init__(
        self,
        storage_path,
        db_name: str = "uniprot",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_protein_data(
        self,
        data: UniProtFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl", "fasta"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save UniProtFetchedData to storage.

        Args:
            data: UniProt data to save.
            filename: Output filename.
            fmt: Output format.
            key: Optional storage key.
            columns: Columns for CSV format.
        """
        if fmt == "fasta":
            fasta_content = data.to_fasta()
            return self.save_text(fasta_content, filename, key=key)
        elif fmt == "csv" and data.entries:
            records = data.as_dict(columns) if columns else data.as_dict()
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.as_dict(), filename, key=key)
        elif fmt == "jsonl" and data.entries:
            return self.stream_json_lines(iter(data.as_dict()), filename, key=key)
        else:
            raise ValueError(f"Cannot save format {fmt} for empty data")
