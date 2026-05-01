from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.models import Repo
from laiagit.ui.theme import STATUS_COLOR, STATUS_ICON, STATUS_LABEL


def repo_card(repo: Repo, on_open: Callable[[Repo], None]) -> ft.Control:
    color = STATUS_COLOR.get(repo.status, ft.Colors.GREY_400)
    icon = STATUS_ICON.get(repo.status, ft.Icons.CIRCLE)
    label = STATUS_LABEL.get(repo.status, "Unknown")

    branch_chip = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ALT_ROUTE, size=14, color=ft.Colors.GREY_700),
                ft.Text(repo.current_branch or "—", size=12, color=ft.Colors.GREY_900),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
        bgcolor=ft.Colors.GREY_200,
        border_radius=10,
    )

    counters: list[ft.Control] = []
    if repo.has_changes:
        counters.append(_counter(ft.Icons.EDIT, len(repo.changes), "files changed"))
    if repo.ahead:
        counters.append(_counter(ft.Icons.ARROW_UPWARD, repo.ahead, "ahead"))
    if repo.behind:
        counters.append(_counter(ft.Icons.ARROW_DOWNWARD, repo.behind, "behind"))

    error_row: ft.Control | None = None
    if repo.error:
        error_row = ft.Text(repo.error, size=11, color=ft.Colors.RED_400, max_lines=2)

    body_children: list[ft.Control] = [
        ft.Row(
            [
                ft.Icon(icon, color=color, size=20),
                ft.Text(label, size=12, color=color, weight=ft.FontWeight.W_500),
            ],
            spacing=6,
        ),
        ft.Text(
            repo.name,
            size=18,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
        ft.Text(
            str(repo.path),
            size=10,
            color=ft.Colors.GREY_600,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
        ft.Container(height=4),
        ft.Row(
            [branch_chip, *counters],
            spacing=6,
            wrap=True,
        ),
    ]
    if error_row is not None:
        body_children.append(error_row)

    card = ft.Container(
        content=ft.Column(body_children, spacing=4, tight=True),
        padding=14,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=12,
        ink=True,
        on_click=lambda _: on_open(repo),
        width=280,
        height=170,
    )
    return card


def _counter(icon: str, value: int, tooltip: str) -> ft.Control:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=12, color=ft.Colors.GREY_700),
                ft.Text(str(value), size=12, color=ft.Colors.GREY_900),
            ],
            spacing=2,
            tight=True,
        ),
        tooltip=tooltip,
        padding=ft.padding.symmetric(horizontal=6, vertical=2),
        bgcolor=ft.Colors.GREY_200,
        border_radius=10,
    )
