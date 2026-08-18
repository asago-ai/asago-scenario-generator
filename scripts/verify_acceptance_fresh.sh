#!/usr/bin/env bash
# Reconstruct the acceptance suite from a throwaway copy of the current source.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
worktree="$root/tmp/acceptance-fresh"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
uv_bin="$(command -v uv || true)"
if [[ -z "$uv_bin" ]]; then
  echo "uv is not available on PATH" >&2
  exit 1
fi

cleanup() {
  rm -rf "$worktree"
}
trap cleanup EXIT

rm -rf "$worktree"
mkdir -p "$worktree"

rsync -a \
  --exclude '.git/' \
  --exclude 'build/' \
  --exclude 'tmp/' \
  --exclude 'output/' \
  --exclude '.venv/' \
  --exclude '.agents/' \
  --exclude '.beads/' \
  --exclude '.claude/' \
  --exclude '.codex/' \
  --exclude '.factory/' \
  --exclude '.swarmforge/' \
  --exclude 'acceptance/ir/' \
  --exclude 'acceptance/generated/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  "$root/" "$worktree/"

rm -rf "$worktree/acceptance/ir" "$worktree/acceptance/generated"

if [[ -e "$worktree/acceptance/ir" || -e "$worktree/acceptance/generated" ]]; then
  echo "fresh checkout still contains committed generated artifacts" >&2
  exit 1
fi

aps="${ASAGO_SCENARIO_GENERATOR_APS_ROOT:-}"
for candidate in \
  "$root/.cache/acceptance-pipeline-specification" \
  "$root/tmp/Acceptance-Pipeline-Specification"
do
  if [[ -z "$aps" && -d "$candidate" ]]; then
    aps="$candidate"
    break
  fi
done
if [[ -z "$aps" ]]; then
  echo "Acceptance-Pipeline-Specification clone not found; set ASAGO_SCENARIO_GENERATOR_APS_ROOT" >&2
  exit 1
fi

source_fingerprint() {
  (
    cd "$worktree"
    find features acceptance scripts CLAUDE.md pyproject.toml \
      -type f \
      ! -path 'acceptance/ir/*' \
      ! -path 'acceptance/generated/*' \
      ! -path '*/__pycache__/*' \
      | sort \
      | xargs shasum
  )
}

before="$(source_fingerprint)"
(
  cd "$worktree"
  ASAGO_SCENARIO_GENERATOR_APS_ROOT="$aps" uv run python acceptance/refresh_snapshot.py
  uv run pytest build/acceptance/generated/ -q --tb=no
)
after_first="$(source_fingerprint)"
if [[ "$before" != "$after_first" ]]; then
  echo "fresh generate changed committed source files" >&2
  diff -u <(printf '%s\n' "$before") <(printf '%s\n' "$after_first") >&2 || true
  exit 1
fi

(
  cd "$worktree"
  ASAGO_SCENARIO_GENERATOR_APS_ROOT="$aps" uv run python acceptance/refresh_snapshot.py
)
after_second="$(source_fingerprint)"
if [[ "$after_first" != "$after_second" ]]; then
  echo "second generate changed committed source files" >&2
  diff -u <(printf '%s\n' "$after_first") <(printf '%s\n' "$after_second") >&2 || true
  exit 1
fi

echo "fresh-checkout acceptance reconstruction passed"
