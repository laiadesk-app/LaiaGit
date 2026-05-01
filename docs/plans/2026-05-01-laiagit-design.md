# LaiaGit — Design Document

**Date:** 2026-05-01
**Status:** Approved, ready for implementation

---

## 1. Vision

> A simple visual desktop dashboard for managing all your local Git repositories — where commits, push, merge, and conflict resolution happen in a click, with AI absorbing the friction.

LaiaGit turns Git workflows that normally require terminal expertise into clicks on a panel. It is **not** a replacement for GitHub Desktop or GitKraken — it is a **personal Git command center** with AI as the differentiator.

### Target user

A developer (junior to senior) who:
- Works on multiple local repos at once.
- Wants to see status across all of them at a glance.
- Prefers visual + keyboard interaction over typing `git` commands.
- Already has Git installed and basic Git knowledge.
- May or may not have AI tools installed (Ollama, Claude Code CLI, API keys).

### Non-goals

- Not a GitHub/GitLab client (no PR/issue management — use the official tools).
- Not a Git history visualizer (no commit graphs / blame UI).
- Not a multi-user collaboration tool — strictly a personal desktop app.
- Not a backend service — runs 100% locally, no telemetry, no cloud sync.

---

## 2. Architecture

### Layered design

```
┌──────────────────────────────────────────────┐
│  UI Layer (Flet)                             │
│  - DashboardView  (cards of all repos)       │
│  - RepoDetailView (files, branches, diff)    │
│  - MergeView      (3-panel conflict UI)      │
│  - SettingsView   (AI engine, root folder)   │
└────────────────┬─────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────┐
│  Service Layer                               │
│  - RepoScanner    (discovers repos)          │
│  - GitService     (wraps GitPython)          │
│  - AIService      (orchestrates backends)    │
│  - ConfigService  (reads/writes YAML)        │
│  - PreflightService (secrets, TODOs, etc.)   │
└────────────────┬─────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────┐
│  Backends                                    │
│  - Git: GitPython + subprocess fallback      │
│  - AI:  OllamaBackend │ ClaudeCodeBackend │  │
│         APIBackend (Anthropic / OpenAI)      │
└──────────────────────────────────────────────┘
```

### Design principles

1. **Stateless.** The app holds no Git state of its own — it always reads from the live repo. The source of truth is `git`, never our cache.
2. **Local-first.** No telemetry, no cloud sync. Data leaves the machine only if the user picks the API backend.
3. **Pluggable AI.** Adding a new AI engine = creating one class implementing `AIBackend`. UI and services do not change.
4. **Fail-safe destructive ops.** Merge, push, and any non-reversible action require confirmation. Every AI action is logged locally for audit.
5. **Detect, don't install.** LaiaGit detects Ollama, Claude Code CLI, or API keys if the user has them. It never installs dependencies on the user's machine.

---

## 3. Project structure

```
laiagit/
├── pyproject.toml
├── README.md
├── LICENSE                     # MIT
├── CONTRIBUTING.md
├── .github/
│   ├── CODEOWNERS
│   └── workflows/
│       └── ci.yml              # tests + lint on PR
│
├── laiagit/
│   ├── __init__.py
│   ├── __main__.py             # entry: `python -m laiagit`
│   ├── app.py                  # Flet bootstrap
│   │
│   ├── ui/
│   │   ├── dashboard.py
│   │   ├── repo_detail.py
│   │   ├── merge_view.py
│   │   ├── settings.py
│   │   └── components/
│   │       ├── repo_card.py
│   │       ├── file_diff.py
│   │       └── conflict_panel.py
│   │
│   ├── services/
│   │   ├── repo_scanner.py
│   │   ├── git_service.py
│   │   ├── ai_service.py
│   │   ├── config_service.py
│   │   └── preflight.py
│   │
│   ├── ai_backends/
│   │   ├── base.py             # AIBackend abstract class
│   │   ├── ollama_backend.py
│   │   ├── claude_code_backend.py
│   │   └── api_backend.py
│   │
│   └── models/
│       ├── repo.py             # Repo, BranchInfo, FileChange
│       └── conflict.py         # Conflict, Resolution
│
└── tests/
    ├── test_repo_scanner.py
    ├── test_git_service.py
    └── test_ai_backends.py     # mocked backends
```

---

## 4. Features

### Base (always active)

1. Auto-discovery of repos under a configurable root folder (default `~/dev/`).
2. Card per repo with status color: clean / pending / behind / conflict.
3. List of changed files with inline diff and per-file selective staging (checkboxes — equivalent to `git add -p` visually).
4. List of branches with the active one highlighted.
5. Action buttons: **Commit**, **Push**, **Merge branch → branch**.

### AI layer (configurable per repo)

6. **AI-generated commit message** from the diff. User can edit before confirming.
7. **AI-assisted merge conflict resolution**, default flow (Option B):
   - LaiaGit runs `git merge --no-commit`.
   - AI resolves all conflicts in memory.
   - Single summary screen: "5 files resolved, X lines changed."
   - User can expand any file to review/edit before confirming.
   - Buttons: **Confirm merge** or **Cancel and resolve manually**.
8. **Pre-flight check before push**: detects secrets (`.env`, API keys), TODOs, `console.log`, oversized files. Blocks push or warns.
9. **Repo narrative summary**: "3 days without push, 2 branches behind, conflicts likely in `src/auth.py`."

### Ergonomics (opt-in in settings)

10. Linear-style keyboard shortcuts (`c` commit, `p` push, `m` merge).
11. **Auto-pilot mode** per repo: commit + AI message + push in one click. Only for repos explicitly marked as personal.
12. Per-repo AI engine selector: local / Claude Code CLI / external API.

