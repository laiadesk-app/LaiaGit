from __future__ import annotations

import os

import httpx

from laiagit.ai_backends.base import (
    COMMIT_SYSTEM_PROMPT,
    CONFLICT_SYSTEM_PROMPT,
    AIBackend,
    AIBackendError,
)
from laiagit.models import ConflictFile, Resolution, ResolutionConfidence


class APIBackend(AIBackend):
    name = "api"

    def __init__(self, provider: str = "anthropic", model: str | None = None, timeout: float = 60.0):
        self.provider = provider
        self.model = model or self._default_model(provider)
        self.timeout = timeout

    def _default_model(self, provider: str) -> str:
        if provider == "anthropic":
            return "claude-sonnet-4-6"
        return "gpt-4o-mini"

    def _api_key(self) -> str | None:
        if self.provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        return os.environ.get("OPENAI_API_KEY")

    def is_available(self) -> bool:
        return bool(self._api_key())

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
        return Resolution(
            content=content,
            confidence=ResolutionConfidence(self.confidence_from_text(content)),
        )

    def _chat(self, system: str, user: str) -> str:
        api_key = self._api_key()
        if not api_key:
            raise AIBackendError(
                f"No API key found in env for provider={self.provider}. "
                f"Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )
        if self.provider == "anthropic":
            return self._anthropic_chat(api_key, system, user)
        return self._openai_chat(api_key, system, user)

    def _anthropic_chat(self, api_key: str, system: str, user: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise AIBackendError(f"Anthropic request failed: {exc}") from exc

        blocks = data.get("content", [])
        if not blocks:
            raise AIBackendError("Anthropic returned no content")
        text_parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        text = "".join(text_parts).strip()
        if not text:
            raise AIBackendError("Anthropic returned empty text")
        return text

    def _openai_chat(self, api_key: str, system: str, user: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise AIBackendError(f"OpenAI request failed: {exc}") from exc

        choices = data.get("choices", [])
        if not choices:
            raise AIBackendError("OpenAI returned no choices")
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise AIBackendError("OpenAI returned empty content")
        return content
