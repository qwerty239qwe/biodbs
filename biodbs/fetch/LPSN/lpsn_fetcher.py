"""LPSN API fetcher."""

from __future__ import annotations

import json
import os
from typing import Any, Iterable
from urllib.parse import urljoin

import requests

from biodbs.data.LPSN.data import LPSNFetchedData, LPSNSearchData
from biodbs.exceptions import APIError, APIValidationError, raise_for_status
from biodbs.fetch._rate_limit import get_rate_limiter, request_with_retry

_BASE_URL = "https://api.lpsn.dsmz.de/"
_HOST = "api.lpsn.dsmz.de"
_TOKEN_URL = "https://sso.dsmz.de/auth/realms/dsmz/protocol/openid-connect/token"
_CLIENT_ID = "api.lpsn.public"

get_rate_limiter().set_rate(_HOST, 5)


class LPSN_Fetcher:
    """Fetcher for the LPSN API."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        refresh_token: str | None = None,
        base_url: str = _BASE_URL,
        token_url: str = _TOKEN_URL,
    ):
        self.username = username or os.getenv("BIODBS_LPSN_USERNAME")
        self.password = password or os.getenv("BIODBS_LPSN_PASSWORD")
        self.access_token = token or os.getenv("BIODBS_LPSN_TOKEN")
        self.refresh_token = refresh_token
        self.base_url = base_url
        self.token_url = token_url

    def fetch(self, ids: int | str | Iterable[int | str]) -> LPSNFetchedData:
        """Fetch detailed LPSN records by ID, chunking at the API limit of 100."""
        id_values = self._normalize_ids(ids)
        records: list[dict[str, Any]] = []
        for chunk in self._chunks(id_values, 100):
            data = self._get(f"fetch/{';'.join(chunk)}")
            records.extend(data.get("results", []))
        return LPSNFetchedData({"count": len(records), "results": records})

    def advanced_search(self, page: int = 0, **params: Any) -> LPSNSearchData:
        """Run LPSN advanced search and return matching IDs."""
        query = {self._api_param_name(key): value for key, value in params.items() if value is not None}
        query["page"] = page
        return LPSNSearchData(self._get("advanced_search", params=query))

    def flexible_search(
        self,
        search: dict[str, Any],
        negate: bool = False,
        page: int = 0,
    ) -> LPSNSearchData:
        """Run LPSN flexible exact-match search and return matching IDs."""
        params = {"search": json.dumps(search), "page": page}
        if negate:
            params["not"] = "yes"
        return LPSNSearchData(self._get("flexible_search", params=params))

    def search_and_fetch(self, search: dict[str, Any] | None = None, **params: Any) -> LPSNFetchedData:
        """Search all result pages, then fetch full records."""
        ids: list[int] = []
        page = int(params.pop("page", 0))
        while True:
            result = (
                self.flexible_search(search, page=page)
                if search is not None
                else self.advanced_search(page=page, **params)
            )
            ids.extend(result.ids())
            if not result.next:
                break
            page += 1
        return self.fetch(ids)

    def _get(self, path_or_url: str, params: dict[str, Any] | None = None, retry_auth: bool = True) -> dict[str, Any]:
        url = path_or_url if path_or_url.startswith(("http://", "https://")) else urljoin(self.base_url, path_or_url)
        response = request_with_retry(url, params=params, headers=self._auth_headers())
        if response.status_code == 401 and retry_auth:
            if self.refresh_token:
                self._refresh()
            elif self.username and self.password:
                self.access_token = None
                self._login()
            else:
                raise APIError(
                    "LPSN token expired or was rejected. Provide a fresh token, "
                    "or username/password so biodbs can request a new one.",
                    service="LPSN",
                    status_code=401,
                    url=url,
                )
            response = request_with_retry(url, params=params, headers=self._auth_headers())
        raise_for_status(response, "LPSN", url=url)
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise APIValidationError("LPSN", detail="Response was not valid JSON.", url=url) from exc

    def _auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            self._login()
        return {"Authorization": f"Bearer {self.access_token}"}

    def _login(self):
        if not self.username or not self.password:
            raise APIError(
                "LPSN authentication requires token=... or BIODBS_LPSN_TOKEN, "
                "or username/password via BIODBS_LPSN_USERNAME and BIODBS_LPSN_PASSWORD.",
                service="LPSN",
            )
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "password",
                "client_id": _CLIENT_ID,
                "username": self.username,
                "password": self.password,
            },
            timeout=30,
        )
        raise_for_status(response, "LPSN", url=self.token_url)
        token = response.json()
        self.access_token = token["access_token"]
        self.refresh_token = token.get("refresh_token")

    def _refresh(self):
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": _CLIENT_ID,
                "refresh_token": self.refresh_token,
            },
            timeout=30,
        )
        raise_for_status(response, "LPSN", url=self.token_url)
        token = response.json()
        self.access_token = token["access_token"]
        self.refresh_token = token.get("refresh_token", self.refresh_token)

    @staticmethod
    def _normalize_ids(ids: int | str | Iterable[int | str]) -> list[str]:
        if isinstance(ids, (str, int)):
            return [str(ids)]
        return [str(item) for item in ids]

    @staticmethod
    def _chunks(items: list[str], size: int):
        for start in range(0, len(items), size):
            yield items[start : start + size]

    @staticmethod
    def _api_param_name(name: str) -> str:
        aliases = {
            "taxon_name": "taxon-name",
            "validly_published": "validly-published",
            "correct_name": "correct-name",
        }
        return aliases.get(name, name.replace("_", "-"))
