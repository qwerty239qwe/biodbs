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
    if target.exists() and not overwrite:
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    response = request_with_retry(url, stream=True)
    checksum_response = None
    part = None
    try:
        raise_for_status(response, service, url)
        fd, name = tempfile.mkstemp(dir=target.parent, suffix=".part")
        part = Path(name)
        digest = hashlib.md5()
        with os.fdopen(fd, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                file.write(chunk)
                digest.update(chunk)

        if md5_url:
            checksum_response = request_with_retry(md5_url)
            raise_for_status(checksum_response, service, md5_url)
            expected = checksum_response.text.split(maxsplit=1)[0].lower()
            if expected != digest.hexdigest():
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
        if checksum_response is not None:
            checksum_response.close()
