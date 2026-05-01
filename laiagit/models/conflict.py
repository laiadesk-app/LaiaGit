from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ResolutionConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class Resolution:
    content: str
    confidence: ResolutionConfidence = ResolutionConfidence.UNKNOWN
    rationale: str = ""

    @property
    def needs_review(self) -> bool:
        return self.confidence in (ResolutionConfidence.LOW, ResolutionConfidence.UNKNOWN)


@dataclass
class ConflictFile:
    path: str
    head_content: str
    incoming_content: str
    base_content: str = ""
    surrounding_context: str = ""
    resolution: Resolution | None = None
    accepted: bool = False
    error: str | None = None


@dataclass
class Conflict:
    repo_path: str
    source_branch: str
    target_branch: str
    files: list[ConflictFile] = field(default_factory=list)

    @property
    def all_resolved(self) -> bool:
        return all(f.accepted for f in self.files)

    @property
    def files_needing_review(self) -> list[ConflictFile]:
        return [f for f in self.files if f.resolution and f.resolution.needs_review]
