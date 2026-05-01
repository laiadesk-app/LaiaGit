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


def test_scan_all_includes_extras_as_folders_and_direct_repos(root_with_repos: Path, tmp_path: Path) -> None:
    """scan_all combines the primary root with extras of two kinds."""
    import subprocess

    # Direct repo path
    standalone = tmp_path / "standalone-repo"
    standalone.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=standalone, check=True, capture_output=True)

    # Another root folder with one repo inside
    other_root = tmp_path / "other-root"
    other_root.mkdir()
    other_repo = other_root / "gamma"
    other_repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=other_repo, check=True, capture_output=True)

    scanner = RepoScanner()
    repos = scanner.scan_all(root_with_repos, [standalone, other_root])
    names = sorted(r.name for r in repos)
    assert names == ["alpha", "beta", "gamma", "standalone-repo"]


def test_scan_all_dedupes_when_extra_overlaps_root(root_with_repos: Path) -> None:
    """If an extra path is already inside the primary root, it should not be duplicated."""
    scanner = RepoScanner()
    extra = root_with_repos / "alpha"  # this repo is already discovered by the main scan
    repos = scanner.scan_all(root_with_repos, [extra])
    names = sorted(r.name for r in repos)
    assert names == ["alpha", "beta"]


def test_scan_all_ignores_missing_extras(root_with_repos: Path, tmp_path: Path) -> None:
    scanner = RepoScanner()
    repos = scanner.scan_all(root_with_repos, [tmp_path / "does-not-exist"])
    assert sorted(r.name for r in repos) == ["alpha", "beta"]
