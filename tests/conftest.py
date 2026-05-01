from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from git import Repo as GitRepo


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a fresh git repo with a single initial commit on `main`."""
    repo_path = tmp_path / "demo"
    repo_path.mkdir()
    git_repo = GitRepo.init(repo_path, initial_branch="main")
    git_repo.config_writer().set_value("user", "name", "Test User").release()
    git_repo.config_writer().set_value("user", "email", "test@example.com").release()
    (repo_path / "README.md").write_text("hello\n")
    git_repo.index.add(["README.md"])
    git_repo.index.commit("chore: init")
    return repo_path


@pytest.fixture
def root_with_repos(tmp_path: Path) -> Path:
    """Create a root folder with two git repos and one non-git folder."""
    root = tmp_path / "root"
    root.mkdir()
    for name in ("alpha", "beta"):
        d = root / name
        d.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=d, check=True, capture_output=True)
    (root / "not-a-repo").mkdir()
    (root / "not-a-repo" / "file.txt").write_text("nope")
    return root
