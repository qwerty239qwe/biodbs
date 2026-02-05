"""NCBI Datasets fetched data and data manager classes."""

from biodbs.data._base import BaseFetchedData, BaseDBManager
from biodbs.data.NCBI._data_model import GeneReport, TaxonomyReport, GenomeReport
from typing import Literal, Optional, List, Dict, Any, Union
import pandas as pd
import polars as pl


class NCBIGeneFetchedData(BaseFetchedData):
    """Fetched data from NCBI Datasets Gene API.

    Contains gene data reports including:
        - Gene ID, symbol, description
        - Taxonomic information
        - Genomic locations
        - Transcript and protein information
        - Cross-references (UniProt, Ensembl, OMIM)

    Attributes:
        genes: List of GeneReport objects.
        total_count: Total number of genes matching the query.
        next_page_token: Token for pagination.
    """

    def __init__(
        self,
        content: Union[dict, list],
        query_ids: Optional[List[Union[int, str]]] = None,
    ):
        """Initialize NCBIGeneFetchedData.

        Args:
            content: Raw API response.
            query_ids: Original query identifiers.
        """
        super().__init__(content)
        self.query_ids = query_ids or []

        # Parse response
        if isinstance(content, dict):
            self.genes = self._parse_genes(content.get("reports", []))
            self.total_count = content.get("total_count", len(self.genes))
            self.next_page_token = content.get("next_page_token")
            self.warnings = content.get("warnings", [])
        elif isinstance(content, list):
            self.genes = self._parse_genes(content)
            self.total_count = len(self.genes)
            self.next_page_token = None
            self.warnings = []
        else:
            self.genes = []
            self.total_count = 0
            self.next_page_token = None
            self.warnings = []

    def _parse_genes(self, reports: List[Dict]) -> List[GeneReport]:
        """Parse gene report data into GeneReport objects."""
        genes = []
        for report in reports:
            # Handle nested structure where 'gene' key contains the data
            gene_data = report.get("gene", report)
            try:
                genes.append(GeneReport(**gene_data))
            except Exception:
                # Skip malformed entries
                pass
        return genes

    def __len__(self) -> int:
        return len(self.genes)

    def __iadd__(self, other: "NCBIGeneFetchedData") -> "NCBIGeneFetchedData":
        """Concatenate results from another NCBIGeneFetchedData."""
        self.genes.extend(other.genes)
        self.total_count += other.total_count
        return self

    @property
    def results(self) -> List[GeneReport]:
        """Get gene results."""
        return self.genes

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary into dot-separated keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                # Skip nested list of dicts
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return genes as list of dicts."""
        results = []
        for gene in self.genes:
            record = {
                "gene_id": gene.gene_id,
                "symbol": gene.symbol,
                "description": gene.description,
                "tax_id": gene.tax_id,
                "taxname": gene.taxname,
                "common_name": gene.common_name,
                "gene_type": gene.gene_type,
                "chromosomes": ", ".join(gene.chromosomes) if gene.chromosomes else None,
                "synonyms": ", ".join(gene.synonyms) if gene.synonyms else None,
                "swiss_prot": ", ".join(gene.swiss_prot_accessions) if gene.swiss_prot_accessions else None,
                "ensembl_ids": ", ".join(gene.ensembl_gene_ids) if gene.ensembl_gene_ids else None,
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
        """
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if flatten:
            data = [self._flatten_dict(record) for record in data]

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def show_columns(self) -> List[str]:
        """Return list of available column names."""
        return [
            "gene_id", "symbol", "description", "tax_id", "taxname",
            "common_name", "gene_type", "chromosomes", "synonyms",
            "swiss_prot", "ensembl_ids"
        ]

    def get_gene_ids(self) -> List[int]:
        """Get list of gene IDs."""
        return [g.gene_id for g in self.genes]

    def get_gene_symbols(self) -> List[str]:
        """Get list of gene symbols."""
        return [g.symbol for g in self.genes if g.symbol]

    def get_gene(self, gene_id: int) -> Optional[GeneReport]:
        """Get a specific gene by ID."""
        for g in self.genes:
            if g.gene_id == gene_id:
                return g
        return None

    def get_gene_by_symbol(self, symbol: str) -> Optional[GeneReport]:
        """Get a specific gene by symbol (case-insensitive)."""
        symbol_lower = symbol.lower()
        for g in self.genes:
            if g.symbol and g.symbol.lower() == symbol_lower:
                return g
        return None

    def filter_by_type(self, gene_type: str) -> "NCBIGeneFetchedData":
        """Filter genes by type.

        Args:
            gene_type: Gene type to filter by (e.g., "protein-coding").

        Returns:
            New NCBIGeneFetchedData with filtered genes.
        """
        filtered = [g for g in self.genes if g.gene_type == gene_type]
        result = NCBIGeneFetchedData.__new__(NCBIGeneFetchedData)
        result._content = self._content
        result.query_ids = self.query_ids
        result.genes = filtered
        result.total_count = len(filtered)
        result.next_page_token = None
        result.warnings = self.warnings
        return result

    def to_id_mapping(self) -> Dict[str, int]:
        """Create a mapping from gene symbol to gene ID."""
        return {g.symbol: g.gene_id for g in self.genes if g.symbol}

    def to_symbol_mapping(self) -> Dict[int, str]:
        """Create a mapping from gene ID to gene symbol."""
        return {g.gene_id: g.symbol for g in self.genes if g.symbol}

    def summary(self) -> str:
        """Get a text summary of the results."""
        lines = [
            "NCBI Gene Data Report",
            "=" * 40,
            f"Query IDs: {len(self.query_ids)}",
            f"Genes found: {len(self.genes)}",
            f"Total count: {self.total_count}",
        ]

        if self.warnings:
            lines.append(f"Warnings: {len(self.warnings)}")

        if self.genes:
            lines.append("\nTop 5 genes:")
            for g in self.genes[:5]:
                lines.append(
                    f"  {g.gene_id}: {g.symbol} - {g.description[:40] if g.description else 'N/A'}..."
                )

        return "\n".join(lines)


