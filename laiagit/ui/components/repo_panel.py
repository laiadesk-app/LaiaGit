from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.ai_backends import AIBackendError
from laiagit.models import FileChange, FileStatus, Repo
from laiagit.services import (
    AIService,
    ConfigService,
    GitError,
    GitService,
    PreflightService,
    WarningLevel,
)
from laiagit.ui._utils import safe_update
from laiagit.ui.components.file_diff_modal import open_diff_modal
from laiagit.ui.theme import STATUS_COLOR, STATUS_ICON, STATUS_LABEL


class _PreflightBlockedError(Exception):
    pass


class RepoPanel:
    """One-line repo panel that expands to show changes + actions when pending."""

    def __init__(
        self,
        page: ft.Page,
        repo: Repo,
        git: GitService,
        ai: AIService,
        config_service: ConfigService,
        on_changed: Callable[[], None],
        on_open_merge: Callable[[Repo], None],
    ):
        self.page = page
        self.repo = repo
        self.git = git
        self.ai = ai
        self.config_service = config_service
        self.on_changed = on_changed
        self.on_open_merge = on_open_merge
        self.repo_config = config_service.load_repo_config(repo.path)
        self.selected_paths: set[str] = set()
        self.expanded: bool = False

        self.commit_message = ft.TextField(
            label="Commit message",
            multiline=True,
            min_lines=1,
            max_lines=3,
            hint_text="Type or click ✨ to generate with AI",
            dense=True,
            expand=True,
        )
        self.merge_source = ft.Dropdown(
            label="Merge from",
            options=self._merge_options(),
            width=160,
            dense=True,
        )
        self.feedback = ft.Text("", size=11, color=ft.Colors.GREY_700, selectable=True)
        self.files_column = ft.Column(spacing=2, tight=True)
        self.select_all = ft.Checkbox(
            label="",
            value=False,
            on_change=lambda e: self._toggle_all(e.control.value),
            tooltip="Select all changes",
        )
        self.changes_label = ft.Text("", size=12, color=ft.Colors.GREY_700)
        self.expand_button = ft.IconButton(
            icon=ft.Icons.EXPAND_MORE,
            tooltip="Expand changes",
            on_click=lambda _: self._toggle_expanded(),
        )
        self.body_container = ft.Container(visible=False)

    # ─────── public API ───────

    def build(self) -> ft.Control:
        self._populate_files()
        self._render_body()
        return ft.Container(
            content=ft.Column(
                [self._header_line(), self.body_container],
                spacing=6,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            margin=ft.margin.only(bottom=8),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
        )

    # ─────── header (single line) ───────

    def _header_line(self) -> ft.Control:
        color = STATUS_COLOR.get(self.repo.status, ft.Colors.GREY_400)
        icon = STATUS_ICON.get(self.repo.status, ft.Icons.CIRCLE)
        label = STATUS_LABEL.get(self.repo.status, "Unknown")

        # Left cluster: name, path, branch, status pill
        name_text = ft.Text(
            self.repo.name,
            size=14,
            weight=ft.FontWeight.BOLD,
            no_wrap=True,
        )
        path_text = ft.Text(
            str(self.repo.path),
            size=10,
            color=ft.Colors.GREY_600,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            tooltip=str(self.repo.path),
            max_lines=1,
        )
        branch_chip = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ALT_ROUTE, size=12, color=ft.Colors.BLUE_700),
                    ft.Text(
                        self.repo.current_branch or "—",
                        size=11,
                        color=ft.Colors.BLUE_900,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        self._ahead_behind_text(),
                        size=11,
                        color=ft.Colors.BLUE_700,
                    ),
                ],
                spacing=3,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
        )
        status_pill = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=color, size=14),
                    ft.Text(label, size=11, color=color, weight=ft.FontWeight.W_500),
                ],
                spacing=4,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            bgcolor=ft.Colors.with_opacity(0.10, color),
            border_radius=8,
        )

        # Right cluster: action buttons (only if there is something to act on)
        right: list[ft.Control] = []

        if self.repo.has_changes:
            right.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.EDIT_NOTE, size=14, color=ft.Colors.AMBER_800),
                            ft.Text(
                                f"{len(self.repo.changes)} change"
                                f"{'s' if len(self.repo.changes) != 1 else ''}",
                                size=11,
                                color=ft.Colors.AMBER_900,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=ft.Colors.AMBER_50,
                    border_radius=8,
                )
            )
            right.append(self.expand_button)
            right.append(
                ft.IconButton(
                    icon=ft.Icons.AUTO_AWESOME,
                    tooltip="Generate commit message with AI",
                    on_click=lambda _: self._generate_message(),
                    icon_size=18,
                )
            )
            right.append(
                ft.FilledButton(
                    "Commit",
                    icon=ft.Icons.CHECK,
                    on_click=lambda _: self._commit(),
                    height=34,
                )
            )

        if self.repo.ahead or self.repo.has_changes:
            right.append(
                ft.FilledTonalButton(
                    "Push",
                    icon=ft.Icons.UPLOAD,
                    on_click=lambda _: self._push(),
                    height=34,
                )
            )

        if self.repo_config.auto_pilot:
            right.append(
                ft.OutlinedButton(
                    "Auto-pilot",
                    icon=ft.Icons.ROCKET_LAUNCH,
                    on_click=lambda _: self._auto_pilot(),
                    height=34,
                )
            )

        if len(self.merge_source.options) > 0:
            right.append(self.merge_source)
            right.append(
                ft.OutlinedButton(
                    "Merge",
                    icon=ft.Icons.MERGE_TYPE,
                    on_click=lambda _: self._merge(),
                    height=34,
                )
            )

        return ft.Row(
            [
                name_text,
                path_text,
                branch_chip,
                status_pill,
                ft.Container(expand=True),
                *right,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # ─────── collapsible body ───────

    def _render_body(self) -> None:
        if not self.repo.has_changes:
            self.body_container.content = None
            self.body_container.visible = False
            return

        self.body_container.visible = self.expanded
        self.body_container.content = ft.Column(
            [
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                ft.Row([self.select_all, self.changes_label], spacing=4),
                ft.Container(
                    content=self.files_column,
                    padding=ft.padding.only(left=24),
                ),
                ft.Container(
                    content=ft.Row([self.commit_message], spacing=4),
                    padding=ft.padding.only(top=4),
                ),
                self.feedback,
            ],
            spacing=4,
            tight=True,
        )

    def _toggle_expanded(self) -> None:
        self.expanded = not self.expanded
        self.expand_button.icon = ft.Icons.EXPAND_LESS if self.expanded else ft.Icons.EXPAND_MORE
        self.expand_button.tooltip = "Collapse" if self.expanded else "Expand changes"
        self._render_body()
        safe_update(self.body_container, self.expand_button)

    # ─────── data ───────

    def _populate_files(self) -> None:
        items: list[ft.Control] = []
        for change in self.repo.changes:
            checkbox = ft.Checkbox(
                value=change.path in self.selected_paths,
                on_change=lambda e, c=change: self._toggle_select(c, e.control.value),
            )
            file_label = ft.Text(
                change.path,
                size=12,
                color=ft.Colors.GREY_900,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                expand=True,
            )
            status_pill = ft.Container(
                content=ft.Text(change.status.value, size=10, color=ft.Colors.GREY_700),
                bgcolor=self._status_bg(change),
                padding=ft.padding.symmetric(horizontal=6, vertical=1),
                border_radius=6,
            )
            view_btn = ft.IconButton(
                icon=ft.Icons.VISIBILITY,
                icon_size=16,
                tooltip="Open diff",
                on_click=lambda _, c=change: self._open_file_diff(c),
            )
            items.append(
                ft.Row(
                    [checkbox, file_label, status_pill, view_btn],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        if not items:
            items.append(ft.Text("No pending changes.", color=ft.Colors.GREY_500, italic=True, size=12))

        self.files_column.controls = items
        self.changes_label.value = self._changes_summary()
        self.select_all.value = bool(self.repo.changes) and len(self.selected_paths) == len(self.repo.changes)

    def _changes_summary(self) -> str:
        n = len(self.repo.changes)
        if n == 0:
            return "No pending changes"
        sel = len(self.selected_paths)
        return f"{n} pending change{'s' if n != 1 else ''} — {sel} selected"

    def _status_bg(self, change: FileChange) -> str:
        return {
            FileStatus.UNTRACKED: ft.Colors.GREEN_50,
            FileStatus.ADDED: ft.Colors.GREEN_100,
            FileStatus.MODIFIED: ft.Colors.AMBER_50,
            FileStatus.DELETED: ft.Colors.RED_50,
            FileStatus.CONFLICTED: ft.Colors.RED_100,
            FileStatus.RENAMED: ft.Colors.BLUE_50,
            FileStatus.STAGED: ft.Colors.PURPLE_50,
        }.get(change.status, ft.Colors.GREY_100)

    def _ahead_behind_text(self) -> str:
        parts: list[str] = []
        if self.repo.ahead:
            parts.append(f"↑{self.repo.ahead}")
        if self.repo.behind:
            parts.append(f"↓{self.repo.behind}")
        return " ".join(parts)

    def _merge_options(self) -> list[ft.dropdown.Option]:
        return [ft.dropdown.Option(b.name) for b in self.repo.branches if b.name != self.repo.current_branch]

    # ─────── interactions ───────

    def _toggle_select(self, change: FileChange, value: bool) -> None:
        if value:
            self.selected_paths.add(change.path)
        else:
            self.selected_paths.discard(change.path)
        self.changes_label.value = self._changes_summary()
        self.select_all.value = bool(self.repo.changes) and len(self.selected_paths) == len(self.repo.changes)
        safe_update(self.changes_label, self.select_all)

    def _toggle_all(self, value: bool) -> None:
        if value:
            self.selected_paths = {c.path for c in self.repo.changes}
        else:
            self.selected_paths = set()
        self._populate_files()
        safe_update(self.files_column, self.changes_label, self.select_all)

    def _open_file_diff(self, change: FileChange) -> None:
        try:
            diff = self.git.diff_for_file(self.repo.path, change.path, staged=change.staged)
        except GitError as exc:
            self._set_feedback(f"Could not load diff: {exc}", error=True)
            return
        if not diff.strip() and change.status == FileStatus.UNTRACKED:
            try:
                content = (self.repo.path / change.path).read_text(encoding="utf-8", errors="replace")
                diff = f"--- /dev/null\n+++ b/{change.path}\n@@\n" + "\n".join(
                    "+" + line for line in content.splitlines()
                )
            except OSError as exc:
                self._set_feedback(f"Could not read file: {exc}", error=True)
                return
        open_diff_modal(self.page, change.path, diff)

    def _generate_message(self) -> None:
        try:
            self._stage_selected(stage_all_if_empty=True)
            diff = self.git.full_diff(self.repo.path, staged_only=True)
            if not diff.strip():
                diff = self.git.full_diff(self.repo.path, staged_only=False)
            if not diff.strip():
                self._set_feedback("Nothing to describe — no changes.", error=True)
                self._ensure_expanded()
                return
            self._set_feedback("Generating commit message…")
            self._ensure_expanded()
            message = self.ai.commit_message(diff, self.repo_config)
        except (GitError, AIBackendError) as exc:
            self._set_feedback(f"AI generation failed: {exc}", error=True)
            self._ensure_expanded()
            return
        self.commit_message.value = message
        safe_update(self.commit_message)
        self._set_feedback("Message generated. Edit if needed before committing.")

    def _commit(self) -> None:
        message = (self.commit_message.value or "").strip()
        if not message:
            self._set_feedback("Type or generate a commit message first.", error=True)
            self._ensure_expanded()
            return
        try:
            self._stage_selected(stage_all_if_empty=True)
            self._run_preflight()
            sha = self.git.commit(self.repo.path, message)
        except GitError as exc:
            self._set_feedback(f"Commit failed: {exc}", error=True)
            return
        except _PreflightBlockedError as exc:
            self._set_feedback(str(exc), error=True)
            return
        self.commit_message.value = ""
        self.selected_paths.clear()
        self._set_feedback(f"Committed {sha[:7]} on {self.repo.current_branch}.")
        safe_update(self.commit_message)
        self.on_changed()

    def _push(self) -> None:
        try:
            summary = self.git.push(self.repo.path)
        except GitError as exc:
            self._set_feedback(f"Push failed: {exc}", error=True)
            self._ensure_expanded()
            return
        self._set_feedback(f"Pushed {self.repo.current_branch}: {summary}")
        self.on_changed()

    def _auto_pilot(self) -> None:
        if not self.repo_config.auto_pilot:
            self._set_feedback("Auto-pilot is disabled for this repo.", error=True)
            return
        try:
            self._stage_selected(stage_all_if_empty=True)
            diff = self.git.full_diff(self.repo.path, staged_only=True)
            if not diff.strip():
                self._set_feedback("Nothing to commit.")
                return
            self._run_preflight()
            message = self.ai.commit_message(diff, self.repo_config)
            self.git.commit(self.repo.path, message)
            summary = self.git.push(self.repo.path)
        except (GitError, AIBackendError, _PreflightBlockedError) as exc:
            self._set_feedback(f"Auto-pilot stopped: {exc}", error=True)
            return
        self._set_feedback(f"Auto-pilot ok. Pushed: {summary}")
        self.on_changed()

    def _merge(self) -> None:
        source = self.merge_source.value
        if not source:
            self._set_feedback("Pick a branch to merge from.", error=True)
            self._ensure_expanded()
            return
        try:
            conflict = self.git.begin_merge(self.repo.path, source)
        except GitError as exc:
            self._set_feedback(f"Merge failed: {exc}", error=True)
            self._ensure_expanded()
            return
        if conflict is None:
            try:
                sha = self.git.commit(
                    self.repo.path,
                    f"Merge branch '{source}' into {self.repo.current_branch}",
                )
            except GitError as exc:
                self._set_feedback(f"Could not finalize merge: {exc}", error=True)
                return
            self._set_feedback(f"Merged {source} → {self.repo.current_branch} ({sha[:7]}).")
            self.on_changed()
            return
        self._set_feedback(f"Merge has {len(conflict.files)} conflict(s). Opening AI conflict resolver…")
        self.on_open_merge(self.repo)

    # ─────── helpers ───────

    def _ensure_expanded(self) -> None:
        if not self.expanded and self.repo.has_changes:
            self.expanded = True
            self.expand_button.icon = ft.Icons.EXPAND_LESS
            self.expand_button.tooltip = "Collapse"
            self._render_body()
            safe_update(self.body_container, self.expand_button)

    def _stage_selected(self, *, stage_all_if_empty: bool = False) -> None:
        targets = list(self.selected_paths)
        if not targets and stage_all_if_empty:
            targets = [c.path for c in self.repo.changes]
        if not targets:
            return
        self.git.stage(self.repo.path, targets)

    def _run_preflight(self) -> None:
        cfg = self.repo_config.preflight
        service = PreflightService(cfg)
        diff = self.git.full_diff(self.repo.path, staged_only=True)
        warnings = service.check_diff(diff)
        warnings += service.check_files(
            self.repo.path,
            [c.path for c in self.repo.staged_changes],
        )
        if not warnings:
            return
        blocking = [w for w in warnings if w.level == WarningLevel.BLOCK]
        if blocking:
            messages = "; ".join(f"{w.file}:{w.line} {w.message}" for w in blocking[:3])
            raise _PreflightBlockedError(f"Pre-flight blocked: {messages}")
        warns = "; ".join(f"{w.file}:{w.line} {w.message}" for w in warnings[:3])
        self._set_feedback(f"Pre-flight warnings (non-blocking): {warns}")

    def _set_feedback(self, message: str, *, error: bool = False) -> None:
        self.feedback.value = message
        self.feedback.color = ft.Colors.RED_400 if error else ft.Colors.GREY_700
        safe_update(self.feedback)
