"""PubChem API data models with Pydantic validation.

PubChem provides two REST APIs:

1. PUG REST - Programmatic access to structured data:
   https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}/{namespace}/{identifiers}/{operation}/{output}

   Used for: compounds, substances, assays, properties, searches, etc.

2. PUG View - Access to annotation/web page content:
   https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/{record_type}/{record_id}/{output}

   Used for: detailed annotations, descriptions, safety data, literature, patents, etc.

Reference:
- https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
- https://pubchem.ncbi.nlm.nih.gov/docs/pug-view
"""

from enum import Enum
from pydantic import BaseModel, model_validator, ConfigDict
from typing import Dict, Any, Optional, List, Union


# =============================================================================
# PUG REST Enums and Model
# =============================================================================

class PUGRestDomain(Enum):
    """PUG REST database domains."""
    compound = "compound"
    substance = "substance"
    assay = "assay"
    gene = "gene"
    protein = "protein"
    pathway = "pathway"
    taxonomy = "taxonomy"
    cell = "cell"


class PUGRestNamespace(Enum):
    """Namespaces for identifying records in PUG REST."""
    # Compound namespaces
    cid = "cid"
    name = "name"
    smiles = "smiles"
    inchi = "inchi"
    inchikey = "inchikey"
    formula = "formula"
    sdf = "sdf"
    # Substance namespaces
    sid = "sid"
    sourceid = "sourceid"
    sourceall = "sourceall"
    # Assay namespaces
    aid = "aid"
    # Gene/protein namespaces
    geneid = "geneid"
    genesymbol = "genesymbol"
    synonym = "synonym"
    accession = "accession"
    gi = "gi"
    # Search namespaces
    substructure = "substructure"
    superstructure = "superstructure"
    similarity = "similarity"
    identity = "identity"
    fastidentity = "fastidentity"
    fastsimilarity_2d = "fastsimilarity_2d"
    fastsimilarity_3d = "fastsimilarity_3d"
    fastsubstructure = "fastsubstructure"
    fastsuperstructure = "fastsuperstructure"
    fastformula = "fastformula"
    # Cross-reference
    xref = "xref"
    # Async list key
    listkey = "listkey"


class PUGRestOperation(Enum):
    """Operations for PUG REST."""
    record = "record"
    property = "property"
    synonyms = "synonyms"
    sids = "sids"
    cids = "cids"
    aids = "aids"
    assaysummary = "assaysummary"
    classification = "classification"
    description = "description"
    conformers = "conformers"
    xrefs = "xrefs"
    summary = "summary"
    concise = "concise"
    targets = "targets"
    doseresponse = "doseresponse"


class PUGRestOutput(Enum):
    """Output formats for PUG REST."""
    JSON = "JSON"
    XML = "XML"
    CSV = "CSV"
    TXT = "TXT"
    SDF = "SDF"
    PNG = "PNG"
    ASNT = "ASNT"


# Valid namespaces per domain
PUGREST_DOMAIN_NAMESPACES = {
    PUGRestDomain.compound: [
        PUGRestNamespace.cid, PUGRestNamespace.name, PUGRestNamespace.smiles,
        PUGRestNamespace.inchi, PUGRestNamespace.inchikey, PUGRestNamespace.formula,
        PUGRestNamespace.sdf, PUGRestNamespace.substructure, PUGRestNamespace.superstructure,
        PUGRestNamespace.similarity, PUGRestNamespace.identity,
        PUGRestNamespace.fastidentity, PUGRestNamespace.fastsimilarity_2d,
        PUGRestNamespace.fastsimilarity_3d, PUGRestNamespace.fastsubstructure,
        PUGRestNamespace.fastsuperstructure, PUGRestNamespace.fastformula,
        PUGRestNamespace.xref, PUGRestNamespace.listkey,
    ],
    PUGRestDomain.substance: [
        PUGRestNamespace.sid, PUGRestNamespace.sourceid, PUGRestNamespace.sourceall,
        PUGRestNamespace.name, PUGRestNamespace.xref, PUGRestNamespace.listkey,
    ],
    PUGRestDomain.assay: [
        PUGRestNamespace.aid, PUGRestNamespace.listkey,
    ],
    PUGRestDomain.gene: [
        PUGRestNamespace.geneid, PUGRestNamespace.genesymbol, PUGRestNamespace.synonym,
    ],
    PUGRestDomain.protein: [
        PUGRestNamespace.accession, PUGRestNamespace.gi, PUGRestNamespace.synonym,
    ],
    PUGRestDomain.pathway: [
        PUGRestNamespace.accession,
    ],
    PUGRestDomain.taxonomy: [
        PUGRestNamespace.synonym,
    ],
    PUGRestDomain.cell: [
        PUGRestNamespace.synonym,
    ],
}

