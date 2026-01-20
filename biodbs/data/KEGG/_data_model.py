from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict


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



class KEGGModel(BaseModel):
    model_config = ConfigDict(frozen=True)
    operation: KEGGOperation
    