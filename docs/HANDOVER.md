# LaiaGit — Handover document

**Last updated:** 2026-05-09
**Project repo:** https://github.com/laiadesk-app/LaiaGit
**Local clone (this machine):** `/Users/juancarlosrodriguez/NexoSmart-repo/LaiaGit`
**Latest published release:** [`v0.1.1`](https://github.com/laiadesk-app/LaiaGit/releases/tag/v0.1.1)
**Branch protection on `main`:** PR + 1 approval + linear history (admin can bypass)

This document is the single source of truth to **resume LaiaGit work in
another session, on another machine, or by another collaborator**, with
zero context loss. It also documents the configuration commands that
were used to set up the platform.

---

## 1. What LaiaGit is, in one paragraph

LaiaGit is a Flet-based desktop dashboard that shows every local Git
repository under your dev folder as a single-line panel. It writes
commit messages with AI (any of Ollama / Claude Code CLI / Anthropic
API / OpenAI API), resolves merge conflicts via AI proposals, runs
pre-flight scans for secrets/secrets-like patterns/oversized
files/`console.log`/`TODO` markers before push, and offers per-repo
configuration. It's MIT-licensed, ships zero telemetry, and is published
publicly as a contribution from LaiaDesk to the developer community.

---

## 2. Daily-use commands (memorise these)

### Run from source (what you do day-to-day)

```sh
cd /Users/juancarlosrodriguez/NexoSmart-repo/LaiaGit
git pull
.venv/bin/pip install -q -e .
.venv/bin/python -m laiagit
```

### Run tests + lint

```sh
cd /Users/juancarlosrodriguez/NexoSmart-repo/LaiaGit
.venv/bin/pytest -q                 # 64 tests, all green
.venv/bin/ruff check .              # lint
.venv/bin/ruff format .             # auto-format
```

### Compile a native binary on this Mac

Requires full **Xcode** (App Store, ~15 GB) + **CocoaPods** installed.

```sh
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
sudo xcodebuild -license accept
brew install cocoapods
flutter doctor                      # all green required

cd /Users/juancarlosrodriguez/NexoSmart-repo/LaiaGit
.venv/bin/flet build macos          # 5-10 min first time
open build/macos/Build/Products/Release/LaiaGit.app
```

For Windows / Linux compile, see `docs/RELEASE.md`.

### Cut a new release (publishes binaries automatically)

```sh
cd /Users/juancarlosrodriguez/NexoSmart-repo/LaiaGit
git checkout main && git pull
git tag -a v0.1.2 -m "v0.1.2"
git push origin v0.1.2
# GitHub Actions builds macOS + Windows + Linux in parallel,
# attaches them to a Release. ~10-15 min.
```

### Check what's on Releases / get download counts

```sh
gh release list --repo laiadesk-app/LaiaGit
gh release view v0.1.1 --repo laiadesk-app/LaiaGit \
  --json assets -q '.assets[] | {name, downloads: .downloadCount}'
```

---

## 3. Repository state at handover

### Branch state

- `main` is at commit **`ebc0625`** (2026-05-02): *"feat(ui): per-repo Fetch + bulk file actions (Add to .gitignore / Hide from view) — no AI"*
- No open PRs (the last 12 were merged).
- Backup branches still on disk: `backup/main`, `backup/feat-initial`, `backup/chore-public-release-polish` — keep until you're sure you don't need them, then `git branch -D backup/*`.

### Versions

- `pyproject.toml` and `laiagit/__init__.py`: `0.1.1`
- Last published GitHub release: `v0.1.1` (3 binaries: macOS / Windows / Linux)
- `main` HAS unreleased commits beyond `v0.1.1` (see "Unreleased" below).

### Unreleased commits on `main` (since `v0.1.1`)

These are LIVE in source but not in any binary yet. Anyone running from
source via `git pull` already has them:

1. `075eb37` — Modal dialogs: migrated to Flet 0.84 `page.show_dialog` / `pop_dialog`. Fixes ghost-paint on hide-repo dialog.
2. `b9fe2d9` — In-place hide repo + per-repo Refresh button.
3. `3f0a043` — README: positions LaiaDesk model as sticky free upgrade for platform users.
4. `ebc0625` — **Per-repo Fetch button** (cloud icon) + **bulk file actions** (Add to .gitignore / Hide from view, multi-select, no AI).

When you cut `v0.1.2`, all four ship to binary users.

---

## 4. Folder structure

```
LaiaGit/
├── README.md                       Public-facing readme (LaiaDesk wow + roadmap)
├── CONTRIBUTING.md                 How to contribute
├── CODE_OF_CONDUCT.md              Contributor Covenant 2.1
├── SECURITY.md                     Vulnerability reporting
├── LICENSE                         MIT
├── pyproject.toml                  Package config + Flet build settings
├── main.py                         Top-level shim for `flet build`
├── laiagit/                        Main package
│   ├── __init__.py                 (__version__ lives here)
│   ├── __main__.py                 `python -m laiagit` entry point
│   ├── app.py                      LaiaGitApp class — page handler
│   ├── models.py                   Repo, FileChange, FileStatus, RepoStatus, Conflict
│   ├── ai_backends/                Ollama / Claude Code CLI / Anthropic / OpenAI
│   ├── services/
│   │   ├── ai_service.py           Pluggable AI backend (commit msgs, conflicts)
│   │   ├── config_service.py       LaiaGitConfig + RepoConfig + YAML I/O
│   │   ├── git_service.py          GitPython wrapper (status, stage, commit,
│   │   │                           push, fetch, merge, stash, gitignore)
│   │   ├── preflight.py            Secret/TODO/log/size scan
│   │   ├── repo_scanner.py         .git discovery + exclusion
│   │   └── update_checker.py       GitHub Releases poll for in-app banner
│   └── ui/
│       ├── dashboard.py            Main dashboard view (orchestrator)
│       ├── merge_view.py           AI conflict resolver UI
│       ├── settings.py             Settings view
│       ├── theme.py                STATUS_COLOR / STATUS_ICON / STATUS_LABEL
│       ├── _utils.py               safe_update() helper
│       └── components/
│           ├── repo_panel.py       Single-row repo panel (the workhorse)
│           ├── update_banner.py    Amber update notification banner
│           ├── conflict_panel.py   Per-file 3-panel conflict review
│           ├── file_diff_modal.py  Diff view modal
│           └── file_diff.py        Diff renderer
├── tests/                          64 pytest tests (no mocks for git)
├── scripts/
│   ├── install.sh                  curl|sh installer for devs
│   └── update.sh                   Companion: git pull + reinstall
├── docs/
│   ├── HANDOVER.md                 ← this file
│   ├── RELEASE.md                  Release pipeline guide
│   ├── STATISTICS.md               What GitHub exposes (downloads/etc.)
│   ├── laiagit_design.md           Architecture doc
│   └── plans/                      Version-by-version roadmap
└── .github/
    ├── workflows/
    │   ├── ci.yml                  Test + lint on every PR
    │   └── release.yml             Tag push → 3 binaries → Release
    ├── ISSUE_TEMPLATE/             bug/feature/config
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 5. Configuration files

### Global config: `~/.laiagit/config.yaml`

Auto-created on first launch. Schema (`LaiaGitConfig` in `config_service.py`):

```yaml
root_folder: ~/dev                    # where to scan for repos
extra_paths: []                       # additional folders or single repos
excluded_repos: []                    # absolute paths to hide globally
repo_order: []                        # custom UI order; auto-managed by drag/menu
default_ai_backend: ollama            # ollama | claude_code | api
ai_backends:
  ollama:
    host: http://localhost:11434
    model: qwen2.5-coder:7b
  claude_code:
    command: claude
  api:
    provider: anthropic               # anthropic | openai
    model: claude-sonnet-4-6
shortcuts_enabled: true
auto_pilot_repos: []                  # paths where auto-pilot is enabled
preflight:
  block_secrets: true
  block_todos: false
  block_console_logs: false
  max_file_size_mb: 5
check_for_updates: true               # in-app update notification
last_dismissed_update: ""             # version the user clicked "later" on
```

### Per-repo config: `<repo>/.laiagit/repo.yaml`

Created when the user changes a per-repo default. Schema (`RepoConfig`):

```yaml
ai_backend: null                      # override default backend for this repo
auto_pilot: false                     # enable Auto-pilot button
default_branch: main                  # the branch this repo defaults to
preflight:
  block_secrets: true
  block_todos: false
  block_console_logs: false
  max_file_size_mb: 5
hidden_paths: []                      # files filtered out of LaiaGit's view
```

### Environment variables

```sh
# Optional — used by the API backend (anthropic provider)
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional — used by the API backend (openai provider)
export OPENAI_API_KEY="sk-..."

# Optional — relocate the install
export LAIAGIT_DIR="$HOME/code/laiagit"
```

---

## 6. AI backends — how to set up each

### Ollama (recommended for local/private)

```sh
# Install Ollama from https://ollama.com
ollama pull qwen2.5-coder:7b           # or mistral, llama3, etc.
ollama serve                           # runs on http://localhost:11434
```

In LaiaGit Settings → set default AI backend to *Ollama*. Model name
must match what you pulled.

### Claude Code CLI

```sh
# If you already have Claude Code installed and authenticated
which claude                           # must resolve
```

In LaiaGit Settings → set default AI backend to *Claude Code CLI*.

### Anthropic API

```sh
export ANTHROPIC_API_KEY="sk-ant-..."  # add to your shell rc
```

In LaiaGit Settings → API backend, provider = `anthropic`.

### OpenAI API

```sh
export OPENAI_API_KEY="sk-..."
```

In LaiaGit Settings → API backend, provider = `openai`.

### Adding a new backend (~150 lines of Python)

See `laiagit/services/ai_service.py` for the contract. Create a new
class in `laiagit/ai_backends/` that implements the same interface
(`commit_message(diff, repo_config) -> str` and
`resolve_conflict(file_content) -> str`). Register it in
`AIService.__init__`.

---

## 7. CI/CD & releases

### CI workflow: `.github/workflows/ci.yml`

Runs on every push to `main` and every PR:
- Python 3.11 + 3.12 matrix
- `ruff check .` + `ruff format --check .`
- `pytest -q`

CI must be green for any PR to merge (branch protection enforces this
unless an admin bypasses).

### Release workflow: `.github/workflows/release.yml`

Triggered by **`git push` of any tag matching `v*`**:
1. Three parallel jobs on `macos-latest`, `windows-latest`, `ubuntu-latest`.
2. Each installs Flutter 3.41.4 + Flet CLI + project deps.
3. Each runs `flet build {target}`.
4. macOS zips just the `.app` bundle (find under `build/macos/Build/Products/Release/*.app`).
5. Final job (`softprops/action-gh-release@v2`) creates a GitHub
   Release tagged with the same `v*`, attaches the three binaries,
   auto-generates release notes from PRs since the last tag.
6. Tags containing `-` (e.g. `v0.2.0-alpha`) are flagged as pre-release.

### Branch protection on `main`

Verified at handover (state on 2026-05-09):

- `required_pull_request_reviews.required_approving_review_count: 1`
- `required_pull_request_reviews.require_code_owner_reviews: true`
- `required_linear_history: true`
- `allow_force_pushes: false`
- `enforce_admins: false` ← admins can bypass with `--admin` flag

To merge a PR as admin (bypassing the review):
```sh
gh pr merge <NUMBER> --rebase --admin --delete-branch
```

To restore admin force-push temporarily (only if absolutely needed):
```sh
gh api -X PUT repos/laiadesk-app/LaiaGit/branches/main/protection \
  --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": true,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF
# do the force-push
# then run the same command again with allow_force_pushes: false
```

---

## 8. Update mechanism (in-app banner)

`laiagit/services/update_checker.py` polls
`https://api.github.com/repos/laiadesk-app/LaiaGit/releases/latest` on
every app launch, with a 4-second timeout. It is **non-blocking** and
**never raises** — any failure (offline, rate-limit, malformed JSON)
returns `None` and the banner stays hidden.

If a newer version is detected:
- `dashboard.update_banner_slot` is populated with the `UpdateBanner`.
- The user sees an amber banner above the dashboard with two CTAs:
  - *Download binary* → opens the GitHub release page.
  - *Update from source* → shows the exact `git pull && pip install -e .` command.
- Dismissing via × persists `last_dismissed_update = <latest_version>` to config so the banner stays hidden until a NEWER version comes out.
- Toggle via Settings → *Check for updates on startup*.

12 unit tests in `tests/test_update_checker.py` cover all failure
paths and version comparison edge cases (incl. pre-release semantics).

---

## 9. Known issues to fix on next session

### A. Push / merge sometimes appear to "do nothing" (high priority)

**Symptom:** user clicks Push or Merge, no error appears, but nothing
seems to have happened on the remote.

**Likely root cause:** GitPython's `remote.push(branch)` does NOT set
upstream tracking, and its return value (`PushInfoList`) contains
flags like `REJECTED`, `ERROR`, `NEW_HEAD` that we are NOT inspecting.
The current code in `laiagit/services/git_service.py:268` only joins
`pi.summary` strings:

```python
push_info = git_repo.remote(remote).push(branch)
messages = [pi.summary.strip() for pi in push_info if pi.summary]
return "; ".join(messages) or "ok"
```

This means a push that was actually rejected (non-fast-forward) or had
no upstream to push to can return `"ok"` to the UI even though nothing
was pushed.

**Debugging starting points for next session:**

1. Reproduce: from a feature branch with no upstream, click Push in
   LaiaGit → check what the remote actually has via `git ls-remote
   origin <branch>`.
2. Check `pi.flags` against `git.PushInfo.ERROR` /
   `git.PushInfo.REJECTED` / `git.PushInfo.REMOTE_REJECTED` and raise
   `GitError` when any of those bits is set.
3. Add upstream support: if `branch.tracking_branch()` is `None`, call
   `remote.push(refspec=f"{branch}:{branch}", set_upstream=True)`.
4. Surface `pi.summary` even when the flag indicates failure (it
   usually contains the rejection reason).

A proposed patch outline (ready to apply):

```python
def push(self, path, remote="origin", branch=None) -> str:
    git_repo = self.open(path)
    if not git_repo.remotes:
        raise GitError("Repository has no configured remote")
    branch = branch or git_repo.active_branch.name
    head = git_repo.heads[branch]
    set_upstream = head.tracking_branch() is None
    try:
        push_info_list = git_repo.remote(remote).push(
            refspec=f"{branch}:{branch}",
            set_upstream=set_upstream,
        )
    except GitCommandError as exc:
        raise GitError(str(exc)) from exc
    failures = [
        pi for pi in push_info_list
        if pi.flags & (pi.ERROR | pi.REJECTED | pi.REMOTE_REJECTED)
    ]
    if failures:
        raise GitError(
            "; ".join(pi.summary.strip() or "rejected" for pi in failures)
        )
    return "; ".join(pi.summary.strip() for pi in push_info_list if pi.summary) or "ok"
```

5. **For merge:** `_merge` in `repo_panel.py:919` calls `checkout_branch(target)` which auto-stashes. If the user is *already on the target branch* (rare but possible — the dropdown might let you pick the current branch), the checkout is a no-op but `begin_merge(source)` then tries to merge a branch into itself, which produces "Already up to date" and silently succeeds. Worth confirming the dropdown excludes the current branch.

6. Whenever this is fixed, **add a regression test** in `tests/test_git_service.py` using a real temp git repo with an upstream pointing to a bare repo (you can create one with `pygit2` or just `git init --bare`). The test should assert that pushing a branch without upstream BOTH (a) sets the upstream and (b) returns success, and that pushing a non-fast-forward returns `GitError`.

### B. Backup branches still on disk

After confirming `v0.1.0-alpha` and forward have been working for a
week or so:

```sh
git branch -D backup/main backup/feat-initial backup/chore-public-release-polish
```

### C. Code signing (cosmetic friction, not a bug)

macOS binaries say *"unidentified developer"*. Windows binaries trip
SmartScreen. Documented in `docs/RELEASE.md`. Not blocking — workaround
in README. If/when sponsored: `MACOS_CERT_P12`, `MACOS_CERT_PASSWORD`,
`WINDOWS_CERT_PFX` secrets + four lines added to release.yml.

### D. Auto-update is Tier 1 only

The in-app banner notifies but does not auto-replace the binary. To
upgrade Tier 2 → Tier 3, see *"Tres niveles de auto-update"* in the
chat history (search for *"Sparkle"*); essentially requires code
signing first.

---

## 10. Roadmap (verbatim from README)

### v0.2 — Search & batch
- Search/filter across repos
- Batch commit-all / push-all / fetch-all
- Multi-repo `git pull --all-mine`
- Promote *Add to .gitignore* and *Hide from view* to cross-repo bulk

### v0.3 — Agent-aware mode + LaiaDesk integration ⭐ **sticky hook**
- Per-repo agent assignments (which AI per repo, with rate-limit awareness)
- Agent-driven branch tagging
- Notification panel for "agent X opened a PR in repo Y"
- **LaiaDesk model included free** for platform users (5th backend)
- **Auto-sync to LaiaDesk Tasks/Projects modules** — commits, PRs,
  merges, pre-flight blocks logged automatically as activity entries
  on the right ticket

### v0.4 — Workspaces
- Multiple grouped dashboards (clients/, internal/, experiments/)
- Per-workspace AI defaults and pre-flight rules

### v0.5 — i18n + signed binaries
- Spanish first, then community translations
- macOS notarisation + Windows code signing

Full plan: `docs/plans/2026-05-01-laiagit-roadmap.md`.

---

## 11. Useful one-liners

```sh
# Where is everything?
LAIAGIT="/Users/juancarlosrodriguez/NexoSmart-repo/LaiaGit"

# Run from source, latest main
cd $LAIAGIT && git pull && .venv/bin/pip install -q -e . && \
  .venv/bin/python -m laiagit

# Tests + lint in one shot
cd $LAIAGIT && .venv/bin/pytest -q && .venv/bin/ruff check .

# Compile macOS binary locally (requires Xcode + CocoaPods)
cd $LAIAGIT && .venv/bin/flet build macos && \
  open build/macos/Build/Products/Release/LaiaGit.app

# See what's in main since last release
cd $LAIAGIT && git log v0.1.1..main --oneline

# Cut next release (replace 0.1.2)
cd $LAIAGIT && git tag -a v0.1.2 -m "v0.1.2" && \
  git push origin v0.1.2

# View the pipeline run for a tag
gh run list --workflow=release.yml --limit 5

# Check release downloads
gh release view v0.1.1 --json assets \
  -q '.assets[] | "\(.name): \(.downloadCount) downloads"'

# Check open issues / discussions
gh issue list --repo laiadesk-app/LaiaGit
gh api repos/laiadesk-app/LaiaGit/discussions \
  --jq '.[] | "\(.number) | \(.title)"'

# Branch backup cleanup (only after confidence)
cd $LAIAGIT && git branch -D backup/main \
  backup/feat-initial backup/chore-public-release-polish

# In-app banner reset (force re-show on next launch)
sed -i '' 's/last_dismissed_update:.*$/last_dismissed_update: ""/' \
  ~/.laiagit/config.yaml
```

---

## 12. Marketing assets (drafts ready to use)

- VEO3 prompt for "el caos sin LaiaGit" (8s) — saved in chat history.
- VEO3 prompt for "la solución" (8s) — saved in chat history.
- LinkedIn / Twitter / TikTok / Instagram captions — saved in chat history.

If you re-run a session without the chat history, regenerate from the
README's *"Why this is different"* section as the source of truth.

---

## 13. The LaiaDesk integration (v0.3) — sticky conversion hook

The `info@laiadesk.com` README CTA is the funnel into:

- **A 5th AI backend, free for LaiaDesk customers**: same prompt
  contract as the other four, no API keys to manage.
- **Auto-logging into LaiaDesk Tasks/Projects modules**: commits,
  PRs, merges, pre-flight blocks become activity entries against the
  right project and task automatically.

When you build this in v0.3, the integration points are:

1. New backend class in `laiagit/ai_backends/laiadesk_backend.py`
   following the same contract as `OllamaBackend`.
2. Auth: OAuth flow against LaiaDesk's API — store the token in
   `~/.laiagit/config.yaml` (encrypted via Keychain on macOS).
3. New service `laiagit/services/laiadesk_sync.py` that takes
   commit/push/merge events from `git_service.py` and POSTs them to
   the LaiaDesk activity ingestion endpoint (define the schema with
   the LaiaDesk team).
4. Settings UI: per-repo "Linked LaiaDesk project" dropdown.

Read README's "Coming soon" callout for the marketing language we've
already committed to publicly.

---

## 14. Closing notes

- The repo is **public, MIT, zero telemetry**. No analytics events leave the user's machine.
- All 64 tests pass on `main` as of handover. Do not regress this.
- Branch protection is your safety net — bypass only with `--admin` and only with intent.
- The README is the single source of marketing truth. If you change positioning, change it there first.
- Backup branches `backup/*` are intentionally kept until you're confident the current state is stable. Don't be in a hurry to delete them.

If you re-enter the project from a fresh session, this document plus
the README + `docs/plans/2026-05-01-laiagit-roadmap.md` are sufficient
to pick up exactly where things left off. Welcome back.
