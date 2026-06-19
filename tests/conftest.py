"""Pytest configuration and fixtures for biodbs tests.

This module configures rate limiting for integration tests to avoid
hitting API rate limits during CI runs.
"""

import os

import pytest

# Network/server error types that indicate an external service is unavailable
# (not a bug in our code).  Integration tests that raise these are skipped
# rather than failed so CI passes even when a third-party API is down.
_EXTERNAL_SERVICE_ERROR_TYPES: tuple = (ConnectionError, TimeoutError)

try:
    import requests.exceptions as _req_exc

    _EXTERNAL_SERVICE_ERROR_TYPES += (
        _req_exc.ConnectTimeout,
        _req_exc.ConnectionError,
        _req_exc.JSONDecodeError,
        _req_exc.Timeout,
        _req_exc.ReadTimeout,
    )
except ImportError:
    pass

try:
    from biodbs.exceptions import (
        APIRateLimitError as _APIRateLimitError,
        APIServerError as _APIServerError,
        APITimeoutError as _APITimeoutError,
    )

    _EXTERNAL_SERVICE_ERROR_TYPES += (
        _APIRateLimitError,
        _APIServerError,
        _APITimeoutError,
    )
except ImportError:
    pass


# CI rate limit overrides - more conservative than defaults
# These are applied only in CI environments to prevent rate limiting
# when tests run in parallel across multiple Python versions
CI_RATE_LIMITS = {
    "api.ncbi.nlm.nih.gov": 2,  # NCBI: 5/s limit, use 2 for CI
    "www.ebi.ac.uk": 5,  # EBI APIs (OLS, ChEMBL, QuickGO)
    "disease-ontology.org": 5,
    "rest.kegg.jp": 5,
    "reactome.org": 5,
    "www.proteinatlas.org": 5,
    "api.fda.gov": 2,  # FDA: 4/s limit
    "pubchem.ncbi.nlm.nih.gov": 2,
    "rest.ensembl.org": 5,
    "maayanlab.cloud": 5,  # EnrichR
    "rest.uniprot.org": 5,  # UniProt
}


def _is_ci_environment() -> bool:
    """Check if running in a CI environment."""
    return (
        os.environ.get("CI", "false").lower() == "true"
        or os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"
    )


@pytest.fixture(scope="session", autouse=True)
def configure_rate_limits_for_ci():
    """Configure conservative rate limits for CI test sessions.

    This runs automatically at the start of the test session.
    In CI environments, it overrides fetcher-registered rate limits
    with more conservative values to prevent rate limiting when
    tests run in parallel.
    """
    from biodbs.fetch._rate_limit import get_rate_limiter

    limiter = get_rate_limiter()

    if _is_ci_environment():
        # Override with conservative CI limits
        for host, rate in CI_RATE_LIMITS.items():
            limiter.set_rate(host, rate)

    yield

    # Reset rate limiter after tests
    limiter.reset()


@pytest.fixture
def rate_limiter():
    """Provide access to the global rate limiter."""
    from biodbs.fetch._rate_limit import get_rate_limiter
    return get_rate_limiter()


def _external_service_skip_reason(exc: BaseException) -> str | None:
    """Return a skip reason for external service failures."""
    if isinstance(exc, _EXTERNAL_SERVICE_ERROR_TYPES):
        return f"External service unavailable ({type(exc).__name__}): {exc}"
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Convert network/server errors in integration tests into skips.

    When an external service (Reactome, BioMart, NCBI, …) is unreachable or
    returns a 5xx error, the test is skipped rather than failed.  This keeps
    CI green even during third-party outages.
    """
    outcome = yield
    if item.get_closest_marker("integration") and outcome.excinfo:
        _, exc_val, _ = outcome.excinfo
        if skip_msg := _external_service_skip_reason(exc_val):
            outcome.force_exception(pytest.skip.Exception(skip_msg))


def pytest_configure(config):
    """Configure pytest based on environment."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (hits real APIs)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
