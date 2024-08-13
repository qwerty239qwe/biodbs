from biodbs.fetcher import BaseAPI
from biodbs.utils import get_rsp


class ChEMBLRestAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://www.ebi.ac.uk/chembl/api/data/{domain}"\
                            "/{identifiers}?format={output_format}{operation_options}{namespace}"


class Fetcher:
    def __init__(self, domain):
        self._api = ChEMBLRestAPI()
        self._api.update_params(domain=domain)

    def fetch(self, ids,  output_format="json", operation_options=None, name_space=None):
        if isinstance(ids, list):
            ids = ",".join(ids)
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