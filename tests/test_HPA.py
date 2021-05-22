import pytest
import pandas as pd
from biodbs import HPA


@pytest.fixture
def HPA_db():
    yield HPA.HPAdb()


def test_list_proteins(HPA_db):
    df, _ = HPA_db.list_proteins()
    assert isinstance(df, pd.DataFrame)


def test_download_HPA_data(HPA_db, tmp_path):
    HPA_db.download_HPA_data(options=[name for name in HPA.DOWNLOADABLE_DATA[:4]],
                             saved_path=tmp_path)