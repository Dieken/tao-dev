#!/bin/sh
# Project-only skill deployment. Usage: ./install.sh --project /project --client codex
# A local checkout needs only Python; a downloaded script also needs Git to fetch source.
set -eu
python=
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,15) else 1)'; then
    python=$candidate
    break
  fi
done
if [ -z "$python" ]; then
  echo 'Python 3.11–3.14 is required; installation needs no pip or document packages.' >&2
  exit 2
fi
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
entry="$base/skills/tao-dev/scripts/tao.py"
if [ -f "$entry" ]; then
  exec "$python" -I -B "$entry" install "$@"
fi
command -v git >/dev/null 2>&1 || { echo 'Git is required to fetch the remote skill source.' >&2; exit 2; }
work=$(mktemp -d "${TMPDIR:-/tmp}/tao-install.XXXXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
git clone --quiet --depth 1 https://github.com/Dieken/tao-dev.git "$work/source"
"$python" -I -B "$work/source/skills/tao-dev/scripts/tao.py" install "$@"
