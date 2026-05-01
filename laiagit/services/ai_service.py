from __future__ import annotations

import datetime as dt
import logging

from laiagit.ai_backends import (
    AIBackend,
    AIBackendError,
    APIBackend,
    ClaudeCodeBackend,
    OllamaBackend,
)
from laiagit.models import Conflict, ConflictFile, Resolution, ResolutionConfidence
from laiagit.services.config_service import (
    AUDIT_LOG,
    AIBackendsConfig,
    LaiaGitConfig,
    RepoConfig,
)

log = logging.getLogger(__name__)


class AIService:
    """Unified entry point for AI features. Picks the backend per call."""

    def __init__(self, config: LaiaGitConfig):
        self.config = config
        self._cached: dict[str, AIBackend] = {}

    def reload(self, config: LaiaGitConfig) -> None:
        self.config = config
        self._cached.clear()

    def detect_available(self) -> dict[str, bool]:
        results = {}
        for name in ("ollama", "claude_code", "api"):
            backend = self._build(name, self.config.ai_backends)
            results[name] = backend.is_available()
        return results

    def get_backend(self, repo_config: RepoConfig | None = None) -> AIBackend:
        name = (
            repo_config.ai_backend if repo_config and repo_config.ai_backend else None
        ) or self.config.default_ai_backend
        if name not in self._cached:
            self._cached[name] = self._build(name, self.config.ai_backends)
        return self._cached[name]

    def commit_message(self, diff: str, repo_config: RepoConfig | None = None) -> str:
        if not diff.strip():
            return "chore: empty change"
        backend = self.get_backend(repo_config)
        if not backend.is_available():
            raise AIBackendError(f"AI backend `{backend.name}` is not available")
        try:
            message = backend.commit_message(diff)
        except AIBackendError:
            raise
        return self._sanitize_commit_message(message)

    def resolve_conflict(
        self,
        conflict_file: ConflictFile,
        repo_config: RepoConfig | None = None,
    ) -> Resolution:
        backend = self.get_backend(repo_config)
        if not backend.is_available():
            return Resolution(
                content=conflict_file.head_content,
                confidence=ResolutionConfidence.UNKNOWN,
                rationale=f"Backend `{backend.name}` not available; kept HEAD",
            )
        return backend.resolve_conflict(conflict_file)

    def resolve_all(
        self,
        conflict: Conflict,
        repo_config: RepoConfig | None = None,
    ) -> Conflict:
        for cf in conflict.files:
            try:
                cf.resolution = self.resolve_conflict(cf, repo_config)
            except Exception as exc:  # noqa: BLE001
                cf.error = str(exc)
                cf.resolution = Resolution(
                    content=cf.head_content,
                    confidence=ResolutionConfidence.UNKNOWN,
                    rationale=f"Error: {exc}; kept HEAD",
                )
            self._audit(conflict.repo_path, cf)
        return conflict

    def _build(self, name: str, backends: AIBackendsConfig) -> AIBackend:
        if name == "ollama":
            return OllamaBackend(host=backends.ollama.host, model=backends.ollama.model)
        if name == "claude_code":
            return ClaudeCodeBackend(command=backends.claude_code.command)
        if name == "api":
            return APIBackend(provider=backends.api.provider, model=backends.api.model)
        raise AIBackendError(f"Unknown AI backend: {name}")

    def _sanitize_commit_message(self, message: str) -> str:
        cleaned = message.strip().strip("`").strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 2:
                cleaned = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        return cleaned.strip()

    def _audit(self, repo_path: str, conflict_file: ConflictFile) -> None:
        try:
            AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
            timestamp = dt.datetime.now(dt.UTC).isoformat()
            confidence = conflict_file.resolution.confidence.value if conflict_file.resolution else "none"
            line = (
                f"[{timestamp}] repo={repo_path} file={conflict_file.path} "
                f"confidence={confidence} error={conflict_file.error or ''}\n"
            )
            with AUDIT_LOG.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError as exc:
            log.warning("Could not write audit log: %s", exc)


def update_ai_service_export() -> None:
    """Helper for editors; imports must be added by caller."""


# Make AIService importable from laiagit.services without changing __init__ at write time.
