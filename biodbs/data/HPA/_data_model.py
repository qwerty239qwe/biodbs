"""Human Protein Atlas (HPA) API data models with Pydantic validation.

HPA provides several ways to access data:

1. Individual entry access via Ensembl gene IDs:
   https://www.proteinatlas.org/{ensembl_id}.{format}
   Formats: xml, tsv, json

2. Search query downloads:
   https://www.proteinatlas.org/search/{query}?format={format}&compress={yes/no}

3. Customized data retrieval API:
   https://www.proteinatlas.org/api/search_download.php?search={query}&format={format}&columns={columns}

Reference:
- https://www.proteinatlas.org/about/help/dataaccess
- https://www.proteinatlas.org/about/download
"""

from enum import Enum
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Dict, Any, Optional, List
import re


class HPAFormat(Enum):
    """Output formats for HPA API."""
    JSON = "json"
    TSV = "tsv"
    XML = "xml"


class HPASearchFormat(Enum):
    """Output formats for HPA search/download API."""
    JSON = "json"
    TSV = "tsv"


class HPACompress(Enum):
    """Compression options for HPA downloads."""
    YES = "yes"
    NO = "no"


class HPAColumnCategory(Enum):
    """Categories of columns available in HPA."""
    GENE = "gene"
    TISSUE = "tissue"
    CELL = "cell"
    PATHOLOGY = "pathology"
    BLOOD = "blood"
    BRAIN = "brain"
    SUBCELLULAR = "subcellular"


# Common column specifiers for HPA search_download API
# Reference: https://www.proteinatlas.org/about/help/dataaccess
HPA_COLUMNS = {
    # Gene information
    "g": "Gene",
    "gs": "Gene synonym",
    "eg": "Ensembl",
    "gd": "Gene description",
    "chr": "Chromosome",
    "chrp": "Position",
    "up": "Uniprot",
    "pe": "Protein evidence",
    "te": "Transcript evidence",
    "rnats_s": "RNA tissue specificity",
    "rnats_d": "RNA tissue distribution",
    "rnacs_s": "RNA cell type specificity",
    "rnacs_d": "RNA cell type distribution",
    "rnabts_s": "RNA blood cell specificity",
    "rnabts_d": "RNA blood cell distribution",
    "rnabrs_s": "RNA brain region specificity",
    "rnabrs_d": "RNA brain region distribution",
    "scl": "Subcellular location",
    "scml": "Subcellular main location",
    "scal": "Subcellular additional location",
    "sec": "Secretome",
    "mclass": "Membrane class",
    "pc": "Protein class",

    # Tissue expression (RNA)
    "rna_tissue": "RNA tissue expression (all tissues)",

    # Blood expression
    "rna_blood": "RNA blood cell expression",

    # Brain expression
    "rna_brain": "RNA brain region expression",

    # Single cell expression
    "rna_sc": "RNA single cell type expression",

    # Cancer/Pathology
    "patho": "Pathology prognostics",
    "tau": "TAU score",

    # Protein evidence
    "antibody": "Antibody",
    "reliability_ih": "Reliability (IH)",
    "reliability_if": "Reliability (IF)",
}

# Tissue-specific RNA columns (example subset - HPA has many more)
HPA_TISSUE_COLUMNS = [
    "rna_adipose_tissue", "rna_adrenal_gland", "rna_appendix", "rna_bone_marrow",
    "rna_breast", "rna_cerebral_cortex", "rna_cervix", "rna_colon", "rna_duodenum",
    "rna_endometrium", "rna_epididymis", "rna_esophagus", "rna_fallopian_tube",
    "rna_gallbladder", "rna_heart_muscle", "rna_hippocampus", "rna_kidney",
    "rna_liver", "rna_lung", "rna_lymph_node", "rna_ovary", "rna_pancreas",
    "rna_parathyroid_gland", "rna_placenta", "rna_prostate", "rna_rectum",
    "rna_salivary_gland", "rna_seminal_vesicle", "rna_skeletal_muscle",
    "rna_skin", "rna_small_intestine", "rna_smooth_muscle", "rna_spleen",
    "rna_stomach", "rna_testis", "rna_thyroid_gland", "rna_tonsil",
    "rna_urinary_bladder", "rna_vagina",
]

# Default columns for common use cases
DEFAULT_GENE_COLUMNS = ["g", "gs", "eg", "gd", "up", "pc"]
DEFAULT_EXPRESSION_COLUMNS = ["g", "eg", "rnats_s", "rnats_d", "rnacs_s", "rnacs_d"]
DEFAULT_SUBCELLULAR_COLUMNS = ["g", "eg", "scl", "scml", "scal"]
DEFAULT_PATHOLOGY_COLUMNS = ["g", "eg", "patho", "tau"]


