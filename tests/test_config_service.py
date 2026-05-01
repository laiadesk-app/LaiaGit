from __future__ import annotations

from pathlib import Path

from laiagit.services import ConfigService
from laiagit.services.config_service import LaiaGitConfig, RepoConfig


def test_load_creates_default_when_missing(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    service = ConfigService(config_path=cfg_path)
    config = service.load()
    assert cfg_path.exists()
    assert config.root_folder == "~/dev"
    assert config.default_ai_backend == "ollama"


def test_save_and_reload_roundtrip(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    service = ConfigService(config_path=cfg_path)
    config = LaiaGitConfig(root_folder="/tmp/x", default_ai_backend="claude_code")
    config.ai_backends.ollama.model = "qwen2.5-coder:14b"
    service.save(config)
    reloaded = service.load()
    assert reloaded.root_folder == "/tmp/x"
    assert reloaded.default_ai_backend == "claude_code"
    assert reloaded.ai_backends.ollama.model == "qwen2.5-coder:14b"


def test_repo_config_default_when_missing(tmp_path: Path) -> None:
    service = ConfigService(config_path=tmp_path / "config.yaml")
    repo_config = service.load_repo_config(tmp_path)
    assert repo_config.auto_pilot is False
    assert repo_config.ai_backend is None


def test_repo_config_save_and_load(tmp_path: Path) -> None:
    service = ConfigService(config_path=tmp_path / "config.yaml")
    rc = RepoConfig(ai_backend="api", auto_pilot=True, default_branch="main")
    service.save_repo_config(tmp_path, rc)
    reloaded = service.load_repo_config(tmp_path)
    assert reloaded.ai_backend == "api"
    assert reloaded.auto_pilot is True
    assert reloaded.default_branch == "main"


def test_repo_config_default_branch_optional(tmp_path: Path) -> None:
    service = ConfigService(config_path=tmp_path / "config.yaml")
    service.save_repo_config(tmp_path, RepoConfig(ai_backend="ollama"))
    reloaded = service.load_repo_config(tmp_path)
    assert reloaded.default_branch is None


def test_extra_paths_roundtrip(tmp_path: Path) -> None:
    service = ConfigService(config_path=tmp_path / "config.yaml")
    config = LaiaGitConfig(
        root_folder="/tmp/dev",
        extra_paths=["/Users/me/work/proj-x", "~/other"],
    )
    service.save(config)
    reloaded = service.load()
    assert reloaded.extra_paths == ["/Users/me/work/proj-x", "~/other"]


def test_extra_paths_default_empty(tmp_path: Path) -> None:
    service = ConfigService(config_path=tmp_path / "config.yaml")
    config = service.load()
    assert config.extra_paths == []


def test_repo_order_roundtrip(tmp_path: Path) -> None:
    service = ConfigService(config_path=tmp_path / "config.yaml")
    config = LaiaGitConfig(
        repo_order=["/Users/me/dev/laiagit", "/Users/me/dev/proj-x"],
    )
    service.save(config)
    reloaded = service.load()
    assert reloaded.repo_order == [
        "/Users/me/dev/laiagit",
        "/Users/me/dev/proj-x",
    ]


def test_excluded_repos_roundtrip(tmp_path: Path) -> None:
    service = ConfigService(config_path=tmp_path / "config.yaml")
    config = LaiaGitConfig(
        excluded_repos=["/Users/me/dev/legacy", "/Users/me/dev/sandbox"],
    )
    service.save(config)
    reloaded = service.load()
    assert reloaded.excluded_repos == [
        "/Users/me/dev/legacy",
        "/Users/me/dev/sandbox",
    ]
