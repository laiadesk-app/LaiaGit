from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.models import Repo
from laiagit.services import GitService, RepoScanner
from laiagit.services.config_service import LaiaGitConfig
from laiagit.ui._utils import safe_update
from laiagit.ui.components.repo_card import repo_card


class DashboardView:
    def __init__(
        self,
        page: ft.Page,
        config: LaiaGitConfig,
        scanner: RepoScanner,
        git: GitService,
        on_open_repo: Callable[[Repo], None],
        on_open_settings: Callable[[], None],
    ):
        self.page = page
        self.config = config
        self.scanner = scanner
        self.git = git
        self.on_open_repo = on_open_repo
        self.on_open_settings = on_open_settings
        self.cards_container = ft.Row(wrap=True, spacing=14, run_spacing=14)
        self.status_text = ft.Text("", size=12, color=ft.Colors.GREY_700)
        self.repos: list[Repo] = []

    def build(self) -> ft.Control:
        return ft.Column(
            [
                self._header(),
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Column(
                        [self.cards_container],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=16,
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
        safe_update(self.status_text)
        self.repos = self.scanner.scan(self.config.root_folder_path)
        for r in self.repos:
            self.git.hydrate(r)
        self.cards_container.controls = [repo_card(r, self.on_open_repo) for r in self.repos] or [
            self._empty_state()
        ]
        self.status_text.value = f"{len(self.repos)} repos in {self.config.root_folder_path}"
        safe_update(self.cards_container, self.status_text)

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
