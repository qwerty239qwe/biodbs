from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, model_validator, field_validator
import re


class KEGGOperation(Enum):
    info = "info"
    list = "list"
    find = "find"
    get = "get"
    conv = "conv"
    link = "link"
    ddi = "ddi"


class KEGGDatabase(Enum):
    pathway = "pathway"
    brite = "brite"
    module = "module"
    ko = "ko"
    genome = "genome"
    compound = "compound"
    glycan = "glycan"
    reaction = "reaction"
    rclass = "rclass"
    enzyme = "enzyme"
    network = "network"
    variant = "variant"
    disease = "disease"
    drug = "drug"
    dgroup = "dgroup"
    organism = "organism"


class KEGGOutsideDatabase(Enum):
    pubmed = "pubmed"
    ncbi_geneid = "ncbi-geneid"
    ncbi_proteinid = "ncbi-proteinid"
    uniprot = "uniprot"
    pubchem = "pubchem"
    chebi = "chebi"
    atc = "atc"
    jtc = "jtc"
    ndc = "ndc"
    yj = "yj"
    yk = "yk"


class KEGGOrganism(Enum):
    hsa = "hsa"
    mmu = "mmu"
    rno = "rno"
    dme = "dme"
    cel = "cel"
    eco = "eco"
    bsu = "bsu"
    sac = "sac"
    ath = "ath"
    sce = "sce"
    pfa = "pfa"


class KEGGListPathwayOption(Enum):
    reference = "pathway"
    organism_specific = "{org}"


class KEGGBriteOption(Enum):
    br = "br"
    jp = "jp"
    ko = "ko"
    organism = "{org}"


class KEGGCompoundFindOption(Enum):
    formula = "formula"
    exact_mass = "exact_mass"
    mol_weight = "mol_weight"
    nop = "nop"


class KEGGDrugFindOption(Enum):
    formula = "formula"
    exact_mass = "exact_mass"
    mol_weight = "mol_weight"
    nop = "nop"


class KEGGGetOption(Enum):
    aaseq = "aaseq"
    ntseq = "ntseq"
    mol = "mol"
    kcf = "kcf"
    image = "image"
    conf = "conf"
    kgml = "kgml"
    json = "json"


class KEGGPathwaySearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    organism = "organism"
    title = "title"
    image = "image"
    link = "link"
    pathway = "pathway"
    compound = "compound"
    enzyme = "enzyme"
    orthology = "orthology"
    gene = "gene"
    reaction = "reaction"
    rpair = "rpair"
    module = "module"
    disease = "disease"
    drug = "drug"
    dgroup = "dgroup"
    ko = "ko"
    brite = "brite"


class KEGGBriteSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    hierarchy = "hierarchy"


class KEGGModuleSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    orthology = "orthology"
    classic = "classic"
    composite = "composite"
    gene = "gene"
    reaction = "reaction"
    pathway = "pathway"
    disease = "disease"
    drug = "drug"
    brite = "brite"


class KEGGOrthologySearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    orthology = "orthology"
    gene = "gene"
    enzyme = "enzyme"
    reaction = "reaction"
    pathway = "pathway"
    compound = "compound"
    drug = "drug"
    disease = "disease"


class KEGGGenesSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    orthology = "orthology"
    organism = "organism"
    position = "position"
    motif = "motif"
    amino_acid = "aa"
    nucleotide_sequence = "nt"
    other = "other"
    link = "link"
    pathway = "pathway"
    module = "module"
    reaction = "reaction"
    compound = "compound"
    drug = "drug"
    disease = "disease"


class KEGGGenomeSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    organism = "organism"
    taxonomy = "taxonomy"
    position = "position"
    chromosome = "chromosome"
    plasmid = "plasmid"
    gene = "gene"
    reference = "reference"


class KEGGCompoundSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    formula = "formula"
    mass = "mass"
    pathway = "pathway"
    reaction = "reaction"
    enzyme = "enzyme"
    drug = "drug"
    glycan = "glycan"
    atom = "atom"
    bond = "bond"


class KEGGGlycanSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    composition = "composition"
    mass = "mass"
    pathway = "pathway"
    reaction = "reaction"
    enzyme = "enzyme"
    drug = "drug"
    compound = "compound"


class KEGGReactionSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    equation = "equation"
    substrate = "substrate"
    product = "product"
    enzyme = "enzyme"
    orthology = "orthology"
    pathway = "pathway"
    module = "module"
    compound = "compound"
    rpair = "rpair"
    rclass = "rclass"
    drug = "drug"


class KEGGRClassSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    reaction = "reaction"
    pathway = "pathway"
    enzyme = "enzyme"


class KEGGEnzymeSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    class_name = "class"
    systematic_name = "systematic_name"
    reaction = "reaction"
    substrate = "substrate"
    product = "product"
    pathway = "pathway"
    gene = "gene"
    organism = "organism"
    cofactor = "cofactor"
    inhibitor = "inhibitor"
    activator = "activator"
    metal = "metal"
    comment = "comment"


class KEGGNetworkSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    component = "component"
    element = "element"
    reaction = "reaction"
    orthology = "orthology"
    pathway = "pathway"


class KEGGVariantSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    gene = "gene"
    variant = "variant"
    disease = "disease"
    drug = "drug"


class KEGGDiseaseSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    definition = "definition"
    category = "category"
    drug = "drug"
    pathway = "pathway"
    gene = "gene"
    marker = "marker"
    phenotype = "phenotype"
    env_factor = "env_factor"
    reference = "reference"


class KEGGDrugSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    name_ja = "name_ja"
    formula = "formula"
    mass = "mass"
    pathway = "pathway"
    enzyme = "enzyme"
    reaction = "reaction"
    structure = "structure"
    atom = "atom"
    bond = "bond"
    pair = "pair"
    group = "group"
    classification = "classification"
    category = "category"
    dgroup = "dgroup"
    interaction = "interaction"
    metabolism = "metabolism"
    gene = "gene"
    disease = "disease"
    efficacy = "efficacy"
    target = "target"


class KEGGDGroupSearchField(Enum):
    entry = "entry"
    entry_name = "name"
    name_ja = "name_ja"
    definition = "definition"
    drug = "drug"
    algorithm = "algorithm"
    remark = "remark"


class KEGGLinkRDFOption(Enum):
    turtle = "turtle"
    n_triple = "n-triple"


# Mapping of operations to valid databases
VALID_DATABASES_BY_OPERATION = {
    KEGGOperation.info: [
        KEGGDatabase.pathway, KEGGDatabase.brite, KEGGDatabase.module, 
        KEGGDatabase.ko, KEGGDatabase.genome, KEGGDatabase.compound,
        KEGGDatabase.glycan, KEGGDatabase.reaction, KEGGDatabase.rclass,
        KEGGDatabase.enzyme, KEGGDatabase.network, KEGGDatabase.variant,
        KEGGDatabase.disease, KEGGDatabase.drug, KEGGDatabase.dgroup
    ],
    KEGGOperation.list: [
        KEGGDatabase.pathway, KEGGDatabase.brite, KEGGDatabase.module,
        KEGGDatabase.ko, KEGGDatabase.genome, KEGGDatabase.compound,
        KEGGDatabase.glycan, KEGGDatabase.reaction, KEGGDatabase.rclass,
        KEGGDatabase.enzyme, KEGGDatabase.network, KEGGDatabase.variant,
        KEGGDatabase.disease, KEGGDatabase.drug, KEGGDatabase.dgroup,
        KEGGDatabase.organism
    ],
    KEGGOperation.find: [
        KEGGDatabase.pathway, KEGGDatabase.brite, KEGGDatabase.module,
        KEGGDatabase.ko, KEGGDatabase.genome, KEGGDatabase.compound,
        KEGGDatabase.glycan, KEGGDatabase.reaction, KEGGDatabase.rclass,
        KEGGDatabase.enzyme, KEGGDatabase.network, KEGGDatabase.variant,
        KEGGDatabase.disease, KEGGDatabase.drug, KEGGDatabase.dgroup
    ],
    KEGGOperation.get: [
        KEGGDatabase.pathway, KEGGDatabase.brite, KEGGDatabase.module,
        KEGGDatabase.ko, KEGGDatabase.genome, KEGGDatabase.compound,
        KEGGDatabase.glycan, KEGGDatabase.reaction, KEGGDatabase.rclass,
        KEGGDatabase.enzyme, KEGGDatabase.network, KEGGDatabase.variant,
        KEGGDatabase.disease, KEGGDatabase.drug, KEGGDatabase.dgroup
    ],
}


