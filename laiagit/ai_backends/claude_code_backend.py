from __future__ import annotations

import shutil
import subprocess

from laiagit.ai_backends.base import (
    COMMIT_SYSTEM_PROMPT,
    CONFLICT_SYSTEM_PROMPT,
    AIBackend,
    AIBackendError,
)
from laiagit.models import ConflictFile, Resolution, ResolutionConfidence


class ClaudeCodeBackend(AIBackend):
    name = "claude_code"

    def __init__(self, command: str = "claude", timeout: float = 120.0):
        self.command = command
        self.timeout = timeout

    def is_available(self) -> bool:
        return shutil.which(self.command) is not None

    def commit_message(self, diff: str) -> str:
        prompt = f"{COMMIT_SYSTEM_PROMPT}\n\n{self.build_commit_prompt(diff)}"
        return self._invoke(prompt).strip()

    def resolve_conflict(self, conflict_file: ConflictFile) -> Resolution:
        prompt = f"{CONFLICT_SYSTEM_PROMPT}\n\n{self.build_conflict_prompt(conflict_file)}"
        try:
            content = self._invoke(prompt)
        except AIBackendError as exc:
            return Resolution(
                content=conflict_file.head_content,
                confidence=ResolutionConfidence.UNKNOWN,
                rationale=f"Backend error, kept HEAD: {exc}",
            )
        return Resolution(
            content=content,
            confidence=ResolutionConfidence(self.confidence_from_text(content)),
        )

    def _invoke(self, prompt: str) -> str:
        if not self.is_available():
            raise AIBackendError(f"`{self.command}` not found on PATH")
        try:
            completed = subprocess.run(
                [self.command, "-p", prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AIBackendError(f"Claude Code CLI timed out after {self.timeout}s") from exc
        except FileNotFoundError as exc:
            raise AIBackendError(f"Claude Code CLI not found: {exc}") from exc

        if completed.returncode != 0:
            raise AIBackendError(
                f"Claude Code CLI exited with code {completed.returncode}: "
                f"{(completed.stderr or '').strip()[:300]}"
            )
        output = (completed.stdout or "").strip()
        if not output:
            raise AIBackendError("Claude Code CLI returned empty output")
        return output
