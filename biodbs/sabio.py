import pandas as pd
import requests


SABIO_ROOT_URL = "http://sabiork.h-its.org/sabioRestWebServices"


class SABIO_DB:
    default_output_fields = {"get_kinetic_law": ['EntryID', 'Organism', 'UniprotID','ECNumber', 'Parameter']}

    def __init__(self, host=SABIO_ROOT_URL):
        self.host = host

    def get_kinetic_law(self, organism, substrate, product, output_fields="default"):
        url = self.host + "/kineticlawsExportTsv"
        query_dict = {"Organism": organism, "Product": product, "Substrate": substrate}
        query_dict = {k: f'"{v}"' for k, v in query_dict if v is not None}
        query_string = ' AND '.join([f'{k}:{v}' for k, v in query_dict.items()])

        query = {'fields[]': self.default_output_fields['get_kinetic_law'], 'q': query_string}
        rsp = requests.post(url, params=query)

        return pd.DataFrame(rsp.text)