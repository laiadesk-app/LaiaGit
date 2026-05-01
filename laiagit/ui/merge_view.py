from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.ai_backends import AIBackendError
from laiagit.models import Conflict, ConflictFile, Repo, ResolutionConfidence
from laiagit.services import AIService, ConfigService, GitError, GitService
from laiagit.ui.components.conflict_panel import conflict_panel


class MergeView:
    def __init__(
        self,
        page: ft.Page,
        repo: Repo,
        git: GitService,
        ai: AIService,
        config_service: ConfigService,
        on_back: Callable[[], None],
    ):
        self.page = page
        self.repo = repo
        self.git = git
        self.ai = ai
        self.config_service = config_service
        self.repo_config = config_service.load_repo_config(repo.path)
        self.on_back = on_back

        self.source_branch = ft.Dropdown(
            label="Source branch (merge from)",
            options=self._branch_options(exclude=self.repo.current_branch),
            width=260,
        )
        self.target_branch = ft.Text(
            self.repo.current_branch or "(no current branch)",
            size=14,
            weight=ft.FontWeight.BOLD,
        )
        self.feedback = ft.Text("", size=12, color=ft.Colors.GREY_700)
        self.summary_box = ft.Container(
            content=ft.Text("Run a merge to see conflicts here.", color=ft.Colors.GREY_600),
            padding=12,
        )
        self.confirm_button = ft.FilledButton(
            "Confirm merge",
            icon=ft.Icons.MERGE,
            on_click=lambda _: self._confirm(),
            disabled=True,
        )
        self.abort_button = ft.OutlinedButton(
            "Abort merge",
            icon=ft.Icons.CANCEL,
            on_click=lambda _: self._abort(),
            disabled=True,
        )
        self.current_conflict: Conflict | None = None

    def build(self) -> ft.Control:
        return ft.Column(
            [
                self._header(),
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Merge configuration", size=14, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    self.source_branch,
                                    ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY_500),
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                ft.Text("Target", size=11, color=ft.Colors.GREY_600),
                                                self.target_branch,
                                            ],
                                            spacing=2,
                                        ),
                                    ),
                                    ft.FilledButton(
                                        "Run merge",
                                        icon=ft.Icons.PLAY_ARROW,
                                        on_click=lambda _: self._run(),
                                    ),
                                ],
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            self.feedback,
                            ft.Divider(),
                            ft.Text("Conflicts and AI proposals", size=14, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Column(
                                    [self.summary_box],
                                    scroll=ft.ScrollMode.AUTO,
                                    expand=True,
                                ),
                                expand=True,
                            ),
                            ft.Row(
                                [self.abort_button, self.confirm_button],
                                alignment=ft.MainAxisAlignment.END,
                                spacing=8,
                            ),
                        ],
                        spacing=12,
                        expand=True,
                    ),
                    padding=14,
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
                        tooltip="Back to repo",
                        on_click=lambda _: self.on_back(),
                    ),
                    ft.Text(f"Merge — {self.repo.name}", size=20, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.Colors.GREY_50,
        )

    def _branch_options(self, exclude: str | None) -> list[ft.dropdown.Option]:
        return [ft.dropdown.Option(b.name) for b in self.repo.branches if b.name != exclude]

    def _run(self) -> None:
        if not self.source_branch.value:
            self._set_feedback("Pick a source branch first.", error=True)
            return
        try:
            conflict = self.git.begin_merge(self.repo.path, self.source_branch.value)
        except GitError as exc:
            self._set_feedback(str(exc), error=True)
            return

        if conflict is None:
            self._set_feedback(
                f"Merge of `{self.source_branch.value}` into `{self.repo.current_branch}` "
                "completed cleanly. Commit it from the repo view."
            )
            self.confirm_button.disabled = True
            self.abort_button.disabled = True
            self.summary_box.content = ft.Text(
                "No conflicts. Merge is staged; commit from repo view.",
                color=ft.Colors.GREEN_600,
            )
            self._maybe_update(self.confirm_button, self.abort_button, self.summary_box)
            return

        self._set_feedback(f"Merge has {len(conflict.files)} conflicts. Resolving with AI…")
        try:
            self.ai.resolve_all(conflict, self.repo_config)
        except AIBackendError as exc:
            self._set_feedback(f"AI resolution failed: {exc}", error=True)

        self.current_conflict = conflict
        self._render_conflict(conflict)
        self.confirm_button.disabled = not conflict.all_resolved
        self.abort_button.disabled = False
        self._maybe_update(self.confirm_button, self.abort_button, self.summary_box)

    def _render_conflict(self, conflict: Conflict) -> None:
        panels: list[ft.Control] = []
        high = sum(
            1 for f in conflict.files if f.resolution and f.resolution.confidence == ResolutionConfidence.HIGH
        )
        review = len(conflict.files_needing_review)
        panels.append(
            ft.Text(
                f"{len(conflict.files)} files in conflict — {high} high confidence, {review} need review.",
                size=12,
                color=ft.Colors.GREY_700,
            )
        )
        for cf in conflict.files:
            panels.append(conflict_panel(cf, on_accept=self._accept, on_edit=self._edit))
        self.summary_box.content = ft.Column(panels, spacing=12)

    def _accept(self, cf: ConflictFile) -> None:
        cf.accepted = True
        if self.current_conflict and self.current_conflict.all_resolved:
            self.confirm_button.disabled = False
        self._render_conflict(self.current_conflict) if self.current_conflict else None
        self._maybe_update(self.summary_box, self.confirm_button)

    def _edit(self, cf: ConflictFile, new_content: str) -> None:
        if cf.resolution is None:
            return
        cf.resolution.content = new_content

    def _abort(self) -> None:
        try:
            self.git.abort_merge(self.repo.path)
        except GitError as exc:
            self._set_feedback(f"Abort failed: {exc}", error=True)
            return
        self._set_feedback("Merge aborted.")
        self.current_conflict = None
        self.summary_box.content = ft.Text("Merge aborted.", color=ft.Colors.GREY_600)
        self.confirm_button.disabled = True
        self.abort_button.disabled = True
        self._maybe_update(self.summary_box, self.confirm_button, self.abort_button)

    def _confirm(self) -> None:
        if self.current_conflict is None:
            return
        if not self.current_conflict.all_resolved:
            self._set_feedback("Accept all resolutions before confirming.", error=True)
            return
        try:
            self.git.write_resolutions(self.repo.path, self.current_conflict)
            message = (
                f"Merge branch '{self.current_conflict.source_branch}' "
                f"into {self.current_conflict.target_branch} (AI-assisted)"
            )
            sha = self.git.finalize_merge(self.repo.path, self.current_conflict, message)
        except GitError as exc:
            self._set_feedback(f"Finalize failed: {exc}", error=True)
            return
        self._set_feedback(f"Merge committed as {sha[:7]}.")
        self.confirm_button.disabled = True
        self.abort_button.disabled = True
        self._maybe_update(self.confirm_button, self.abort_button)

    def _set_feedback(self, message: str, *, error: bool = False) -> None:
        self.feedback.value = message
        self.feedback.color = ft.Colors.RED_400 if error else ft.Colors.GREY_700
        if self.feedback.page is not None:
            self.feedback.update()

    def _maybe_update(self, *controls: ft.Control) -> None:
        for c in controls:
            if c.page is not None:
                c.update()