# Valid operations per domain
PUGREST_DOMAIN_OPERATIONS = {
    PUGRestDomain.compound: [
        PUGRestOperation.record, PUGRestOperation.property, PUGRestOperation.synonyms,
        PUGRestOperation.sids, PUGRestOperation.cids, PUGRestOperation.aids,
        PUGRestOperation.assaysummary, PUGRestOperation.classification,
        PUGRestOperation.description, PUGRestOperation.conformers, PUGRestOperation.xrefs,
    ],
    PUGRestDomain.substance: [
        PUGRestOperation.record, PUGRestOperation.synonyms, PUGRestOperation.sids,
        PUGRestOperation.cids, PUGRestOperation.aids, PUGRestOperation.assaysummary,
        PUGRestOperation.classification, PUGRestOperation.xrefs, PUGRestOperation.description,
    ],
    PUGRestDomain.assay: [
        PUGRestOperation.record, PUGRestOperation.concise, PUGRestOperation.sids,
        PUGRestOperation.cids, PUGRestOperation.aids, PUGRestOperation.summary,
        PUGRestOperation.classification, PUGRestOperation.xrefs, PUGRestOperation.description,
        PUGRestOperation.targets, PUGRestOperation.doseresponse,
    ],
    PUGRestDomain.gene: [
        PUGRestOperation.summary, PUGRestOperation.aids, PUGRestOperation.concise,
    ],
    PUGRestDomain.protein: [
        PUGRestOperation.summary, PUGRestOperation.aids, PUGRestOperation.concise,
    ],
    PUGRestDomain.pathway: [
        PUGRestOperation.summary, PUGRestOperation.cids,
    ],
    PUGRestDomain.taxonomy: [
        PUGRestOperation.summary, PUGRestOperation.aids,
    ],
    PUGRestDomain.cell: [
        PUGRestOperation.summary, PUGRestOperation.aids,
    ],
}

# Compound properties available via property operation
COMPOUND_PROPERTIES = [
    "MolecularFormula", "MolecularWeight", "CanonicalSMILES", "IsomericSMILES",
    "InChI", "InChIKey", "IUPACName", "Title", "XLogP", "ExactMass",
    "MonoisotopicMass", "TPSA", "Complexity", "Charge", "HBondDonorCount",
    "HBondAcceptorCount", "RotatableBondCount", "HeavyAtomCount", "IsotopeAtomCount",
    "AtomStereoCount", "DefinedAtomStereoCount", "UndefinedAtomStereoCount",
    "BondStereoCount", "DefinedBondStereoCount", "UndefinedBondStereoCount",
    "CovalentUnitCount", "Volume3D", "XStericQuadrupole3D", "YStericQuadrupole3D",
    "ZStericQuadrupole3D", "FeatureCount3D", "FeatureAcceptorCount3D",
    "FeatureDonorCount3D", "FeatureAnionCount3D", "FeatureCationCount3D",
    "FeatureRingCount3D", "FeatureHydrophobeCount3D", "ConformerModelRMSD3D",
    "EffectiveRotorCount3D", "ConformerCount3D", "Fingerprint2D",
]


