import pytest
from unittest.mock import patch, MagicMock
from biodbs.fetch.QuickGO import QuickGODB, SearchFetcher, SlimFetcher, ChartFetcher, TermFetcher


@pytest.fixture
def quickgo_db():
    return QuickGODB()


class TestQuickGOAPI:
    def test_init_default_host(self, quickgo_db):
        assert quickgo_db.host == "https://www.ebi.ac.uk/QuickGO/services/ontology/go"
        assert quickgo_db.json_header == {"Accept": "application/json"}
        assert quickgo_db.png_header == {"Accept": "image/png"}

    def test_init_custom_host(self):
        db = QuickGODB(host="https://custom.example.com")
        assert db.host == "https://custom.example.com/ontology/go"


class TestSearchFetcher:
    @patch('biodbs.fetch.QuickGO.api.get_rsp')
    def test_search_returns_dataframe(self, mock_get_rsp, quickgo_db):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "GO:0001", "name": "test"}],
            "numberOfHits": 1,
            "pageInfo": None
        }
        mock_get_rsp.return_value = mock_response

        result = quickgo_db.search("test_query")

        assert not result.empty
        assert "id" in result.columns
        assert result.iloc[0]["id"] == "GO:0001"


class TestSlimFetcher:
    @patch('biodbs.fetch.QuickGO.api.get_rsp')
    def test_slim_accepts_list_relations(self, mock_get_rsp, quickgo_db):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "GO:0002"}],
            "numberOfHits": 1,
            "pageInfo": None
        }
        mock_get_rsp.return_value = mock_response

        result = quickgo_db.fetch_slim("GO:0001", relations=["is_a", "part_of"])

        assert not result.empty


class TestChartFetcher:
    @patch('biodbs.fetch.QuickGO.fetchers.get_rsp')
    def test_save_chart_calls_get_rsp(self, mock_get_rsp, quickgo_db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get_rsp.return_value = mock_response

        with patch('biodbs.fetch.QuickGO.fetchers.save_image_from_rsp') as mock_save:
            quickgo_db.save_chart(["GO:0001"], "test.png")
            mock_save.assert_called_once()


class TestTermFetcher:
    @patch('biodbs.fetch.QuickGO.fetchers.get_rsp')
    def test_get_ancestors_returns_dataframe(self, mock_get_rsp, quickgo_db):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "GO:0001", "ancestors": []}]
        }
        mock_get_rsp.return_value = mock_response

        result = quickgo_db.get_ancestors(["GO:0001"])

        assert not result.empty

    @patch('biodbs.fetch.QuickGO.fetchers.get_rsp')
    def test_get_children_returns_dataframe(self, mock_get_rsp, quickgo_db):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "GO:0002"}]
        }
        mock_get_rsp.return_value = mock_response

        result = quickgo_db.get_children(["GO:0001"])

        assert not result.empty
