#!/bin/sh
# LaiaGit installer — clones (or updates) the source and prepares a venv
# so you can run LaiaGit from source. Designed for developers who already
# have git + python3.11+ on their machine.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/laiadesk-app/LaiaGit/main/scripts/install.sh | sh
#
# Override the install location:
#   LAIAGIT_DIR=~/code/laiagit curl -fsSL ... | sh
#
# After install, run with:
#   ~/.laiagit-src/.venv/bin/python -m laiagit
#
# Or add to your shell rc:
#   alias laiagit='~/.laiagit-src/.venv/bin/python -m laiagit'

set -eu

DIR="${LAIAGIT_DIR:-$HOME/.laiagit-src}"
REPO="https://github.com/laiadesk-app/LaiaGit.git"

require() {
    cmd="$1"
    msg="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        printf '\033[31m✗ %s\033[0m\n' "$msg" >&2
        exit 1
    fi
}

require git "git not found. Install git first (https://git-scm.com)."
require python3 "python3 not found. Install Python 3.11+ first."

# Verify Python version is 3.11+
PY_OK=$(python3 -c 'import sys; print(1 if sys.version_info >= (3,11) else 0)')
if [ "$PY_OK" != "1" ]; then
    PY_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    printf '\033[31m✗ Python %s detected. LaiaGit needs 3.11 or newer.\033[0m\n' "$PY_VER" >&2
    exit 1
fi

if [ -d "$DIR/.git" ]; then
    printf '→ Updating LaiaGit at %s\n' "$DIR"
    cd "$DIR"
    git fetch --quiet origin
    git checkout --quiet main
    git pull --ff-only --quiet
else
    printf '→ Cloning LaiaGit into %s\n' "$DIR"
    git clone --depth 50 --branch main "$REPO" "$DIR"
    cd "$DIR"
fi

if [ ! -d ".venv" ]; then
    printf '→ Creating virtualenv at %s/.venv\n' "$DIR"
    python3 -m venv .venv
fi

printf '→ Installing dependencies (editable)\n'
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e .

VERSION=$(.venv/bin/python -c 'import laiagit; print(laiagit.__version__)' 2>/dev/null || echo "?")

printf '\n\033[32m✓ LaiaGit %s installed at %s\033[0m\n' "$VERSION" "$DIR"
printf '\nRun with:\n'
printf '  %s/.venv/bin/python -m laiagit\n' "$DIR"
printf '\nTip — add an alias to your shell:\n'
printf "  alias laiagit='%s/.venv/bin/python -m laiagit'\n" "$DIR"
printf '\nUpdate later with:\n'
printf '  %s/scripts/update.sh\n' "$DIR"
