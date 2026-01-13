from biodbs.fetch import BaseAPIConfig


class PUGViewAPI(BaseAPIConfig):
    def __init__(self):
        super().__init__()
        self._url_format = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/{record_type}/{id}/{file_format}"


class Fetcher:
    def __init__(self, record_type):
        self._api = PUGViewAPI()
        self._api.update_params(record_type=record_type)

    def fetch(self, cid, file_format) -> dict:
        fetched_api = self._api.apply(id=cid, file_format=file_format)
        resp = get_rsp(fetched_api.api)
        return resp.json()

    def get_processed_data(self, cid):
        result = self.fetch(cid=cid, file_format="JSON")
        return clean_value(parse_cmp(result["Record"]["Section"]))


class CompoundFetcher(Fetcher):
    def __init__(self):
        super().__init__("compound")


class SubstanceFetcher(Fetcher):
    def __init__(self):
        super().__init__("substance")


class AssayFetcher(Fetcher):
    def __init__(self):
        super().__init__("assay")


class BioAssayFetcher(Fetcher):
    def __init__(self):
        super().__init__("bioassay")


class GeneFetcher(Fetcher):
    def __init__(self):
        super().__init__("gene")


class ProteinFetcher(Fetcher):
    def __init__(self):
        super().__init__("protein")


class CellFetcher(Fetcher):
    def __init__(self):
        super().__init__("cell")