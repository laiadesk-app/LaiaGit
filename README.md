# LaiaGit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/laiadesk-app/LaiaGit/actions/workflows/ci.yml/badge.svg)](https://github.com/laiadesk-app/LaiaGit/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/laiadesk-app/LaiaGit?style=social)](https://github.com/laiadesk-app/LaiaGit/stargazers)

> A visual desktop dashboard for managing all your local Git repositories — with AI that writes your commit messages, resolves merge conflicts, and runs pre-flight checks before you push.

LaiaGit shows every repo under your dev folder as a single-line card. Commit, push, and merge happen with one click. AI fills in the boring parts (writing messages, resolving conflicts) — you stay in control.

## What it does

- **One-line panel per repo** with status, branch, pending changes, and inline actions.
- **AI-generated commit messages** in Conventional Commits format. If you click *Commit* with an empty field, it auto-generates one and commits in a single step.
- **AI-assisted merge conflict resolution**. The model proposes a resolution per file, you review or regenerate, then confirm.
- **Pre-flight checks** detect secrets (AWS, Anthropic, OpenAI, GitHub, etc.), TODOs, oversized files, and `console.log` calls before letting you push.
- **Per-repo defaults**: pick the default branch, the AI backend, opt into auto-pilot.
- **Custom ordering**: drag repos to your preferred sequence; persisted across sessions.
- **Hide/exclude** repos you don't want in the dashboard (without deleting them on disk).
- **Pluggable AI backends**: Ollama (fully local), Claude Code CLI, or Anthropic / OpenAI APIs.

## Stack

- Python 3.11+
- [Flet](https://flet.dev) for the desktop UI
- GitPython for git operations
- Ollama / Claude Code CLI / Anthropic / OpenAI for AI

## Requirements (you install your own)

LaiaGit only detects what's already on your machine:

- **Git**
- *(Optional)* [Ollama](https://ollama.com) with a model like `qwen2.5-coder:7b` or `mistral`
- *(Optional)* [Claude Code CLI](https://docs.claude.com/en/docs/claude-code)
- *(Optional)* `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in your env

## Installation (development build)

```bash
git clone https://github.com/laiadesk-app/LaiaGit.git
cd LaiaGit
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m laiagit
```

The first launch creates `~/.laiagit/config.yaml`. Default root folder is `~/dev` — change it from Settings or via the folder picker.

> Pre-built binaries (.dmg / .exe / .AppImage) are coming once we cut the first stable release.

## Quick tour

1. **Dashboard**: every repo as a single line. Pending changes shown as an amber chip with an expand toggle.
2. **Click ✨** next to a commit field → AI writes the message based on your staged diff.
3. **Click Commit** with the field empty → AI writes the message AND commits in one step.
4. **Pick a source branch + click "Merge into main"** → if there are conflicts, the AI conflict resolver opens.
5. **Click 👁‍🗨** on a repo to hide it from the dashboard (the repo on disk is untouched).
6. **Settings** → root folder, additional paths, default AI backend, pre-flight rules.

## Contributing

Contributions are welcome. The workflow:

1. **Fork** the repository.
2. Create a branch in your fork: `feat/your-feature` or `fix/your-bug`.
3. Make focused changes, add tests where applicable.
4. Run `pytest`, `ruff check .`, `ruff format --check .` — they all need to be green.
5. Open a Pull Request against `main`.

Every PR must pass CI and be approved by a code owner before merging. Squash and rebase merges only — no merge commits.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details, [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards, and [SECURITY.md](SECURITY.md) for reporting security issues.

If you're new and want to help, look for issues labeled `good first issue` or `help wanted`.

## Roadmap

See [docs/plans/2026-05-01-laiagit-roadmap.md](docs/plans/2026-05-01-laiagit-roadmap.md) for the five-version plan.

## License

[MIT](LICENSE) — feel free to fork, modify, ship, sell, study.
