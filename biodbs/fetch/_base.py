from pydantic import BaseModel, ValidationError
from typing import Tuple


class BaseAPIConfig:
    def __init__(self, url_format):
        self._url_format = url_format
        self._params = {}

    def __str__(self):
        disp_names = [self.__class__.__name__, 
                      f"API format: {self._url_format}", 
                      f"Current params: {self._params}"]
        return "\n".join(disp_names) 

    def update_params(self, **kwargs):
        self._params.update(kwargs)

    @property
    def api_url(self):
        if self._url_format is None:
            raise NotImplementedError("This class must be inherited")
        return self._url_format.format(**self._params)

    def copy(self):
        new = self.__class__()
        new.update_params(**self._params)
        return new

    def apply(self, **params):
        new_api = self.copy()
        new_api.update_params(**params)
        return new_api


class NameSpace:
    def __init__(self, model: type[BaseModel]):
        self._model = model
        self._valid_params = {}
    
    def validate(self, **kwargs) -> Tuple[bool, str]:
        err_msg = "No error found"
        try:
            ins = self._model(**kwargs)
            self._valid_params = ins.model_dump()
        except ValidationError as e:
            err_msg = str(e)
            return False, err_msg
        
        return True, err_msg
    
    @property
    def valid_params(self):
        return self._valid_params


class BaseDataFetcher:
    def __init__(self, api_config: BaseAPIConfig, namespace: NameSpace, headers):
        self._api_config = api_config
        self._namespace = namespace
        self._headers = headers
    
    def get(self, *args, **kwargs):
        raise NotImplementedError()