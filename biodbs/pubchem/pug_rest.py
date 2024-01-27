from biodbs.fetcher import BaseAPI
from biodbs.utils import get_rsp


class PUGRestAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}/{namespace}/" \
                           "{identifiers}/{operation}/{output_format}{operation_options}"


class Fetcher:
    def __init__(self, domain):
        self._api = PUGRestAPI()
        self._api.update_params(domain=domain)

    def fetch(self, name_space, ids, operation, output_format="JSON"):
        if isinstance(ids, list):
            ids = ",".join(ids)

        fetched_api = self._api.apply(namespace=name_space,
                                      identifiers=ids,
                                      operation=operation,
                                      output_format=output_format,
                                      )