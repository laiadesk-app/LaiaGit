from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from laiagit.ai_backends import AIBackendError, ClaudeCodeBackend, OllamaBackend
from laiagit.ai_backends.base import AIBackend
from laiagit.models import Conflict, ConflictFile, Resolution, ResolutionConfidence
from laiagit.services import AIService
from laiagit.services.config_service import LaiaGitConfig


class FakeBackend(AIBackend):
    name = "fake"

    def __init__(self, *, available: bool = True, message: str = "feat(x): hello"):
        self.available = available
        self.message = message
        self.commit_calls: list[str] = []
        self.resolve_calls: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def commit_message(self, diff: str) -> str:
        self.commit_calls.append(diff)
        return self.message

    def resolve_conflict(self, cf: ConflictFile) -> Resolution:
        self.resolve_calls.append(cf.path)
        return Resolution(
            content=f"merged {cf.path}",
            confidence=ResolutionConfidence.HIGH,
        )


def test_commit_message_routes_to_default_backend(tmp_path: Path) -> None:
    config = LaiaGitConfig()
    service = AIService(config)
    fake = FakeBackend(message="feat(scope): real message")
    service._cached["ollama"] = fake
    out = service.commit_message("diff text")
    assert out == "feat(scope): real message"
    assert fake.commit_calls == ["diff text"]


def test_commit_message_strips_code_fences() -> None:
    config = LaiaGitConfig()
    service = AIService(config)
    fake = FakeBackend(message="```\nfeat(x): wrapped\n```")
    service._cached["ollama"] = fake
    out = service.commit_message("diff")
    assert out == "feat(x): wrapped"


def test_commit_message_raises_when_backend_unavailable() -> None:
    config = LaiaGitConfig()
    service = AIService(config)
    fake = FakeBackend(available=False)
    service._cached["ollama"] = fake
    with pytest.raises(AIBackendError):
        service.commit_message("diff")


def test_resolve_all_falls_back_when_unavailable() -> None:
    config = LaiaGitConfig()
    service = AIService(config)
    service._cached["ollama"] = FakeBackend(available=False)
    conflict = Conflict(
        repo_path="/tmp/x",
        source_branch="feature",
        target_branch="main",
        files=[ConflictFile(path="a.py", head_content="HEAD", incoming_content="THEIRS")],
    )
    service.resolve_all(conflict)
    assert conflict.files[0].resolution is not None
    assert conflict.files[0].resolution.confidence == ResolutionConfidence.UNKNOWN
    assert conflict.files[0].resolution.content == "HEAD"


def test_resolve_all_uses_backend_when_available() -> None:
    config = LaiaGitConfig()
    service = AIService(config)
    fake = FakeBackend()
    service._cached["ollama"] = fake
    conflict = Conflict(
        repo_path="/tmp/x",
        source_branch="feature",
        target_branch="main",
        files=[ConflictFile(path="a.py", head_content="H", incoming_content="I")],
    )
    service.resolve_all(conflict)
    assert fake.resolve_calls == ["a.py"]
    assert conflict.files[0].resolution.confidence == ResolutionConfidence.HIGH
    assert conflict.files[0].resolution.content == "merged a.py"


def test_repo_config_overrides_default_backend() -> None:
    from laiagit.services.config_service import RepoConfig

    config = LaiaGitConfig(default_ai_backend="ollama")
    service = AIService(config)
    fake_ollama = FakeBackend(message="from ollama")
    fake_api = FakeBackend(message="from api")
    service._cached["ollama"] = fake_ollama
    service._cached["api"] = fake_api
    out = service.commit_message("diff", RepoConfig(ai_backend="api"))
    assert out == "from api"
    assert fake_api.commit_calls == ["diff"]
    assert fake_ollama.commit_calls == []


def test_ollama_is_available_with_mocked_response() -> None:
    backend = OllamaBackend(host="http://x", model="qwen2.5-coder:7b")
    fake_response = MagicMock(status_code=200, json=lambda: {"models": [{"name": "qwen2.5-coder:7b"}]})
    with patch("httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = fake_response
        assert backend.is_available() is True


def test_ollama_unavailable_when_request_fails() -> None:
    backend = OllamaBackend(host="http://x", model="qwen2.5-coder:7b")
    with patch("httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = OSError("boom")
        assert backend.is_available() is False


def test_claude_code_is_available_only_when_on_path() -> None:
    backend = ClaudeCodeBackend(command="definitely-not-a-real-command-xyz")
    assert backend.is_available() is False
