"""Tests for integration-test external service skip handling."""

import pytest
from requests.exceptions import JSONDecodeError

from biodbs.exceptions import APIRateLimitError, APIServerError, APITimeoutError, APIValidationError
from tests.conftest import _external_service_skip_reason


@pytest.mark.parametrize(
    "exc",
    [
        APIRateLimitError("EnrichR"),
        APIServerError("Reactome", 500),
        APITimeoutError("Ensembl"),
        JSONDecodeError("Expecting value", "", 0),
    ],
)
def test_external_service_errors_are_skippable(exc):
    assert _external_service_skip_reason(exc)


def test_validation_errors_still_fail():
    assert _external_service_skip_reason(APIValidationError("KEGG")) is None
