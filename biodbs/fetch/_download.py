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
    target = Path(target)
    expected = None
    if md5_url:
        checksum_response = request_with_retry(md5_url)
        try:
            raise_for_status(checksum_response, service, md5_url)
            parts = checksum_response.text.split(maxsplit=1)
            expected = parts[0].lower() if parts else ""
            if len(expected) != 32 or any(
                char not in "0123456789abcdef" for char in expected
            ):
                raise APIError("Invalid MD5 checksum response", service=service, url=md5_url)
        finally:
            checksum_response.close()

    if target.exists() and not overwrite:
        if expected is None:
            return target
        digest = hashlib.md5(usedforsecurity=False)
        with target.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() == expected:
            return target

    target.parent.mkdir(parents=True, exist_ok=True)
    response = request_with_retry(url, stream=True)
    part = None
    try:
        raise_for_status(response, service, url)
        if response.headers.get("content-type", "").lower().startswith("text/html"):
            raise APIError("Downloaded URL returned HTML instead of a binary file", service=service, url=url)
        fd, name = tempfile.mkstemp(dir=target.parent, suffix=".part")
        part = Path(name)
        digest = hashlib.md5(usedforsecurity=False)
        first_chunk = True
        with os.fdopen(fd, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                if first_chunk:
                    first_chunk = False
                    prefix = chunk[:512].lstrip().lower()
                    if prefix.startswith(b"<!doctype html") or b"<html" in prefix:
                        raise APIError(
                            "Downloaded URL returned HTML instead of a binary file",
                            service=service,
                            url=url,
                        )
                file.write(chunk)
                digest.update(chunk)

        if expected is not None and expected != digest.hexdigest():
            raise APIError(
                "Downloaded file checksum does not match",
                service=service,
                url=url,
            )

        os.replace(part, target)
        return target
    finally:
        if part:
            part.unlink(missing_ok=True)
        response.close()
