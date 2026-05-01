from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RepoStatus(str, Enum):
    CLEAN = "clean"
    PENDING = "pending"  # uncommitted changes
    UNPUSHED = "unpushed"  # commits ahead of origin
    BEHIND = "behind"  # commits behind origin
    CONFLICT = "conflict"  # merge in progress with conflicts
    ERROR = "error"  # cannot read state


class FileStatus(str, Enum):
    UNTRACKED = "untracked"
    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    RENAMED = "renamed"
    STAGED = "staged"
    CONFLICTED = "conflicted"


@dataclass
class FileChange:
    path: str
    status: FileStatus
    staged: bool = False
    diff: str = ""


@dataclass
class BranchInfo:
    name: str
    is_current: bool = False
    is_remote: bool = False
    upstream: str | None = None
    ahead: int = 0
    behind: int = 0


@dataclass
class Repo:
    path: Path
    name: str
    status: RepoStatus = RepoStatus.CLEAN
    current_branch: str | None = None
    branches: list[BranchInfo] = field(default_factory=list)
    changes: list[FileChange] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0
    has_remote: bool = False
    error: str | None = None

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def staged_changes(self) -> list[FileChange]:
        return [c for c in self.changes if c.staged]

    @property
    def unstaged_changes(self) -> list[FileChange]:
        return [c for c in self.changes if not c.staged]
