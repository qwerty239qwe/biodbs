from biodbs.fetch.GBIF import funcs


class DummyFetcher:
    def match_name(self, name, strict=False):
        return ("match", name, strict)

    def match_names(self, names, strict=False):
        return ("matches", tuple(names), strict)


def test_convenience_functions_delegate(monkeypatch):
    monkeypatch.setattr(funcs, "_fetcher", DummyFetcher())
    assert funcs.gbif_match_name("Escherichia coli") == ("match", "Escherichia coli", False)
    assert funcs.gbif_match_names(["a", "b"]) == ("matches", ("a", "b"), False)


def test_public_imports():
    from biodbs import gbif_match_name as top_level
    from biodbs.fetch import gbif_match_name

    assert top_level is gbif_match_name
