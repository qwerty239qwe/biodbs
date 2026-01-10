from biodbs.fetcher import BaseAPI
from enum import Enum

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
    category = [FDACategory(name="drug", endpoints=["label"])]


class FDA_API(BaseAPI):
    def __init__(self):
        super().__init__()
        self._url_format = "https://api.fda.gov/{category}/{endpoint}.json"
    

class FDA_Fetcher:
    def __init__(self):
        self._api = FDA_API()

    