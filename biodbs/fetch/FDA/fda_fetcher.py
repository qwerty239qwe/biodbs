from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher
from biodbs.data.FDA._data_model import FDAModel
from biodbs.data.FDA.data import FDAFetchedData
from biodbs.utils import get_rsp
from typing import Tuple, Literal



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
        kwargs["api_key"] = self._api_key if kwargs.get("api_key") is None else kwargs.get("api_key")
        kwargs["limit"] = self._limit if kwargs.get("limit") is None else kwargs.get("limit")

        is_valid, err_msg = self._namespace.validate(category=category, 
                                                     endpoint=endpoint, 
                                                     search=kwargs.get("search"),
                                                     limit=kwargs.get("limit"),
                                                     sort=kwargs.get("sort"),
                                                     count=kwargs.get("count"),
                                                     skip=kwargs.get("skip"))
        if not is_valid:
            raise ValueError(err_msg)
        self._api_config.update_params(**self._namespace.valid_params)
        url = self._api_config.api_url

        response = get_rsp(url, params=kwargs)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to fetch data from FDA API. Status code: {response.status_code}, Message: {response.text}")
        
        data_class = FDAFetchedData
        if data_class is None:
            raise NotImplementedError(f"The data class for category '{category}' and endpoint '{endpoint}' is not implemented.")
        return data_class(response.json())
    
    def get_all(self, 
                category, 
                endpoint, 
                method: Literal["concat", "stream_to_db"],
                conn,
                batch_size=100, 
                max_records=-1, 
                **kwargs):
        all_results = []
        total_fetched = 0
        while total_fetched < max_records:
            current_limit = min(batch_size, max_records - total_fetched)
            kwargs.update({"limit": current_limit, "skip": total_fetched})
            data = self.get(category, endpoint, **kwargs)
            if not data.results:
                break
            all_results.extend(data.results)
            fetched_count = len(data.results)
            total_fetched += fetched_count
            if fetched_count < current_limit:
                break
        data.results = all_results
        return data


if __name__ == "__main__":
    fetcher = FDA_Fetcher()
    params = dict(search={"receivedate": "[20040101+TO+20081231]"}, limit=3)
    data = fetcher.get(category="drug", endpoint="event", **params)

    print(data.show_valid_columns())
    print(data.format_results(columns=["receivedate", "patient.patientonsetage", 
                                       "patient.patientsex", "patient.drug.medicinalproduct", 
                                       "patient.drug.drugindication"]))
    
    print(data.as_dataframe(columns=["receivedate", "patient.patientonsetage"],))