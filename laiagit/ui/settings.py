from __future__ import annotations

from collections.abc import Callable

import flet as ft

from laiagit.services import AIService, ConfigService
from laiagit.services.config_service import LaiaGitConfig
from laiagit.ui._utils import safe_update


class SettingsView:
    def __init__(
        self,
        page: ft.Page,
        config: LaiaGitConfig,
        config_service: ConfigService,
        ai: AIService,
        on_back: Callable[[], None],
        on_saved: Callable[[LaiaGitConfig], None],
    ):
        self.page = page
        self.config = config
        self.config_service = config_service
        self.ai = ai
        self.on_back = on_back
        self.on_saved = on_saved

        self.root_field = ft.TextField(
            label="Root folder",
            value=config.root_folder,
            width=420,
            hint_text="~/dev",
        )
        self.default_backend = ft.Dropdown(
            label="Default AI backend",
            options=[
                ft.dropdown.Option("ollama"),
                ft.dropdown.Option("claude_code"),
                ft.dropdown.Option("api"),
            ],
            value=config.default_ai_backend,
            width=220,
        )
        self.ollama_host = ft.TextField(
            label="Ollama host",
            value=config.ai_backends.ollama.host,
            width=300,
        )
        self.ollama_model = ft.TextField(
            label="Ollama model",
            value=config.ai_backends.ollama.model,
            width=220,
        )
        self.claude_command = ft.TextField(
            label="Claude Code command",
            value=config.ai_backends.claude_code.command,
            width=220,
        )
        self.api_provider = ft.Dropdown(
            label="API provider",
            options=[
                ft.dropdown.Option("anthropic"),
                ft.dropdown.Option("openai"),
            ],
            value=config.ai_backends.api.provider,
            width=200,
        )
        self.api_model = ft.TextField(
            label="API model",
            value=config.ai_backends.api.model,
            width=260,
        )
        self.shortcuts = ft.Switch(
            label="Enable keyboard shortcuts",
            value=config.shortcuts_enabled,
        )
        self.preflight_secrets = ft.Switch(
            label="Block secrets",
            value=config.preflight.block_secrets,
        )
        self.preflight_todos = ft.Switch(
            label="Warn on TODOs",
            value=config.preflight.block_todos,
        )
        self.preflight_console = ft.Switch(
            label="Warn on console.*",
            value=config.preflight.block_console_logs,
        )
        self.detection_text = ft.Text("", size=12, color=ft.Colors.GREY_700)
        self.feedback = ft.Text("", size=12, color=ft.Colors.GREY_700)

        self.extra_paths_list = ft.Column(spacing=4, tight=True)
        self.extra_path_input = ft.TextField(
            label="Add a folder to scan or a single repo path",
            hint_text="/Users/me/work/special-project",
            expand=True,
            dense=True,
            on_submit=lambda _: self._add_extra_path(),
        )

        self.excluded_repos_list = ft.Column(spacing=4, tight=True)

        # FilePicker is a Service in Flet 0.84+, not a Control — it must
        # live in `page.services`, not `page.overlay`. Reuse an existing
        # one if present so re-entering Settings doesn't accumulate copies.
        existing = next(
            (s for s in self.page.services if isinstance(s, ft.FilePicker)),
            None,
        )
        if existing is None:
            self.folder_picker = ft.FilePicker()
            self.page.services.append(self.folder_picker)
        else:
            self.folder_picker = existing

    def build(self) -> ft.Control:
        self._update_detection()
        self._render_extra_paths()
        self._render_excluded_repos()
        return ft.Column(
            [
                self._header(),
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("General", size=14, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    self.root_field,
                                    ft.IconButton(
                                        icon=ft.Icons.FOLDER_OPEN,
                                        tooltip="Browse for a folder",
                                        on_click=lambda _: self._pick_folder("root"),
                                    ),
                                ],
                                spacing=4,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                "Additional folders & specific repos",
                                size=13,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.GREY_800,
                            ),
                            ft.Text(
                                "Add a folder to scan recursively, or the path of a single repo "
                                "to include directly. The dashboard merges them with the main "
                                "root folder above.",
                                size=11,
                                color=ft.Colors.GREY_600,
                            ),
                            self.extra_paths_list,
                            ft.Row(
                                [
                                    self.extra_path_input,
                                    ft.IconButton(
                                        icon=ft.Icons.FOLDER_OPEN,
                                        tooltip="Browse for a folder",
                                        on_click=lambda _: self._pick_folder("extra"),
                                    ),
                                    ft.FilledTonalButton(
                                        "Add",
                                        icon=ft.Icons.ADD,
                                        on_click=lambda _: self._add_extra_path(),
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                "Excluded repos",
                                size=13,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.GREY_800,
                            ),
                            ft.Text(
                                "Repos hidden from the dashboard. Click 🗑 to bring one back.",
                                size=11,
                                color=ft.Colors.GREY_600,
                            ),
                            self.excluded_repos_list,
                            ft.Divider(),
                            ft.Text("AI backends", size=14, weight=ft.FontWeight.BOLD),
                            self.detection_text,
                            ft.Row(
                                [
                                    self.default_backend,
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        tooltip="Re-detect backends",
                                        on_click=lambda _: self._update_detection(),
                                    ),
                                ],
                                spacing=4,
                            ),
                            ft.Text("Ollama", size=12, weight=ft.FontWeight.W_500),
                            ft.Row([self.ollama_host, self.ollama_model], spacing=8, wrap=True),
                            ft.Text("Claude Code CLI", size=12, weight=ft.FontWeight.W_500),
                            self.claude_command,
                            ft.Text("External API", size=12, weight=ft.FontWeight.W_500),
                            ft.Row([self.api_provider, self.api_model], spacing=8, wrap=True),
                            ft.Text(
                                "API keys are read from env: ANTHROPIC_API_KEY or OPENAI_API_KEY.",
                                size=11,
                                color=ft.Colors.GREY_600,
                            ),
                            ft.Divider(),
                            ft.Text("Pre-flight defaults", size=14, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    self.preflight_secrets,
                                    self.preflight_todos,
                                    self.preflight_console,
                                ],
                                spacing=12,
                                wrap=True,
                            ),
                            ft.Divider(),
                            ft.Text("Ergonomics", size=14, weight=ft.FontWeight.BOLD),
                            self.shortcuts,
                            ft.Divider(),
                            ft.Row(
                                [
                                    self.feedback,
                                    ft.Container(expand=True),
                                    ft.FilledButton(
                                        "Save",
                                        icon=ft.Icons.SAVE,
                                        on_click=lambda _: self._save(),
                                    ),
                                ]
                            ),
                        ],
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=20,
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
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Back to dashboard",
                        on_click=lambda _: self.on_back(),
                    ),
                    ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.Colors.GREY_50,
        )

    def _pick_folder(self, target: str) -> None:
        # `get_directory_path()` is a coroutine in Flet 0.84+, so we have to
        # schedule it on the page event loop via `run_task`.
        self.page.run_task(self._async_pick_folder, target)

    async def _async_pick_folder(self, target: str) -> None:
        try:
            picked = await self.folder_picker.get_directory_path(dialog_title="Pick a folder")
        except Exception as exc:  # noqa: BLE001
            self._set_feedback(f"Folder picker unavailable: {exc}", error=True)
            return
        if not picked:
            return
        if target == "root":
            self.root_field.value = picked
            safe_update(self.root_field)
            self._set_feedback(f"Root folder set to `{picked}`. Click Save to persist.")
        elif target == "extra":
            self.extra_path_input.value = picked
            safe_update(self.extra_path_input)

    def _render_extra_paths(self) -> None:
        if not self.config.extra_paths:
            self.extra_paths_list.controls = [
                ft.Text(
                    "No additional paths configured.",
                    size=11,
                    color=ft.Colors.GREY_500,
                    italic=True,
                )
            ]
        else:
            self.extra_paths_list.controls = [self._extra_path_row(p) for p in self.config.extra_paths]
        safe_update(self.extra_paths_list)

    def _extra_path_row(self, path: str) -> ft.Control:
        from pathlib import Path as _Path

        resolved = _Path(path).expanduser()
        is_repo = (resolved / ".git").exists()
        kind = "repo" if is_repo else ("folder" if resolved.is_dir() else "missing")
        kind_color = {
            "repo": ft.Colors.GREEN_700,
            "folder": ft.Colors.BLUE_700,
            "missing": ft.Colors.RED_500,
        }[kind]
        return ft.Row(
            [
                ft.Icon(ft.Icons.FOLDER if not is_repo else ft.Icons.SOURCE, size=16, color=kind_color),
                ft.Text(path, size=12, expand=True, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(
                    content=ft.Text(kind, size=10, color=kind_color),
                    padding=ft.padding.symmetric(horizontal=6, vertical=1),
                    bgcolor=ft.Colors.with_opacity(0.10, kind_color),
                    border_radius=6,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=18,
                    tooltip="Remove",
                    on_click=lambda _, p=path: self._remove_extra_path(p),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _render_excluded_repos(self) -> None:
        if not self.config.excluded_repos:
            self.excluded_repos_list.controls = [
                ft.Text(
                    "No repos excluded.",
                    size=11,
                    color=ft.Colors.GREY_500,
                    italic=True,
                )
            ]
        else:
            self.excluded_repos_list.controls = [self._excluded_row(p) for p in self.config.excluded_repos]
        safe_update(self.excluded_repos_list)

    def _excluded_row(self, path: str) -> ft.Control:
        return ft.Row(
            [
                ft.Icon(ft.Icons.VISIBILITY_OFF, size=16, color=ft.Colors.GREY_600),
                ft.Text(
                    path,
                    size=12,
                    expand=True,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=18,
                    tooltip="Re-include this repo",
                    on_click=lambda _, p=path: self._unexclude_repo(p),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _unexclude_repo(self, path: str) -> None:
        if path in self.config.excluded_repos:
            self.config.excluded_repos.remove(path)
            self._render_excluded_repos()
            self._set_feedback(f"Re-included `{path}`. Click Save to persist.")

    def _add_extra_path(self) -> None:
        raw = (self.extra_path_input.value or "").strip()
        if not raw:
            return
        if raw in self.config.extra_paths:
            self._set_feedback(f"`{raw}` is already in the list.", error=True)
            return
        self.config.extra_paths.append(raw)
        self.extra_path_input.value = ""
        safe_update(self.extra_path_input)
        self._render_extra_paths()
        self._set_feedback(f"Added `{raw}`. Click Save to persist.")

    def _remove_extra_path(self, path: str) -> None:
        if path in self.config.extra_paths:
            self.config.extra_paths.remove(path)
            self._render_extra_paths()
            self._set_feedback(f"Removed `{path}`. Click Save to persist.")

    def _set_feedback(self, message: str, *, error: bool = False) -> None:
        self.feedback.value = message
        self.feedback.color = ft.Colors.RED_400 if error else ft.Colors.GREY_700
        safe_update(self.feedback)

    def _update_detection(self) -> None:
        results = self.ai.detect_available()
        self.detection_text.value = "Detected backends:  " + "    ".join(
            f"{'✔' if results.get(n) else '✘'} {n}" for n in ("ollama", "claude_code", "api")
        )
        safe_update(self.detection_text)

    def _save(self) -> None:
        self.config.root_folder = self.root_field.value or "~/dev"
        self.config.default_ai_backend = self.default_backend.value or "ollama"
        self.config.ai_backends.ollama.host = self.ollama_host.value or "http://localhost:11434"
        self.config.ai_backends.ollama.model = self.ollama_model.value or "qwen2.5-coder:7b"
        self.config.ai_backends.claude_code.command = self.claude_command.value or "claude"
        self.config.ai_backends.api.provider = self.api_provider.value or "anthropic"
        self.config.ai_backends.api.model = self.api_model.value or "claude-sonnet-4-6"
        self.config.shortcuts_enabled = bool(self.shortcuts.value)
        self.config.preflight.block_secrets = bool(self.preflight_secrets.value)
        self.config.preflight.block_todos = bool(self.preflight_todos.value)
        self.config.preflight.block_console_logs = bool(self.preflight_console.value)
        try:
            self.config_service.save(self.config)
        except OSError as exc:
            self.feedback.value = f"Could not save: {exc}"
            self.feedback.color = ft.Colors.RED_400
            safe_update(self.feedback)
            return
        self.ai.reload(self.config)
        self.on_saved(self.config)
        # Auto-navigate back to dashboard. The dashboard will show its own
        # loading indicator while it re-scans with the new config.
        self.on_back()
