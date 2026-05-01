"""Visual constants used across the UI."""

from __future__ import annotations

import flet as ft

from laiagit.models import RepoStatus

STATUS_COLOR: dict[RepoStatus, str] = {
    RepoStatus.CLEAN: ft.Colors.GREEN_400,
    RepoStatus.PENDING: ft.Colors.AMBER_400,
    RepoStatus.UNPUSHED: ft.Colors.BLUE_400,
    RepoStatus.BEHIND: ft.Colors.PURPLE_400,
    RepoStatus.CONFLICT: ft.Colors.RED_400,
    RepoStatus.ERROR: ft.Colors.GREY_500,
}

STATUS_LABEL: dict[RepoStatus, str] = {
    RepoStatus.CLEAN: "Clean",
    RepoStatus.PENDING: "Pending changes",
    RepoStatus.UNPUSHED: "Unpushed commits",
    RepoStatus.BEHIND: "Behind origin",
    RepoStatus.CONFLICT: "Conflicts",
    RepoStatus.ERROR: "Error",
}

STATUS_ICON: dict[RepoStatus, str] = {
    RepoStatus.CLEAN: ft.Icons.CHECK_CIRCLE,
    RepoStatus.PENDING: ft.Icons.EDIT_NOTE,
    RepoStatus.UNPUSHED: ft.Icons.UPLOAD,
    RepoStatus.BEHIND: ft.Icons.DOWNLOAD,
    RepoStatus.CONFLICT: ft.Icons.WARNING_AMBER,
    RepoStatus.ERROR: ft.Icons.ERROR_OUTLINE,
}
