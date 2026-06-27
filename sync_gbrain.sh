#!/usr/bin/env bash
# Keep the gbrain knowledge graph in sync with the wiki.
#
# Run this after /ingest (or after editing wiki pages) so gbrain re-indexes
# the new/changed knowledge. It imports the knowledge folders, re-wires the
# [[wikilink]] graph, and embeds anything new — all local, no API keys.
#
# Usage:
#   ./sync_gbrain.sh
#
# Requires: gbrain (via bun) on PATH, and the Ollama service running
# (brew services start ollama).

set -euo pipefail

export PATH="$HOME/.bun/bin:$PATH"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI="$HERE/wiki"

echo "→ Importing knowledge folders..."
gbrain import "$WIKI/concepts" --no-embed
gbrain import "$WIKI/source-summaries" --no-embed
# projects/ holds NUS module hub pages once /module has run; import if present
if ls "$WIKI/projects"/*.md >/dev/null 2>&1; then
  gbrain import "$WIKI/projects" --no-embed
fi

echo "→ Wiring the [[wikilink]] graph..."
gbrain config set link_resolution.global_basename true >/dev/null 2>&1 || true
gbrain extract links --source db

echo "→ Embedding new/changed pages (local Ollama)..."
gbrain embed --stale

echo "→ Done. Current graph:"
gbrain stats | sed -n '1,6p'
