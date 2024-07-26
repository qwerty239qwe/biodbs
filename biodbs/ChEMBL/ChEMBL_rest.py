from biodbs.fetcher import BaseAPI
from biodbs.utils import get_rsp
from biodbs.ChEMBL.__params import *


class ChEMBLRestAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://www.ebi.ac.uk/chembl/api/data/{domain}"\
                            "?{namespace}={identifier}&format={output_format}{operation_option}"


class Fetcher:
    def __init__(self, domain):
        self._api = ChEMBLRestAPI()
        self._api.update_params(domain=domain)
        self._valid_ns = ChEMBLNameSpace(domain=domain)

        self._valid_params = {"namespace": self._valid_ns}

    def _check_params(self, param, param_name):
        return self._valid_params[param_name].match(param)

    def fetch(self, name_space, ids,output_format="JSON", operation_options=None):
        if isinstance(ids, list):
            ids = ",".join(ids)

        if not self._check_params(name_space, "namespace"):
            raise ValueError("namespace got an invalid value. Please choose from: "
                             f"{self._valid_params['namespace'].name_space}")

        operation_options = operation_options or ""
        fetched_api = self._api.apply(namespace=name_space,
                                      identifiers=ids,
                                      output_format=output_format,
                                      operation_options=operation_options,
                                      )

        resp = get_rsp(fetched_api.api)
        return resp.json()


class ActivityFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="activity")


class AssayFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="assay")


class ATCFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="atc_class")


class BindingSiteFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="binding_site")


class BiotheraputicFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="biotheraputic")


class CellLine(Fetcher):
    def __init__(self):
        super().__init__(domain="cell_line")


class CompoundRecordFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="compound_record")


class DocumentFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="document")


class DrugFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="drug")


class MechanismFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="mechanism")


class MetabolismFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="metabolism")


class MoleculeFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="molecule")


class OrganismFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="organism")


class ProteinFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="protein_classfication")


class SourceFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="source")


class StatusFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="status")


class SubstructureFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="substructure")


class TargetFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="target")


class TissueFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="tissue")


class OthersFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="others")