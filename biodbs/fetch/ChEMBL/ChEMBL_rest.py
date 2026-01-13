from biodbs.fetch._base import BaseAPIConfig


class PUGRestAPI(BaseAPIConfig):
    def __init__(self):
        super().__init__()
        self._url_format = "https://www.ebi.ac.uk/chembl/api/data/{domain}"\
                            "{identifiers}&format={output_format}"


class Fetcher:
    def __init__(self, domain):
        self._api = PUGRestAPI()
        self._api.update_params(domain=domain)

    def _check_params(self, param, param_name):
        return self._valid_params[param_name].match(param)

    def fetch(self, ids, output_format):
        if isinstance(ids, list):
            ids = ",".join(ids)

        fetched_api = self._api.apply(identifiers=ids,
                                      output_format=output_format,
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

class CHEMBLIDLookUp(Fetcher):
    def __init__(self):
        super().__init__(domain="chembl_id_lookup")

class CompoundRecordFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="compound_record")

class CompoundStructuralAlert(Fetcher):
    def __init__(self):
        super().__init__(domain="compound_structural_alert")

class DocumentFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="document")

class DocumentSimilarity(Fetcher):
    def __init__(self):
        super().__init__(domain="document_similarity")

class DocumentTerm(Fetcher):
    def __init__(self):
        super().__init__(domain="document_term")

class DrugFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="drug")

class DrugIndication(Fetcher):
    def __init__(self):
        super().__init__(domain="drug_indication")

class DrugWarning(Fetcher):
    def __init__(self):
        super().__init__(domain="drug_warning")

class GOSlim(Fetcher):
    def __init__(self):
        super().__init__(domain="go_slim")

class Image(Fetcher):
    def __init__(self):
        super().__init__(domain="image")

class MechanismFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="mechanism")

class MetabolismFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="metabolism")

class MoleculeFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="molecule")

class MoleculeForm(Fetcher):
    def __init__(self):
        super().__init__(domain="molecule_form")

class OrganismFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="organism")

class ProteinFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="protein_classfication")

class Similarity(Fetcher):
    def __init__(self):
        super().__init__(domain="similarity")

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

class TargetComponent(Fetcher):
    def __init__(self):
        super().__init__(domain="target_component")

class TargetRelation(Fetcher):
    def __init__(self):
        super().__init__(domain="target_ralation")

class TissueFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="tissue")

class OthersFetcher(Fetcher):
    def __init__(self):
        super().__init__(domain="others")