from __future__ import annotations

from pathlib import Path

from laiagit.services import PreflightService, WarningLevel
from laiagit.services.config_service import PreflightConfig

SAMPLE_DIFF_WITH_SECRET = """\
diff --git a/.env b/.env
index 0000000..1111111 100644
--- a/.env
+++ b/.env
@@ -0,0 +1,2 @@
+ANTHROPIC_API_KEY=sk-ant-abcdefghijklmnopqrstuvwxyz0123456
+OTHER=value
"""

SAMPLE_DIFF_WITH_TODO = """\
diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -0,0 +1,2 @@
+# TODO: refactor this later
+def f(): pass
"""

SAMPLE_DIFF_CLEAN = """\
diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -0,0 +1,1 @@
+def f(): return 42
"""


def test_secret_detection_blocks() -> None:
    service = PreflightService(PreflightConfig(block_secrets=True))
    warnings = service.check_diff(SAMPLE_DIFF_WITH_SECRET)
    assert warnings, "Expected at least one warning"
    assert any(w.level == WarningLevel.BLOCK for w in warnings)
    assert service.has_blocking(warnings)


def test_todo_detection_when_enabled() -> None:
    service = PreflightService(PreflightConfig(block_todos=True))
    warnings = service.check_diff(SAMPLE_DIFF_WITH_TODO)
    assert any("TODO" in w.message for w in warnings)
    assert all(w.level == WarningLevel.WARN for w in warnings)


def test_todo_detection_off_by_default() -> None:
    service = PreflightService(PreflightConfig())
    warnings = service.check_diff(SAMPLE_DIFF_WITH_TODO)
    assert not any("TODO" in w.message for w in warnings)


def test_clean_diff_returns_no_warnings() -> None:
    service = PreflightService(PreflightConfig(block_secrets=True, block_todos=True))
    warnings = service.check_diff(SAMPLE_DIFF_CLEAN)
    assert warnings == []


def test_oversized_file_triggers_block(tmp_path: Path) -> None:
    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    service = PreflightService(PreflightConfig(max_file_size_mb=2))
    warnings = service.check_files(tmp_path, ["big.bin"])
    assert warnings and warnings[0].level == WarningLevel.BLOCK
    assert "exceeds" in warnings[0].message