### Auto-pilot total (Option C, opt-in)

For repos flagged as auto-pilot:
- Merge resolves automatically and commits without intermediate review.
- Stops only if AI reports high uncertainty on any file.
- Final notification: "Merge complete, review commit X."

---

## 5. AI engine architecture

### Unified contract

```python
# laiagit/ai_backends/base.py
from abc import ABC, abstractmethod

class AIBackend(ABC):
    @abstractmethod
    def commit_message(self, diff: str) -> str: ...

    @abstractmethod
    def resolve_conflict(self, head: str, incoming: str, context: str) -> Resolution: ...

    @abstractmethod
    def preflight(self, diff: str) -> list[Warning]: ...

    @abstractmethod
    def is_available(self) -> bool: ...
```

### Backends shipped at launch

- **OllamaBackend** — calls a local Ollama server via HTTP. User picks the model in settings (recommended: `qwen2.5-coder:7b` or `mistral:7b`).
- **ClaudeCodeBackend** — invokes the local `claude` CLI as a subprocess.
- **APIBackend** — direct HTTP to Anthropic or OpenAI, using a key the user supplies.

### Detection flow on first launch

1. Check if `claude` is on `PATH`.
2. Check if Ollama is running on `localhost:11434` and list models.
3. Check if `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set in env.
4. Show settings panel with detected backends pre-filled, others greyed out with a link to install instructions.

LaiaGit never installs anything. The user is expected to have these tools ready.

---

## 6. Conflict resolution flow (the core differentiator)

**Default:** Option B — auto-resolve with batched review.
**Opt-in per repo:** Option C — auto-pilot total.

### Option B step-by-step

```
User clicks "Merge feature/x → main"
        │
        ▼
GitService runs `git merge --no-commit --no-ff`
        │
        ├── No conflicts ──► proceed to commit + show summary
        │
        ▼
Conflicts detected — list of files in conflict
        │
        ▼
For each file: AIService.resolve_conflict(head, incoming, surrounding_context)
        │
        ▼
MergeView shows a single summary screen:
  - "5 files resolved, 3 with high confidence, 2 to review"
  - Expandable sections per file (3-panel: HEAD | incoming | AI proposal)
  - Per-file actions: Accept | Regenerate (with optional prompt) | Edit manually
        │
        ▼
User clicks "Confirm merge"
        │
        ▼
GitService applies resolutions, stages files, commits with AI-generated message
        │
        ▼
Log entry written to `~/.laiagit/audit.log`
```

### Safety rails

- The merge is `--no-commit` until the user confirms. Cancelling = `git merge --abort`.
- Every AI proposal is logged to `~/.laiagit/audit.log` with timestamp, repo, file, before/after.
- If the AI backend is unavailable mid-flow, fall back to the standard manual conflict UI (3-panel view, no AI proposal).

---

## 7. Configuration

### Global config: `~/.laiagit/config.yaml`

```yaml
root_folder: ~/dev
default_ai_backend: ollama          # ollama | claude_code | api
ai_backends:
  ollama:
    host: http://localhost:11434
    model: qwen2.5-coder:7b
  claude_code:
    command: claude
  api:
    provider: anthropic              # anthropic | openai
    # api_key is read from env, never stored here
shortcuts_enabled: true
auto_pilot_repos: []                 # paths to repos in auto-pilot mode
```

### Per-repo overrides: `<repo>/.laiagit/repo.yaml` (optional)

```yaml
ai_backend: claude_code              # overrides the global default
auto_pilot: false
preflight:
  block_secrets: true
  block_todos: false
  max_file_size_mb: 5
```

---

## 8. Tech stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Universal, huge AI ecosystem, low barrier for OSS contributors |
| UI | [Flet](https://flet.dev) | Flutter-rendered desktop UI from pure Python; modern look without CSS |
| Git | GitPython + subprocess | Mature library; subprocess fallback for edge cases |
| AI HTTP | `httpx` | Async-capable, modern |
| Config | `pyyaml` | Human-readable, standard |
| Packaging | PyInstaller / `flet pack` | Single executable per platform |
| Testing | pytest + pytest-mock | Standard |
| Lint/format | ruff | Fast, single tool |

---

## 9. Governance

- **License:** MIT.
- **Repo:** [github.com/laiadesk-app/LaiaGit](https://github.com/laiadesk-app/LaiaGit), public.
- **Contribution model:** fork → PR → admin approval.
- **Branch protection on `main`:**
  - 1 PR review required, must be from CODEOWNERS.
  - Stale approvals dismissed on new commits.
  - Linear history enforced.
  - No force pushes, no deletions.
  - Admin can override in emergencies (`enforce_admins: false`).

---

## 10. Out of scope (deferred or rejected)

| Item | Reason |
|---|---|
| Commit graph / history visualizer | High complexity, low daily value; competes with GitKraken |
| GitHub PR/issue management | Solved by official GitHub Desktop / `gh` CLI |
| Multi-user / team collaboration | Personal desktop tool by design |
| Cloud sync of settings | Adds infra; settings are tiny and local |
| In-app installation of Ollama/Claude Code | Out of scope; user installs their own tools |
| Mobile/web version | Desktop-first; mobile editing of Git makes no sense |

---

## 11. Open questions for implementation phase

These are not blockers for v0.1 but should be answered as we build:

- Default behavior when no AI backend is detected? (Likely: degrade gracefully — Git operations still work, AI buttons are disabled with a tooltip.)
- How aggressive should the pre-flight check be? Block push, or just warn?
- What happens if `git merge --no-commit` triggers on top of existing dirty state? (Likely: refuse, prompt to stash first.)
- Audit log retention policy? (Likely: keep last 1000 entries, rotate.)
