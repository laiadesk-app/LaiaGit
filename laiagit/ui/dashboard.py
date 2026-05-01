from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.models import Repo
from laiagit.services import AIService, ConfigService, GitService, RepoScanner
from laiagit.services.config_service import LaiaGitConfig
from laiagit.ui._utils import safe_update
from laiagit.ui.components.repo_panel import RepoPanel


class DashboardView:
    def __init__(
        self,
        page: ft.Page,
        config: LaiaGitConfig,
        scanner: RepoScanner,
        git: GitService,
        ai: AIService,
        config_service: ConfigService,
        on_open_settings: Callable[[], None],
        on_open_merge: Callable[[Repo], None],
    ):
        self.page = page
        self.config = config
        self.scanner = scanner
        self.git = git
        self.ai = ai
        self.config_service = config_service
        self.on_open_settings = on_open_settings
        self.on_open_merge = on_open_merge

        self.panels_column = ft.Column(spacing=0, tight=True)
        self.status_text = ft.Text("", size=12, color=ft.Colors.GREY_700)
        self.scan_progress = ft.ProgressBar(
            visible=False,
            bar_height=2,
            color=ft.Colors.BLUE_500,
            bgcolor=ft.Colors.BLUE_50,
        )
        self.repos: list[Repo] = []

    def build(self) -> ft.Control:
        return ft.Column(
            [
                self._header(),
                self.scan_progress,
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Column(
                        [self.panels_column],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
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
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.Colors.BLUE_500),
                            ft.Text("LaiaGit", size=22, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"  {self.config.root_folder_path}",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            self.status_text,
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                tooltip="Refresh repos",
                                on_click=lambda _: self.refresh(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS,
                                tooltip="Settings",
                                on_click=lambda _: self.on_open_settings(),
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.Colors.GREY_50,
        )

    def refresh(self) -> None:
        self.status_text.value = "Scanning…"
        self.scan_progress.visible = True
        safe_update(self.status_text, self.scan_progress)

        self.repos = self.scanner.scan_all(
            self.config.root_folder_path,
            self.config.extra_path_paths,
        )
        for r in self.repos:
            self.git.hydrate(r)

        # Sort: repos with pending changes / unpushed first
        self.repos.sort(
            key=lambda r: (
                r.status.value not in ("pending", "conflict", "unpushed"),
                r.name.lower(),
            )
        )

        if not self.repos:
            self.panels_column.controls = [self._empty_state()]
        else:
            self.panels_column.controls = [
                RepoPanel(
                    page=self.page,
                    repo=repo,
                    git=self.git,
                    ai=self.ai,
                    config_service=self.config_service,
                    on_changed=self.refresh,
                    on_open_merge=self.on_open_merge,
                ).build()
                for repo in self.repos
            ]

        actionable = sum(1 for r in self.repos if r.status.value in ("pending", "unpushed", "conflict"))
        self.status_text.value = (
            f"{len(self.repos)} repos · {actionable} need attention"
            if self.repos
            else f"0 repos in {self.config.root_folder_path}"
        )
        self.scan_progress.visible = False
        safe_update(self.panels_column, self.status_text, self.scan_progress)
        # Force a full page render so panels rebuilt from worker threads
        # (e.g. after a branch switch) actually show their new state.
        safe_update(self.page)

    def _empty_state(self) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.FOLDER_OFF, size=40, color=ft.Colors.GREY_400),
                    ft.Text(
                        "No repositories found.",
                        size=14,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Text(
                        f"Set a different root folder in Settings (currently "
                        f"{self.config.root_folder_path}).",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=40,
        )
