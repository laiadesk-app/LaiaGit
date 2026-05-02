#!/bin/sh
# Pull the latest LaiaGit and reinstall dependencies in the editable venv.
# Run from inside the cloned repo, or set LAIAGIT_DIR to its path.

set -eu

DIR="${LAIAGIT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$DIR"

if [ ! -d ".git" ]; then
    printf '\033[31m✗ %s does not look like a LaiaGit checkout (no .git here).\033[0m\n' "$DIR" >&2
    printf 'Set LAIAGIT_DIR to the directory you cloned into.\n' >&2
    exit 1
fi

printf '→ Pulling main\n'
git fetch --quiet origin
git checkout --quiet main
git pull --ff-only --quiet

if [ ! -d ".venv" ]; then
    printf '→ Creating virtualenv\n'
    python3 -m venv .venv
fi

printf '→ Reinstalling deps\n'
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e .

VERSION=$(.venv/bin/python -c 'import laiagit; print(laiagit.__version__)' 2>/dev/null || echo "?")
printf '\n\033[32m✓ Now running LaiaGit %s\033[0m\n' "$VERSION"
printf 'Launch with: %s/.venv/bin/python -m laiagit\n' "$DIR"