class HPAEntryModel(BaseModel):
    """Pydantic model for HPA individual entry request validation.

    URL format: https://www.proteinatlas.org/{ensembl_id}.{format}
    """
    model_config = ConfigDict(use_enum_values=True)

    ensembl_id: str
    format: HPAFormat = HPAFormat.JSON

    @field_validator("ensembl_id")
    @classmethod
    def validate_ensembl_id(cls, v: str) -> str:
        """Validate Ensembl gene ID format."""
        if not re.match(r"^ENSG\d{11}$", v):
            raise ValueError(
                f"Invalid Ensembl gene ID format: {v}. "
                "Expected format: ENSG followed by 11 digits (e.g., ENSG00000134057)"
            )
        return v

    def build_url(self) -> str:
        """Build the full URL for individual entry access."""
        fmt = self.format if isinstance(self.format, str) else self.format
        return f"https://www.proteinatlas.org/{self.ensembl_id}.{fmt}"


class HPASearchModel(BaseModel):
    """Pydantic model for HPA search query download validation.

    URL format: https://www.proteinatlas.org/search/{query}?format={format}&compress={compress}
    """
    model_config = ConfigDict(use_enum_values=True)

    query: str
    format: HPAFormat = HPAFormat.JSON
    compress: HPACompress = HPACompress.NO

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query is not empty."""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()

    def build_url(self) -> str:
        """Build the full URL for search query download."""
        base_url = f"https://www.proteinatlas.org/search/{self.query}"
        return base_url

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters."""
        fmt = self.format if isinstance(self.format, str) else self.format
        compress = self.compress if isinstance(self.compress, str) else self.compress
        return {
            "format": fmt,
            "compress": compress,
        }


class HPASearchDownloadModel(BaseModel):
    """Pydantic model for HPA customized search/download API validation.

    URL format: https://www.proteinatlas.org/api/search_download.php
    Parameters:
        - search: Gene list search string
        - format: json or tsv
        - columns: Comma-separated column specifiers
        - compress: yes or no (optional)
    """
    model_config = ConfigDict(use_enum_values=True)

    search: str
    format: HPASearchFormat = HPASearchFormat.JSON
    columns: List[str]
    compress: HPACompress = HPACompress.NO

    @field_validator("search")
    @classmethod
    def validate_search(cls, v: str) -> str:
        """Validate search query is not empty."""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()

    @field_validator("columns")
    @classmethod
    def validate_columns(cls, v: List[str]) -> List[str]:
        """Validate columns list is not empty."""
        if not v:
            raise ValueError("Columns list cannot be empty")
        return v

    def build_url(self) -> str:
        """Build the API URL."""
        return "https://www.proteinatlas.org/api/search_download.php"

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters."""
        fmt = self.format if isinstance(self.format, str) else self.format
        compress = self.compress if isinstance(self.compress, str) else self.compress
        # Ensure compress is string value, not enum
        if hasattr(compress, 'value'):
            compress = compress.value
        return {
            "search": self.search,
            "format": fmt,
            "columns": ",".join(self.columns),
            "compress": compress,
        }


class HPABulkDownloadModel(BaseModel):
    """Pydantic model for HPA bulk data file downloads.

    Available files:
        - proteinatlas.tsv.zip: Subset of data in TSV format
        - proteinatlas.json.gz: Same as TSV but in JSON (for APIs)
        - proteinatlas.xml.gz: Most comprehensive data including protein expression,
          antigen sequences, Western blot data, RNA-seq data, external references
    """
    model_config = ConfigDict(use_enum_values=True)

    file_type: str = "json"  # "tsv", "json", or "xml"
    version: Optional[str] = None  # e.g., "24" for v24.proteinatlas.org

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """Validate file type."""
        valid_types = ["tsv", "json", "xml"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid file type: {v}. Valid types: {valid_types}")
        return v.lower()

    def build_url(self) -> str:
        """Build the download URL for bulk data files."""
        if self.version:
            base_url = f"https://v{self.version}.proteinatlas.org/download"
        else:
            base_url = "https://www.proteinatlas.org/download"

        file_map = {
            "tsv": "proteinatlas.tsv.zip",
            "json": "proteinatlas.json.gz",
            "xml": "proteinatlas.xml.gz",
        }
        return f"{base_url}/{file_map[self.file_type]}"


if __name__ == "__main__":
    # Test HPAEntryModel
    print("=== HPAEntryModel Tests ===")
    entry = HPAEntryModel(ensembl_id="ENSG00000134057", format="json")
    print(f"Entry URL: {entry.build_url()}")

    # Test HPASearchModel
    print("\n=== HPASearchModel Tests ===")
    search = HPASearchModel(query="TP53", format="json", compress="no")
    print(f"Search URL: {search.build_url()}")
    print(f"Query params: {search.build_query_params()}")

    # Test HPASearchDownloadModel
    print("\n=== HPASearchDownloadModel Tests ===")
    download = HPASearchDownloadModel(
        search="TP53",
        format="json",
        columns=["g", "gs", "eg", "gd"],
    )
    print(f"Download URL: {download.build_url()}")
    print(f"Query params: {download.build_query_params()}")

    # Test HPABulkDownloadModel
    print("\n=== HPABulkDownloadModel Tests ===")
    bulk = HPABulkDownloadModel(file_type="json")
    print(f"Bulk download URL: {bulk.build_url()}")

    bulk_versioned = HPABulkDownloadModel(file_type="xml", version="24")
    print(f"Versioned bulk URL: {bulk_versioned.build_url()}")
