"""Custom exceptions for biodbs.

Provides a clear exception hierarchy so users can distinguish between
server-side failures, rate limiting, invalid input, and other errors.

Example::

    from biodbs.exceptions import APIServerError, APIRateLimitError

    try:
        data = fetcher.get(...)
    except APIServerError as e:
        print(f"{e.service} is down (HTTP {e.status_code}), retry later")
    except APIRateLimitError as e:
        time.sleep(e.retry_after)
"""

from typing import Optional


class BiodBSError(Exception):
    """Base exception for all biodbs errors."""


class APIError(BiodBSError):
    """Base exception for API-related errors.

    Attributes:
        service: Name of the API service (e.g. "ChEMBL", "KEGG").
        status_code: HTTP status code, if applicable.
        url: The URL that failed, if available.
    """

    def __init__(
        self,
        message: str,
        *,
        service: str = "",
        status_code: Optional[int] = None,
        url: str = "",
    ):
        self.service = service
        self.status_code = status_code
        self.url = url
        super().__init__(message)


class APIServerError(APIError):
    """Raised when an API returns a 5xx server error.

    This indicates a server-side issue — not a problem with your code
    or biodbs. Retry the request later.
    """

    def __init__(
        self,
        service: str,
        status_code: int,
        url: str = "",
        response_text: str = "",
    ):
        msg = (
            f"The {service} server is temporarily unavailable (HTTP {status_code}).\n"
            f"This is a server-side issue, not a problem with your code or biodbs.\n"
            f"Please try again later."
        )
        if url:
            msg += f"\nURL: {url}"
        super().__init__(
            msg, service=service, status_code=status_code, url=url
        )
        self.response_text = response_text


class APIRateLimitError(APIError):
    """Raised when an API returns HTTP 429 (Too Many Requests).

    Attributes:
        retry_after: Suggested seconds to wait before retrying.
    """

    def __init__(
        self,
        service: str,
        retry_after: Optional[float] = None,
        url: str = "",
    ):
        self.retry_after = retry_after
        wait = f" Retry after {retry_after}s." if retry_after else ""
        msg = f"Rate limit exceeded for {service}.{wait}"
        if url:
            msg += f"\nURL: {url}"
        super().__init__(
            msg, service=service, status_code=429, url=url
        )


class APINotFoundError(APIError):
    """Raised when an API returns HTTP 404 (Not Found)."""

    def __init__(
        self,
        service: str,
        url: str = "",
        detail: str = "",
    ):
        msg = f"Resource not found on {service}."
        if detail:
            msg += f" {detail}"
        if url:
            msg += f"\nURL: {url}"
        super().__init__(
            msg, service=service, status_code=404, url=url
        )


class APITimeoutError(APIError):
    """Raised when a request to an API times out."""

    def __init__(
        self,
        service: str,
        url: str = "",
        timeout: Optional[float] = None,
    ):
        msg = f"Request to {service} timed out"
        if timeout:
            msg += f" after {timeout}s"
        msg += "."
        if url:
            msg += f"\nURL: {url}"
        super().__init__(
            msg, service=service, status_code=None, url=url
        )
        self.timeout = timeout


class APIValidationError(APIError):
    """Raised when an API returns HTTP 400 (Bad Request)."""

    def __init__(
        self,
        service: str,
        detail: str = "",
        url: str = "",
    ):
        msg = f"Invalid request to {service}."
        if detail:
            msg += f" {detail}"
        if url:
            msg += f"\nURL: {url}"
        super().__init__(
            msg, service=service, status_code=400, url=url
        )


class IDTranslationError(BiodBSError):
    """Raised when gene/chemical ID translation fails."""

    def __init__(
        self,
        message: str,
        *,
        source_db: str = "",
        target_db: str = "",
        failed_ids: Optional[list] = None,
    ):
        self.source_db = source_db
        self.target_db = target_db
        self.failed_ids = failed_ids or []
        super().__init__(message)


def raise_for_status(
    response,
    service: str,
    url: str = "",
):
    """Raise an appropriate exception based on HTTP response status.

    Args:
        response: A ``requests.Response`` object.
        service: Name of the API service for error messages.
        url: Override URL (defaults to ``response.url``).

    Raises:
        APIRateLimitError: On HTTP 429.
        APINotFoundError: On HTTP 404.
        APIValidationError: On HTTP 400.
        APIServerError: On HTTP 5xx.
        APIError: On other non-200 status codes.
    """
    url = url or getattr(response, "url", "")
    code = response.status_code

    if 200 <= code < 300:
        return

    # Truncate long response bodies for error messages
    text = getattr(response, "text", "")
    if len(text) > 500:
        text = text[:500] + "..."

    if code == 429:
        retry_after = None
        raw = response.headers.get("Retry-After")
        if raw:
            try:
                retry_after = float(raw)
            except ValueError:
                pass
        raise APIRateLimitError(service, retry_after=retry_after, url=url)

    if code == 404:
        raise APINotFoundError(service, url=url, detail=text)

    if code == 400:
        raise APIValidationError(service, detail=text, url=url)

    if code >= 500:
        raise APIServerError(service, code, url=url, response_text=text)

    # Other client errors (401, 403, etc.)
    raise APIError(
        f"{service} request failed (HTTP {code}). {text}",
        service=service,
        status_code=code,
        url=url,
    )
