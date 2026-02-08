"""BioMart API data models with Pydantic validation.

BioMart (Ensembl) provides access to genomic data through a hierarchical structure:

1. Server - Contains multiple marts
   URL: http://{host}/biomart/martservice?type=registry

2. Mart - Contains multiple datasets
   URL: http://{host}/biomart/martservice?type=datasets&mart={mart_name}

3. Dataset - Contains filters and attributes for queries
   URL: http://{host}/biomart/martservice?type=configuration&dataset={dataset_name}

4. Query - XML-based query with filters and attributes
   URL: http://{host}/biomart/martservice?query={xml_query}

Reference:
- https://www.ensembl.org/info/data/biomart/biomart_restful.html
- https://www.ensembl.org/biomart/martview
"""

from enum import Enum
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Dict, Any, Optional, List, Union
import xml.etree.ElementTree as ET


class BioMartHost(str, Enum):
    """Available BioMart/Ensembl hosts."""
    main = "www.ensembl.org"
    # GRCh37 archive (hg19)
    grch37 = "grch37.ensembl.org"
    # Ensembl release archives
    ensembl_115 = "sep2025.archive.ensembl.org"
    ensembl_114 = "may2025.archive.ensembl.org"
    ensembl_113 = "oct2024.archive.ensembl.org"
    ensembl_112 = "may2024.archive.ensembl.org"
    ensembl_111 = "jan2024.archive.ensembl.org"
    ensembl_110 = "jul2023.archive.ensembl.org"
    ensembl_109 = "feb2023.archive.ensembl.org"
    ensembl_108 = "oct2022.archive.ensembl.org"
    ensembl_107 = "jul2022.archive.ensembl.org"
    ensembl_106 = "apr2022.archive.ensembl.org"
    ensembl_105 = "dec2021.archive.ensembl.org"
    ensembl_104 = "may2021.archive.ensembl.org"
    ensembl_103 = "feb2021.archive.ensembl.org"
    ensembl_102 = "nov2020.archive.ensembl.org"
    ensembl_101 = "aug2020.archive.ensembl.org"
    ensembl_100 = "apr2020.archive.ensembl.org"
    ensembl_80 = "may2015.archive.ensembl.org"
    ensembl_77 = "oct2014.archive.ensembl.org"
    ensembl_75 = "feb2014.archive.ensembl.org"
    ensembl_54 = "may2009.archive.ensembl.org"
    # Specialized
    plants = "plants.ensembl.org"
    fungi = "fungi.ensembl.org"
    protists = "protists.ensembl.org"
    metazoa = "metazoa.ensembl.org"
    bacteria = "bacteria.ensembl.org"


class BioMartMart(str, Enum):
    """Common BioMart mart names."""
    ensembl = "ENSEMBL_MART_ENSEMBL"
    mouse = "ENSEMBL_MART_MOUSE"
    sequence = "ENSEMBL_MART_SEQUENCE"
    ontology = "ENSEMBL_MART_ONTOLOGY"
    genomic = "ENSEMBL_MART_GENOMIC"
    snp = "ENSEMBL_MART_SNP"
    funcgen = "ENSEMBL_MART_FUNCGEN"


class BioMartDataset(str, Enum):
    """Common BioMart dataset names."""
    # Human
    hsapiens_gene = "hsapiens_gene_ensembl"
    hsapiens_snp = "hsapiens_snp"
    hsapiens_structvar = "hsapiens_structvar"
    # Mouse
    mmusculus_gene = "mmusculus_gene_ensembl"
    # Rat
    rnorvegicus_gene = "rnorvegicus_gene_ensembl"
    # Zebrafish
    drerio_gene = "drerio_gene_ensembl"
    # Fly
    dmelanogaster_gene = "dmelanogaster_gene_ensembl"
    # Worm
    celegans_gene = "celegans_gene_ensembl"
    # Yeast
    scerevisiae_gene = "scerevisiae_gene_ensembl"


