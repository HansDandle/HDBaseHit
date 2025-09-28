"""Lightweight client for Prowlarr API integration.

This client allows the DVR app to search across all indexers configured in Prowlarr
instead of using direct indexer access. Falls back to BiratePay if Prowlarr is unavailable.

Configuration (env vars override defaults):
  PROWLARR_API_URL     Base URL of Prowlarr instance (default: http://127.0.0.1:9696)
  PROWLARR_API_KEY     API key for Prowlarr authentication
  PROWLARR_TIMEOUT     Per-request timeout in seconds (default 15)

Prowlarr API endpoints used:
  GET /api/v1/search?query=<term>&categories=<cats>&type=search
  GET /api/v1/indexer  -> List available indexers

Returned search results are normalized to match BiratePay format for compatibility.
"""
from __future__ import annotations

import os
import requests
from typing import List, Dict, Any, Optional
import logging

# Configuration
API_URL = os.getenv("PROWLARR_API_URL", "http://127.0.0.1:9696")
API_KEY = os.getenv("PROWLARR_API_KEY", "")
TIMEOUT = float(os.getenv("PROWLARR_TIMEOUT", "15"))

# TV/Movie categories - Prowlarr uses Torznab category codes
TV_CATEGORIES = [5000, 5010, 5020, 5030, 5040, 5045, 5050, 5060, 5070, 5080, 5090]  # TV categories
MOVIE_CATEGORIES = [2000, 2010, 2020, 2030, 2040, 2045, 2050, 2060, 2070, 2080, 2090]  # Movie categories

logger = logging.getLogger(__name__)


class ProwlarrClientError(Exception):
    """Raised for Prowlarr client errors."""
    pass


def _make_request(endpoint: str, params: Dict[str, Any] = None) -> requests.Response:
    """Make authenticated request to Prowlarr API."""
    if not API_KEY:
        raise ProwlarrClientError("PROWLARR_API_KEY environment variable not set")
    
    url = f"{API_URL.rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
    headers = {"X-Api-Key": API_KEY}
    
    try:
        resp = requests.get(url, headers=headers, params=params or {}, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp
    except requests.exceptions.ConnectionError as e:
        raise ProwlarrClientError(f"Connection error contacting Prowlarr at {API_URL}: {e}") from e
    except requests.HTTPError as e:
        raise ProwlarrClientError(f"HTTP error from Prowlarr (status {e.response.status_code}): {e}") from e


def get_indexers() -> List[Dict[str, Any]]:
    """Get list of configured indexers from Prowlarr."""
    try:
        resp = _make_request("indexer")
        indexers = resp.json()
        
        active_indexers = []
        for indexer in indexers:
            if indexer.get("enable", False):
                active_indexers.append({
                    "id": indexer.get("id"),
                    "name": indexer.get("name"),
                    "protocol": indexer.get("protocol"),
                    "categories": indexer.get("capabilities", {}).get("categories", [])
                })
        
        logger.info(f"Found {len(active_indexers)} active indexers in Prowlarr")
        return active_indexers
        
    except Exception as e:
        logger.warning(f"Failed to get indexers from Prowlarr: {e}")
        return []


def search(term: str, content_type: str = "tv", indexer_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Search torrents via Prowlarr API.
    
    Args:
        term: Search query
        content_type: "tv" or "movie" to determine categories
        indexer_ids: Optional list of specific indexer IDs to search
        
    Returns:
        List of normalized torrent dictionaries compatible with BiratePay format
    """
    if not term:
        return []
    
    # Determine categories based on content type
    categories = TV_CATEGORIES if content_type.lower() == "tv" else MOVIE_CATEGORIES
    
    params = {
        "query": term,
        "type": "search",
        "limit": 100,
        "offset": 0
    }
    
    # Add categories as separate parameters
    for i, cat in enumerate(categories):
        params[f"categories[{i}]"] = cat
    
    # Add indexer filter if specified
    if indexer_ids:
        for i, idx_id in enumerate(indexer_ids):
            params[f"indexerIds[{i}]"] = idx_id
    
    try:
        resp = _make_request("search", params)
        data = resp.json()
        
        if not isinstance(data, list):
            logger.warning("Prowlarr returned unexpected response format")
            return []
        
        # Normalize results to match BiratePay format
        normalized = []
        for result in data:
            if not isinstance(result, dict):
                continue
                
            # Parse size from bytes or string format
            size_bytes = None
            size_val = result.get("size")
            if isinstance(size_val, (int, float)):
                size_bytes = int(size_val)
            elif isinstance(size_val, str):
                try:
                    size_bytes = int(size_val)
                except ValueError:
                    pass
            
            # Parse seeders/leechers
            seeders = result.get("seeders", 0)
            leechers = result.get("peers", 0) - seeders if result.get("peers") else result.get("leechers", 0)
            
            normalized.append({
                "title": result.get("title", ""),
                "magnet": result.get("magnetUrl", result.get("downloadUrl", "")),
                "seeders": seeders,
                "leechers": max(0, leechers),  # Ensure non-negative
                "size_bytes": size_bytes,
                "uploader": result.get("uploader", ""),
                "category": result.get("categoryDesc", ""),
                "subcat": "",  # Prowlarr doesn't typically have subcategories in this format
                "id": result.get("guid", ""),
                "time": result.get("publishDate", ""),
                "indexer": result.get("indexer", ""),
                "raw": result,
            })
        
        logger.info(f"Prowlarr search for '{term}' returned {len(normalized)} results")
        return normalized
        
    except ProwlarrClientError:
        raise  # Re-raise Prowlarr-specific errors
    except Exception as e:
        raise ProwlarrClientError(f"Failed to search Prowlarr: {e}") from e


def test_connection() -> bool:
    """Test if Prowlarr is accessible and properly configured."""
    try:
        indexers = get_indexers()
        return len(indexers) > 0
    except Exception as e:
        logger.warning(f"Prowlarr connection test failed: {e}")
        return False


__all__ = ["search", "get_indexers", "test_connection", "ProwlarrClientError"]