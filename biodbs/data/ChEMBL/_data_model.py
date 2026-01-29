"""ChEMBL API data model with Pydantic validation.

ChEMBL REST API structure:
    https://www.ebi.ac.uk/chembl/api/data/{resource}.{format}
    https://www.ebi.ac.uk/chembl/api/data/{resource}/{chembl_id}.{format}
    https://www.ebi.ac.uk/chembl/api/data/{resource}/search.{format}?q={query}

Supported operations:
    - List: GET /data/{resource} - list all entries with pagination
    - Get by ID: GET /data/{resource}/{chembl_id} - get specific entry
    - Search: GET /data/{resource}/search?q={query} - full-text search
    - Filter: GET /data/{resource}?{field}={value} - filter by field

Common parameters:
    - limit: max records per page (default 20, max 1000)
    - offset: pagination offset
    - format: json or xml (default json)
"""

from enum import Enum
from pydantic import BaseModel, model_validator, ConfigDict, field_validator
from typing import Dict, Any, Optional, List, Union


class ChEMBLResource(Enum):
    """Available ChEMBL API resources."""
    activity = "activity"
    assay = "assay"
    atc_class = "atc_class"
    binding_site = "binding_site"
    biotherapeutic = "biotherapeutic"
    cell_line = "cell_line"
    chembl_id_lookup = "chembl_id_lookup"
    compound_record = "compound_record"
    compound_structural_alert = "compound_structural_alert"
    document = "document"
    document_similarity = "document_similarity"
    drug = "drug"
    drug_indication = "drug_indication"
    drug_warning = "drug_warning"
    go_slim = "go_slim"
    mechanism = "mechanism"
    metabolism = "metabolism"
    molecule = "molecule"
    molecule_form = "molecule_form"
    organism = "organism"
    protein_class = "protein_class"
    source = "source"
    target = "target"
    target_component = "target_component"
    target_relation = "target_relation"
    tissue = "tissue"
    # Special endpoints
    image = "image"
    substructure = "substructure"
    similarity = "similarity"
    status = "status"


class ChEMBLFormat(Enum):
    """Output formats for ChEMBL API."""
    json = "json"
    xml = "xml"


# Common filterable fields per resource
RESOURCE_FILTER_FIELDS = {
    ChEMBLResource.activity: [
        "activity_id", "assay_chembl_id", "assay_description", "assay_type",
        "canonical_smiles", "document_chembl_id", "molecule_chembl_id",
        "molecule_pref_name", "pchembl_value", "standard_relation",
        "standard_type", "standard_units", "standard_value",
        "target_chembl_id", "target_organism", "target_pref_name",
    ],
    ChEMBLResource.assay: [
        "assay_chembl_id", "assay_cell_type", "assay_organism",
        "assay_strain", "assay_subcellular_fraction", "assay_tax_id",
        "assay_tissue", "assay_type", "assay_type_description",
        "bao_format", "bao_label", "cell_chembl_id", "confidence_description",
        "confidence_score", "document_chembl_id", "relationship_description",
        "relationship_type", "src_assay_id", "src_id", "target_chembl_id",
        "tissue_chembl_id", "variant_sequence",
    ],
    ChEMBLResource.molecule: [
        "availability_type", "biotherapeutic", "black_box_warning",
        "chebi_par_id", "chirality", "dosed_ingredient", "first_approval",
        "first_in_class", "helm_notation", "indication_class", "inorganic_flag",
        "max_phase", "molecule_chembl_id", "molecule_hierarchy",
        "molecule_properties", "molecule_structures", "molecule_synonyms",
        "molecule_type", "natural_product", "oral", "parenteral",
        "polymer_flag", "pref_name", "prodrug", "structure_type",
        "therapeutic_flag", "topical", "usan_stem", "usan_stem_definition",
        "usan_substem", "usan_year", "withdrawn_class", "withdrawn_country",
        "withdrawn_flag", "withdrawn_reason", "withdrawn_year",
    ],
    ChEMBLResource.target: [
        "cross_references", "organism", "pref_name", "species_group_flag",
        "target_chembl_id", "target_components", "target_type",
        "tax_id",
    ],
    ChEMBLResource.drug: [
        "applicants", "atc_classifications", "availability_type",
        "biotherapeutic", "black_box_warning", "chirality", "development_phase",
        "drug_type", "first_approval", "first_in_class", "helm_notation",
        "indication_class", "inorganic_flag", "max_phase", "molecule_chembl_id",
        "molecule_properties", "molecule_structures", "molecule_synonyms",
        "molecule_type", "natural_product", "ob_patent", "oral", "parenteral",
        "polymer_flag", "pref_name", "prodrug", "research_codes", "rule_of_five",
        "sc_patent", "structure_type", "therapeutic_flag", "topical",
        "trade_names", "usan_stem", "usan_stem_definition", "usan_substem",
        "usan_year", "withdrawn_class", "withdrawn_country", "withdrawn_flag",
        "withdrawn_reason", "withdrawn_year",
    ],
    ChEMBLResource.drug_indication: [
        "drugind_id", "efo_id", "efo_term", "indication_refs",
        "max_phase_for_ind", "mesh_heading", "mesh_id", "molecule_chembl_id",
        "parent_molecule_chembl_id",
    ],
    ChEMBLResource.mechanism: [
        "action_type", "binding_site_comment", "direct_interaction",
        "disease_efficacy", "mec_id", "mechanism_comment", "mechanism_of_action",
        "mechanism_refs", "molecular_mechanism", "molecule_chembl_id",
        "parent_molecule_chembl_id", "record_id", "selectivity_comment",
        "site_id", "target_chembl_id",
    ],
    ChEMBLResource.document: [
        "abstract", "authors", "doc_type", "document_chembl_id", "doi",
        "first_page", "issue", "journal", "journal_full_title", "last_page",
        "patent_id", "pubmed_id", "src_id", "title", "volume", "year",
    ],
    ChEMBLResource.cell_line: [
        "cell_chembl_id", "cell_description", "cell_id", "cell_name",
        "cell_source_organism", "cell_source_tax_id", "cell_source_tissue",
        "cellosaurus_id", "cl_lincs_id", "clo_id", "efo_id",
    ],
}