class BioMartQueryType(str, Enum):
    """BioMart query types."""
    registry = "registry"
    datasets = "datasets"
    configuration = "configuration"
    attributes = "attributes"
    filters = "filters"


# Common attributes for gene queries
COMMON_GENE_ATTRIBUTES = [
    "ensembl_gene_id",
    "ensembl_transcript_id",
    "ensembl_peptide_id",
    "external_gene_name",
    "gene_biotype",
    "transcript_biotype",
    "chromosome_name",
    "start_position",
    "end_position",
    "strand",
    "description",
]

# Common attributes for sequence queries
COMMON_SEQUENCE_ATTRIBUTES = [
    "ensembl_gene_id",
    "ensembl_transcript_id",
    "cdna",
    "coding",
    "peptide",
    "gene_exon_intron",
    "5utr",
    "3utr",
]

# Common filters
COMMON_FILTERS = [
    "ensembl_gene_id",
    "ensembl_transcript_id",
    "external_gene_name",
    "chromosome_name",
    "biotype",
]

# Default query attributes
DEFAULT_QUERY_ATTRIBUTES = [
    "ensembl_gene_id",
    "external_gene_name",
    "description",
    "chromosome_name",
    "start_position",
    "end_position",
]


class BioMartServerModel(BaseModel):
    """Model for BioMart server registry request."""
    model_config = ConfigDict(use_enum_values=True)

    host: BioMartHost = BioMartHost.main

    def build_url(self) -> str:
        """Build the URL for registry request."""
        return f"http://{self.host}/biomart/martservice"

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for registry."""
        return {"type": "registry"}


class BioMartMartModel(BaseModel):
    """Model for BioMart mart datasets request."""
    model_config = ConfigDict(use_enum_values=True)

    host: BioMartHost = BioMartHost.main
    mart: str = BioMartMart.ensembl

    def build_url(self) -> str:
        """Build the URL for datasets request."""
        return f"http://{self.host}/biomart/martservice"

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for datasets."""
        mart = self.mart if isinstance(self.mart, str) else self.mart.value
        return {"type": "datasets", "mart": mart}


class BioMartConfigModel(BaseModel):
    """Model for BioMart dataset configuration request."""
    model_config = ConfigDict(use_enum_values=True)

    host: BioMartHost = BioMartHost.main
    dataset: str = BioMartDataset.hsapiens_gene

    def build_url(self) -> str:
        """Build the URL for configuration request."""
        return f"http://{self.host}/biomart/martservice"

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for configuration."""
        dataset = self.dataset if isinstance(self.dataset, str) else self.dataset.value
        return {"type": "configuration", "dataset": dataset}


class BioMartQueryModel(BaseModel):
    """Model for BioMart data query with XML.

    BioMart queries are XML-based with the structure:
    <Query>
        <Dataset name="..." interface="default">
            <Filter name="..." value="..."/>
            <Attribute name="..."/>
        </Dataset>
    </Query>
    """
    model_config = ConfigDict(use_enum_values=True)

    host: BioMartHost = BioMartHost.main
    dataset: str = BioMartDataset.hsapiens_gene
    attributes: List[str]
    filters: Optional[Dict[str, Union[str, List[str]]]] = None
    unique_rows: bool = True
    header: bool = True

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, v: List[str]) -> List[str]:
        """Validate attributes list is not empty."""
        if not v:
            raise ValueError("Attributes list cannot be empty")
        return v

    def build_url(self) -> str:
        """Build the URL for query request."""
        return f"http://{self.host}/biomart/martservice"

    def build_xml_query(self) -> str:
        """Build the XML query string."""
        # Create Query element
        query = ET.Element("Query")
        query.set("virtualSchemaName", "default")
        query.set("formatter", "TSV")
        query.set("header", "1" if self.header else "0")
        query.set("uniqueRows", "1" if self.unique_rows else "0")
        query.set("datasetConfigVersion", "0.6")

        # Create Dataset element
        dataset = self.dataset if isinstance(self.dataset, str) else self.dataset.value
        dataset_elem = ET.SubElement(query, "Dataset")
        dataset_elem.set("name", dataset)
        dataset_elem.set("interface", "default")

        # Add Filters
        if self.filters:
            for filter_name, filter_value in self.filters.items():
                filter_elem = ET.SubElement(dataset_elem, "Filter")
                filter_elem.set("name", filter_name)
                if isinstance(filter_value, list):
                    filter_elem.set("value", ",".join(str(v) for v in filter_value))
                else:
                    filter_elem.set("value", str(filter_value))

        # Add Attributes
        for attr in self.attributes:
            attr_elem = ET.SubElement(dataset_elem, "Attribute")
            attr_elem.set("name", attr)

        return ET.tostring(query, encoding="unicode")

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters with XML."""
        return {"query": self.build_xml_query()}


