# LaiaGit — Implementation Roadmap

**Date:** 2026-05-01
**Companion to:** `2026-05-01-laiagit-design.md`

---

## Strategy

Ship in five small versions. Each version stands on its own — even `v0.1` should be useful as a Git dashboard, before any AI lands. We add AI features incrementally so each release is testable and contributors can pick up isolated tasks.

Every version ends with: tagged release on GitHub, updated CHANGELOG, working binary for at least one platform.

---

## v0.1 — Bare Git dashboard (no AI)

**Goal:** replace `git status` + `git add` + `git commit` + `git push` for daily flow on multiple repos.

### Scope
- Project skeleton: `__main__.py`, Flet bootstrap, package structure.
- `ConfigService`: read/write `~/.laiagit/config.yaml`.
- `RepoScanner`: walk root folder, find `.git` dirs, return `Repo` models.
- `GitService`: status, diff, list branches, stage, unstage, commit, push.
- `DashboardView`: grid of `RepoCard` components with status color.
- `RepoDetailView`: list changed files, inline diff, checkboxes for selective staging, manual commit message field, push button.
- `SettingsView`: minimal — set root folder.
- Tests: `RepoScanner` and `GitService` (with temp git repos as fixtures).

### Done when
- I can open the app, see all my repos under `~/dev/`, click into one, stage files, commit, and push — without touching a terminal.

### Estimated effort
4–6 issues, ~2 weeks of part-time work.

---

## v0.2 — AI commit messages

**Goal:** "I never write a commit message again."

### Scope
- `AIBackend` abstract class with `commit_message`, `is_available`, version stub for future methods.
- `OllamaBackend`: HTTP call to `localhost:11434`, configurable model.
- `ClaudeCodeBackend`: subprocess wrapper around `claude` CLI.
- `AIService`: orchestrator that picks the active backend.
- Detection on first launch: which backends are available.
- `SettingsView` extended: pick default backend, model.
- UI: "Generate with AI" button next to commit message field.
- Tests: backends mocked.

### Done when
- I click "Generate with AI" on a commit, get a sensible message based on the diff, can edit it, commit.

---

## v0.3 — AI merge with conflict resolution (the killer feature)

**Goal:** merge a branch with conflicts, let AI resolve, review in batch, confirm.

### Scope
- `MergeView`: branch-from / branch-to selectors, "Merge" button.
- Flow Option B (default):
  - Run `git merge --no-commit --no-ff`.
  - Detect conflicts → for each file, call `AIBackend.resolve_conflict`.
  - Summary screen with expandable per-file 3-panel view.
  - Confirm or cancel (`git merge --abort`).
- `Conflict` and `Resolution` models.
- Audit log: every AI resolution written to `~/.laiagit/audit.log`.
- Fallback: if AI unavailable, show standard 3-panel view with no AI proposal.
- Tests: conflict detection, resolution flow with mocked AI.

### Done when
- I trigger a merge with known conflicts, AI proposes resolutions, I review and confirm, commit lands cleanly.

---

## v0.4 — Pre-flight + auto-pilot + repo summary

**Goal:** maximum automation for repos the user trusts.

### Scope
- `PreflightService`: scan diff for secrets (regex patterns), TODOs, console.logs, oversized files.
- Pre-push hook in UI: shows warnings, optional block.
- Auto-pilot mode (Option C): per-repo flag, runs full commit + AI message + push in one click.
- Repo narrative: AI summarizes the repo state on the dashboard card hover or detail view.
- Settings: per-repo overrides (`<repo>/.laiagit/repo.yaml`).

### Done when
- I flag a personal repo as auto-pilot, click one button, commit + push happens with AI message; pre-flight warns me if I'm about to push a `.env` file.

---

## v0.5 — Polish + distribution

**Goal:** shippable to non-developer-friendly users.

### Scope
- Linear-style keyboard shortcuts.
- `APIBackend`: direct Anthropic / OpenAI calls.
- `flet pack` or PyInstaller builds for macOS, Windows, Linux.
- GitHub Actions: build artifacts on tag.
- Auto-update check (optional).
- Documentation: install guide per platform, screenshots.
- README updates with install instructions.

### Done when
- A non-Python user downloads a `.dmg` / `.exe` / `.AppImage`, installs, opens, configures their root folder, and starts using LaiaGit.

---

## How we work

- Every feature lives on its own branch in a fork: `feat/<short-name>`.
- One PR = one logical change.
- PR description must reference the version (e.g. "Part of v0.2").
- Tests required for service layer and AI backends.
- UI changes: include a screenshot in the PR.
- Admin (only `@laiadesk-app`) reviews and merges.

## CI (added in v0.1, expanded over time)

- v0.1: ruff format check, ruff lint, pytest.
- v0.2: add coverage report.
- v0.5: add cross-platform build smoke tests.

---

## First batch of issues to open

These will be the v0.1 starting point, opened as GitHub issues:

1. `chore: scaffold package layout and Flet entry point`
2. `feat(config): ConfigService with ~/.laiagit/config.yaml`
3. `feat(scan): RepoScanner walks root folder for .git dirs`
4. `feat(git): GitService — status, diff, branches`
5. `feat(git): GitService — stage, unstage, commit, push`
6. `feat(ui): DashboardView with RepoCard status colors`
7. `feat(ui): RepoDetailView with file diff + commit + push`
8. `feat(ui): SettingsView for root folder`
9. `chore(ci): GitHub Actions workflow — ruff + pytest`
10. `docs: README with screenshots for v0.1`
