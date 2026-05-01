from __future__ import annotations

from abc import ABC, abstractmethod

from laiagit.models import ConflictFile, Resolution


class AIBackendError(Exception):
    pass


COMMIT_SYSTEM_PROMPT = """You write Conventional Commits messages.

Rules:
- First line: <type>(<scope>): <short summary>, <= 72 chars, imperative mood, lowercase summary.
- type is one of: feat, fix, docs, style, refactor, perf, test, chore, build, ci.
- Optional scope in parentheses, derived from the most relevant directory.
- Optional body: a blank line, then 1-3 short sentences explaining WHY (not WHAT).
- Do NOT include any other text, no markdown, no code fences, no quotes.
"""

CONFLICT_SYSTEM_PROMPT = """You resolve git merge conflicts.

Given the HEAD version, the incoming version, and surrounding context, produce a single merged version.

Rules:
- Output ONLY the resolved file content, nothing else. No markdown fences, no commentary.
- Preserve the file's language, syntax, and indentation style.
- When in doubt, prefer the side that better fits the surrounding context.
- Never delete code that is clearly intentional in either side.
- If you cannot reconcile, prefer HEAD and add `// CONFLICT: review needed` near the ambiguous part.
"""


class AIBackend(ABC):
    name: str = "abstract"

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def commit_message(self, diff: str) -> str: ...

    @abstractmethod
    def resolve_conflict(self, conflict_file: ConflictFile) -> Resolution: ...

    def preflight_review(self, diff: str) -> str:
        return ""

    @staticmethod
    def build_conflict_prompt(conflict_file: ConflictFile) -> str:
        return (
            f"File: {conflict_file.path}\n\n"
            f"=== HEAD VERSION ===\n{conflict_file.head_content}\n\n"
            f"=== INCOMING VERSION ===\n{conflict_file.incoming_content}\n\n"
            f"=== BASE (common ancestor) ===\n{conflict_file.base_content}\n\n"
            f"=== SURROUNDING CONTEXT ===\n{conflict_file.surrounding_context}\n\n"
            "Output the resolved file content only."
        )

    @staticmethod
    def build_commit_prompt(diff: str) -> str:
        truncated = diff
        if len(diff) > 16000:
            truncated = diff[:16000] + "\n\n[... diff truncated ...]"
        return (
            "Generate a Conventional Commits message for the following diff. "
            "Output only the message.\n\n"
            f"=== DIFF ===\n{truncated}"
        )

    @staticmethod
    def confidence_from_text(text: str) -> str:
        from laiagit.models import ResolutionConfidence

        lowered = text.lower()
        if "conflict: review needed" in lowered:
            return ResolutionConfidence.LOW
        if len(text.strip()) < 10:
            return ResolutionConfidence.LOW
        return ResolutionConfidence.MEDIUM
