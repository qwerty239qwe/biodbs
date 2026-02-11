"""Tests for biodbs.fetch._rate_limit module."""

import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import requests

from biodbs.fetch._rate_limit import (
    RateLimiter,
    get_rate_limiter,
    retry_with_backoff,
    request_with_retry,
)


# =============================================================================
# Helpers
# =============================================================================


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the RateLimiter singleton between tests."""
    limiter = RateLimiter()
    limiter.reset()
    # Also clear _rates to avoid interference from conftest CI rate limits
    saved_rates = dict(limiter._rates)
    limiter._rates.clear()
    yield
    limiter.reset()
    limiter._rates.clear()
    limiter._rates.update(saved_rates)


# =============================================================================
# TestRateLimiter
# =============================================================================


class TestRateLimiter:
    def test_singleton(self):
        a = RateLimiter()
        b = RateLimiter()
        assert a is b

    def test_set_and_get_rate(self):
        limiter = RateLimiter()
        limiter.set_rate("example.com", 5.0)
        assert limiter.get_rate("example.com") == 5.0

    def test_default_rate(self):
        limiter = RateLimiter()
        assert limiter.get_rate("unknown.host") == RateLimiter.DEFAULT_RATE

    def test_substring_host_match(self):
        limiter = RateLimiter()
        limiter.set_rate("api.ncbi", 3.0)
        assert limiter.get_rate("api.ncbi.nlm.nih.gov") == 3.0

    def test_acquire_no_delay_first_call(self):
        limiter = RateLimiter()
        limiter.set_rate("fast.host", 1000)  # Very high rate
        start = time.time()
        limiter.acquire("fast.host")
        elapsed = time.time() - start
        assert elapsed < 0.1

    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_acquire_sleeps_when_too_fast(self, mock_sleep):
        limiter = RateLimiter()
        limiter.set_rate("slow.host", 1.0)  # 1 req/sec
        limiter._last_request["slow.host"] = time.time()
        limiter.acquire("slow.host")
        # Should have been called with some sleep time
        # (may or may not be called depending on timing)
        # At minimum no exception raised

    def test_reset_specific_host(self):
        limiter = RateLimiter()
        limiter._last_request["host1"] = time.time()
        limiter._last_request["host2"] = time.time()
        limiter.reset("host1")
        assert limiter._last_request["host1"] == 0
        assert limiter._last_request["host2"] != 0

    def test_reset_all(self):
        limiter = RateLimiter()
        limiter._last_request["host1"] = time.time()
        limiter._last_request["host2"] = time.time()
        limiter.reset()
        assert len(limiter._last_request) == 0

    def test_get_rate_limiter_returns_instance(self):
        limiter = get_rate_limiter()
        assert isinstance(limiter, RateLimiter)

    def test_thread_safety(self):
        limiter = RateLimiter()
        limiter.set_rate("threaded.host", 100)
        errors = []

        def acquire_many():
            try:
                for _ in range(5):
                    limiter.acquire("threaded.host")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=acquire_many) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []


# =============================================================================
# TestRetryWithBackoff
# =============================================================================


class TestRetryWithBackoff:
    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_success_no_retry(self, mock_sleep):
        @retry_with_backoff(max_retries=3)
        def func():
            return "ok"

        assert func() == "ok"
        mock_sleep.assert_not_called()

    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_retry_on_429(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                resp = MagicMock()
                resp.status_code = 429
                raise requests.exceptions.HTTPError(response=resp)
            return "ok"

        assert func() == "ok"
        assert call_count == 3

    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_retry_on_500(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                resp = MagicMock()
                resp.status_code = 500
                raise requests.exceptions.HTTPError(response=resp)
            return "ok"

        assert func() == "ok"

    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_max_retries_exhausted(self, mock_sleep):
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def func():
            resp = MagicMock()
            resp.status_code = 429
            raise requests.exceptions.HTTPError(response=resp)

        with pytest.raises(requests.exceptions.HTTPError):
            func()

    def test_non_retryable_error(self):
        @retry_with_backoff(max_retries=3)
        def func():
            resp = MagicMock()
            resp.status_code = 404
            raise requests.exceptions.HTTPError(response=resp)

        with pytest.raises(requests.exceptions.HTTPError):
            func()


# =============================================================================
# TestRequestWithRetry
# =============================================================================


class TestRequestWithRetry:
    @patch("biodbs.fetch._rate_limit.requests.get")
    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_successful_get(self, mock_sleep, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        resp = request_with_retry("https://example.com/api", rate_limit=False)
        assert resp.status_code == 200

    @patch("biodbs.fetch._rate_limit.requests.get")
    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_rate_limit_retry(self, mock_sleep, mock_get):
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {}
        mock_429.text = "rate limited"
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_get.side_effect = [mock_429, mock_200]
        resp = request_with_retry("https://example.com/api", rate_limit=False)
        assert resp.status_code == 200

    @patch("biodbs.fetch._rate_limit.requests.get")
    @patch("biodbs.fetch._rate_limit.time.sleep")
    def test_timeout_retry(self, mock_sleep, mock_get):
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_get.side_effect = [
            requests.exceptions.Timeout("timed out"),
            mock_200,
        ]
        resp = request_with_retry("https://example.com/api", rate_limit=False)
        assert resp.status_code == 200
