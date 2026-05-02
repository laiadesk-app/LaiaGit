from __future__ import annotations

import threading
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
        on_exclude: Callable[[Repo], None] | None = None,
        on_reorder: Callable[[Repo, str], None] | None = None,
        on_refresh_one: Callable[[Repo], None] | None = None,
    ):
        self.page = page
        self.repo = repo
        self.git = git
        self.ai = ai
        self.config_service = config_service
        self.on_changed = on_changed
        self.on_open_merge = on_open_merge
        self.on_exclude = on_exclude
        self.on_reorder = on_reorder
        self.on_refresh_one = on_refresh_one
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
        self.merge_target = ft.Dropdown(
            hint_text="target branch",
            options=self._merge_options(),
            width=140,
            height=30,
            dense=True,
            text_size=11,
            text_style=ft.TextStyle(size=11),
            hint_style=ft.TextStyle(size=11, color=ft.Colors.GREY_500),
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_select=lambda _: self._refresh_merge_button(),
            tooltip=(
                f"Target branch (where the merge lands). "
                f"Your current branch `{self.repo.current_branch}` is the source."
            ),
        )
        self.merge_button: ft.OutlinedButton | None = None
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
        self.progress = ft.ProgressRing(
            width=18,
            height=18,
            stroke_width=2,
            visible=False,
            tooltip="Working…",
        )
        self.is_busy = False

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
        branch_chip = self._branch_popup()
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
        right: list[ft.Control] = [self.progress]

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
                    icon_size=16,
                )
            )
            right.append(self._compact_button("Commit", ft.Icons.CHECK, self._commit, kind="filled"))

        if self.repo.ahead or self.repo.has_changes:
            right.append(self._compact_button("Push", ft.Icons.UPLOAD, self._push, kind="tonal"))

        if self.repo_config.auto_pilot:
            right.append(
                self._compact_button("Auto-pilot", ft.Icons.ROCKET_LAUNCH, self._auto_pilot, kind="outlined")
            )

        if len(self.merge_target.options) > 0:
            right.append(self.merge_target)
            self.merge_button = self._compact_button(
                self._merge_button_text(),
                ft.Icons.MERGE_TYPE,
                self._merge,
                kind="outlined",
                tooltip=(
                    f"Merges your current branch `{self.repo.current_branch or 'current'}` "
                    f"into the chosen target branch."
                ),
            )
            right.append(self.merge_button)

        if self.on_reorder is not None:
            right.append(
                ft.PopupMenuButton(
                    icon=ft.Icons.DRAG_HANDLE,
                    icon_size=16,
                    tooltip="Reorder this repo",
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.VERTICAL_ALIGN_TOP, size=14),
                                    ft.Text("Move to top", size=12),
                                ],
                                spacing=6,
                            ),
                            on_click=lambda _: self.on_reorder(self.repo, "top"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.ARROW_UPWARD, size=14),
                                    ft.Text("Move up", size=12),
                                ],
                                spacing=6,
                            ),
                            on_click=lambda _: self.on_reorder(self.repo, "up"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.ARROW_DOWNWARD, size=14),
                                    ft.Text("Move down", size=12),
                                ],
                                spacing=6,
                            ),
                            on_click=lambda _: self.on_reorder(self.repo, "down"),
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.VERTICAL_ALIGN_BOTTOM, size=14),
                                    ft.Text("Move to bottom", size=12),
                                ],
                                spacing=6,
                            ),
                            on_click=lambda _: self.on_reorder(self.repo, "bottom"),
                        ),
                    ],
                )
            )

        if self.on_refresh_one is not None:
            right.append(
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_size=16,
                    tooltip="Refresh just this repo (no full rescan)",
                    on_click=lambda _: self.on_refresh_one(self.repo),
                )
            )

        if self.on_exclude is not None:
            right.append(
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY_OFF_OUTLINED,
                    icon_size=16,
                    tooltip=(
                        "Hide this repo from the dashboard. "
                        "The files on disk are NOT deleted — only hidden from LaiaGit. "
                        "Restore from Settings → Excluded repos."
                    ),
                    on_click=lambda _: self._exclude_clicked(),
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

    # ─────── branch popup ───────

    def _branch_popup(self) -> ft.Control:
        default = self.repo_config.default_branch
        current = self.repo.current_branch or "—"
        is_default = bool(default) and current == default

        items: list[ft.PopupMenuItem] = []
        for branch in self.repo.branches:
            star = " ★" if branch.name == default else ""
            dot = "● " if branch.is_current else "    "
            items.append(
                ft.PopupMenuItem(
                    content=ft.Text(f"{dot}{branch.name}{star}", size=12),
                    on_click=lambda _, b=branch.name: self._switch_branch(b),
                )
            )

        if not is_default and self.repo.current_branch:
            items.append(
                ft.PopupMenuItem(
                    content=ft.Text(
                        f"★ Set '{current}' as default",
                        size=12,
                        color=ft.Colors.AMBER_800,
                    ),
                    on_click=lambda _: self._set_default_branch(current),
                )
            )
        if default:
            items.append(
                ft.PopupMenuItem(
                    content=ft.Text(
                        f"Clear default ({default})",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                    on_click=lambda _: self._clear_default_branch(),
                )
            )

        chip = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ALT_ROUTE, size=12, color=ft.Colors.BLUE_700),
                    ft.Text(
                        current,
                        size=11,
                        color=ft.Colors.BLUE_900,
                        weight=ft.FontWeight.W_500,
                    ),
                    *([ft.Icon(ft.Icons.STAR, size=11, color=ft.Colors.AMBER_700)] if is_default else []),
                    ft.Text(
                        self._ahead_behind_text(),
                        size=11,
                        color=ft.Colors.BLUE_700,
                    ),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=14, color=ft.Colors.BLUE_700),
                ],
                spacing=3,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
        )

        return ft.PopupMenuButton(
            content=chip,
            items=items,
            tooltip="Switch branch / manage default",
        )

    def _switch_branch(self, branch: str) -> None:
        if branch == self.repo.current_branch:
            return

        def work() -> None:
            try:
                result = self.git.checkout_branch(self.repo.path, branch)
            except GitError as exc:
                self._set_feedback(f"Switch failed: {exc}", error=True)
                return
            if result == "switched":
                self._set_feedback(f"Switched to `{branch}`.")
            elif result == "switched-with-stash":
                self._set_feedback(f"Switched to `{branch}` and restored your changes.")
            elif result == "switched-stash-conflict":
                self._set_feedback(
                    f"Switched to `{branch}`, but stash pop has conflicts. "
                    "Resolve manually with `git stash list` / `git stash pop`.",
                    error=True,
                )
            self.on_changed()

        self._run_async(f"Switching to `{branch}`…", work)

    def _set_default_branch(self, branch: str) -> None:
        self.repo_config.default_branch = branch
        try:
            self.config_service.save_repo_config(self.repo.path, self.repo_config)
        except OSError as exc:
            self._set_feedback(f"Could not save default: {exc}", error=True)
            return
        self._set_feedback(f"`{branch}` is now the default branch for this repo.")
        self.on_changed()

    def _clear_default_branch(self) -> None:
        self.repo_config.default_branch = None
        try:
            self.config_service.save_repo_config(self.repo.path, self.repo_config)
        except OSError as exc:
            self._set_feedback(f"Could not save: {exc}", error=True)
            return
        self._set_feedback("Default branch cleared.")
        self.on_changed()

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

    def _merge_button_text(self) -> str:
        # Source = current branch (where you stand). Target = picked in the
        # dropdown. Reads as "Merge develop into main" when on develop and
        # main is chosen as target.
        source = self.repo.current_branch or "current"
        target = self.merge_target.value
        if target:
            return f"Merge {source} into {target}"
        return f"Merge {source} into…"

    def _refresh_merge_button(self) -> None:
        if self.merge_button is None:
            return
        self.merge_button.content = self._merge_button_text()
        safe_update(self.merge_button)

    def _compact_button(
        self,
        label: str,
        icon: str,
        on_click: Callable[[], None],
        *,
        kind: str = "outlined",
        tooltip: str | None = None,
    ) -> ft.Control:
        style = ft.ButtonStyle(
            text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500),
            padding=ft.padding.symmetric(horizontal=10, vertical=2),
            shape=ft.RoundedRectangleBorder(radius=6),
        )
        # Flet 0.84 dropped the `text` kwarg on buttons in favour of `content`.
        common: dict = {
            "content": label,
            "icon": icon,
            "on_click": lambda _: on_click(),
            "height": 30,
            "style": style,
        }
        if tooltip is not None:
            common["tooltip"] = tooltip
        if kind == "filled":
            return ft.FilledButton(**common)
        if kind == "tonal":
            return ft.FilledTonalButton(**common)
        return ft.OutlinedButton(**common)

    def _exclude_clicked(self) -> None:
        if self.on_exclude is None:
            return
        self._set_feedback(f"Excluding `{self.repo.name}`…")
        self.on_exclude(self.repo)

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

    def _run_async(self, label: str, fn: Callable[[], None]) -> None:
        if self.is_busy:
            self._set_feedback("Busy with another task — please wait.", error=True)
            return
        self.is_busy = True
        self.progress.visible = True
        self._set_feedback(label)
        self._ensure_expanded()
        safe_update(self.progress)

        def runner() -> None:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — final safety net for thread
                self._set_feedback(f"Unexpected error: {exc}", error=True)
            finally:
                self.is_busy = False
                self.progress.visible = False
                safe_update(self.progress)

        threading.Thread(target=runner, daemon=True).start()

    def _generate_message(self) -> None:
        def work() -> None:
            try:
                self._stage_selected(stage_all_if_empty=True)
                diff = self.git.full_diff(self.repo.path, staged_only=True)
                if not diff.strip():
                    diff = self.git.full_diff(self.repo.path, staged_only=False)
                if not diff.strip():
                    self._set_feedback("Nothing to describe — no changes.", error=True)
                    return
                message = self.ai.commit_message(diff, self.repo_config)
            except (GitError, AIBackendError) as exc:
                self._set_feedback(f"AI generation failed: {exc}", error=True)
                return
            self.commit_message.value = message
            safe_update(self.commit_message)
            self._set_feedback("Message generated. Edit if needed before committing.")

        self._run_async("✨ Generating commit message…", work)

    def _commit(self) -> None:
        message = (self.commit_message.value or "").strip()

        if not message:
            # Smart commit: empty field → auto-generate via AI then commit.
            def smart_work() -> None:
                try:
                    self._stage_selected(stage_all_if_empty=True)
                    diff = self.git.full_diff(self.repo.path, staged_only=True)
                    if not diff.strip():
                        self._set_feedback("Nothing to commit.", error=True)
                        return
                    generated = self.ai.commit_message(diff, self.repo_config)
                    self.commit_message.value = generated
                    safe_update(self.commit_message)
                    self._run_preflight()
                    sha = self.git.commit(self.repo.path, generated)
                except (GitError, AIBackendError) as exc:
                    self._set_feedback(f"Commit failed: {exc}", error=True)
                    return
                except _PreflightBlockedError as exc:
                    self._set_feedback(str(exc), error=True)
                    return
                self.commit_message.value = ""
                self.selected_paths.clear()
                self._set_feedback(
                    f"Committed {sha[:7]} on {self.repo.current_branch} (AI-generated message)."
                )
                safe_update(self.commit_message)
                self.on_changed()

            self._run_async(
                f"✨ Generating message + committing on {self.repo.current_branch}…",
                smart_work,
            )
            return

        def work() -> None:
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

        self._run_async(f"Committing on {self.repo.current_branch}…", work)

    def _push(self) -> None:
        def work() -> None:
            try:
                summary = self.git.push(self.repo.path)
            except GitError as exc:
                self._set_feedback(f"Push failed: {exc}", error=True)
                return
            self._set_feedback(f"Pushed {self.repo.current_branch}: {summary}")
            self.on_changed()

        self._run_async(f"Pushing {self.repo.current_branch}…", work)

    def _auto_pilot(self) -> None:
        if not self.repo_config.auto_pilot:
            self._set_feedback("Auto-pilot is disabled for this repo.", error=True)
            return

        def work() -> None:
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

        self._run_async("🚀 Auto-pilot: stage → commit → push…", work)

    def _merge(self) -> None:
        # Source = current branch (the work you've done). Target = where
        # you want to land it (picked in the dropdown).
        source = self.repo.current_branch
        target = self.merge_target.value
        if not target:
            self._set_feedback("Pick a target branch to merge into.", error=True)
            self._ensure_expanded()
            return
        if not source:
            self._set_feedback("Cannot merge from a detached HEAD.", error=True)
            return

        def work() -> None:
            # 1) Switch to the target branch (auto-stash if dirty).
            try:
                checkout_result = self.git.checkout_branch(self.repo.path, target)
            except GitError as exc:
                self._set_feedback(f"Could not switch to `{target}`: {exc}", error=True)
                return
            if checkout_result == "switched-stash-conflict":
                self._set_feedback(
                    f"Switched to `{target}` but stash has conflicts. Resolve manually before merging.",
                    error=True,
                )
                self.on_changed()
                return

            # 2) Merge the original source branch into the now-current target.
            try:
                conflict = self.git.begin_merge(self.repo.path, source)
            except GitError as exc:
                self._set_feedback(f"Merge failed: {exc}", error=True)
                return

            if conflict is None:
                try:
                    sha = self.git.commit(
                        self.repo.path,
                        f"Merge branch '{source}' into {target}",
                    )
                except GitError as exc:
                    self._set_feedback(f"Could not finalize merge: {exc}", error=True)
                    return
                self._set_feedback(f"Merged {source} → {target} ({sha[:7]}). You are now on `{target}`.")
                self.on_changed()
                return

            self._set_feedback(f"Merge has {len(conflict.files)} conflict(s). Opening AI conflict resolver…")
            self.on_open_merge(self.repo)

        self._run_async(f"Switching to {target} and merging {source}…", work)

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
