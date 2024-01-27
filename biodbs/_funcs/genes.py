from biodbs.BioMart import Dataset


def translate_genes(genes, from_id, to_id, **kwargs):
    biom_ds = Dataset(**kwargs)
    filter_kws = {to_id: genes}
    result = biom_ds.get_data(attribs=[from_id], **filter_kws)
    return result[to_id]