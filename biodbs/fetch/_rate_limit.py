"""Rate limiting and retry utilities for API fetchers.

This module provides:
    - RateLimiter: Per-host rate limiting to prevent API throttling
    - retry_with_backoff: Decorator for automatic retry with exponential backoff
    - request_with_retry: Helper function for making rate-limited requests with retry
"""

import time
import logging
import threading
from collections import defaultdict
from typing import Callable, Optional, TypeVar, Any, Dict
from functools import wraps
import requests

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """Thread-safe rate limiter that enforces requests per second limits.

    Uses a token bucket algorithm to smooth out request rates.
    Each API host can have its own rate limit.

    This class follows the Open-Closed Principle: it provides generic
    rate limiting without knowledge of specific APIs. Each fetcher
    registers its own rate limit via set_rate().

    Example::

        limiter = RateLimiter()
        limiter.set_rate("api.ncbi.nlm.nih.gov", 5)  # 5 requests per second

        # Before each request:
        limiter.acquire("api.ncbi.nlm.nih.gov")
    """

    # Global instance for sharing across fetchers
    _instance: Optional["RateLimiter"] = None
    _lock = threading.Lock()

    # Default fallback rate when no specific rate is registered
    DEFAULT_RATE = 10

    def __new__(cls) -> "RateLimiter":
        """Singleton pattern to share rate limiter across all fetchers."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._rates: Dict[str, float] = {}  # host -> requests per second
        self._last_request: Dict[str, float] = defaultdict(float)  # host -> timestamp
        self._request_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()

    def set_rate(self, host: str, requests_per_second: float):
        """Set rate limit for a specific host.

        Args:
            host: API hostname (e.g., "api.ncbi.nlm.nih.gov")
            requests_per_second: Maximum requests per second
        """
        with self._global_lock:
            self._rates[host] = requests_per_second

    def get_rate(self, host: str) -> float:
        """Get rate limit for a host.

        Args:
            host: API hostname

        Returns:
            Requests per second limit (DEFAULT_RATE if not set)
        """
        with self._global_lock:
            if host in self._rates:
                return self._rates[host]
            # Check if any registered host is a substring match
            for registered_host, rate in self._rates.items():
                if registered_host in host or host in registered_host:
                    return rate
            return self.DEFAULT_RATE

    def acquire(self, host: str):
        """Acquire permission to make a request, blocking if necessary.

        This method will block until it's safe to make a request
        without exceeding the rate limit.

        Args:
            host: API hostname
        """
        rate = self.get_rate(host)
        min_interval = 1.0 / rate

        # Get lock for this specific host
        with self._global_lock:
            if host not in self._request_locks:
                self._request_locks[host] = threading.Lock()
            lock = self._request_locks[host]

        with lock:
            now = time.time()
            last = self._last_request[host]
            elapsed = now - last

            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug(f"Rate limiting {host}: sleeping {sleep_time:.3f}s")
                time.sleep(sleep_time)

            self._last_request[host] = time.time()

    def reset(self, host: Optional[str] = None):
        """Reset rate limiter state.

        Args:
            host: If provided, reset only this host. Otherwise reset all.
        """
        with self._global_lock:
            if host:
                self._last_request[host] = 0
            else:
                self._last_request.clear()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: tuple = (429, 500, 502, 503, 504),
):
    """Decorator for retrying functions with exponential backoff.

    Retries on rate limit (429) and server errors with increasing delays.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        retry_on: HTTP status codes to retry on

    Example::

        @retry_with_backoff(max_retries=3)
        def make_api_call():
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code if e.response else None
                    if status_code not in retry_on or attempt == max_retries:
                        raise

                    last_exception = e
                    logger.warning(
                        f"Request failed with status {status_code}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)

                except ConnectionError as e:
                    # Handle our custom ConnectionError from fetchers
                    error_msg = str(e)
                    if "429" in error_msg or "rate limit" in error_msg.lower():
                        if attempt == max_retries:
                            raise
                        last_exception = e
                        logger.warning(
                            f"Rate limited, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        raise

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")

        return wrapper

    return decorator


def request_with_retry(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    json: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    rate_limit: bool = True,
    timeout: float = 30.0,
) -> requests.Response:
    """Make an HTTP request with rate limiting and automatic retry.

    This is a convenience function that combines rate limiting and retry logic.

    Args:
        url: Request URL
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        headers: Request headers
        data: Request body data
        json: JSON body data
        max_retries: Maximum retry attempts
        initial_delay: Initial retry delay in seconds
        rate_limit: Whether to apply rate limiting
        timeout: Request timeout in seconds

    Returns:
        Response object

    Raises:
        ConnectionError: If all retries fail
    """
    # Extract host from URL for rate limiting
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.netloc

    limiter = get_rate_limiter()
    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            # Apply rate limiting
            if rate_limit:
                limiter.acquire(host)

            # Make request
            if method.upper() == "GET":
                response = requests.get(
                    url, params=params, headers=headers, timeout=timeout
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    params=params,
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=timeout,
                )
            else:
                response = requests.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    data=data,
                    json=json,
                    timeout=timeout,
                )

            # Check for rate limiting response
            if response.status_code == 429:
                if attempt == max_retries:
                    raise ConnectionError(
                        f"Rate limited after {max_retries} retries. "
                        f"Status: 429, Message: {response.text}"
                    )
                # Get retry-after header if available
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        pass

                logger.warning(
                    f"Rate limited (429), retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue

            # Check for server errors
            if response.status_code >= 500:
                if attempt == max_retries:
                    raise ConnectionError(
                        f"Server error after {max_retries} retries. "
                        f"Status: {response.status_code}, Message: {response.text}"
                    )
                logger.warning(
                    f"Server error ({response.status_code}), retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue

            return response

        except requests.exceptions.Timeout as e:
            if attempt == max_retries:
                raise ConnectionError(f"Request timed out after {max_retries} retries: {e}")
            last_exception = e
            logger.warning(
                f"Request timed out, retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(delay)
            delay = min(delay * 2, 60.0)

        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                raise ConnectionError(f"Request failed after {max_retries} retries: {e}")
            last_exception = e
            logger.warning(
                f"Request failed ({e}), retrying in {delay:.1f}s "
                f"(attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(delay)
            delay = min(delay * 2, 60.0)

    # Should not reach here
    if last_exception:
        raise ConnectionError(f"Request failed: {last_exception}")
    raise RuntimeError("Unexpected request loop exit")
