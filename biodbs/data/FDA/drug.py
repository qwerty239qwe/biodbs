from biodbs.data._base import BasedFDAFetchedData


class FDADrugEventData(BasedFDAFetchedData):
    def __init__(self, content):
        super().__init__(content)

    