class ChEMBLModel(BaseModel):
    """Pydantic model for ChEMBL API request validation.

    Validates:
        - resource: Must be a valid ChEMBL resource
        - chembl_id: Optional ChEMBL ID for single-entry lookup
        - search_query: Optional full-text search query
        - filters: Optional field filters
        - limit: Must be 1-1000
        - offset: Must be >= 0
        - format: Must be json or xml
    """
    model_config = ConfigDict(use_enum_values=True)

    resource: ChEMBLResource
    chembl_id: Optional[str] = None
    search_query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    format: ChEMBLFormat = ChEMBLFormat.json
    # For similarity/substructure search
    smiles: Optional[str] = None
    similarity_threshold: Optional[int] = None

    @field_validator("chembl_id")
    @classmethod
    def validate_chembl_id(cls, v):
        """Validate ChEMBL ID format."""
        if v is not None:
            v = v.upper()
            if not v.startswith("CHEMBL"):
                raise ValueError(
                    f"Invalid ChEMBL ID format: {v}. "
                    "Must start with 'CHEMBL' (e.g., CHEMBL25)"
                )
        return v

    @model_validator(mode="after")
    def validate_limit(self):
        """Validate limit is within bounds."""
        if self.limit is not None:
            if not (1 <= self.limit <= 1000):
                raise ValueError("limit must be between 1 and 1000")
        return self

    @model_validator(mode="after")
    def validate_offset(self):
        """Validate offset is non-negative."""
        if self.offset is not None:
            if self.offset < 0:
                raise ValueError("offset must be >= 0")
        return self

    @model_validator(mode="after")
    def validate_operation_mode(self):
        """Ensure only one operation mode is specified."""
        modes = [
            self.chembl_id is not None,
            self.search_query is not None,
            self.smiles is not None,
        ]
        if sum(modes) > 1:
            raise ValueError(
                "Only one of chembl_id, search_query, or smiles can be specified"
            )
        return self

    @model_validator(mode="after")
    def validate_similarity_params(self):
        """Validate similarity search parameters."""
        if self.resource == ChEMBLResource.similarity.value:
            if self.smiles is None:
                raise ValueError(
                    "smiles is required for similarity search"
                )
            if self.similarity_threshold is not None:
                if not (40 <= self.similarity_threshold <= 100):
                    raise ValueError(
                        "similarity_threshold must be between 40 and 100"
                    )
        return self

    @model_validator(mode="after")
    def validate_substructure_params(self):
        """Validate substructure search parameters."""
        if self.resource == ChEMBLResource.substructure.value:
            if self.smiles is None:
                raise ValueError(
                    "smiles is required for substructure search"
                )
        return self

    @model_validator(mode="after")
    def validate_filters(self):
        """Validate filter fields against known fields for resource."""
        if self.filters:
            resource_enum = ChEMBLResource(self.resource)
            valid_fields = RESOURCE_FILTER_FIELDS.get(resource_enum, [])
            if valid_fields:  # Only validate if we have a known field list
                for field in self.filters.keys():
                    # Allow nested field access with __
                    base_field = field.split("__")[0]
                    if base_field not in valid_fields:
                        raise ValueError(
                            f"Invalid filter field '{field}' for resource '{self.resource}'. "
                            f"Valid fields: {sorted(valid_fields)}"
                        )
        return self

    def build_path(self) -> str:
        """Build the URL path component."""
        resource = self.resource

        if self.chembl_id:
            return f"{resource}/{self.chembl_id}"
        elif self.search_query:
            return f"{resource}/search"
        elif self.smiles:
            if resource == ChEMBLResource.similarity.value:
                threshold = self.similarity_threshold or 70
                return f"{resource}/{self.smiles}/{threshold}"
            else:  # substructure
                return f"{resource}/{self.smiles}"
        else:
            return resource

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for the request."""
        params = {}

        if self.search_query:
            params["q"] = self.search_query

        if self.filters:
            params.update(self.filters)

        if self.limit is not None:
            params["limit"] = self.limit

        if self.offset is not None:
            params["offset"] = self.offset

        # Extract enum value for format
        fmt = self.format.value if hasattr(self.format, "value") else self.format
        params["format"] = fmt

        return params


if __name__ == "__main__":
    # Test basic validation
    model = ChEMBLModel(resource="molecule", chembl_id="CHEMBL25", limit=10)
    print(f"Path: {model.build_path()}")
    print(f"Params: {model.build_query_params()}")

    # Test search
    search_model = ChEMBLModel(
        resource="molecule",
        search_query="aspirin",
        limit=5
    )
    print(f"Search path: {search_model.build_path()}")
    print(f"Search params: {search_model.build_query_params()}")

    # Test filters
    filter_model = ChEMBLModel(
        resource="activity",
        filters={"target_chembl_id": "CHEMBL240", "pchembl_value__gte": 5},
        limit=100
    )
    print(f"Filter path: {filter_model.build_path()}")
    print(f"Filter params: {filter_model.build_query_params()}")
