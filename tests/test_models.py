from __future__ import annotations

from pathlib import Path

from laiagit.models import (
    Conflict,
    ConflictFile,
    FileChange,
    FileStatus,
    Repo,
    RepoStatus,
    Resolution,
    ResolutionConfidence,
)


def test_repo_helper_properties() -> None:
    repo = Repo(path=Path("/tmp/x"), name="x", status=RepoStatus.PENDING)
    repo.changes = [
        FileChange(path="a.py", status=FileStatus.MODIFIED, staged=True),
        FileChange(path="b.py", status=FileStatus.MODIFIED, staged=False),
    ]
    assert repo.has_changes is True
    assert [c.path for c in repo.staged_changes] == ["a.py"]
    assert [c.path for c in repo.unstaged_changes] == ["b.py"]


def test_resolution_needs_review() -> None:
    low = Resolution(content="x", confidence=ResolutionConfidence.LOW)
    high = Resolution(content="x", confidence=ResolutionConfidence.HIGH)
    unknown = Resolution(content="x")
    assert low.needs_review is True
    assert unknown.needs_review is True
    assert high.needs_review is False


def test_conflict_all_resolved() -> None:
    conflict = Conflict(
        repo_path="/tmp",
        source_branch="feature",
        target_branch="main",
        files=[
            ConflictFile(path="a", head_content="", incoming_content="", accepted=True),
            ConflictFile(path="b", head_content="", incoming_content="", accepted=False),
        ],
    )
    assert conflict.all_resolved is False
    conflict.files[1].accepted = True
    assert conflict.all_resolved is True


def test_conflict_files_needing_review() -> None:
    conflict = Conflict(repo_path="/", source_branch="f", target_branch="m")
    cf1 = ConflictFile(path="a", head_content="", incoming_content="")
    cf1.resolution = Resolution(content="x", confidence=ResolutionConfidence.LOW)
    cf2 = ConflictFile(path="b", head_content="", incoming_content="")
    cf2.resolution = Resolution(content="y", confidence=ResolutionConfidence.HIGH)
    conflict.files = [cf1, cf2]
    needing = conflict.files_needing_review
    assert len(needing) == 1
    assert needing[0].path == "a"
