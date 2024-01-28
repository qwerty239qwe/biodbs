from biodbs.fetcher import BaseAPI
from biodbs.utils import get_rsp
from biodbs.pubchem._params import *


class PUGRestAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}/{namespace}/" \
                           "{identifiers}/{operation}/{output_format}{operation_options}"


class Fetcher:
    def __init__(self, domain):
        self._api = PUGRestAPI()
        self._api.update_params(domain=domain)
        self._valid_ns = PUBRESTNameSpace(domain=domain)
        self._valid_ops = PUBRESTOperation(domain=domain)

        self._valid_params = {"namespace": self._valid_ns, "operation": self._valid_ops}

    def _check_params(self, param, param_name):
        return self._valid_params[param_name].match(param)

    def fetch(self, name_space, ids, operation, output_format="JSON", operation_options=None):
        if isinstance(ids, list):
            ids = ",".join(ids)

        if not self._check_params(name_space, "namespace"):
            raise ValueError("namespace got an invalid value. Please choose from: "
                             f"{self._valid_params['namespace'].name_space}")

        if not self._check_params(operation, "operation"):
            raise ValueError("namespace got an invalid value. Please choose from: "
                             f"{self._valid_params['operation'].operations}")

        operation_options = operation_options or ""
        fetched_api = self._api.apply(namespace=name_space,
                                      identifiers=ids,
                                      operation=operation,
                                      output_format=output_format,
                                      operation_options=operation_options,
                                      )

        resp = get_rsp(fetched_api.api)
        return resp.json()


class CompoundFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="compound")


class SubstanceFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="substance")


class AssayFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="assay")


class GeneFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="gene")


class ProteinFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="protein")


class TaxonomyFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="taxonomy")


class CellFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="cell")


class OthersFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="others")