class NCBITaxonomyFetchedData(BaseFetchedData):
    """Fetched data from NCBI Datasets Taxonomy API.

    Contains taxonomy data reports including:
        - Taxonomy ID and names
        - Taxonomic rank and lineage
        - Genetic code information
    """

    def __init__(
        self,
        content: Union[dict, list],
        query_taxons: Optional[List[Union[int, str]]] = None,
    ):
        """Initialize NCBITaxonomyFetchedData.

        Args:
            content: Raw API response.
            query_taxons: Original query taxonomy IDs/names.
        """
        super().__init__(content)
        self.query_taxons = query_taxons or []

        if isinstance(content, dict):
            self.taxa = self._parse_taxa(content.get("reports", []))
            self.total_count = content.get("total_count", len(self.taxa))
            self.next_page_token = content.get("next_page_token")
        elif isinstance(content, list):
            self.taxa = self._parse_taxa(content)
            self.total_count = len(self.taxa)
            self.next_page_token = None
        else:
            self.taxa = []
            self.total_count = 0
            self.next_page_token = None

    def _parse_taxa(self, reports: List[Dict]) -> List[TaxonomyReport]:
        """Parse taxonomy report data into TaxonomyReport objects."""
        taxa = []
        for report in reports:
            # Handle nested structure
            tax_data = report.get("taxonomy", report)
            try:
                taxa.append(TaxonomyReport(**tax_data))
            except Exception:
                # Try to handle legacy format
                try:
                    # Map old format to new format
                    mapped_data = {
                        "tax_id": tax_data.get("taxId", tax_data.get("tax_id")),
                        "rank": tax_data.get("rank"),
                        "current_scientific_name": {"name": tax_data.get("organismName", "")},
                        "curator_common_name": tax_data.get("commonName"),
                    }
                    taxa.append(TaxonomyReport(**mapped_data))
                except Exception:
                    pass
        return taxa

    def __len__(self) -> int:
        return len(self.taxa)

    @property
    def results(self) -> List[TaxonomyReport]:
        """Get taxonomy results."""
        return self.taxa

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return taxa as list of dicts."""
        results = []
        for tax in self.taxa:
            record = {
                "tax_id": tax.tax_id,
                "organism_name": tax.organism_name,
                "common_name": tax.common_name,
                "rank": tax.rank,
                "parent_tax_id": tax.parent_tax_id,
                "group_name": tax.group_name,
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
        """Convert results to a DataFrame."""
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def get_taxon(self, tax_id: int) -> Optional[TaxonomyReport]:
        """Get a specific taxon by ID."""
        for tax in self.taxa:
            if tax.tax_id == tax_id:
                return tax
        return None

    def get_taxon_by_name(self, name: str) -> Optional[TaxonomyReport]:
        """Get taxon by name (case-insensitive partial match)."""
        name_lower = name.lower()
        for tax in self.taxa:
            if tax.organism_name and name_lower in tax.organism_name.lower():
                return tax
            if tax.common_name and name_lower in tax.common_name.lower():
                return tax
        return None


class NCBIGenomeFetchedData(BaseFetchedData):
    """Fetched data from NCBI Datasets Genome API.

    Contains genome assembly data reports including:
        - Assembly accession and name
        - Organism information
        - Assembly statistics
        - Annotation information
    """

    def __init__(
        self,
        content: Union[dict, list],
        query_accessions: Optional[List[str]] = None,
    ):
        """Initialize NCBIGenomeFetchedData.

        Args:
            content: Raw API response.
            query_accessions: Original query accessions.
        """
        super().__init__(content)
        self.query_accessions = query_accessions or []

        if isinstance(content, dict):
            self.assemblies = self._parse_assemblies(content.get("reports", []))
            self.total_count = content.get("total_count", len(self.assemblies))
            self.next_page_token = content.get("next_page_token")
        elif isinstance(content, list):
            self.assemblies = self._parse_assemblies(content)
            self.total_count = len(self.assemblies)
            self.next_page_token = None
        else:
            self.assemblies = []
            self.total_count = 0
            self.next_page_token = None

    def _parse_assemblies(self, reports: List[Dict]) -> List[GenomeReport]:
        """Parse assembly report data into GenomeReport objects."""
        assemblies = []
        for report in reports:
            try:
                assemblies.append(GenomeReport(**report))
            except Exception:
                pass
        return assemblies

    def __len__(self) -> int:
        return len(self.assemblies)

    @property
    def results(self) -> List[GenomeReport]:
        """Get assembly results."""
        return self.assemblies

    def as_dict(self, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Return assemblies as list of dicts."""
        results = []
        for asm in self.assemblies:
            record = {
                "accession": asm.accession,
                "organism_name": asm.organism_name,
                "organism_tax_id": asm.organism_tax_id,
                "assembly_name": asm.assembly_name,
                "assembly_level": asm.assembly_level,
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
        """Convert results to a DataFrame."""
        data = self.as_dict(columns)
        if not data:
            if engine == "pandas":
                return pd.DataFrame()
            return pl.DataFrame()

        if engine == "pandas":
            return pd.DataFrame(data)
        return pl.DataFrame(data)

    def get_accessions(self) -> List[str]:
        """Get list of assembly accessions."""
        return [a.accession for a in self.assemblies]


class NCBIDataManager(BaseDBManager):
    """Data manager for NCBI data."""

    def __init__(
        self,
        storage_path,
        db_name: str = "ncbi",
        cache_expiry_days: Optional[int] = None,
        auto_create_dirs: bool = True,
    ):
        super().__init__(storage_path, db_name, cache_expiry_days, auto_create_dirs)

    def save_gene_data(
        self,
        data: NCBIGeneFetchedData,
        filename: str,
        fmt: Literal["csv", "json", "jsonl"] = "json",
        key: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Save NCBIGeneFetchedData to storage."""
        if fmt == "csv" and data.genes:
            records = data.as_dict(columns) if columns else data.as_dict()
            return self.save_csv(records, filename, key=key)
        elif fmt == "json":
            return self.save_json(data.as_dict(), filename, key=key)
        elif fmt == "jsonl" and data.genes:
            return self.stream_json_lines(iter(data.as_dict()), filename, key=key)
        else:
            raise ValueError(f"Cannot save format {fmt} for empty data")
