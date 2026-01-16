from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.fetch.FDA._data_model import FDAModel
from biodbs.utils import get_rsp
from typing import Tuple


class QuickGONameSpace(NameSpace):
    def __init__(self):
        model = FDAModel
        super().__init__(model)
    

class QuickGO_APIConfig(BaseAPIConfig):
    def __init__(self):
        super().__init__(url_format="https://www.ebi.ac.uk/QuickGO/services/{category}/{endpoint}")