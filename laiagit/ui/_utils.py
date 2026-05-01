"""UI helpers."""

from __future__ import annotations

import contextlib

import flet as ft


def safe_update(*controls: ft.Control) -> None:
    """Call .update() on each control, swallowing the RuntimeError raised
    by Flet 0.84+ when a control is not yet attached to the page.
    """
    for control in controls:
        with contextlib.suppress(RuntimeError, AssertionError):
            control.update()
