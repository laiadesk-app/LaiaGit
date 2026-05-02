from __future__ import annotations

import contextlib

import flet as ft

from laiagit.ui.components.file_diff import diff_view


def open_diff_modal(page: ft.Page, file_path: str, diff_text: str) -> None:
    """Open a modal dialog showing the diff for one file (Flet 0.84)."""

    def close(_: ft.ControlEvent | None = None) -> None:
        # Flet 0.84 canonical close: pop the top dialog from the page
        # stack. Older patterns (toggling .open + manual overlay removal)
        # leave a ghost paint on macOS.
        with contextlib.suppress(Exception):
            page.pop_dialog()
            page.update()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.DESCRIPTION, size=18, color=ft.Colors.BLUE_400),
                ft.Text(file_path, size=14, weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=diff_view(diff_text),
            width=900,
            height=520,
        ),
        actions=[ft.TextButton("Close", on_click=close)],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.show_dialog(dialog)
