from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from laiagit.services.config_service import PreflightConfig


class WarningLevel(str, Enum):
    BLOCK = "block"
    WARN = "warn"


@dataclass
class PreflightWarning:
    file: str
    line: int
    message: str
    snippet: str
    level: WarningLevel


SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    (
        "AWS secret access key",
        re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}"),
    ),
    (
        "Generic API key assignment",
        re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{16,}['\"]"),
    ),
    ("Anthropic API key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("GitHub PAT", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Private key block", re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
]

TODO_PATTERN = re.compile(r"(?i)\b(TODO|FIXME|XXX|HACK)\b[: ]")
CONSOLE_LOG_PATTERN = re.compile(r"\bconsole\.(log|debug|info|warn|error)\s*\(")


class PreflightService:
    def __init__(self, config: PreflightConfig | None = None):
        self.config = config or PreflightConfig()

    def check_diff(self, diff: str) -> list[PreflightWarning]:
        warnings: list[PreflightWarning] = []
        current_file = ""
        line_no = 0

        for raw_line in diff.splitlines():
            if raw_line.startswith("+++ b/"):
                current_file = raw_line[6:]
                line_no = 0
                continue
            if raw_line.startswith("@@"):
                m = re.search(r"\+(\d+)", raw_line)
                if m:
                    line_no = int(m.group(1)) - 1
                continue
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                line_no += 1
                added = raw_line[1:]

                if self.config.block_secrets:
                    warnings.extend(self._scan_secrets(current_file, line_no, added))
                if self.config.block_todos and TODO_PATTERN.search(added):
                    warnings.append(
                        PreflightWarning(
                            file=current_file,
                            line=line_no,
                            message="TODO/FIXME marker added",
                            snippet=added.strip(),
                            level=WarningLevel.WARN,
                        )
                    )
                if self.config.block_console_logs and CONSOLE_LOG_PATTERN.search(added):
                    warnings.append(
                        PreflightWarning(
                            file=current_file,
                            line=line_no,
                            message="console.* call added",
                            snippet=added.strip(),
                            level=WarningLevel.WARN,
                        )
                    )
            elif not raw_line.startswith("-"):
                line_no += 1

        return warnings

    def check_files(self, repo_path: Path, files: list[str]) -> list[PreflightWarning]:
        warnings: list[PreflightWarning] = []
        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        for rel_path in files:
            target = repo_path / rel_path
            if not target.exists() or not target.is_file():
                continue
            try:
                size = target.stat().st_size
            except OSError:
                continue
            if size > max_bytes:
                size_mb = size // (1024 * 1024)
                warnings.append(
                    PreflightWarning(
                        file=rel_path,
                        line=0,
                        message=f"File exceeds {self.config.max_file_size_mb} MB ({size_mb} MB)",
                        snippet="",
                        level=WarningLevel.BLOCK,
                    )
                )
        return warnings

    def has_blocking(self, warnings: list[PreflightWarning]) -> bool:
        return any(w.level == WarningLevel.BLOCK for w in warnings)

    def _scan_secrets(self, file: str, line: int, content: str) -> list[PreflightWarning]:
        results: list[PreflightWarning] = []
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                results.append(
                    PreflightWarning(
                        file=file,
                        line=line,
                        message=f"Possible secret detected: {label}",
                        snippet=content.strip()[:120],
                        level=WarningLevel.BLOCK,
                    )
                )
        return results
