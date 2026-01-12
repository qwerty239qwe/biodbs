from biodbs.fetch import BaseAPI
from typing import Tuple



class FDACategory:
    def __init__(self, name, endpoints):
        self._name = name
        self._endpoints = endpoints

    @property
    def name(self):
        return self._name
    
    @property
    def endpoints(self):
        return self._endpoints
    

class FDANameSpace:
    all_categories = [FDACategory(name="drug", endpoints=["label", "event", "ndc"]),
                      FDACategory(name="food", endpoints=["event", "enforcement"])]
    
    def validate(self, category, endpoint) -> Tuple[bool, str]:
        if category not in [cate.name for cate in self.all_categories]:
            return False, f"{category} is not a valid category."

        for cate in self.all_categories:
            if category == cate.name:
                is_valid_endpoint = endpoint in cate.endpoints

                return is_valid_endpoint, "" if is_valid_endpoint else f"{endpoint} is not a valid endpoint"
        return False, f"{category} is not a valid category."
        


class FDA_API(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://api.fda.gov/{category}/{endpoint}.json"
        self.namespace = FDANameSpace()
        
    

class FDA_Fetcher:
    def __init__(self):
        self._api = FDA_API()

    