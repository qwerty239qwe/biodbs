from enum import StrEnum


class BiomartHost(StrEnum):
    main = "www.ensembl.org",
    apr2018 = "apr2018.archive.ensembl.org",  # Ensembl version: 92.38 - used by HPA
    may2015 = "may2015.archive.ensembl.org",  # Ensembl version: GRCh38.p2
    plants = "plants.ensembl.org",
    fungi = "fungi.ensembl.org",
    protist = "protist.ensembl.org",
    metazoa = "metazoa.ensembl.org"


class BiomartDatabase(StrEnum):
    human = "hsapiens_gene_ensembl"
    mouse = "mmusculus_gene_ensembl"
    rat = "rnorvegicus_gene_ensembl"
    chicken = "ggallus_gene_ensembl"


class BiomartMart(StrEnum):
    default = "ENSEMBL_MART_ENSEMBL"
    ontology = "ENSEMBL_MART_ONTOLOGY"