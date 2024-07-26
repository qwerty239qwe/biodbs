from biodbs.fetcher import BaseAPI
from biodbs.utils import get_rsp
from biodbs.ChEMBL.utils import parse_cmp, clean_value


class ChEMBLViewAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://www.ebi.ac.uk/chembl/api/data/{record_type}/{id}?format={file_format}"


class Fetcher:
    def __init__(self, record_type):
        self._api = ChEMBLViewAPI()
        self._api.update_params(record_type=record_type)

    def fetch(self, chembl_id, file_format) -> dict:
        fetched_api = self._api.apply(id=chembl_id, file_format=file_format)
        resp = get_rsp(fetched_api.api)
        return resp.json()

    def get_processed_data(self, chembl_id):
        result = self.fetch(chembl_id=chembl_id, file_format="JSON")
        return clean_value(parse_cmp(result["Record"]["Section"]))


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
