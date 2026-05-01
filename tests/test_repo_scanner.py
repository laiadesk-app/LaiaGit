from __future__ import annotations

from pathlib import Path

from laiagit.services import RepoScanner


def test_scan_finds_repos(root_with_repos: Path) -> None:
    scanner = RepoScanner()
    repos = scanner.scan(root_with_repos)
    names = sorted(r.name for r in repos)
    assert names == ["alpha", "beta"]


def test_scan_returns_empty_for_missing_dir(tmp_path: Path) -> None:
    scanner = RepoScanner()
    repos = scanner.scan(tmp_path / "does-not-exist")
    assert repos == []


def test_scan_does_not_recurse_inside_a_git_repo(root_with_repos: Path) -> None:
    nested = root_with_repos / "alpha" / "submodule"
    nested.mkdir()
    (nested / ".git").mkdir()
    scanner = RepoScanner()
    repos = scanner.scan(root_with_repos)
    paths = [str(r.path) for r in repos]
    assert all("submodule" not in p for p in paths)
