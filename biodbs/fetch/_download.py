"""Shared atomic binary downloader with optional MD5 verification.

Streams a remote file to a temporary ``.part`` sibling and only ``os.replace``s
it into place on success, so an interrupted transfer never leaves a partial file
that later calls would mistake for a complete download.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from biodbs.exceptions import APIError, raise_for_status
from biodbs.fetch._rate_limit import request_with_retry


def download_binary(
    url: str,
    target: str | Path,
    service: str,
    *,
    overwrite: bool = False,
    md5_url: str | None = None,
) -> Path:
    """Download *url* to *target*, verifying an optional published MD5.

    *target* must be a concrete file path (callers resolve directories first).
    When *md5_url* is given, the download is rejected unless its MD5 matches the
    first whitespace-delimited token of the fetched checksum file.
    """
    target = Path(target)
    if target.exists() and not overwrite:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    response = request_with_retry(url, stream=True)
    raise_for_status(response, service, url=url)
    fd, part_name = tempfile.mkstemp(prefix=f"{target.name}.", suffix=".part", dir=target.parent)
    part = Path(part_name)
    digest = hashlib.md5()
    try:
        with os.fdopen(fd, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
                    digest.update(chunk)
        if md5_url:
            checksum_response = request_with_retry(md5_url)
            raise_for_status(checksum_response, service, url=md5_url)
            expected = checksum_response.text.split()[0].lower()
            if digest.hexdigest() != expected:
                raise APIError(
                    f"{service} checksum mismatch for {url!r}.",
                    service=service,
                    url=url,
                )
        os.replace(part, target)
    finally:
        part.unlink(missing_ok=True)
        close = getattr(response, "close", None)
        if close:
            close()
    return target
