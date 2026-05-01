from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".laiagit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
AUDIT_LOG = CONFIG_DIR / "audit.log"


@dataclass
class OllamaConfig:
    host: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"


@dataclass
class ClaudeCodeConfig:
    command: str = "claude"


@dataclass
class APIBackendConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"


@dataclass
class AIBackendsConfig:
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    claude_code: ClaudeCodeConfig = field(default_factory=ClaudeCodeConfig)
    api: APIBackendConfig = field(default_factory=APIBackendConfig)


@dataclass
class PreflightConfig:
    block_secrets: bool = True
    block_todos: bool = False
    block_console_logs: bool = False
    max_file_size_mb: int = 5


@dataclass
class RepoConfig:
    ai_backend: str | None = None
    auto_pilot: bool = False
    default_branch: str | None = None
    preflight: PreflightConfig = field(default_factory=PreflightConfig)


@dataclass
class LaiaGitConfig:
    root_folder: str = "~/dev"
    extra_paths: list[str] = field(default_factory=list)
    excluded_repos: list[str] = field(default_factory=list)
    default_ai_backend: str = "ollama"
    ai_backends: AIBackendsConfig = field(default_factory=AIBackendsConfig)
    shortcuts_enabled: bool = True
    auto_pilot_repos: list[str] = field(default_factory=list)
    preflight: PreflightConfig = field(default_factory=PreflightConfig)

    @property
    def root_folder_path(self) -> Path:
        return Path(self.root_folder).expanduser().resolve()

    @property
    def extra_path_paths(self) -> list[Path]:
        return [Path(p).expanduser().resolve() for p in self.extra_paths if p.strip()]

    @property
    def excluded_repo_paths(self) -> set[Path]:
        return {Path(p).expanduser().resolve() for p in self.excluded_repos if p.strip()}


class ConfigService:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path

    def load(self) -> LaiaGitConfig:
        if not self.config_path.exists():
            cfg = LaiaGitConfig()
            self.save(cfg)
            return cfg

        with self.config_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        return self._from_dict(raw)

    def save(self, config: LaiaGitConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = self._to_dict(config)
        with self.config_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)

    def load_repo_config(self, repo_path: Path) -> RepoConfig:
        repo_config_file = repo_path / ".laiagit" / "repo.yaml"
        if not repo_config_file.exists():
            return RepoConfig()
        with repo_config_file.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        preflight_raw = raw.get("preflight", {})
        return RepoConfig(
            ai_backend=raw.get("ai_backend"),
            auto_pilot=raw.get("auto_pilot", False),
            default_branch=raw.get("default_branch"),
            preflight=PreflightConfig(**preflight_raw) if preflight_raw else PreflightConfig(),
        )

    def save_repo_config(self, repo_path: Path, repo_config: RepoConfig) -> None:
        repo_config_dir = repo_path / ".laiagit"
        repo_config_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "ai_backend": repo_config.ai_backend,
            "auto_pilot": repo_config.auto_pilot,
            "default_branch": repo_config.default_branch,
            "preflight": {
                "block_secrets": repo_config.preflight.block_secrets,
                "block_todos": repo_config.preflight.block_todos,
                "block_console_logs": repo_config.preflight.block_console_logs,
                "max_file_size_mb": repo_config.preflight.max_file_size_mb,
            },
        }
        with (repo_config_dir / "repo.yaml").open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)

    def _from_dict(self, raw: dict[str, Any]) -> LaiaGitConfig:
        backends_raw = raw.get("ai_backends", {})
        backends = AIBackendsConfig(
            ollama=OllamaConfig(**backends_raw.get("ollama", {})),
            claude_code=ClaudeCodeConfig(**backends_raw.get("claude_code", {})),
            api=APIBackendConfig(**backends_raw.get("api", {})),
        )
        preflight_raw = raw.get("preflight", {})
        return LaiaGitConfig(
            root_folder=raw.get("root_folder", "~/dev"),
            extra_paths=list(raw.get("extra_paths", [])),
            excluded_repos=list(raw.get("excluded_repos", [])),
            default_ai_backend=raw.get("default_ai_backend", "ollama"),
            ai_backends=backends,
            shortcuts_enabled=raw.get("shortcuts_enabled", True),
            auto_pilot_repos=raw.get("auto_pilot_repos", []),
            preflight=PreflightConfig(**preflight_raw) if preflight_raw else PreflightConfig(),
        )

    def _to_dict(self, config: LaiaGitConfig) -> dict[str, Any]:
        return {
            "root_folder": config.root_folder,
            "extra_paths": config.extra_paths,
            "excluded_repos": config.excluded_repos,
            "default_ai_backend": config.default_ai_backend,
            "ai_backends": {
                "ollama": {
                    "host": config.ai_backends.ollama.host,
                    "model": config.ai_backends.ollama.model,
                },
                "claude_code": {
                    "command": config.ai_backends.claude_code.command,
                },
                "api": {
                    "provider": config.ai_backends.api.provider,
                    "model": config.ai_backends.api.model,
                },
            },
            "shortcuts_enabled": config.shortcuts_enabled,
            "auto_pilot_repos": config.auto_pilot_repos,
            "preflight": {
                "block_secrets": config.preflight.block_secrets,
                "block_todos": config.preflight.block_todos,
                "block_console_logs": config.preflight.block_console_logs,
                "max_file_size_mb": config.preflight.max_file_size_mb,
            },
        }