class BioMartBatchQueryModel(BaseModel):
    """Model for batched BioMart queries.

    BioMart has limits on query size, so large filter lists need batching.
    This model helps manage batching of filter values.
    """
    model_config = ConfigDict(use_enum_values=True)

    host: BioMartHost = BioMartHost.main
    dataset: str = BioMartDataset.hsapiens_gene
    attributes: List[str]
    filter_name: str
    filter_values: List[str]
    batch_size: int = 500
    unique_rows: bool = True
    header: bool = True

    @field_validator("filter_values")
    @classmethod
    def validate_filter_values(cls, v: List[str]) -> List[str]:
        """Validate filter values list is not empty."""
        if not v:
            raise ValueError("Filter values list cannot be empty")
        return v

    def get_batches(self) -> List[List[str]]:
        """Split filter values into batches."""
        return [
            self.filter_values[i:i + self.batch_size]
            for i in range(0, len(self.filter_values), self.batch_size)
        ]

    def build_query_for_batch(self, batch: List[str]) -> BioMartQueryModel:
        """Build a query model for a single batch."""
        return BioMartQueryModel(
            host=self.host,
            dataset=self.dataset,
            attributes=self.attributes,
            filters={self.filter_name: batch},
            unique_rows=self.unique_rows,
            header=self.header,
        )


if __name__ == "__main__":
    # Test BioMartServerModel
    print("=== BioMartServerModel Tests ===")
    server = BioMartServerModel(host="www.ensembl.org")
    print(f"URL: {server.build_url()}")
    print(f"Params: {server.build_query_params()}")

    # Test BioMartMartModel
    print("\n=== BioMartMartModel Tests ===")
    mart = BioMartMartModel(host="www.ensembl.org", mart="ENSEMBL_MART_ENSEMBL")
    print(f"URL: {mart.build_url()}")
    print(f"Params: {mart.build_query_params()}")

    # Test BioMartConfigModel
    print("\n=== BioMartConfigModel Tests ===")
    config = BioMartConfigModel(dataset="hsapiens_gene_ensembl")
    print(f"URL: {config.build_url()}")
    print(f"Params: {config.build_query_params()}")

    # Test BioMartQueryModel
    print("\n=== BioMartQueryModel Tests ===")
    query = BioMartQueryModel(
        dataset="hsapiens_gene_ensembl",
        attributes=["ensembl_gene_id", "external_gene_name"],
        filters={"ensembl_gene_id": ["ENSG00000141510", "ENSG00000012048"]},
    )
    print(f"URL: {query.build_url()}")
    print(f"XML Query:\n{query.build_xml_query()}")

    # Test BioMartBatchQueryModel
    print("\n=== BioMartBatchQueryModel Tests ===")
    batch_query = BioMartBatchQueryModel(
        dataset="hsapiens_gene_ensembl",
        attributes=["ensembl_gene_id", "external_gene_name"],
        filter_name="ensembl_gene_id",
        filter_values=["ENSG" + str(i).zfill(11) for i in range(1200)],
        batch_size=500,
    )
    batches = batch_query.get_batches()
    print(f"Total values: 1200, Batch size: 500, Num batches: {len(batches)}")
