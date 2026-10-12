#!/usr/bin/env bash
# publish-report.sh — regenerate results/report.html from the local pool and
# push it to the gh-pages branch, where GitHub Pages serves it as the public
# scoreboard (https://<owner>.github.io/<repo>/).
#
# The pool with the raw receipts stays local (gitignored): only the rendered
# single-file report goes public. Safe to re-run any time; force-pushes
# gh-pages with a fresh orphan commit every time.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REPORT="$REPO_ROOT/results/report.html"

# 1. fresh render from the local pool (package import needs the parent dir,
#    same rule as every other command: see AGENTS.md §Commands)
cd "$REPO_ROOT/.."
python3 -m ggufbench.html_report
[ -f "$REPORT" ] || { echo "no report at $REPORT (empty pool?)"; exit 1; }

# 2. ship it as the gh-pages root: temp repo, orphan branch, one file
SLUG="$(git -C "$REPO_ROOT" remote get-url origin | sed -E 's#.*github\.com[:/]##; s#\.git$##')"
MAIN_SHA="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp "$REPORT" "$TMP/index.html"
git -C "$TMP" init -q
git -C "$TMP" checkout -q -b gh-pages
git -C "$TMP" add index.html
git -C "$TMP" commit -q -m "publish: scoreboard report $(date -u '+%Y-%m-%d %H:%M UTC') (main $MAIN_SHA)"
git -C "$TMP" remote add origin "$(git -C "$REPO_ROOT" remote get-url origin)"
git -C "$TMP" push -q --force origin gh-pages

echo "published → https://${SLUG%%/*}.github.io/${SLUG#*/} (main $MAIN_SHA)"
