import logging
import json
from pathlib import Path


class BaseData:
    def __init__(self, content):
        self._content = content  # returns of the requests

    def to_json(self, file_name, mode="w"):
        with open(file_name, mode=mode) as f:
            json.dump(self._content, f)
    