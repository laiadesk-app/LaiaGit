# LaiaGit

> A simple visual desktop dashboard for managing all your local Git repositories — with AI that handles commit messages, merge conflicts, and pre-flight checks.

LaiaGit shows your repos as cards, lets you commit, push, and merge in one click, and uses AI (local or via API) to write commit messages and resolve merge conflicts.

## Status

Early development. Design phase complete — implementation starting.

## Planned features

- Visual dashboard of all local repos as cards with status colors
- One-click commit, push, and branch-to-branch merge
- AI-generated commit messages from your diff (editable before confirming)
- AI-assisted merge conflict resolution with a 3-panel review UI
- Pre-flight checks: detects secrets, TODOs, console.logs, large files before push
- Pluggable AI backends: Ollama (local), Claude Code CLI, or external API
- Per-repo configuration: choose AI engine, opt into auto-pilot mode, etc.
- Keyboard-first ergonomics (Linear-style shortcuts)

## Stack

- Python 3.11+
- [Flet](https://flet.dev) for the desktop UI
- GitPython for Git operations
- Ollama / Claude Code CLI / Anthropic API for AI

## Requirements (user-installed)

LaiaGit only detects what you already have:

- Git
- (Optional) [Ollama](https://ollama.com) with a model like `mistral` or `qwen2.5-coder`
- (Optional) Claude Code CLI
- (Optional) An Anthropic or OpenAI API key

## Installation

Coming soon.

## Contributing

Contributions are welcome via pull request from a fork. See [CONTRIBUTING.md](CONTRIBUTING.md).

All PRs require admin approval and a passing CI before merging.

## License

[MIT](LICENSE)
