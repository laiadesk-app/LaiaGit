from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.models import ConflictFile, ResolutionConfidence

CONFIDENCE_COLOR: dict[ResolutionConfidence, str] = {
    ResolutionConfidence.HIGH: ft.Colors.GREEN_400,
    ResolutionConfidence.MEDIUM: ft.Colors.AMBER_400,
    ResolutionConfidence.LOW: ft.Colors.RED_400,
    ResolutionConfidence.UNKNOWN: ft.Colors.GREY_500,
}


def conflict_panel(
    cf: ConflictFile,
    on_accept: Callable[[ConflictFile], None],
    on_edit: Callable[[ConflictFile, str], None],
) -> ft.Control:
    confidence = cf.resolution.confidence if cf.resolution else ResolutionConfidence.UNKNOWN
    badge_color = CONFIDENCE_COLOR[confidence]

    text_field = ft.TextField(
        value=cf.resolution.content if cf.resolution else cf.head_content,
        multiline=True,
        min_lines=8,
        max_lines=20,
        text_size=12,
        text_style=ft.TextStyle(font_family="monospace"),
        on_change=lambda e: on_edit(cf, e.control.value),
    )

    accept_button = ft.FilledButton(
        text="Accept resolution" if not cf.accepted else "Accepted",
        icon=ft.Icons.CHECK if not cf.accepted else ft.Icons.CHECK_CIRCLE,
        on_click=lambda _: on_accept(cf),
        disabled=cf.accepted,
    )

    head_panel = _side_panel("HEAD", cf.head_content, ft.Colors.BLUE_300)
    incoming_panel = _side_panel("Incoming", cf.incoming_content, ft.Colors.PURPLE_300)

    header = ft.Row(
        [
            ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.RED_400),
            ft.Text(cf.path, size=14, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(
                    f"AI confidence: {confidence.value}",
                    size=11,
                    color=ft.Colors.WHITE,
                ),
                bgcolor=badge_color,
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                border_radius=10,
            ),
        ],
        spacing=8,
    )

    body = ft.Column(
        [
            header,
            ft.Row([head_panel, incoming_panel], expand=True),
            ft.Text("AI proposal (editable):", size=12, weight=ft.FontWeight.W_500),
            text_field,
            ft.Row([accept_button], alignment=ft.MainAxisAlignment.END),
        ],
        spacing=10,
        tight=True,
    )

    return ft.Container(
        content=body,
        padding=14,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=10,
    )


def _side_panel(title: str, content: str, color: str) -> ft.Control:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=12, color=color, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=ft.Text(
                        content or "(empty)",
                        font_family="monospace",
                        size=11,
                        selectable=True,
                    ),
                    bgcolor=ft.Colors.GREY_900,
                    padding=8,
                    border_radius=6,
                    height=180,
                ),
            ],
            spacing=4,
            tight=True,
        ),
        expand=True,
        padding=4,
    )
