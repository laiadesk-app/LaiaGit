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
- [`tests/`](tests/) — 47 unit tests, real Git temp repos (no mocks), real config round-trips. The test patterns are reusable.

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

### Pre-built binaries (recommended)

Grab the asset for your OS from the [latest release](https://github.com/laiadesk-app/LaiaGit/releases/latest):

- **macOS** — `LaiaGit-macos.zip` → unzip → drag `LaiaGit.app` to *Applications*.
- **Windows** — `LaiaGit-windows.zip` → unzip → run `LaiaGit.exe`.
- **Linux** — `LaiaGit-linux.tar.gz` → untar → run the `LaiaGit` binary.

> Binaries are **unsigned** for now (signing certs are expensive — open
> a discussion if your org would sponsor signing). On macOS:
> right-click → *Open* the first time. On Windows: *More info → Run anyway*.

### From source (developers / contributors)

```bash
git clone https://github.com/laiadesk-app/LaiaGit.git
cd LaiaGit
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m laiagit
```

First launch creates `~/.laiagit/config.yaml`. Default root folder is
`~/dev` — change it from *Settings* or the folder picker.

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

## Roadmap

We're shipping in five short versions; full plan in
[`docs/plans/2026-05-01-laiagit-roadmap.md`](docs/plans/2026-05-01-laiagit-roadmap.md).

Highlights in flight:

- **v0.2** — search/filter across repos, batch operations (commit-all, push-all).
- **v0.3** — per-repo agent assignments (which AI backend per repo, with rate-limit awareness).
- **v0.4** — workspace concept (multiple grouped dashboards, per-workspace AI defaults).
- **v0.5** — i18n + signed binaries.

---

## About LaiaDesk

[LaiaDesk](https://laiadesk.com) builds AI agents for healthcare and
medtech operations — quality systems, regulatory affairs, ISMS, clinical
documentation, and the day-to-day code that supports them. We work
across many repositories, with many agents, and with many strict
compliance constraints. The internal tooling we built to keep that
working is **part of what makes the product possible**.

LaiaGit is one slice of that tooling, given back. We hope it helps
you, and if it does, we'd love to hear about it — open a discussion,
star the repo, or just drop us a note at
[`info@laiadesk.com`](mailto:info@laiadesk.com).

---

## License

[MIT](LICENSE) — fork it, modify it, ship it, sell it, study it. No
strings. If you build something cool on top, we'd love a link back.
