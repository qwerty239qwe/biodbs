

class BaseAPI:
    def __init__(self):
        self._url_format = None
        self._params = {}

    def __str__(self):
        disp_names = [self.__class__.__name__, 
                      f"API format: {self._url_format}", 
                      f"Current params: {self._params}"]
        return "\n".join(disp_names) 

    def update_params(self, **kwargs):
        self._params.update(kwargs)

    @property
    def api(self):
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


class BaseDataFetcher:
    def __init__(self, api, namespace, headers):
        self._api = api
        self._namespace = namespace
        self._headers = headers

    def _get_data(self, *args, **kwargs):
        raise NotImplementedError()

    def get(self, *args, **kwargs):
        is_valid, err_msg = self._namespace.validate(*args, **kwargs)
        if not is_valid:
            raise ValueError(err_msg)
        
        return self._get_data(*args, **kwargs)