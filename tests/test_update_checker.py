"""Tests for update_checker — must NEVER raise on failure paths."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest

from laiagit.services.update_checker import UpdateInfo, check_for_update


def _mock_response(payload: dict[str, Any], status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload, request=httpx.Request("GET", "https://x"))


@pytest.fixture
def patched_get():
    """Yield a patcher for httpx.Client.get; tests set the return_value."""
    with patch("httpx.Client.get") as p:
        yield p


def test_returns_update_when_remote_is_newer(patched_get):
    patched_get.return_value = _mock_response(
        {
            "tag_name": "v0.2.0",
            "html_url": "https://github.com/laiadesk-app/LaiaGit/releases/tag/v0.2.0",
            "body": "Highlights:\n- Search across repos\n- Batch commits",
        }
    )
    info = check_for_update(current="0.1.0")
    assert isinstance(info, UpdateInfo)
    assert info.current == "0.1.0"
    assert info.latest == "0.2.0"
    assert "Search across repos" in info.body_excerpt
    assert info.release_url.endswith("/v0.2.0")


def test_returns_none_when_remote_equal(patched_get):
    patched_get.return_value = _mock_response({"tag_name": "v0.1.1"})
    assert check_for_update(current="0.1.1") is None


def test_returns_none_when_remote_older(patched_get):
    patched_get.return_value = _mock_response({"tag_name": "v0.1.0"})
    assert check_for_update(current="0.2.0") is None


def test_handles_pre_release_semantics(patched_get):
    # 0.1.0-alpha (== 0.1.0a0) is older than 0.1.0 final
    patched_get.return_value = _mock_response({"tag_name": "v0.1.0"})
    info = check_for_update(current="0.1.0-alpha")
    assert info is not None
    assert info.latest == "0.1.0"


def test_returns_none_on_http_error(patched_get):
    patched_get.side_effect = httpx.ConnectError("offline")
    assert check_for_update(current="0.1.0") is None


def test_returns_none_on_5xx(patched_get):
    patched_get.return_value = httpx.Response(503, request=httpx.Request("GET", "https://x"))
    assert check_for_update(current="0.1.0") is None


def test_returns_none_on_malformed_json(patched_get):
    patched_get.return_value = httpx.Response(
        200, content=b"not json at all", request=httpx.Request("GET", "https://x")
    )
    assert check_for_update(current="0.1.0") is None


def test_returns_none_when_tag_missing(patched_get):
    patched_get.return_value = _mock_response({"name": "Release"})
    assert check_for_update(current="0.1.0") is None


def test_returns_none_when_tag_is_garbage(patched_get):
    patched_get.return_value = _mock_response({"tag_name": "release-2026-spring"})
    assert check_for_update(current="0.1.0") is None


def test_returns_none_when_current_unparseable(patched_get):
    # Should not even try the network when local version is bogus.
    patched_get.return_value = _mock_response({"tag_name": "v9.9.9"})
    assert check_for_update(current="garbage-version") is None


def test_body_truncated_to_280_chars(patched_get):
    long_body = "x " * 500
    patched_get.return_value = _mock_response({"tag_name": "v9.9.9", "body": long_body})
    info = check_for_update(current="0.1.0")
    assert info is not None
    assert len(info.body_excerpt) <= 280


def test_falls_back_to_releases_page_when_html_url_missing(patched_get):
    patched_get.return_value = _mock_response({"tag_name": "v9.9.9"})
    info = check_for_update(current="0.1.0")
    assert info is not None
    assert info.release_url.startswith("https://github.com/laiadesk-app/LaiaGit/")
