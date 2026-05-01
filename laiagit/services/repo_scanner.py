from __future__ import annotations

from pathlib import Path

from laiagit.models import Repo


class RepoScanner:
    def __init__(self, max_depth: int = 4):
        self.max_depth = max_depth

    def scan(self, root: Path) -> list[Repo]:
        """Scan a single root folder for git repositories."""
        root = root.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            return []

        repos: list[Repo] = []
        for git_dir in self._find_git_dirs(root):
            repo_path = git_dir.parent
            repos.append(Repo(path=repo_path, name=repo_path.name))
        repos.sort(key=lambda r: r.name.lower())
        return repos

    def scan_all(
        self,
        primary_root: Path,
        extras: list[Path] | None = None,
        excluded: set[Path] | None = None,
    ) -> list[Repo]:
        """Scan the primary root plus any extra paths, dropping excluded repos.

        Each extra path is auto-classified:
        - If `<path>/.git` exists, treat the path itself as a single repository.
        - Otherwise, treat it as a folder to scan recursively for repos.

        `excluded` is a set of resolved Paths the user has chosen to hide; any
        match is filtered out before being returned (and never hydrated).
        Repositories are deduplicated by resolved path. Sorted by name.
        """
        seen: set[Path] = set()
        repos: list[Repo] = []
        excluded_set: set[Path] = excluded or set()

        def _accept(repo: Repo) -> bool:
            resolved = repo.path.resolve()
            if resolved in seen or resolved in excluded_set:
                return False
            seen.add(resolved)
            return True

        for repo in self.scan(primary_root):
            if _accept(repo):
                repos.append(repo)

        for raw in extras or []:
            path = raw.expanduser().resolve() if isinstance(raw, Path) else Path(raw).expanduser().resolve()
            if not path.exists():
                continue
            git_dir = path / ".git"
            if git_dir.exists() and git_dir.is_dir():
                candidate = Repo(path=path, name=path.name)
                if _accept(candidate):
                    repos.append(candidate)
                continue
            if not path.is_dir():
                continue
            for found in self.scan(path):
                if _accept(found):
                    repos.append(found)

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
