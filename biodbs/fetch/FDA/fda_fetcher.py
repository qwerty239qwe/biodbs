from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.fetch.FDA._data_model import FDAModel
from biodbs.utils import get_rsp
from typing import Tuple


class FDANameSpace(NameSpace):
    def __init__(self):
        model = FDAModel
        super().__init__(model)
    

class FDA_APIConfig(BaseAPIConfig):
    def __init__(self):
        super().__init__(url_format="https://api.fda.gov/{category}/{endpoint}.json")
        

class FDA_Fetcher(BaseDataFetcher):
    def __init__(self, api_key: str = None, limit: int = None):
        super().__init__(FDA_APIConfig(), FDANameSpace(), {})
        self._api_key = api_key
        self._limit = limit

    def get(self, category, endpoint, **kwargs):
        is_valid, err_msg = self._namespace.validate(category=category, 
                                                     endpoint=endpoint, 
                                                     search=kwargs.get("search"))
        if not is_valid:
            raise ValueError(err_msg)
        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url

        return get_rsp(url, **kwargs)
    


if __name__ == "__main__":
    fetcher = FDA_Fetcher()
    params = dict(search={"receivedate": "[20040101+TO+20081231]"}, limit=1)
    data = fetcher.get(category="drug", endpoint="event", query=params)
    print(data.json())