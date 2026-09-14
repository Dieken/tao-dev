#!/bin/sh
# Only locate Python and forward arguments; runtime.py owns environment policy.
set -eu
target=${1:-cli}
shift || true
case "$target" in
  cli) entry=tao.py ;;
  hook) entry=hook.py ;;
  validate) entry=validate_documents.py ;;
  *) echo "Unknown tao entry point." >&2; exit 2 ;;
esac
if [ "$target" = hook ]; then
  project=$PWD
  while [ ! -f "$project/.tao/config.toml" ]; do
    if [ "$project" = / ]; then echo '{}'; exit 0; fi
    project=${project%/*}
    [ -n "$project" ] || project=/
  done
fi
directory=${0%/*}
[ "$directory" != "$0" ] || directory=.
scripts=$(CDPATH= cd -- "$directory" && pwd)
probe='import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 2)'
if [ -n "${TAO_PYTHON:-}" ]; then
  if "$TAO_PYTHON" -I -c "$probe" >/dev/null 2>&1; then
    exec "$TAO_PYTHON" -I -B "$scripts/$entry" "$@"
  fi
else
  for candidate in python3 python; do
    if "$candidate" -I -c "$probe" >/dev/null 2>&1; then
      exec "$candidate" -I -B "$scripts/$entry" "$@"
    fi
  done
  if py -3 -I -c "$probe" >/dev/null 2>&1; then
    exec py -3 -I -B "$scripts/$entry" "$@"
  fi
fi
if [ "$target" = hook ]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"tao docs not_run: Python 3.11+ is unavailable; configure TAO_PYTHON. No dependencies were installed."}}'
  exit 0
fi
echo '{"tool":"tao-dev","status":"not_run","diagnostics":[{"rule_id":"TAO-RUNTIME-001","message":"Python 3.11+ is unavailable; configure TAO_PYTHON."}]}'
exit 2
