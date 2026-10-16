#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
if [[ -x .venv/bin/python ]]; then
    exec .venv/bin/python horyhours_notes.py "$@"
fi

exec python3 horyhours_notes.py "$@"
