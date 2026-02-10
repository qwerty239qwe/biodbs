"""Tests for biodbs.fetch._base module."""

import pytest
from pydantic import BaseModel
from biodbs.fetch._base import BaseAPIConfig, NameSpace, BaseDataFetcher


# =============================================================================
# TestBaseAPIConfig
# =============================================================================


class TestBaseAPIConfig:
    def test_template_mode(self):
        config = BaseAPIConfig(url_format="https://api.example.com/{category}/{endpoint}")
        config.update_params(category="data", endpoint="search")
        assert config.api_url == "https://api.example.com/data/search"

    def test_builder_mode(self):
        def builder(params):
            return f"https://api.example.com/{params['path']}"

        config = BaseAPIConfig(url_builder=builder)
        config.update_params(path="test")
        assert config.api_url == "https://api.example.com/test"

    def test_builder_takes_precedence(self):
        def builder(params):
            return "https://custom.url"

        config = BaseAPIConfig(
            url_format="https://template.url/{x}",
            url_builder=builder,
        )
        config.update_params(x="val")
        assert config.api_url == "https://custom.url"

    def test_update_params(self):
        config = BaseAPIConfig(url_format="https://api.example.com/{a}/{b}")
        config.update_params(a="1")
        config.update_params(b="2")
        assert config.api_url == "https://api.example.com/1/2"

    def test_apply_returns_new(self):
        config = BaseAPIConfig(url_format="https://api.example.com/{x}")
        config.update_params(x="old")
        new_config = config.apply(x="new")
        assert new_config.api_url == "https://api.example.com/new"
        assert config.api_url == "https://api.example.com/old"

    def test_copy(self):
        config = BaseAPIConfig(url_format="https://api.example.com/{x}")
        config.update_params(x="val")
        copied = config.copy()
        assert copied.api_url == config.api_url
        assert copied is not config

    def test_no_format_raises(self):
        config = BaseAPIConfig()
        with pytest.raises(NotImplementedError):
            _ = config.api_url

    def test_str(self):
        config = BaseAPIConfig(url_format="https://api.example.com/{x}")
        s = str(config)
        assert "BaseAPIConfig" in s
        assert "api.example.com" in s


# =============================================================================
# TestNameSpace
# =============================================================================


class _TestModel(BaseModel):
    name: str
    value: int = 10


class TestNameSpace:
    def test_validate_valid(self):
        ns = NameSpace(_TestModel)
        ok, msg = ns.validate(name="test", value=5)
        assert ok is True
        assert ns.valid_params == {"name": "test", "value": 5}

    def test_validate_with_defaults(self):
        ns = NameSpace(_TestModel)
        ok, msg = ns.validate(name="test")
        assert ok is True
        assert ns.valid_params["value"] == 10

    def test_validate_invalid(self):
        ns = NameSpace(_TestModel)
        ok, msg = ns.validate(value=5)  # Missing required 'name'
        assert ok is False
        assert "name" in msg.lower() or "field" in msg.lower()

    def test_validate_wrong_type(self):
        ns = NameSpace(_TestModel)
        ok, msg = ns.validate(name="test", value="not_an_int")
        assert ok is False


# =============================================================================
# TestBaseDataFetcher
# =============================================================================


class TestBaseDataFetcher:
    def test_get_raises(self):
        config = BaseAPIConfig(url_format="https://example.com")
        ns = NameSpace(_TestModel)
        fetcher = BaseDataFetcher(config, ns, {})
        with pytest.raises(NotImplementedError):
            fetcher.get()

    def test_schedule_process_empty(self):
        config = BaseAPIConfig(url_format="https://example.com")
        ns = NameSpace(_TestModel)
        fetcher = BaseDataFetcher(config, ns, {})
        result = fetcher.schedule_process(lambda: None)
        assert result == []

    def test_schedule_process_mismatched_lengths(self):
        config = BaseAPIConfig(url_format="https://example.com")
        ns = NameSpace(_TestModel)
        fetcher = BaseDataFetcher(config, ns, {})
        with pytest.raises(ValueError, match="same length"):
            fetcher.schedule_process(
                lambda x: x,
                args_list=[(1,), (2,)],
                kwargs_list=[{}],
            )
