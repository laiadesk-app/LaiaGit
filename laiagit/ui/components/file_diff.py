from __future__ import annotations

import flet as ft


def diff_view(diff_text: str) -> ft.Control:
    if not diff_text.strip():
        return ft.Container(
            content=ft.Text("No diff available.", color=ft.Colors.GREY_600, italic=True),
            padding=10,
        )

    lines: list[ft.Control] = []
    for line in diff_text.splitlines():
        color, bg = _colors_for_line(line)
        lines.append(
            ft.Container(
                content=ft.Text(
                    line if line else " ",
                    selectable=True,
                    font_family="monospace",
                    size=12,
                    color=color,
                ),
                bgcolor=bg,
                padding=ft.padding.symmetric(horizontal=8, vertical=1),
            )
        )
    return ft.Container(
        content=ft.Column(lines, spacing=0, scroll=ft.ScrollMode.AUTO),
        bgcolor=ft.Colors.GREY_900,
        border_radius=6,
        padding=4,
        height=400,
    )


def _colors_for_line(line: str) -> tuple[str, str | None]:
    if line.startswith("+++") or line.startswith("---"):
        return ft.Colors.GREY_300, None
    if line.startswith("@@"):
        return ft.Colors.CYAN_300, None
    if line.startswith("+"):
        return ft.Colors.GREEN_300, ft.Colors.with_opacity(0.2, ft.Colors.GREEN_900)
    if line.startswith("-"):
        return ft.Colors.RED_300, ft.Colors.with_opacity(0.2, ft.Colors.RED_900)
    return ft.Colors.GREY_400, None
