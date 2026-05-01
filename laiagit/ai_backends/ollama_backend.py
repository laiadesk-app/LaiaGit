from __future__ import annotations

import httpx

from laiagit.ai_backends.base import (
    COMMIT_SYSTEM_PROMPT,
    CONFLICT_SYSTEM_PROMPT,
    AIBackend,
    AIBackendError,
)
from laiagit.models import ConflictFile, Resolution, ResolutionConfidence


class OllamaBackend(AIBackend):
    name = "ollama"

    def __init__(self, host: str, model: str, timeout: float = 60.0):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.host}/api/tags")
            if response.status_code != 200:
                return False
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return any(self.model in m or m.startswith(self.model.split(":")[0]) for m in models)
        except Exception:  # noqa: BLE001
            return False

    def commit_message(self, diff: str) -> str:
        prompt = self.build_commit_prompt(diff)
        return self._chat(system=COMMIT_SYSTEM_PROMPT, user=prompt).strip()

    def resolve_conflict(self, conflict_file: ConflictFile) -> Resolution:
        prompt = self.build_conflict_prompt(conflict_file)
        try:
            content = self._chat(system=CONFLICT_SYSTEM_PROMPT, user=prompt)
        except AIBackendError as exc:
            return Resolution(
                content=conflict_file.head_content,
                confidence=ResolutionConfidence.UNKNOWN,
                rationale=f"Backend error, kept HEAD: {exc}",
            )
        confidence = self.confidence_from_text(content)
        return Resolution(content=content, confidence=ResolutionConfidence(confidence))

    def _chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.host}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise AIBackendError(f"Ollama request failed: {exc}") from exc

        message = data.get("message", {})
        content = message.get("content")
        if not content:
            raise AIBackendError("Ollama returned empty response")
        return content
