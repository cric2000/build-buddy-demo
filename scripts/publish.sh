#!/usr/bin/env bash
set -euo pipefail
: "${SVG_DIR:?Set SVG_DIR}"
: "${BADGE_REPO:?Set BADGE_REPO}"
# Refuse incomplete output instead of publishing an old or misleading live image.
python3 - "$SVG_DIR" <<'PY'
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
root = Path(sys.argv[1])
summary = json.loads((root / 'results.json').read_text())
assert summary['selected_status'] in ('queued', 'running', 'passing', 'failing', 'unknown')
assert (root / 'mascot.svg').read_bytes() == (root / f"{summary['selected_status']}.svg").read_bytes()
for path in root.glob('*.svg'):
    svg = ET.parse(path).getroot()
    assert svg.get('data-character') == 'chopper', path
PY
if git show-ref --verify --quiet refs/remotes/origin/badge-artifact; then
  git worktree add --detach "$BADGE_REPO" origin/badge-artifact
else
  git worktree add --detach "$BADGE_REPO"
  git -C "$BADGE_REPO" switch --orphan badge-artifact
fi
# A single-state run changes its own snapshot and the selected image; other gallery states remain.
cp "$SVG_DIR"/*.svg "$BADGE_REPO/"
cp "$SVG_DIR/results.json" "$BADGE_REPO/"
git -C "$BADGE_REPO" add -- '*.svg' results.json
if ! git -C "$BADGE_REPO" diff --cached --quiet; then
  git -C "$BADGE_REPO" -c user.name='github-actions[bot]' \
    -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
    commit -m "Publish Chopper demo snapshots [skip ci]"
  git -C "$BADGE_REPO" push origin HEAD:refs/heads/badge-artifact
fi

# Pin README URLs to the complete artifact commit so image caches cannot show an older run.
artifact_sha=$(git -C "$BADGE_REPO" rev-parse HEAD)
git fetch origin main
git switch --detach origin/main
python3 scripts/update_readme.py --artifact-sha "$artifact_sha" --results "$SVG_DIR/results.json"
git add README.md
if ! git diff --cached --quiet; then
  git -c user.name='github-actions[bot]' \
    -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
    commit -m "Update Chopper README result [skip ci]"
  git push origin HEAD:refs/heads/main
fi
