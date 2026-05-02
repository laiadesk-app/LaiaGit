"""Background check against GitHub Releases for newer versions of LaiaGit.

Best-effort by design. Network failures, rate limits, JSON oddities, and
clock skew never raise — they return None. The dashboard treats None as
"no update info available right now" and stays silent.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from packaging.version import InvalidVersion, Version

from laiagit import __version__

CURRENT_VERSION = __version__

GITHUB_RELEASES_LATEST_API = "https://api.github.com/repos/laiadesk-app/LaiaGit/releases/latest"
RELEASES_PAGE_URL = "https://github.com/laiadesk-app/LaiaGit/releases/latest"
DEFAULT_TIMEOUT_SECONDS = 4.0


@dataclass(frozen=True)
class UpdateInfo:
    """Metadata about an available newer release."""

    current: str
    latest: str
    release_url: str
    body_excerpt: str  # first ~280 chars of release notes, plain text


def _parse(v: str) -> Version | None:
    try:
        return Version(v.lstrip("v"))
    except InvalidVersion:
        return None


def check_for_update(
    *,
    current: str = CURRENT_VERSION,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    api_url: str = GITHUB_RELEASES_LATEST_API,
) -> UpdateInfo | None:
    """Return UpdateInfo if a newer published release exists, else None.

    Never raises — any failure returns None so the UI stays silent.
    """
    cur = _parse(current)
    if cur is None:
        return None
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(
                api_url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"LaiaGit/{current}",
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    tag = data.get("tag_name")
    if not isinstance(tag, str):
        return None
    latest = _parse(tag)
    if latest is None or latest <= cur:
        return None

    body = data.get("body") or ""
    excerpt = body.strip().replace("\r\n", "\n")
    if len(excerpt) > 280:
        excerpt = excerpt[:277].rstrip() + "…"

    release_url = data.get("html_url") or RELEASES_PAGE_URL
    return UpdateInfo(
        current=current,
        latest=tag.lstrip("v"),
        release_url=release_url,
        body_excerpt=excerpt,
    )
