# Contributing to LaiaGit

Thanks for your interest in improving LaiaGit.

## Workflow

1. **Fork** the repository.
2. Create a branch in your fork (`feat/your-feature` or `fix/your-bug`).
3. Make changes. Keep them focused — one logical change per PR.
4. Add or update tests where applicable.
5. Run the test suite locally and ensure it passes.
6. Open a Pull Request against `main`.

## Review process

- Every PR requires admin approval before merging.
- CI must pass (tests, lint).
- Stale approvals are dismissed when new commits are pushed — the PR will need re-review.
- Linear history only: PRs are squashed or rebased, no merge commits.

## What to contribute

- Bug fixes
- New AI backends (see `laiagit/ai_backends/base.py` for the contract)
- UI improvements
- Documentation
- Tests

For larger features, please open an issue first to discuss.

## Code style

- Python 3.11+
- Format with `ruff format`
- Lint with `ruff check`
- Type hints encouraged

## Reporting bugs

Open an issue with:
- Your OS and Python version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (no secrets, please)
