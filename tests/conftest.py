"""Pytest configuration and fixtures for biodbs tests.

This module configures rate limiting for integration tests to avoid
hitting API rate limits during CI runs.
"""

import pytest
import os


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


def pytest_configure(config):
    """Configure pytest based on environment."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (hits real APIs)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
