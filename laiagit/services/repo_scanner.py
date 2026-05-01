from __future__ import annotations

from pathlib import Path

from laiagit.models import Repo


class RepoScanner:
    def __init__(self, max_depth: int = 4):
        self.max_depth = max_depth

    def scan(self, root: Path) -> list[Repo]:
        root = root.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            return []

        repos: list[Repo] = []
        for git_dir in self._find_git_dirs(root):
            repo_path = git_dir.parent
            repos.append(Repo(path=repo_path, name=repo_path.name))
        repos.sort(key=lambda r: r.name.lower())
        return repos

    def _find_git_dirs(self, root: Path) -> list[Path]:
        results: list[Path] = []
        self._walk(root, current_depth=0, results=results)
        return results

    def _walk(self, directory: Path, current_depth: int, results: list[Path]) -> None:
        if current_depth > self.max_depth:
            return
        try:
            entries = list(directory.iterdir())
        except (PermissionError, OSError):
            return

        for entry in entries:
            if entry.is_dir() and entry.name == ".git":
                results.append(entry)
                return

        for entry in entries:
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue
            self._walk(entry, current_depth + 1, results)
