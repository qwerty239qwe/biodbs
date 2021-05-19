# bioDBs
bioDBs is a Python package for getting data from biological databases.

## List of the databases
* BioMart
* KEGG
* QuickGO
* HPA

## How to use

### BioMart
```python
from biodbs import BioMart

ds = BioMart.Dataset(dataset_name="hsapiens_gene_ensembl")

ds.get_data(attribs=["ensembl_gene_id", 
                     "ensembl_transcript_id", 
                     "entrezgene_id", 
                     "hgnc_symbol", 
                     "uniprotswissprot"],
            ensembl_gene_id=["ENSG00000139618", "ENSG00000272104"])
```

### KEGG
```python
from biodbs import KEGG

# list available databases
KEGG.list_database()

kegg = KEGG.KEGGdb()
# get entry links
kegg.list_entry_link(target_db="pathway", source_db="hsa")
```

### QuickGO
```python
from biodbs import QuickGO

qgo = QuickGO.QuickGOdb()
# search by text and list the results
qgo.list_search_result("mito")

# save a GO-term tree chart
qgo.save_chart(["GO:1903695", "GO:1904922", "GO:0000423", "GO:0042645"], "test.png")

```

### Human Protein Atlas (HPA)
```python
from biodbs import HPA

hpa = HPA.HPAdb()

# list downloadable tsv files
print(HPA.DOWNLOADABLE_DATA)
# download tsv file from HPA
hpa.download_HPA_data("normal_tissue", saved_path="./")

```