"""Lightweight client for the local BiratePay (Pirate Bay test) API.

The client is optional. If the service is not running, callers should
gracefully handle connection errors and fall back to existing behavior.

Configuration (env vars override defaults):
  BIRATEPAY_API_URL   Base URL of the running BiratePay Flask service
  BIRATEPAY_TIMEOUT   Per-request timeout in seconds (default 10)

Expected API endpoints (mirrors the included thebiratepay-master project):
  GET /search/<term>/<page>/  -> JSON list of torrents

Returned torrent object keys from the API (subset we exploit):
  title, magnet, seeds, leeches, size, time, uploader, category, subcat, id

We normalize a subset into a canonical structure consumed by the DVR UI.
"""
from __future__ import annotations

import os
import requests
from typing import List, Dict, Any


API_URL = os.getenv("BIRATEPAY_API_URL", "http://127.0.0.1:5055")  # Avoid port clash with main DVR Flask
TIMEOUT = float(os.getenv("BIRATEPAY_TIMEOUT", "10"))


class BiratePayClientError(Exception):
    """Raised for non-network logical client errors."""
    pass


def search(term: str, page: int = 0, sort: str | None = None) -> List[Dict[str, Any]]:
    """Search torrents.

    term: search phrase (spaces allowed; will be url-encoded by requests)
    page: results page (0-based as per API)
    sort: optional sort key supported by upstream (e.g. seeds_desc)

    Returns list[dict] normalized with the fields we care about. If the
    upstream API returns an unexpected shape we surface what we can.
    """
    if not term:
        return []
    # Build path; upstream ignores trailing slash after page integer.
    url = f"{API_URL}/search/{term}/{page}/"
    params = {}
    if sort:
        params["sort"] = sort
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise BiratePayClientError("Unexpected response format (not a list)")
        normalized = []
        for t in data:
            if not isinstance(t, dict):
                continue
            normalized.append({
                "title": t.get("title") or t.get("name"),
                "magnet": t.get("magnet"),
                "seeders": t.get("seeds") or t.get("seeders"),
                "leechers": t.get("leeches") or t.get("leechers"),
                "size_bytes": t.get("size"),
                "uploader": t.get("uploader"),
                "category": t.get("category"),
                "subcat": t.get("subcat"),
                "id": t.get("id"),
                "raw": t,
            })
        return normalized
    except requests.exceptions.ConnectionError as e:
        raise BiratePayClientError(f"Connection error contacting BiratePay at {API_URL}: {e}") from e
    except requests.HTTPError as e:
        raise BiratePayClientError(f"HTTP error from BiratePay: {e}") from e
    except ValueError as e:
        raise BiratePayClientError(f"Failed to decode JSON from BiratePay: {e}") from e


__all__ = ["search", "BiratePayClientError"]
