from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.ai_backends import AIBackendError
from laiagit.models import FileChange, Repo
from laiagit.services import (
    AIService,
    ConfigService,
    GitError,
    GitService,
    PreflightService,
    WarningLevel,
)
from laiagit.ui._utils import safe_update
from laiagit.ui.components.file_diff import diff_view


class RepoDetailView:
    def __init__(
        self,
        page: ft.Page,
        repo: Repo,
        git: GitService,
        ai: AIService,
        config_service: ConfigService,
        on_back: Callable[[], None],
        on_merge: Callable[[Repo], None],
    ):
        self.page = page
        self.repo = repo
        self.git = git
        self.ai = ai
        self.config_service = config_service
        self.on_back = on_back
        self.on_merge = on_merge
        self.repo_config = config_service.load_repo_config(repo.path)

        self.commit_message = ft.TextField(
            label="Commit message",
            multiline=True,
            min_lines=2,
            max_lines=6,
            hint_text="Type or click 'Generate with AI'",
        )
        self.diff_panel = ft.Container(
            content=ft.Text("Select a file to see its diff.", color=ft.Colors.GREY_600),
            expand=True,
        )
        self.files_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)
        self.feedback = ft.Text("", color=ft.Colors.GREY_700, size=12)
        self.selected_paths: set[str] = set()

    def build(self) -> ft.Control:
        self._refresh_files()
        return ft.Column(
            [
                self._header(),
                ft.Divider(height=1),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Changes", size=14, weight=ft.FontWeight.BOLD),
                                    self.files_list,
                                    ft.Divider(),
                                    ft.Text("Branches", size=14, weight=ft.FontWeight.BOLD),
                                    self._branches_view(),
                                ],
                                spacing=8,
                                expand=True,
                            ),
                            padding=12,
                            width=320,
                            border=ft.border.only(right=ft.border.BorderSide(1, ft.Colors.GREY_300)),
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    self.diff_panel,
                                    ft.Divider(),
                                    self.commit_message,
                                    self.feedback,
                                    self._actions_row(),
                                ],
                                spacing=10,
                                expand=True,
                            ),
                            padding=12,
                            expand=True,
                        ),
                    ],
                    expand=True,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _header(self) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Back to dashboard",
                        on_click=lambda _: self.on_back(),
                    ),
                    ft.Text(self.repo.name, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"  {self.repo.path}", size=11, color=ft.Colors.GREY_600),
                    ft.Container(expand=True),
                    ft.FilledButton(
                        "Merge",
                        icon=ft.Icons.MERGE_TYPE,
                        on_click=lambda _: self.on_merge(self.repo),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.Colors.GREY_50,
        )

    def _refresh_files(self) -> None:
        self.git.hydrate(self.repo)
        self.repo_config = self.config_service.load_repo_config(self.repo.path)
        items: list[ft.Control] = []
        for change in self.repo.changes:
            checkbox = ft.Checkbox(
                value=change.path in self.selected_paths or change.staged,
                on_change=lambda e, c=change: self._toggle_select(c, e.control.value),
            )
            label = ft.Text(
                change.path,
                size=12,
                color=ft.Colors.RED_500 if change.staged else ft.Colors.GREY_900,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
            status = ft.Text(change.status.value, size=10, color=ft.Colors.GREY_600)
            row = ft.Container(
                content=ft.Row(
                    [checkbox, label, ft.Container(expand=True), status],
                    spacing=6,
                ),
                padding=ft.padding.symmetric(horizontal=4, vertical=2),
                ink=True,
                on_click=lambda _, c=change: self._show_diff(c),
                border_radius=4,
            )
            items.append(row)
        if not items:
            items.append(ft.Text("No changes.", color=ft.Colors.GREY_600, italic=True))
        self.files_list.controls = items
        safe_update(self.files_list)

    def _branches_view(self) -> ft.Control:
        rows: list[ft.Control] = []
        for branch in self.repo.branches:
            indicator = "•" if branch.is_current else "  "
            label = ft.Text(
                f"{indicator} {branch.name}",
                weight=ft.FontWeight.W_500 if branch.is_current else ft.FontWeight.NORMAL,
                size=12,
            )
            sub = ""
            if branch.upstream:
                sub = f" ↑{branch.ahead} ↓{branch.behind}"
            rows.append(
                ft.Row(
                    [label, ft.Text(sub, size=10, color=ft.Colors.GREY_600)],
                    spacing=4,
                )
            )
        if not rows:
            rows.append(ft.Text("No branches.", color=ft.Colors.GREY_600, italic=True))
        return ft.Column(rows, spacing=2)

    def _actions_row(self) -> ft.Control:
        return ft.Row(
            [
                ft.OutlinedButton(
                    "Generate with AI",
                    icon=ft.Icons.AUTO_AWESOME,
                    on_click=lambda _: self._generate_message(),
                ),
                ft.FilledButton(
                    "Commit",
                    icon=ft.Icons.CHECK,
                    on_click=lambda _: self._commit(),
                ),
                ft.FilledTonalButton(
                    "Push",
                    icon=ft.Icons.UPLOAD,
                    on_click=lambda _: self._push(),
                ),
                ft.OutlinedButton(
                    "Auto-pilot",
                    icon=ft.Icons.ROCKET_LAUNCH,
                    on_click=lambda _: self._auto_pilot(),
                    disabled=not self.repo_config.auto_pilot,
                    tooltip=(
                        "Enabled in settings"
                        if self.repo_config.auto_pilot
                        else "Enable in repo settings to use auto-pilot"
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
            spacing=8,
        )

    def _toggle_select(self, change: FileChange, value: bool) -> None:
        if value:
            self.selected_paths.add(change.path)
        else:
            self.selected_paths.discard(change.path)

    def _show_diff(self, change: FileChange) -> None:
        try:
            diff = self.git.diff_for_file(self.repo.path, change.path, staged=change.staged)
        except GitError as exc:
            self._set_feedback(f"Could not load diff: {exc}", error=True)
            return
        self.diff_panel.content = diff_view(diff)
        safe_update(self.diff_panel)

    def _generate_message(self) -> None:
        self._set_feedback("Generating commit message…")
        try:
            self._stage_selected()
            diff = self.git.full_diff(self.repo.path, staged_only=True)
            if not diff.strip():
                diff = self.git.full_diff(self.repo.path, staged_only=False)
            message = self.ai.commit_message(diff, self.repo_config)
        except (GitError, AIBackendError) as exc:
            self._set_feedback(f"AI generation failed: {exc}", error=True)
            return
        self.commit_message.value = message
        safe_update(self.commit_message)
        self._set_feedback("Message generated. Edit if needed before committing.")

    def _commit(self) -> None:
        message = (self.commit_message.value or "").strip()
        if not message:
            self._set_feedback("Commit message cannot be empty.", error=True)
            return
        try:
            self._stage_selected()
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
        self._set_feedback(f"Committed {sha[:7]}.")
        self._refresh_files()
        safe_update(self.commit_message)

    def _push(self) -> None:
        try:
            summary = self.git.push(self.repo.path)
        except GitError as exc:
            self._set_feedback(f"Push failed: {exc}", error=True)
            return
        self._set_feedback(f"Pushed: {summary}")
        self._refresh_files()

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
        self._refresh_files()

    def _stage_selected(self, *, stage_all_if_empty: bool = False) -> None:
        targets = list(self.selected_paths)
        if not targets and stage_all_if_empty:
            targets = [c.path for c in self.repo.changes if not c.staged]
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


class _PreflightBlockedError(Exception):
    pass
