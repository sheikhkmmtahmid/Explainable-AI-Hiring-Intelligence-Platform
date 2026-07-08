"""
Thin wrapper around the public ESCO (European Skills, Competences,
Qualifications and Occupations) REST API. No API key required.

Contract verified directly against the live production endpoint:
  https://ec.europa.eu/esco/api/search?text={query}&language=en&type=skill&limit={n}
  -> {"total": int, "_embedded": {"results": [{"uri": str, "title": str,
       "preferredLabel": {"en": str}, "_links": {"self": {"href": str}}}]}}

  https://ec.europa.eu/esco/api/resource/skill?uri={uri}&language=en
  -> {"preferredLabel": {"en": str}, "alternativeLabel": {"en": [str, ...]},
       "description": {...}}
"""
import logging

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://ec.europa.eu/esco/api/search"
RESOURCE_URL = "https://ec.europa.eu/esco/api/resource/skill"
REQUEST_TIMEOUT = 10


def search_skills(query: str, limit: int = 10) -> list[dict]:
    """Search ESCO for skills matching a free-text query. Returns a list of
    {"uri": str, "title": str} dicts, or [] on any network/API failure --
    the sync should degrade gracefully, not crash the caller."""
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"text": query, "language": "en", "type": "skill", "limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("ESCO search failed for query %r: %s", query, exc)
        return []

    results = data.get("_embedded", {}).get("results", [])
    out = []
    for r in results:
        title = r.get("preferredLabel", {}).get("en") or r.get("title")
        uri = r.get("uri")
        if title and uri:
            out.append({"uri": uri, "title": title})
    return out


def get_skill_aliases(uri: str) -> list[str]:
    """Fetch alternative labels (aliases) for a specific ESCO skill concept."""
    try:
        resp = requests.get(
            RESOURCE_URL, params={"uri": uri, "language": "en"}, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("ESCO resource fetch failed for uri %r: %s", uri, exc)
        return []
    return data.get("alternativeLabel", {}).get("en", []) or []
