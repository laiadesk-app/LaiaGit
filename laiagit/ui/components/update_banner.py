"""Update banner shown above the dashboard when a newer release exists."""

from __future__ import annotations

import contextlib
import webbrowser
from collections.abc import Callable

import flet as ft

from laiagit.services.update_checker import UpdateInfo
from laiagit.ui._utils import safe_update


class UpdateBanner:
    """Amber banner offering both binary download and source-update paths."""

    def __init__(
        self,
        page: ft.Page,
        info: UpdateInfo,
        on_dismiss: Callable[[str], None],
    ) -> None:
        self.page = page
        self.info = info
        self.on_dismiss = on_dismiss
        self._container: ft.Container | None = None

    def build(self) -> ft.Control:
        title = ft.Text(
            f"LaiaGit v{self.info.latest} is available — you have v{self.info.current}",
            size=12,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.AMBER_900,
        )
        notes = ft.Text(
            self.info.body_excerpt or "See release notes on GitHub for details.",
            size=11,
            color=ft.Colors.AMBER_900,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        download_btn = ft.FilledButton(
            content="Download binary",
            icon=ft.Icons.DOWNLOAD,
            height=30,
            on_click=lambda _: self._open_release_page(),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.AMBER_700,
                color=ft.Colors.WHITE,
                text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500),
                padding=ft.padding.symmetric(horizontal=10, vertical=2),
            ),
            tooltip="Open the GitHub release page in your browser",
        )
        source_btn = ft.OutlinedButton(
            content="Update from source",
            icon=ft.Icons.TERMINAL,
            height=30,
            on_click=lambda _: self._show_source_command(),
            style=ft.ButtonStyle(
                color=ft.Colors.AMBER_900,
                text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500),
                padding=ft.padding.symmetric(horizontal=10, vertical=2),
            ),
            tooltip="Show the shell command to update an editable install",
        )
        dismiss_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=16,
            tooltip="Hide this until the next release",
            on_click=lambda _: self._dismiss(),
        )

        self._container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.UPGRADE, color=ft.Colors.AMBER_700, size=22),
                    ft.Column(
                        [title, notes],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                    download_btn,
                    source_btn,
                    dismiss_btn,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            bgcolor=ft.Colors.AMBER_50,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.AMBER_200)),
        )
        return self._container

    def _open_release_page(self) -> None:
        with contextlib.suppress(webbrowser.Error):
            webbrowser.open(self.info.release_url)

    def _show_source_command(self) -> None:
        cmd = (
            "cd ~/.laiagit-src && git pull --ff-only "
            "&& .venv/bin/pip install -q -e . "
            "&& .venv/bin/python -m laiagit"
        )
        dialog: ft.AlertDialog | None = None

        def close(_: ft.ControlEvent | None = None) -> None:
            if dialog is not None:
                dialog.open = False
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
                self.page.update()

        def copy(_: ft.ControlEvent) -> None:
            self.page.set_clipboard(cmd)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Command copied to clipboard"),
                open=True,
            )
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Update from source", size=16),
            content=ft.Column(
                [
                    ft.Text(
                        "Run this in a terminal where LaiaGit is cloned. Adjust the path "
                        "if you cloned somewhere other than ~/.laiagit-src:",
                        size=12,
                    ),
                    ft.Container(
                        content=ft.Text(
                            cmd,
                            font_family="monospace",
                            size=11,
                            selectable=True,
                        ),
                        bgcolor=ft.Colors.GREY_100,
                        padding=ft.padding.all(10),
                        border_radius=6,
                    ),
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Copy", icon=ft.Icons.CONTENT_COPY, on_click=copy),
                ft.TextButton("Close", on_click=close),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _dismiss(self) -> None:
        self.on_dismiss(self.info.latest)
        if self._container is not None:
            self._container.visible = False
            safe_update(self._container)
