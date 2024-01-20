from biodbs.fetcher import BaseAPI
from biodbs.utils import get_rsp


class PUGViewAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/{record_type}/{id}/{file_format}"


class CompoundFetcher:
    def __init__(self):
        self._api = PUGViewAPI()
        self._api.update_params(record_type="compound")

    def fetch(self, cid, file_format):
        fetched_api = self._api.apply(id=cid, file_format=file_format)
        resp = get_rsp(fetched_api.api)
        return resp.json()

    def fetch_and_process(self, cid, file_format):
        result = self.fetch(cid=cid, file_format=file_format)


