from __future__ import annotations

import contextlib

import flet as ft

from laiagit.ui.components.file_diff import diff_view


def open_diff_modal(page: ft.Page, file_path: str, diff_text: str) -> None:
    """Open a modal dialog showing the diff for one file (Flet 0.84-compatible)."""

    def close(_: ft.ControlEvent | None = None) -> None:
        dialog.open = False
        with contextlib.suppress(Exception):
            page.update()
        # Clean up: drop the dialog from page.overlay so opening many files
        # in a row does not accumulate stale dialogs.
        with contextlib.suppress(ValueError):
            page.overlay.remove(dialog)
        with contextlib.suppress(Exception):
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

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