class PUGRestModel(BaseModel):
    """Pydantic model for PUG REST API request validation."""
    model_config = ConfigDict(use_enum_values=True)

    domain: PUGRestDomain
    namespace: PUGRestNamespace
    identifiers: Optional[Union[str, List[Union[str, int]]]] = None
    operation: Optional[PUGRestOperation] = None
    properties: Optional[List[str]] = None
    output: PUGRestOutput = PUGRestOutput.JSON
    # For structure searches
    search_type: Optional[str] = None  # smiles, smarts, inchi, sdf, cid
    # Query parameters
    threshold: Optional[int] = None  # For similarity search (0-100)
    max_records: Optional[int] = None

    @model_validator(mode="after")
    def validate_namespace_for_domain(self):
        """Validate namespace is valid for the domain."""
        domain_enum = PUGRestDomain(self.domain)
        namespace_enum = PUGRestNamespace(self.namespace)
        valid_namespaces = PUGREST_DOMAIN_NAMESPACES.get(domain_enum, [])
        if valid_namespaces and namespace_enum not in valid_namespaces:
            valid_names = [ns.value for ns in valid_namespaces]
            raise ValueError(
                f"Namespace '{self.namespace}' is not valid for domain '{self.domain}'. "
                f"Valid namespaces: {valid_names}"
            )
        return self

    @model_validator(mode="after")
    def validate_operation_for_domain(self):
        """Validate operation is valid for the domain."""
        if self.operation:
            domain_enum = PUGRestDomain(self.domain)
            operation_enum = PUGRestOperation(self.operation)
            valid_ops = PUGREST_DOMAIN_OPERATIONS.get(domain_enum, [])
            if valid_ops and operation_enum not in valid_ops:
                valid_names = [op.value for op in valid_ops]
                raise ValueError(
                    f"Operation '{self.operation}' is not valid for domain '{self.domain}'. "
                    f"Valid operations: {valid_names}"
                )
        return self

    @model_validator(mode="after")
    def validate_properties(self):
        """Validate properties for property operation."""
        if self.operation == PUGRestOperation.property.value:
            if not self.properties:
                raise ValueError("properties list is required for property operation")
            for prop in self.properties:
                if prop not in COMPOUND_PROPERTIES:
                    raise ValueError(
                        f"Invalid property '{prop}'. Valid properties: {COMPOUND_PROPERTIES}"
                    )
        return self

    @model_validator(mode="after")
    def validate_similarity_threshold(self):
        """Validate similarity threshold."""
        if self.threshold is not None:
            if not (0 <= self.threshold <= 100):
                raise ValueError("threshold must be between 0 and 100")
        return self

    def build_path(self) -> str:
        """Build the URL path component for PUG REST."""
        parts = [self.domain]
        parts.append(self.namespace)

        # Check if this is a structure search namespace
        search_namespaces = [
            PUGRestNamespace.substructure.value, PUGRestNamespace.superstructure.value,
            PUGRestNamespace.similarity.value, PUGRestNamespace.identity.value,
            PUGRestNamespace.fastidentity.value, PUGRestNamespace.fastsimilarity_2d.value,
            PUGRestNamespace.fastsimilarity_3d.value, PUGRestNamespace.fastsubstructure.value,
            PUGRestNamespace.fastsuperstructure.value, PUGRestNamespace.fastformula.value,
        ]

        if self.namespace in search_namespaces:
            # Structure search: /compound/fastsimilarity_2d/smiles/CCCC/cids/JSON
            if self.search_type:
                parts.append(self.search_type)
            if self.identifiers:
                ids = self._format_identifiers()
                parts.append(ids)
        else:
            # Regular lookup
            if self.identifiers:
                ids = self._format_identifiers()
                parts.append(ids)

        # Add operation
        if self.operation:
            if self.operation == PUGRestOperation.property.value and self.properties:
                prop_list = ",".join(self.properties)
                parts.append(f"property/{prop_list}")
            else:
                parts.append(self.operation)

        # Add output format
        output = self.output if isinstance(self.output, str) else self.output
        parts.append(output)

        return "/".join(parts)

    def _format_identifiers(self) -> str:
        """Format identifiers for URL."""
        if isinstance(self.identifiers, list):
            return ",".join(str(i) for i in self.identifiers)
        return str(self.identifiers)

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for PUG REST."""
        params = {}
        if self.threshold is not None:
            params["Threshold"] = self.threshold
        if self.max_records is not None:
            params["MaxRecords"] = self.max_records
        return params


# =============================================================================
# PUG View Enums and Model
# =============================================================================

class PUGViewRecordType(Enum):
    """Record types for PUG View API."""
    compound = "compound"
    substance = "substance"
    assay = "assay"
    gene = "gene"
    protein = "protein"
    cell = "cell"
    source = "source"
    sourcetable = "sourcetable"
    element = "element"
    annotation = "annotation"
    heading = "heading"


class PUGViewOutput(Enum):
    """Output formats for PUG View."""
    JSON = "JSON"
    XML = "XML"


class PUGViewHeading(Enum):
    """Common headings for PUG View annotation retrieval."""
    # Compound headings
    names_and_identifiers = "Names and Identifiers"
    chemical_and_physical_properties = "Chemical and Physical Properties"
    related_records = "Related Records"
    drug_and_medication_information = "Drug and Medication Information"
    pharmacology_and_biochemistry = "Pharmacology and Biochemistry"
    safety_and_hazards = "Safety and Hazards"
    toxicity = "Toxicity"
    literature = "Literature"
    patents = "Patents"
    biomolecular_interactions = "Biomolecular Interactions and Pathways"
    biological_test_results = "Biological Test Results"
    classification = "Classification"
    # General
    information = "Information"


class PUGViewModel(BaseModel):
    """Pydantic model for PUG View API request validation.

    PUG View URL format:
        /rest/pug_view/data/{record_type}/{record_id}/{output}
        /rest/pug_view/data/{record_type}/{record_id}/{output}?heading={heading}
    """
    model_config = ConfigDict(use_enum_values=True)

    record_type: PUGViewRecordType
    record_id: Union[int, str]
    output: PUGViewOutput = PUGViewOutput.JSON
    heading: Optional[str] = None  # Filter to specific heading/section

    def build_path(self) -> str:
        """Build the URL path component for PUG View."""
        output = self.output if isinstance(self.output, str) else self.output
        return f"data/{self.record_type}/{self.record_id}/{output}"

    def build_query_params(self) -> Dict[str, Any]:
        """Build query parameters for PUG View."""
        params = {}
        if self.heading:
            params["heading"] = self.heading
        return params


# =============================================================================
# Convenience aliases
# =============================================================================

# For backwards compatibility
PubChemModel = PUGRestModel
PubChemDomain = PUGRestDomain
PubChemNamespace = PUGRestNamespace
PubChemOperation = PUGRestOperation
PubChemOutput = PUGRestOutput


if __name__ == "__main__":
    # Test PUG REST model
    print("=== PUG REST Tests ===")
    model = PUGRestModel(
        domain="compound",
        namespace="cid",
        identifiers=[2244],
        output="JSON"
    )
    print(f"Basic path: {model.build_path()}")

    prop_model = PUGRestModel(
        domain="compound",
        namespace="cid",
        identifiers=[2244, 3672],
        operation="property",
        properties=["MolecularFormula", "MolecularWeight"],
        output="JSON"
    )
    print(f"Property path: {prop_model.build_path()}")

    # Test PUG View model
    print("\n=== PUG View Tests ===")
    view_model = PUGViewModel(
        record_type="compound",
        record_id=2244,
        output="JSON"
    )
    print(f"View path: {view_model.build_path()}")

    view_model_heading = PUGViewModel(
        record_type="compound",
        record_id=2244,
        output="JSON",
        heading="Safety and Hazards"
    )
    print(f"View with heading: {view_model_heading.build_path()}")
    print(f"Query params: {view_model_heading.build_query_params()}")
