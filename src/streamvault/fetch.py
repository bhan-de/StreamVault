"""Step 2: download each film from TMDb.

How it works, in plain words:
- One request per film. We ask for the film's details and its cast/crew
  in the same request, so TMDb gets half as many calls.
- Every answer is saved in a local cache file. Running again reads from
  that file instead of calling TMDb, so reruns are fast and work offline.
  The token is never saved in that file.
- Each film is also saved as its own JSON file, so you can open and read it.
- We slow ourselves down to a few requests per second, to be polite.
- If TMDb is busy (429) or has a server error (5xx), we wait and try again,
  waiting longer each time. "Not found" (404) is a real answer, so we
  just record it and move on.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import requests
import requests_cache
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

RETRY_STATUS = {429, 500, 502, 503, 504}


class RetryableHTTPError(Exception):
    pass


@dataclass
class FetchResult:
    tmdb_id: int
    http_status: int | None      # empty if we never got an answer
    from_cache: bool
    error: str | None = None


def get_token(names: list[str]) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    raise RuntimeError(f"No TMDb token found in any of {names}")


class TMDbClient:
    def __init__(self, base_url: str, token: str, cache_path: Path,
                 max_per_second: float, max_retries: int):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")
        self.session = requests_cache.CachedSession(
            str(cache_path), backend="sqlite",
            expire_after=-1,                 # keep answers forever, so reruns match
            allowable_codes=(200, 404),      # also remember "not found" answers
        )
        self.session.headers.update({"Authorization": f"Bearer {token}",
                                     "Accept": "application/json"})
        self.min_interval = 1.0 / max_per_second
        self._last_network_call = 0.0
        self.network_calls = 0
        self._get = retry(
            retry=retry_if_exception_type((RetryableHTTPError, requests.ConnectionError,
                                           requests.Timeout)),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            stop=stop_after_attempt(max_retries),
            reraise=True,
        )(self._get_once)

    def _pace(self) -> None:
        wait = self.min_interval - (time.monotonic() - self._last_network_call)
        if wait > 0:
            time.sleep(wait)
        self._last_network_call = time.monotonic()

    def _get_once(self, path: str, params: dict) -> requests.Response:
        url = f"{self.base_url}{path}"
        # Only slow down when we really call TMDb (not for cached answers).
        if not self.session.cache.contains(request=self.session.prepare_request(
                requests.Request("GET", url, params=params, headers=self.session.headers))):
            self._pace()
        resp = self.session.get(url, params=params, timeout=20)
        if not getattr(resp, "from_cache", False):
            self.network_calls += 1
        if resp.status_code in RETRY_STATUS:
            raise RetryableHTTPError(f"HTTP {resp.status_code} for {path}")
        return resp

    def movie(self, tmdb_id: int) -> tuple[FetchResult, dict | None]:
        try:
            resp = self._get(f"/movie/{tmdb_id}", {"append_to_response": "credits"})
        except Exception as err:          # gave up after retries: note it and keep going
            return FetchResult(tmdb_id, None, False, f"{type(err).__name__}: {err}"), None
        payload = resp.json() if resp.status_code == 200 else None
        error = None if resp.status_code == 200 else resp.json().get("status_message")
        return FetchResult(tmdb_id, resp.status_code, resp.from_cache, error), payload

    def collection(self, collection_id: int) -> tuple[int | None, dict | None]:
        """Get the full list of films in one franchise (TMDb calls it a collection)."""
        try:
            resp = self._get(f"/collection/{collection_id}", {})
        except Exception:                 # gave up after retries: note it and keep going
            return None, None
        return resp.status_code, (resp.json() if resp.status_code == 200 else None)

    def find_imdb(self, imdb_id: str) -> list[int]:
        """Ask TMDb which of its films matches an IMDb id (like tt0468569)."""
        resp = self._get(f"/find/{imdb_id}", {"external_source": "imdb_id"})
        resp.raise_for_status()
        return [m["id"] for m in resp.json().get("movie_results", [])]


def save_payload(raw_dir: Path, item_id: int, payload: dict) -> None:
    """Save one answer as <id>.json so it can be opened and read.
    Always UTF-8: film titles and names can contain any language's letters, and
    Windows would otherwise use its old default (cp1252) and crash on them."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / f"{item_id}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
