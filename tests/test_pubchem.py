from biodbs.pubchem.pug_view import CompoundFetcher, AssayFetcher


def test_compound_fetcher():
    fetcher = CompoundFetcher()
    cmp = fetcher.fetch("123", "JSON")
    fetcher.get_processed_data("123")