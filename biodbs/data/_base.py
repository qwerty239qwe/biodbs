import logging
import json
from pathlib import Path


class BaseFetchedData:
    def __init__(self, content):
        self._content = content  # returns of the requests

    def to_json(self, file_name, mode="w"):
        with open(file_name, mode=mode) as f:
            json.dump(self._content, f)
    
    def to_text(self, file_name, mode="w"):
        with open(file_name, mode=mode) as f:
            f.write(str(self._content)) 

    def to_csv(self, file_name, mode="w"):
        raise NotImplementedError("This method should be implemented in subclass.")

    def as_dict(self):
        raise NotImplementedError("This method should be implemented in subclass.")
    
    def as_dataframe(self, engine="pandas"):
        raise NotImplementedError("This method should be implemented in subclass.")


class BasedFDAFetchedData(BaseFetchedData):
    def __init__(self, content):
        super().__init__(content)
        self.metadata = content.get("meta", {})
        self.results = content.get("results", [])
    