"""Pydantic models for UniProt REST API requests and responses."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class UniProtBase(str, Enum):
    """UniProt REST API base URL."""

    BASE = "https://rest.uniprot.org"


class UniProtEndpoint(str, Enum):
    """UniProt REST API endpoints."""

    # Entry retrieval
    ENTRY = "uniprotkb/{accession}"

    # Search and stream
    SEARCH = "uniprotkb/search"
    STREAM = "uniprotkb/stream"

    # ID mapping
    IDMAPPING_RUN = "idmapping/run"
    IDMAPPING_STATUS = "idmapping/status/{job_id}"
    IDMAPPING_RESULTS = "idmapping/uniprotkb/results/{job_id}"
    IDMAPPING_STREAM = "idmapping/uniprotkb/results/stream/{job_id}"


class EntryType(str, Enum):
    """UniProtKB entry type."""

    SWISSPROT = "UniProtKB reviewed (Swiss-Prot)"
    TREMBL = "UniProtKB unreviewed (TrEMBL)"
    INACTIVE = "Inactive"
    UNKNOWN = "UNKNOWN"


class ProteinExistence(str, Enum):
    """Protein existence evidence level."""

    PROTEIN_LEVEL = "1: Evidence at protein level"
    TRANSCRIPT_LEVEL = "2: Evidence at transcript level"
    HOMOLOGY = "3: Inferred from homology"
    PREDICTED = "4: Predicted"
    UNCERTAIN = "5: Uncertain"
    UNKNOWN = "UNKNOWN"


class CommentType(str, Enum):
    """UniProt comment types."""

    FUNCTION = "FUNCTION"
    CATALYTIC_ACTIVITY = "CATALYTIC ACTIVITY"
    COFACTOR = "COFACTOR"
    ACTIVITY_REGULATION = "ACTIVITY REGULATION"
    PATHWAY = "PATHWAY"
    SUBUNIT = "SUBUNIT"
    INTERACTION = "INTERACTION"
    SUBCELLULAR_LOCATION = "SUBCELLULAR LOCATION"
    TISSUE_SPECIFICITY = "TISSUE SPECIFICITY"
    DISEASE = "DISEASE"
    PTM = "PTM"
    SIMILARITY = "SIMILARITY"
    MISCELLANEOUS = "MISCELLANEOUS"


class FeatureType(str, Enum):
    """UniProt feature types."""

    SIGNAL = "Signal"
    CHAIN = "Chain"
    PEPTIDE = "Peptide"
    DOMAIN = "Domain"
    REPEAT = "Repeat"
    REGION = "Region"
    MOTIF = "Motif"
    ACTIVE_SITE = "Active site"
    BINDING_SITE = "Binding site"
    SITE = "Site"
    MODIFIED_RESIDUE = "Modified residue"
    GLYCOSYLATION = "Glycosylation"
    DISULFIDE_BOND = "Disulfide bond"
    NATURAL_VARIANT = "Natural variant"
    MUTAGENESIS = "Mutagenesis"
    HELIX = "Helix"
    BETA_STRAND = "Beta strand"
    TURN = "Turn"


# ----- Evidence Models -----


class Evidence(BaseModel):
    """Evidence for an annotation."""

    evidenceCode: Optional[str] = Field(default=None, description="Evidence code (ECO)")
    source: Optional[str] = Field(default=None, description="Source database")
    id: Optional[str] = Field(default=None, description="Source ID")

    model_config = ConfigDict(populate_by_name=True)


# ----- Gene Models -----


class GeneName(BaseModel):
    """Gene name with evidence."""

    value: str = Field(..., description="Gene name")
    evidences: Optional[List[Evidence]] = None

    model_config = ConfigDict(populate_by_name=True)


class Gene(BaseModel):
    """Gene information."""

    geneName: Optional[GeneName] = Field(default=None, description="Primary gene name")
    synonyms: Optional[List[GeneName]] = Field(default=None, description="Gene name synonyms")
    orderedLocusNames: Optional[List[GeneName]] = Field(default=None, description="Ordered locus names")
    orfNames: Optional[List[GeneName]] = Field(default=None, description="ORF names")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def primary_name(self) -> Optional[str]:
        """Get primary gene name."""
        return self.geneName.value if self.geneName else None

    @property
    def all_names(self) -> List[str]:
        """Get all gene names including synonyms."""
        names = []
        if self.geneName:
            names.append(self.geneName.value)
        if self.synonyms:
            names.extend(s.value for s in self.synonyms)
        return names


# ----- Organism Models -----


class Organism(BaseModel):
    """Organism information."""

    taxonId: int = Field(..., description="NCBI Taxonomy ID")
    scientificName: str = Field(..., description="Scientific name")
    commonName: Optional[str] = Field(default=None, description="Common name")
    synonyms: Optional[List[str]] = Field(default=None, description="Synonyms")
    lineage: Optional[List[str]] = Field(default=None, description="Taxonomic lineage")

    model_config = ConfigDict(populate_by_name=True)


# ----- Protein Description Models -----


class ProteinNameValue(BaseModel):
    """Protein name value with evidence."""

    value: str = Field(..., description="Name value")
    evidences: Optional[List[Evidence]] = None

    model_config = ConfigDict(populate_by_name=True)


class ECNumber(BaseModel):
    """EC number for enzyme."""

    value: str = Field(..., description="EC number")
    evidences: Optional[List[Evidence]] = None

    model_config = ConfigDict(populate_by_name=True)


class ProteinName(BaseModel):
    """Protein name with full and short names."""

    fullName: Optional[ProteinNameValue] = Field(default=None, description="Full name")
    shortNames: Optional[List[ProteinNameValue]] = Field(default=None, description="Short names")
    ecNumbers: Optional[List[ECNumber]] = Field(default=None, description="EC numbers")

    model_config = ConfigDict(populate_by_name=True)


class ProteinDescription(BaseModel):
    """Protein description with recommended and alternative names."""

    recommendedName: Optional[ProteinName] = Field(default=None, description="Recommended name")
    alternativeNames: Optional[List[ProteinName]] = Field(default=None, description="Alternative names")
    submissionNames: Optional[List[ProteinName]] = Field(default=None, description="Submission names")
    flag: Optional[str] = Field(default=None, description="Description flag")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def full_name(self) -> Optional[str]:
        """Get recommended full name."""
        if self.recommendedName and self.recommendedName.fullName:
            return self.recommendedName.fullName.value
        if self.submissionNames and self.submissionNames[0].fullName:
            return self.submissionNames[0].fullName.value
        return None


# ----- Sequence Models -----


class Sequence(BaseModel):
    """Protein sequence information."""

    value: Optional[str] = Field(default=None, description="Amino acid sequence")
    length: Optional[int] = Field(default=None, description="Sequence length")
    molWeight: Optional[int] = Field(default=None, description="Molecular weight")
    crc64: Optional[str] = Field(default=None, description="CRC64 checksum")
    md5: Optional[str] = Field(default=None, description="MD5 checksum")

    model_config = ConfigDict(populate_by_name=True)


# ----- Feature Models -----


class FeatureLocation(BaseModel):
    """Feature location on sequence."""

    start: Optional[Dict[str, Any]] = Field(default=None, description="Start position")
    end: Optional[Dict[str, Any]] = Field(default=None, description="End position")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def start_position(self) -> Optional[int]:
        """Get start position value."""
        if self.start and "value" in self.start:
            return self.start["value"]
        return None

    @property
    def end_position(self) -> Optional[int]:
        """Get end position value."""
        if self.end and "value" in self.end:
            return self.end["value"]
        return None


class Feature(BaseModel):
    """Protein feature annotation."""

    type: str = Field(..., description="Feature type")
    location: Optional[FeatureLocation] = Field(default=None, description="Feature location")
    description: Optional[str] = Field(default=None, description="Feature description")
    featureId: Optional[str] = Field(default=None, description="Feature ID")
    evidences: Optional[List[Evidence]] = Field(default=None, description="Evidences")

    model_config = ConfigDict(populate_by_name=True)


# ----- Comment Models -----


class CommentText(BaseModel):
    """Comment text with evidence."""

    value: str = Field(..., description="Text value")
    evidences: Optional[List[Evidence]] = None

    model_config = ConfigDict(populate_by_name=True)


class Comment(BaseModel):
    """UniProt comment/annotation."""

    commentType: str = Field(..., description="Comment type")
    texts: Optional[List[CommentText]] = Field(default=None, description="Comment texts")
    molecule: Optional[str] = Field(default=None, description="Molecule")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def text(self) -> Optional[str]:
        """Get first comment text."""
        if self.texts:
            return self.texts[0].value
        return None


# ----- Cross-Reference Models -----


class CrossReference(BaseModel):
    """Cross-reference to external database."""

    database: str = Field(..., description="Database name")
    id: str = Field(..., description="Database ID")
    properties: Optional[List[Dict[str, str]]] = Field(default=None, description="Properties")
    isoformId: Optional[str] = Field(default=None, description="Isoform ID")

    model_config = ConfigDict(populate_by_name=True)

    def get_property(self, key: str) -> Optional[str]:
        """Get property value by key."""
        if self.properties:
            for prop in self.properties:
                if prop.get("key") == key:
                    return prop.get("value")
        return None


# ----- Keyword Models -----


class Keyword(BaseModel):
    """UniProt keyword."""

    id: str = Field(..., description="Keyword ID (KW-XXXX)")
    category: Optional[str] = Field(default=None, description="Keyword category")
    name: str = Field(..., description="Keyword name")

    model_config = ConfigDict(populate_by_name=True)


# ----- Entry Audit Models -----


class EntryAudit(BaseModel):
    """Entry audit information."""

    firstPublicDate: Optional[str] = Field(default=None, description="First public date")
    lastAnnotationUpdateDate: Optional[str] = Field(default=None, description="Last annotation update")
    lastSequenceUpdateDate: Optional[str] = Field(default=None, description="Last sequence update")
    entryVersion: Optional[int] = Field(default=None, description="Entry version")
    sequenceVersion: Optional[int] = Field(default=None, description="Sequence version")

    model_config = ConfigDict(populate_by_name=True)


# ----- Main Entry Model -----


class UniProtEntry(BaseModel):
    """UniProtKB entry model.

    Represents a protein entry from UniProtKB.
    """

    primaryAccession: str = Field(..., description="Primary accession (e.g., P05067)")
    secondaryAccessions: Optional[List[str]] = Field(default=None, description="Secondary accessions")
    uniProtkbId: Optional[str] = Field(default=None, description="Entry name (e.g., A4_HUMAN)")
    entryType: Optional[str] = Field(default=None, description="Entry type (Swiss-Prot or TrEMBL)")
    proteinExistence: Optional[str] = Field(default=None, description="Protein existence level")
    annotationScore: Optional[float] = Field(default=None, description="Annotation score")

    proteinDescription: Optional[ProteinDescription] = Field(default=None, description="Protein description")
    genes: Optional[List[Gene]] = Field(default=None, description="Gene information")
    organism: Optional[Organism] = Field(default=None, description="Source organism")
    sequence: Optional[Sequence] = Field(default=None, description="Protein sequence")
    features: Optional[List[Feature]] = Field(default=None, description="Sequence features")
    comments: Optional[List[Comment]] = Field(default=None, description="Comments/annotations")
    keywords: Optional[List[Keyword]] = Field(default=None, description="Keywords")
    uniProtKBCrossReferences: Optional[List[CrossReference]] = Field(
        default=None, description="Cross-references"
    )
    entryAudit: Optional[EntryAudit] = Field(default=None, description="Entry audit")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def accession(self) -> str:
        """Alias for primaryAccession."""
        return self.primaryAccession

    @property
    def entry_name(self) -> Optional[str]:
        """Alias for uniProtkbId."""
        return self.uniProtkbId

    @property
    def protein_name(self) -> Optional[str]:
        """Get recommended protein name."""
        if self.proteinDescription:
            return self.proteinDescription.full_name
        return None

    @property
    def gene_name(self) -> Optional[str]:
        """Get primary gene name."""
        if self.genes and self.genes[0].geneName:
            return self.genes[0].geneName.value
        return None

    @property
    def gene_names(self) -> List[str]:
        """Get all gene names."""
        names = []
        if self.genes:
            for gene in self.genes:
                names.extend(gene.all_names)
        return names

    @property
    def organism_name(self) -> Optional[str]:
        """Get organism scientific name."""
        return self.organism.scientificName if self.organism else None

    @property
    def tax_id(self) -> Optional[int]:
        """Get NCBI taxonomy ID."""
        return self.organism.taxonId if self.organism else None

    @property
    def is_reviewed(self) -> bool:
        """Check if entry is reviewed (Swiss-Prot)."""
        return self.entryType == EntryType.SWISSPROT.value

    @property
    def sequence_length(self) -> Optional[int]:
        """Get sequence length."""
        return self.sequence.length if self.sequence else None

    def get_function(self) -> Optional[str]:
        """Get function comment."""
        if self.comments:
            for comment in self.comments:
                if comment.commentType == "FUNCTION":
                    return comment.text
        return None

    def get_subcellular_location(self) -> Optional[str]:
        """Get subcellular location comment."""
        if self.comments:
            for comment in self.comments:
                if comment.commentType == "SUBCELLULAR LOCATION":
                    return comment.text
        return None

    def get_xref(self, database: str) -> Optional[str]:
        """Get cross-reference ID for a database.

        Args:
            database: Database name (e.g., "PDB", "Ensembl", "GeneID").

        Returns:
            First matching database ID, or None.
        """
        if self.uniProtKBCrossReferences:
            for xref in self.uniProtKBCrossReferences:
                if xref.database.upper() == database.upper():
                    return xref.id
        return None

    def get_all_xrefs(self, database: str) -> List[str]:
        """Get all cross-reference IDs for a database.

        Args:
            database: Database name.

        Returns:
            List of database IDs.
        """
        ids = []
        if self.uniProtKBCrossReferences:
            for xref in self.uniProtKBCrossReferences:
                if xref.database.upper() == database.upper():
                    ids.append(xref.id)
        return ids

    @property
    def pdb_ids(self) -> List[str]:
        """Get PDB structure IDs."""
        return self.get_all_xrefs("PDB")

    @property
    def ensembl_gene_id(self) -> Optional[str]:
        """Get Ensembl gene ID."""
        return self.get_xref("Ensembl")

    @property
    def entrez_gene_id(self) -> Optional[str]:
        """Get NCBI Gene ID."""
        return self.get_xref("GeneID")

    @property
    def refseq_ids(self) -> List[str]:
        """Get RefSeq IDs."""
        return self.get_all_xrefs("RefSeq")


# ----- Request Models -----


class UniProtSearchRequest(BaseModel):
    """Request model for UniProt search."""

    query: str = Field(..., min_length=1, description="Search query")
    fields: Optional[str] = Field(default=None, description="Fields to return")
    sort: Optional[str] = Field(default=None, description="Sort field and direction")
    size: int = Field(default=25, ge=1, le=500, description="Results per page")
    includeIsoform: bool = Field(default=False, description="Include isoforms")

    def get_params(self) -> Dict[str, Any]:
        """Get query parameters for API request."""
        params = {
            "query": self.query,
            "size": self.size,
        }
        if self.fields:
            params["fields"] = self.fields
        if self.sort:
            params["sort"] = self.sort
        if self.includeIsoform:
            params["includeIsoform"] = "true"
        return params


class IDMappingRequest(BaseModel):
    """Request model for ID mapping."""

    ids: List[str] = Field(..., description="IDs to map")
    from_db: str = Field(..., alias="from", description="Source database")
    to_db: str = Field(..., alias="to", description="Target database")

    model_config = ConfigDict(populate_by_name=True)

    def get_data(self) -> Dict[str, str]:
        """Get form data for API request."""
        return {
            "ids": ",".join(self.ids),
            "from": self.from_db,
            "to": self.to_db,
        }