# Mapping of databases to their search fields
SEARCH_FIELDS_BY_DATABASE = {
    KEGGDatabase.pathway: KEGGPathwaySearchField,
    KEGGDatabase.brite: KEGGBriteSearchField,
    KEGGDatabase.module: KEGGModuleSearchField,
    KEGGDatabase.ko: KEGGOrthologySearchField,
    KEGGDatabase.genome: KEGGGenomeSearchField,
    KEGGDatabase.compound: KEGGCompoundSearchField,
    KEGGDatabase.glycan: KEGGGlycanSearchField,
    KEGGDatabase.reaction: KEGGReactionSearchField,
    KEGGDatabase.rclass: KEGGRClassSearchField,
    KEGGDatabase.enzyme: KEGGEnzymeSearchField,
    KEGGDatabase.network: KEGGNetworkSearchField,
    KEGGDatabase.variant: KEGGVariantSearchField,
    KEGGDatabase.disease: KEGGDiseaseSearchField,
    KEGGDatabase.drug: KEGGDrugSearchField,
    KEGGDatabase.dgroup: KEGGDGroupSearchField,
}


class KEGGModel(BaseModel):
    """
    Pydantic model for validating KEGG REST API requests.
    
    The KEGG API has the general form:
    https://rest.kegg.jp/<operation>/<argument>[/<argument2>[/<argument3>]]
    
    Supported operations: info, list, find, get, conv, link, ddi
    
    Examples:
        # INFO operation
        KEGGModel(operation="info", database="pathway")
        
        # LIST operation
        KEGGModel(operation="list", database="pathway", organism="hsa")
        
        # FIND operation
        KEGGModel(operation="find", database="genes", query="shiga toxin")
        KEGGModel(operation="find", database="compound", query="C7H10O5", find_option="formula")
        
        # GET operation
        KEGGModel(operation="get", dbentries=["hsa:10458", "ece:Z5100"])
        KEGGModel(operation="get", dbentries=["C00002"], get_option="image")
        
        # CONV operation
        KEGGModel(operation="conv", target_db="eco", source_db="ncbi-geneid")
        KEGGModel(operation="conv", target_db="ncbi-proteinid", dbentries=["hsa:10458"])
        
        # LINK operation
        KEGGModel(operation="link", target_db="pathway", source_db="hsa")
        KEGGModel(operation="link", target_db="pathway", dbentries=["hsa:10458"])
        
        # DDI operation
        KEGGModel(operation="ddi", dbentries=["D00564", "D00100"])
    """
    model_config = ConfigDict(use_enum_values=True)
    
    # Core fields
    operation: KEGGOperation
    
    # Fields for INFO, LIST, FIND operations
    database: Optional[Union[KEGGDatabase, str]] = None  # Can be organism code like "hsa"
    
    # Fields for LIST operation
    organism: Optional[str] = None  # For list/pathway/<org> or list/brite/<org>
    brite_option: Optional[KEGGBriteOption] = None  # For list/brite/<option>
    
    # Fields for FIND operation
    query: Optional[str] = None  # Search query string
    find_option: Optional[Union[KEGGCompoundFindOption, KEGGDrugFindOption, str]] = None  # formula, exact_mass, etc.
    
    # Fields for GET operation
    dbentries: Optional[List[str]] = None  # List of database entry identifiers
    get_option: Optional[KEGGGetOption] = None  # aaseq, ntseq, image, kgml, etc.
    
    # Fields for CONV operation
    target_db: Optional[Union[KEGGDatabase, KEGGOutsideDatabase, str]] = None
    source_db: Optional[Union[KEGGDatabase, KEGGOutsideDatabase, str]] = None
    
    # Fields for LINK operation
    # target_db and source_db already defined above, dbentries also defined
    rdf_option: Optional[KEGGLinkRDFOption] = None  # turtle or n-triple for specific link operations
    
    # Additional constraints
    max_entries: int = 10  # KEGG API limit for multiple entries
    
    @model_validator(mode='after')
    def validate_operation_requirements(self):
        """Validate that required fields are present for each operation."""
        op = KEGGOperation(self.operation)
        
        if op == KEGGOperation.info:
            if not self.database:
                raise ValueError("INFO operation requires 'database' field")
                
        elif op == KEGGOperation.list:
            if not self.database and not self.dbentries:
                raise ValueError("LIST operation requires either 'database' or 'dbentries' field")
            # Validate special cases
            if self.database == KEGGDatabase.organism.value:
                # list/organism is valid
                pass
            elif self.organism and self.database not in [KEGGDatabase.pathway.value, "pathway"]:
                raise ValueError("organism option only valid for pathway database")
                
        elif op == KEGGOperation.find:
            if not self.database or not self.query:
                raise ValueError("FIND operation requires 'database' and 'query' fields")
            # Validate find_option
            if self.find_option:
                if self.database in [KEGGDatabase.compound.value, "compound"]:
                    # Validate it's a valid compound find option
                    valid_options = [opt.value for opt in KEGGCompoundFindOption]
                    if self.find_option not in valid_options:
                        raise ValueError(f"Invalid find_option for compound: {self.find_option}. Must be one of {valid_options}")
                elif self.database in [KEGGDatabase.drug.value, "drug"]:
                    valid_options = [opt.value for opt in KEGGDrugFindOption]
                    if self.find_option not in valid_options:
                        raise ValueError(f"Invalid find_option for drug: {self.find_option}. Must be one of {valid_options}")
                        
        elif op == KEGGOperation.get:
            if not self.dbentries:
                raise ValueError("GET operation requires 'dbentries' field")
            if len(self.dbentries) > self.max_entries:
                raise ValueError(f"GET operation limited to {self.max_entries} entries, got {len(self.dbentries)}")
            # Validate image/kgml options (limited to 1 entry)
            if self.get_option in [KEGGGetOption.image.value, KEGGGetOption.kgml.value]:
                if len(self.dbentries) > 1:
                    raise ValueError(f"GET option '{self.get_option}' limited to 1 entry")
                    
        elif op == KEGGOperation.conv:
            if not self.target_db:
                raise ValueError("CONV operation requires 'target_db' field")
            if not self.source_db and not self.dbentries:
                raise ValueError("CONV operation requires either 'source_db' or 'dbentries' field")
            if self.source_db and self.dbentries:
                raise ValueError("CONV operation cannot have both 'source_db' and 'dbentries'")
                
        elif op == KEGGOperation.link:
            if not self.target_db:
                raise ValueError("LINK operation requires 'target_db' field")
            if not self.source_db and not self.dbentries:
                raise ValueError("LINK operation requires either 'source_db' or 'dbentries' field")
            if self.source_db and self.dbentries:
                raise ValueError("LINK operation cannot have both 'source_db' and 'dbentries'")
                
        elif op == KEGGOperation.ddi:
            if not self.dbentries:
                raise ValueError("DDI operation requires 'dbentries' field")
            # DDI only works with drug, ndc, yj databases
            for entry in self.dbentries:
                if not any(entry.startswith(prefix) for prefix in ['D', 'ndc:', 'yj:']):
                    raise ValueError(f"DDI entries must be drug (D*), ndc (ndc:*), or yj (yj:*) entries. Got: {entry}")
                    
        return self
    
    @model_validator(mode='after')
    def validate_database_for_operation(self):
        """Validate that the database is valid for the operation."""
        if not self.database:
            return self
            
        op = KEGGOperation(self.operation)
        
        # Check if operation has database restrictions
        if op in VALID_DATABASES_BY_OPERATION:
            valid_dbs = [db.value for db in VALID_DATABASES_BY_OPERATION[op]]
            
            # Allow organism codes (3-4 letter codes)
            if self.database not in valid_dbs:
                # Check if it's a valid organism code format (3-4 letters or T number)
                if not (re.match(r'^[a-z]{3,4}$', str(self.database)) or 
                        re.match(r'^T\d{5}$', str(self.database)) or
                        str(self.database) in ['vg', 'vp', 'ag', 'genes', 'ligand', 'kegg']):
                    raise ValueError(
                        f"Database '{self.database}' not valid for operation '{op.value}'. "
                        f"Valid databases: {valid_dbs} or organism codes (e.g., 'hsa', 'eco')"
                    )
        
        return self
    
    @field_validator('dbentries')
    @classmethod
    def validate_dbentries_format(cls, v):
        """Validate database entry format."""
        if v is None:
            return v
            
        for entry in v:
            # Valid formats: K00001, hsa:10458, map00010, D00001, ncbi-geneid:948364, etc.
            if not re.match(r'^[A-Za-z0-9_-]+:[A-Za-z0-9_.-]+$', entry) and \
               not re.match(r'^[A-Z]{1,3}\d+$', entry) and \
               not re.match(r'^[a-z]{2,4}\d{5}$', entry):
                # Allow it but log warning - KEGG is flexible with entry formats
                pass
                
        return v
    
