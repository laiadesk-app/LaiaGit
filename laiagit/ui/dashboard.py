from __future__ import annotations

import contextlib
import threading
import time
from collections.abc import Callable

import flet as ft

from laiagit.models import Repo
from laiagit.services import AIService, ConfigService, GitService, RepoScanner
from laiagit.services.config_service import LaiaGitConfig
from laiagit.services.update_checker import check_for_update
from laiagit.ui._utils import safe_update
from laiagit.ui.components.repo_panel import RepoPanel
from laiagit.ui.components.update_banner import UpdateBanner


class DashboardView:
    def __init__(
        self,
        page: ft.Page,
        config: LaiaGitConfig,
        scanner: RepoScanner,
        git: GitService,
        ai: AIService,
        config_service: ConfigService,
        on_open_settings: Callable[[], None],
        on_open_merge: Callable[[Repo], None],
    ):
        self.page = page
        self.config = config
        self.scanner = scanner
        self.git = git
        self.ai = ai
        self.config_service = config_service
        self.on_open_settings = on_open_settings
        self.on_open_merge = on_open_merge

        self.panels_column = ft.Column(spacing=0, tight=True)
        self.update_banner_slot = ft.Container(visible=False)
        self.status_text = ft.Text("", size=12, color=ft.Colors.GREY_700)
        self.scan_progress = ft.ProgressBar(
            visible=False,
            bar_height=2,
            color=ft.Colors.BLUE_500,
            bgcolor=ft.Colors.BLUE_50,
        )
        self.repos: list[Repo] = []

    def build(self) -> ft.Control:
        return ft.Column(
            [
                self._header(),
                self.update_banner_slot,
                self.scan_progress,
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Column(
                        [self.panels_column],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    expand=True,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _header(self) -> ft.Control:
        right_items: list[ft.Control] = [self.status_text]

        hidden_count = len(self.config.excluded_repos)
        if hidden_count > 0:
            right_items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.VISIBILITY_OFF,
                                size=14,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(
                                f"{hidden_count} hidden",
                                size=11,
                                color=ft.Colors.GREY_800,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=10,
                    on_click=lambda _: self.on_open_settings(),
                    tooltip="Open Settings to restore hidden repos",
                    ink=True,
                )
            )

        right_items.extend(
            [
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh repos",
                    on_click=lambda _: self.refresh(),
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    tooltip="Settings",
                    on_click=lambda _: self.on_open_settings(),
                ),
            ]
        )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.Colors.BLUE_500),
                            ft.Text("LaiaGit", size=22, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"  {self.config.root_folder_path}",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(right_items, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.Colors.GREY_50,
        )

    def check_for_update_async(self) -> None:
        """Kick off a non-blocking GitHub Releases check on startup."""
        if not self.config.check_for_updates:
            return
        threading.Thread(target=self._update_check_worker, daemon=True).start()

    def _update_check_worker(self) -> None:
        info = check_for_update()
        if info is None:
            return
        if info.latest == self.config.last_dismissed_update:
            return  # user already dismissed this exact version
        banner = UpdateBanner(
            page=self.page,
            info=info,
            on_dismiss=self._dismiss_update,
        )
        self.update_banner_slot.content = banner.build()
        self.update_banner_slot.visible = True
        safe_update(self.update_banner_slot)

    def _dismiss_update(self, version: str) -> None:
        # Persist failure is non-fatal — banner stays hidden this session anyway.
        self.config.last_dismissed_update = version
        with contextlib.suppress(OSError):
            self.config_service.save(self.config)

    def refresh(self) -> None:
        # Show loading immediately on the UI thread so the user sees
        # the spinner and "Scanning…" before any heavy work begins.
        self.status_text.value = "Scanning repositories…"
        self.scan_progress.visible = True
        self.panels_column.controls = [self._loading_placeholder()]
        safe_update(self.status_text, self.scan_progress, self.panels_column)
        safe_update(self.page)

        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self) -> None:
        try:
            # Phase 1 — discover repo names. This is fast: it just walks
            # the filesystem looking for `.git` directories.
            repos = self.scanner.scan_all(
                self.config.root_folder_path,
                self.config.extra_path_paths,
                self.config.excluded_repo_paths,
            )

            if not repos:
                self.panels_column.controls = [self._empty_state()]
                self.status_text.value = f"0 repos in {self.config.root_folder_path}"
                self.scan_progress.visible = False
                safe_update(self.panels_column, self.status_text, self.scan_progress)
                safe_update(self.page)
                return

            # Show all repos as skeleton panels (just names) immediately so
            # the user sees the full list while the per-repo data loads.
            repos.sort(key=lambda r: r.name.lower())
            self.panels_column.controls = [self._skeleton_panel(r) for r in repos]
            self.status_text.value = f"{len(repos)} repos found — loading details (0/{len(repos)})…"
            safe_update(self.panels_column, self.status_text)
            safe_update(self.page)
            # Tiny pause so the skeleton list is visible at least one frame
            # before hydrate replaces panels. No per-repo delay — that just
            # made big root folders feel stuck.
            time.sleep(0.08)

            # Phase 2 — hydrate one at a time and swap the skeleton with
            # the real RepoPanel as soon as that repo's git data is ready.
            for i, repo in enumerate(repos):
                self.git.hydrate(repo)
                self.panels_column.controls[i] = RepoPanel(
                    page=self.page,
                    repo=repo,
                    git=self.git,
                    ai=self.ai,
                    config_service=self.config_service,
                    on_changed=self.refresh,
                    on_open_merge=self.on_open_merge,
                    on_exclude=self._request_exclude,
                    on_reorder=self._reorder_repo,
                ).build()
                self.status_text.value = f"{len(repos)} repos · loading details ({i + 1}/{len(repos)})…"
                safe_update(self.panels_column, self.status_text)

            # Phase 3 — apply ordering: user's manual `config.repo_order`
            # wins; everything else falls back to status priority + name.
            pairs = list(zip(repos, self.panels_column.controls, strict=True))
            sorted_pairs = self._apply_order(pairs)
            sorted_repos, sorted_panels = (list(s) for s in zip(*sorted_pairs, strict=True))
            self.panels_column.controls = sorted_panels
            self.repos = sorted_repos

            actionable = sum(1 for r in sorted_repos if r.status.value in ("pending", "unpushed", "conflict"))
            self.status_text.value = f"{len(sorted_repos)} repos · {actionable} need attention"
        except Exception as exc:  # noqa: BLE001
            self.status_text.value = f"Scan failed: {exc}"
            self.panels_column.controls = [
                ft.Text(f"Scan failed: {exc}", color=ft.Colors.RED_400, italic=True)
            ]
        finally:
            self.scan_progress.visible = False
            safe_update(self.panels_column, self.status_text, self.scan_progress)
            safe_update(self.page)

    def _skeleton_panel(self, repo: Repo) -> ft.Control:
        """Lightweight placeholder shown while a repo is hydrating."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.ProgressRing(width=14, height=14, stroke_width=2),
                    ft.Text(
                        repo.name,
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        no_wrap=True,
                    ),
                    ft.Text(
                        str(repo.path),
                        size=10,
                        color=ft.Colors.GREY_600,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                    ),
                    ft.Text(
                        "Loading…",
                        size=11,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            margin=ft.margin.only(bottom=8),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=10,
        )

    def _apply_order(self, pairs: list[tuple[Repo, ft.Control]]) -> list[tuple[Repo, ft.Control]]:
        """Order (repo, panel) pairs.

        Repos whose path appears in `config.repo_order` come first, in that
        explicit order. Remaining repos go after, sorted by status priority
        and then name.
        """
        order = self.config.repo_order
        order_set = set(order)
        in_order = [p for p in pairs if str(p[0].path) in order_set]
        rest = [p for p in pairs if str(p[0].path) not in order_set]

        in_order.sort(key=lambda pair: order.index(str(pair[0].path)))
        rest.sort(
            key=lambda pair: (
                pair[0].status.value not in ("pending", "conflict", "unpushed"),
                pair[0].name.lower(),
            )
        )
        return in_order + rest

    def _reorder_repo(self, repo: Repo, direction: str) -> None:
        """Move a repo up/down/top/bottom in the visible order.

        In-place: reshuffles the already-loaded panels and persists the
        new order. No filesystem scan or git hydrate — those happened
        during the previous refresh and the data is still valid.
        """
        if not self.repos:
            return
        panels = list(self.panels_column.controls)
        if len(panels) != len(self.repos):
            self.refresh()
            return
        try:
            current_index = next(i for i, r in enumerate(self.repos) if str(r.path) == str(repo.path))
        except StopIteration:
            return

        if direction == "top":
            new_index = 0
        elif direction == "bottom":
            new_index = len(self.repos) - 1
        elif direction == "up":
            new_index = max(0, current_index - 1)
        elif direction == "down":
            new_index = min(len(self.repos) - 1, current_index + 1)
        else:
            return
        if new_index == current_index:
            return

        new_repos = list(self.repos)
        new_repos.insert(new_index, new_repos.pop(current_index))
        panels.insert(new_index, panels.pop(current_index))

        self.repos = new_repos
        self.panels_column.controls = panels
        self.config.repo_order = [str(r.path) for r in new_repos]
        try:
            self.config_service.save(self.config)
        except OSError as exc:
            self.status_text.value = f"Could not save order: {exc}"
            safe_update(self.status_text)
            return
        safe_update(self.panels_column)

    def _request_exclude(self, repo: Repo) -> None:
        """Open a confirmation dialog before hiding a repo."""
        dialog: ft.AlertDialog | None = None

        def close() -> None:
            if dialog is not None:
                dialog.open = False
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
                self.page.update()

        def confirm(_: ft.ControlEvent) -> None:
            close()
            self._exclude_repo(repo)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.VISIBILITY_OFF, color=ft.Colors.AMBER_700),
                    ft.Text(f"Hide '{repo.name}' from the dashboard?", size=15),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "This only HIDES the repository from LaiaGit's dashboard. "
                            "Your files and the .git folder are NOT touched on disk — "
                            "the repository keeps working with git outside LaiaGit.",
                            size=12,
                        ),
                        ft.Text(
                            "You can bring it back any time from Settings → Excluded repos.",
                            size=11,
                            color=ft.Colors.GREY_700,
                            italic=True,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.FOLDER, size=14, color=ft.Colors.GREY_700),
                                    ft.Text(
                                        str(repo.path),
                                        size=11,
                                        color=ft.Colors.GREY_800,
                                        selectable=True,
                                    ),
                                ],
                                spacing=6,
                            ),
                            padding=ft.padding.symmetric(horizontal=8, vertical=6),
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=6,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=460,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: close()),
                ft.FilledButton(
                    "Hide repo",
                    icon=ft.Icons.VISIBILITY_OFF,
                    on_click=confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _exclude_repo(self, repo: Repo) -> None:
        path_str = str(repo.path)
        if path_str in self.config.excluded_repos:
            return
        self.config.excluded_repos.append(path_str)
        try:
            self.config_service.save(self.config)
        except OSError as exc:
            self.status_text.value = f"Could not save exclusion: {exc}"
            safe_update(self.status_text)
            return
        self.refresh()

    def _loading_placeholder(self) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=28, height=28, stroke_width=3),
                    ft.Text(
                        "Loading your repositories…",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=40,
        )

    def _empty_state(self) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.FOLDER_OFF, size=40, color=ft.Colors.GREY_400),
                    ft.Text(
                        "No repositories found.",
                        size=14,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Text(
                        f"Set a different root folder in Settings (currently "
                        f"{self.config.root_folder_path}).",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=40,
        )
