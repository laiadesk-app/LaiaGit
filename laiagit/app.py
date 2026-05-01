from __future__ import annotations

import flet as ft

from laiagit.models import Repo
from laiagit.services import (
    AIService,
    ConfigService,
    GitService,
    RepoScanner,
)
from laiagit.ui.dashboard import DashboardView
from laiagit.ui.merge_view import MergeView
from laiagit.ui.repo_detail import RepoDetailView
from laiagit.ui.settings import SettingsView


class LaiaGitApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.config_service = ConfigService()
        self.config = self.config_service.load()
        self.scanner = RepoScanner()
        self.git = GitService()
        self.ai = AIService(self.config)
        self.dashboard: DashboardView | None = None

    def run(self) -> None:
        self.page.title = "LaiaGit"
        self.page.window.width = 1180
        self.page.window.height = 760
        self.page.window.min_width = 900
        self.page.window.min_height = 600
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.bgcolor = ft.Colors.WHITE
        self.page.on_keyboard_event = self._handle_shortcut
        self._show_dashboard()

    def _show_dashboard(self) -> None:
        self.dashboard = DashboardView(
            page=self.page,
            config=self.config,
            scanner=self.scanner,
            git=self.git,
            on_open_repo=self._show_repo,
            on_open_settings=self._show_settings,
        )
        self._render(self.dashboard.build())
        self.dashboard.refresh()

    def _show_repo(self, repo: Repo) -> None:
        view = RepoDetailView(
            page=self.page,
            repo=repo,
            git=self.git,
            ai=self.ai,
            config_service=self.config_service,
            on_back=self._show_dashboard,
            on_merge=self._show_merge,
        )
        self._render(view.build())

    def _show_merge(self, repo: Repo) -> None:
        view = MergeView(
            page=self.page,
            repo=repo,
            git=self.git,
            ai=self.ai,
            config_service=self.config_service,
            on_back=lambda: self._show_repo(repo),
        )
        self._render(view.build())

    def _show_settings(self) -> None:
        view = SettingsView(
            page=self.page,
            config=self.config,
            config_service=self.config_service,
            ai=self.ai,
            on_back=self._show_dashboard,
            on_saved=self._on_config_saved,
        )
        self._render(view.build())

    def _on_config_saved(self, config) -> None:
        self.config = config

    def _render(self, control: ft.Control) -> None:
        self.page.controls.clear()
        self.page.add(control)
        self.page.update()

    def _handle_shortcut(self, event: ft.KeyboardEvent) -> None:
        if not self.config.shortcuts_enabled:
            return
        if self.dashboard is None:
            return
        if event.key in ("F5", "R") and event.ctrl:
            self.dashboard.refresh()


def main(page: ft.Page) -> None:
    LaiaGitApp(page).run()


def run() -> None:
    ft.app(target=main)
