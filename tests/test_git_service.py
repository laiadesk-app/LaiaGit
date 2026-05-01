from __future__ import annotations

from pathlib import Path

import pytest

from laiagit.models import FileStatus, Repo, RepoStatus
from laiagit.services import GitError, GitService


def test_hydrate_clean_repo(tmp_git_repo: Path) -> None:
    git = GitService()
    repo = git.hydrate(Repo(path=tmp_git_repo, name=tmp_git_repo.name))
    assert repo.status == RepoStatus.CLEAN
    assert repo.current_branch == "main"
    assert any(b.name == "main" and b.is_current for b in repo.branches)
    assert repo.has_changes is False


def test_hydrate_pending_repo(tmp_git_repo: Path) -> None:
    (tmp_git_repo / "new.txt").write_text("hi")
    git = GitService()
    repo = git.hydrate(Repo(path=tmp_git_repo, name=tmp_git_repo.name))
    assert repo.status == RepoStatus.PENDING
    paths = [c.path for c in repo.changes]
    assert "new.txt" in paths
    untracked = [c for c in repo.changes if c.path == "new.txt"][0]
    assert untracked.status == FileStatus.UNTRACKED


def test_stage_and_commit(tmp_git_repo: Path) -> None:
    (tmp_git_repo / "added.py").write_text("print(1)\n")
    git = GitService()
    git.stage(tmp_git_repo, ["added.py"])
    sha = git.commit(tmp_git_repo, "feat: add added.py")
    assert isinstance(sha, str) and len(sha) >= 7
    repo = git.hydrate(Repo(path=tmp_git_repo, name=tmp_git_repo.name))
    assert repo.status == RepoStatus.CLEAN


def test_commit_empty_message_raises(tmp_git_repo: Path) -> None:
    (tmp_git_repo / "x.txt").write_text("x")
    git = GitService()
    git.stage(tmp_git_repo, ["x.txt"])
    with pytest.raises(GitError):
        git.commit(tmp_git_repo, "   ")


def test_full_diff_shows_modified_lines(tmp_git_repo: Path) -> None:
    (tmp_git_repo / "README.md").write_text("hello\nupdated line\n")
    git = GitService()
    diff = git.full_diff(tmp_git_repo, staged_only=False)
    assert "README.md" in diff
    assert "+updated line" in diff


def test_unstage_files(tmp_git_repo: Path) -> None:
    (tmp_git_repo / "u.txt").write_text("u")
    git = GitService()
    git.stage(tmp_git_repo, ["u.txt"])
    git.unstage(tmp_git_repo, ["u.txt"])
    repo = git.hydrate(Repo(path=tmp_git_repo, name=tmp_git_repo.name))
    untracked = [c for c in repo.changes if c.path == "u.txt"]
    assert untracked and untracked[0].status == FileStatus.UNTRACKED


def test_invalid_repo_raises(tmp_path: Path) -> None:
    git = GitService()
    with pytest.raises(GitError):
        git.open(tmp_path)


def test_merge_conflict_detection(tmp_git_repo: Path) -> None:
    """Create a real conflict and verify begin_merge returns a Conflict object."""
    git = GitService()

    from git import Repo as GitRepo

    git_repo = GitRepo(str(tmp_git_repo))

    target_file = tmp_git_repo / "shared.txt"
    target_file.write_text("base\n")
    git_repo.index.add(["shared.txt"])
    git_repo.index.commit("chore: add shared")

    feature = git_repo.create_head("feature")
    feature.checkout()
    target_file.write_text("feature change\n")
    git_repo.index.add(["shared.txt"])
    git_repo.index.commit("feat: change shared on feature")

    git_repo.heads.main.checkout()
    target_file.write_text("main change\n")
    git_repo.index.add(["shared.txt"])
    git_repo.index.commit("chore: change shared on main")

    conflict = git.begin_merge(tmp_git_repo, "feature")
    assert conflict is not None
    paths = [cf.path for cf in conflict.files]
    assert "shared.txt" in paths
    git.abort_merge(tmp_git_repo)
