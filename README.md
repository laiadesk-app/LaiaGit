# LaiaGit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/laiadesk-app/LaiaGit/actions/workflows/ci.yml/badge.svg)](https://github.com/laiadesk-app/LaiaGit/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/laiadesk-app/LaiaGit?include_prereleases)](https://github.com/laiadesk-app/LaiaGit/releases)
[![GitHub stars](https://img.shields.io/github/stars/laiadesk-app/LaiaGit?style=social)](https://github.com/laiadesk-app/LaiaGit/stargazers)
[![Discussions](https://img.shields.io/github/discussions/laiadesk-app/LaiaGit)](https://github.com/laiadesk-app/LaiaGit/discussions)

> **A visual desktop dashboard that turns "managing 30 repos" into a 5-second
> glance** — with AI that writes your commit messages, resolves merge
> conflicts, and runs pre-flight checks before you push.

---

## ✨ Why this is different

There are dozens of git clients. There are dozens of AI coding tools.
**LaiaGit is the only thing that does both, in one window, with the AI
*you* choose.**

### 🗂️ Built for many repos at once

One window, every repo under your dev folder, **single-line panels with
status, branch and inline actions**. Commit, push, merge, refresh **per
repo or batch**, without losing context. Custom ordering, hide noisy
projects, per-repo defaults — designed from day one for **30+
repositories**, not a single project.

### 🔌 Bring your own AI — already four backends shipped

**LaiaGit ships open from day one with four AI backends**, so you're
never locked into one provider, one billing model, or one network
boundary. Same prompt contract across all of them — switch any time,
per-repo or globally.

| Backend | Why pick it |
|---|---|
| **[Ollama](https://ollama.com)** (local) | Fully on-device, free, private — your diffs never leave your machine |
| **[Claude Code CLI](https://docs.claude.com/en/docs/claude-code)** | If you're already using it elsewhere, reuse the same auth |
| **Anthropic API** (`ANTHROPIC_API_KEY`) | Best quality for commit messages and conflict resolution |
| **OpenAI API** (`OPENAI_API_KEY`) | Drop-in if your org standardised on it |

Switch backend per-repo or globally from *Settings*. Add a new one in
~150 lines of Python — see [`laiagit/services/ai_service.py`](laiagit/services/ai_service.py).

> #### 🎁 Coming soon — **LaiaDesk model + auto activity logging**, free for platform users
>
> A fifth backend is on its way: **LaiaDesk's own model, included free**
> with any [LaiaDesk platform](https://laiadesk.com) account — no API
> keys, no separate billing, no extra setup. Sign in to your LaiaDesk
> workspace from LaiaGit and the model is ready.
>
> **And here's the part nobody else is doing.** When the LaiaDesk
> backend is connected, LaiaGit auto-syncs with the **Tasks** and
> **Projects** modules of your workspace:
>
> - Significant commits, PRs, merge resolutions and pre-flight blocks
>   are **logged automatically as activity entries** on the right
>   project and the right task.
> - No manual time-tracking. No stale Jira tickets. No "what did I do
>   yesterday" mid-standup.
> - Your engineering work shows up next to your team's tasks where
>   leadership, PMs, QA and regulatory already look — without anyone
>   asking you to fill in another form.
>
> If you're already on LaiaDesk, this turns LaiaGit from "useful
> standalone tool" into **the missing link between your code and your
> operational backbone** — for free. If you're not on LaiaDesk yet, the
> open-source app stays fully usable forever; this is just the extra
> superpower you unlock if/when you join the platform.
>
> *Targeted for v0.3. Want early access? [Open a discussion](https://github.com/laiadesk-app/LaiaGit/discussions)
> or write `info@laiadesk.com` — we're picking the first cohort of
> integration testers now.*

### 🛡️ Pre-flight catches what AI agents leak

When AI tools (Cursor, Claude Code, Copilot, agents) generate code, they
sometimes hardcode tokens, leave `console.log("DEBUG", apiKey)` in,
include 200 MB dumps, or miss `TODO` markers. **LaiaGit blocks the push
before any of that lands on the remote.** AWS / Anthropic / OpenAI /
GitHub secret patterns out of the box, fully extensible.

---

## A contribution from LaiaDesk to the developer community

LaiaGit is a **gift** from the team behind [LaiaDesk](https://laiadesk.com).
It's one of the **internal layers we use to build, run, and observe our
own AI agents** — generalised, stripped of LaiaDesk-specific glue, and
released under the MIT license so anyone can use it, study it, fork it,
or build on top of it.

If you've ever wondered *"how does a team running multiple AI agents
actually keep their code organised across dozens of repos?"* — this is a
working answer. We're publishing the layer that handles **multi-repo
code control**, the same pattern we use day-to-day to coordinate
features, fixes, and experiments across our agent stack.

We believe the best way to advance AI tooling is to **publish what
works**. This is one of several layers we plan to open up. We'd love
your help making them better.

---

## Why this exists

Modern dev teams — and especially teams working with AI agents — don't
have *one* repo. They have **many**: a backend, a frontend, a few
shared libraries, a handful of experimental forks, an internal tools
project, an infra repo. Switching between them is friction. Knowing
which ones have uncommitted work, which ones are behind `main`, which
ones have conflicts — that's mental load that compounds across your day.

LaiaGit removes that friction. **One window, one row per repo, one
click per action**. The boring stuff (writing a sensible commit
message, resolving a trivial three-way merge, catching a leaked API
key before push) is handled by AI you can configure — local
([Ollama](https://ollama.com)), via [Claude Code CLI](https://docs.claude.com/en/docs/claude-code),
or through Anthropic / OpenAI API keys you already have.

You stay in control. The AI proposes; you confirm.

---

## What it does

| Feature | What you get |
|---|---|
| **Single-line repo panels** | Every repo under your dev folder, status colour-coded, branch + pending changes + actions inline. |
| **AI commit messages** | Click ✨ to fill the field, or click *Commit* on an empty field for one-step generate-and-commit. Conventional Commits format. |
| **AI merge conflict resolution** | Per-file 3-panel review (theirs / ours / proposed). Regenerate or edit before accepting. |
| **Pre-flight checks** | Block pushes that contain AWS / Anthropic / OpenAI / GitHub secrets, oversized files, stray `console.log`s, or `TODO` markers. |
| **Per-repo Fetch + single-repo Refresh** | One click to `git fetch origin` (so you see if you're behind) or to re-hydrate the local state of a single repo — no full rescan, no flicker on the other 29 panels. |
| **Bulk file actions (no AI required)** | Multi-select files in the changes list and either *Add to .gitignore* (writes a literal entry per path, deduped) or *Hide from view* (per-repo config — your files on disk are NEVER touched, just removed from this dashboard). |
| **Custom ordering** | Reorder repos with a click; persisted across sessions. Move-to-top, move-up, move-down, move-to-bottom. |
| **Hide repos** | Exclude noisy or archived projects from the dashboard without deleting them on disk. |
| **Per-repo defaults** | Default branch, AI backend, auto-pilot opt-in — configured once per repo. |
| **Pluggable AI** | Ollama (local, free, private), Claude Code CLI, Anthropic API, OpenAI API. Switch any time. |
| **Zero telemetry** | LaiaGit ships **no** analytics, no phone-home, no tracking. Your code never leaves your machine unless *you* call an external API. |

---

## What's inside (and worth studying)

LaiaGit is intentionally a **small, readable codebase** (~3 kLOC) so
it can serve as a reference for how to structure this kind of tool.
Worth a look if you're building something similar:

- [`laiagit/services/git_service.py`](laiagit/services/git_service.py) — thin wrapper around GitPython with the operations that actually matter (status, stage, commit, push, merge, stash, branch list/switch). No leaky abstraction over plumbing — just porcelain you'd actually use.
- [`laiagit/services/ai_service.py`](laiagit/services/ai_service.py) — pluggable AI backend with the **same prompt contract** across Ollama / Claude / Anthropic / OpenAI. The interesting bit is how we keep the model-agnostic prompt small and load context (diff, file tree, branch state) deterministically.
- [`laiagit/services/preflight.py`](laiagit/services/preflight.py) — the secret-scanning regex set + size/TODO/log-call detection. Tiny, focused, easy to extend.
- [`laiagit/services/repo_scanner.py`](laiagit/services/repo_scanner.py) — recursive `.git` discovery with exclusion sets and progressive hydration so a 50-repo dashboard doesn't block on the first paint.
- [`laiagit/ui/dashboard.py`](laiagit/ui/dashboard.py) — the orchestrator: phased UI (skeleton → hydrate → reorder), threading model, in-place reorder vs. full refresh.
- [`laiagit/ui/components/repo_panel.py`](laiagit/ui/components/repo_panel.py) — single-row component with all per-repo actions; canonical example of how we keep complex UI state local and side-effects explicit.
- [`tests/`](tests/) — ~60 unit tests, real Git temp repos (no mocks), real config round-trips. The test patterns are reusable.

The architecture is described in [`docs/laiagit_design.md`](docs/laiagit_design.md)
and the version-by-version plan in [`docs/plans/2026-05-01-laiagit-roadmap.md`](docs/plans/2026-05-01-laiagit-roadmap.md).

---

## Stack

- **Python 3.11+** — the whole thing is one Python package.
- [**Flet**](https://flet.dev) — Flutter-based desktop UI without writing Dart. Compiles to native `.app` / `.exe` / Linux binary.
- **GitPython** — Git operations, no shelling out.
- **Ollama / Claude Code CLI / Anthropic / OpenAI** — pluggable AI backends.

---

## Install

There are three ways, depending on whether you're a curious user or a
developer who wants to live on `main`.

### Option 1 — One-liner installer (developers, recommended)

If you have `git` and `python3` (3.11+), this is the fastest way and the
one we recommend if you want **automatic updates by `git pull`**. LaiaGit
will tell you when a new version is out and offer to update from source
in one click.

```bash
curl -fsSL https://raw.githubusercontent.com/laiadesk-app/LaiaGit/main/scripts/install.sh | sh
```

That clones to `~/.laiagit-src`, sets up a virtualenv, installs
LaiaGit in editable mode, and prints the launch command. Update later
with `~/.laiagit-src/scripts/update.sh` or by clicking *"Update from
source"* on the in-app banner.

> Want it elsewhere? `LAIAGIT_DIR=~/code/laiagit curl ... | sh`.

### Option 2 — Pre-built binary

Grab the asset for your OS from the
[latest release](https://github.com/laiadesk-app/LaiaGit/releases/latest):

- **macOS** — `LaiaGit-macos.zip` → unzip → drag `LaiaGit.app` to *Applications*.
- **Windows** — `LaiaGit-windows.zip` → unzip → run `LaiaGit.exe`.
- **Linux** — `LaiaGit-linux.tar.gz` → untar → run the `LaiaGit` binary.

LaiaGit checks GitHub for newer releases on launch and shows a banner
when one is available. **You still download the new binary manually** —
true auto-update needs code signing, which we haven't paid for yet.

> Binaries are **unsigned** for now. On macOS: right-click → *Open* the
> first time. On Windows: *More info → Run anyway*.
> Sponsoring signing certs ($300-600/year)? Open a discussion.

### Option 3 — Manual clone (contributors)

```bash
git clone https://github.com/laiadesk-app/LaiaGit.git
cd LaiaGit
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m laiagit
```

First launch creates `~/.laiagit/config.yaml`. Default root folder is
`~/dev` — change it from *Settings* or the folder picker.

### Update notifications

Every time you launch LaiaGit, it asks the GitHub Releases API
(non-blocking, never raises) whether there's a newer version. If so, an
amber banner appears with two buttons:

- *Download binary* — opens the Releases page in your browser.
- *Update from source* — shows the exact `git pull && pip install -e .`
  command, ready to copy.

Dismiss it for the current version with the **×** button; it stays
hidden until a newer version exists. Toggle the whole feature off in
*Settings → Check for updates on startup*.

---

## Quick tour

1. **Dashboard** — every repo as a single line. Amber chip = pending changes; click to expand.
2. **Click ✨** next to a commit field → AI writes the message based on your staged diff.
3. **Click *Commit*** with the field empty → AI writes the message *and* commits in one step.
4. **Pick a target branch + click "Merge {current} into {target}"** → if there are conflicts, the AI conflict resolver opens automatically.
5. **Reorder** — click the ≡ menu on any repo to move it; the order is saved.
6. **Hide** — 👁‍🗨 button removes a repo from the dashboard (it stays on disk).
7. **Settings** — root folder, extra paths, default AI backend, pre-flight rules.

---

## We want collaborators

LaiaGit is **early** and that's the point — there's a lot of room to
shape it, and we'd much rather build it *with* you than *for* you. If
any of these sound like you, please come in:

- **You manage many repos** and feel the pain LaiaGit solves. File issues for the workflows it doesn't cover yet.
- **You build with AI agents** and want the multi-repo control layer to be richer (per-repo agent assignments, agent-driven branches, batch ops). Open a discussion — we have ideas and want yours.
- **You like Flet / Python desktop UIs** and want a real-world codebase to contribute to. Most components are ~150 lines, friendly to refactor.
- **You care about secure-by-default tooling.** The pre-flight scanner is the highest-leverage place to harden — more rule packs welcome.
- **You speak a language we don't yet support.** i18n is on the roadmap; help us seed it.
- **You're a designer.** Single-row repo cards still have headroom (icons, density, dark theme nuance).

### How to contribute

1. **Browse open issues** — look for `good first issue` or `help wanted` labels.
2. **Or open a discussion** at [github.com/laiadesk-app/LaiaGit/discussions](https://github.com/laiadesk-app/LaiaGit/discussions) before coding anything substantial — we'd love to align early.
3. **Fork → branch → PR.** See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow, [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community norms, [SECURITY.md](SECURITY.md) for vulnerability reports.
4. **Tests + lint required.** `pytest`, `ruff check .`, `ruff format --check .` must all pass. CI runs them on every PR.
5. **Squash or rebase only** — no merge commits. Branch protection enforces linear history on `main`.

If you're not sure where to start, **post in Discussions and say hi** — one of us will point you at something.

---

## What's new

### Latest on `main` (unreleased — pull from source to try)

- 📥 **Per-repo Fetch button.** New cloud-download icon on every repo
  row runs `git fetch origin` and re-hydrates the panel so the
  ahead/behind counters reflect remote state. No merge, no surprises.
- ✂️ **Bulk file actions without AI.** Tick the files you want and the
  selection toolbar offers *Add to .gitignore* (writes a literal
  pattern per file, deduped against the existing file) or *Hide from
  view* (per-repo config; files on disk are **never** touched, only
  removed from this dashboard's body). Both are idempotent and
  scriptable.
- 🪟 **Modal dialogs actually close on Flet 0.84.** Migrated all three
  dialog sites (hide-repo confirm, file diff, update-from-source) to
  Flet 0.84's canonical `page.show_dialog` / `pop_dialog` API.
- ⚡ **In-place hide + per-repo refresh** (no full rescan; just the row
  in question redraws).

### v0.1.1 — last published release

- ✨ **Update notifications.** LaiaGit checks GitHub on launch and
  surfaces a banner when a newer version is out. One-click open the
  release page or copy the source-update command. Fully toggleable.
- 🚀 **One-liner installer** (`curl ... | sh`) for developers who want
  to track `main` directly.
- 🔧 Build pipeline finalised: `v0.1.0-alpha` and forward ship native
  binaries for macOS / Windows / Linux on every tag push.
- 🐛 Windows release build no longer chokes on flet's Unicode spinner.
- ⚡ Repo reordering is now in-place (no rescan, no git hydrate).

### Roadmap

Full plan in
[`docs/plans/2026-05-01-laiagit-roadmap.md`](docs/plans/2026-05-01-laiagit-roadmap.md).
Highlights:

- **v0.2 — Search & batch.** Search/filter across repos, batch
  commit-all / push-all / fetch-all, multi-repo `git pull --all-mine`.
  Promotes today's *Add to .gitignore* and *Hide from view* file-level
  actions to **cross-repo bulk** versions ("apply to all my repos").
  Adds the actions you'd otherwise script in bash.
- **v0.3 — Agent-aware mode + LaiaDesk integration.** First-class
  integration with AI agent workflows: per-repo agent assignments,
  agent-driven branch tagging, notification panel for "agent X opened a
  PR in repo Y". **Plus the LaiaDesk model as a built-in free backend
  for platform users**, with auto-sync to the LaiaDesk Tasks and
  Projects modules so your engineering activity logs itself onto the
  right tickets. This is where LaiaGit stops being a git client and
  starts being an agent control room — and, for LaiaDesk users, the
  bridge between code and operations.
- **v0.4 — Workspaces.** Multiple grouped dashboards (e.g.
  *clients/*, *internal/*, *experiments/*) with per-workspace AI
  defaults and pre-flight rules.
- **v0.5 — i18n + signed binaries.** Spanish first, then community
  translations. macOS notarisation + Windows code signing so first-run
  warnings disappear.

We move fast and ship small. If you want to influence what lands when,
**open a discussion** — we read all of them.

---

## About LaiaDesk

[LaiaDesk](https://laiadesk.com) builds AI agents for healthcare and
medtech operations — quality systems, regulatory affairs, ISMS, clinical
documentation, and the day-to-day code that supports them. We work
across many repositories, with many agents, and with many strict
compliance constraints. The internal tooling we built to keep that
working is **part of what makes the product possible**.

LaiaGit is one slice of that tooling, given back. **Use it forever, for
free, with the AI provider of your choice — that's the deal**, no
strings, no telemetry, no upgrade nags.

If you happen to *also* be a LaiaDesk customer, v0.3 will give you a
sticky bonus: our included model and auto-logging into your Tasks and
Projects modules, so your engineering activity ends up where the rest
of your team already works — without any manual time entry. That's our
way of saying *thank you* to the people who pay for the platform that
funds this work.

Want to try the platform? [laiadesk.com](https://laiadesk.com). Want to
star the repo, file an issue, or just say hi? Open a discussion or drop
us a note at [`info@laiadesk.com`](mailto:info@laiadesk.com).

---

## License

[MIT](LICENSE) — fork it, modify it, ship it, sell it, study it. No
strings. If you build something cool on top, we'd love a link back.
