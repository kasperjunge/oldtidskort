#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"

uv run oldtidskort build fund_og_fortidsminder --refresh
uv run python scripts/build_runestone_research.py --refresh
uv run python scripts/build_static_site.py

release_dir="$(mktemp -d)"
trap 'rm -rf "$release_dir"' EXIT
cp -R .pages-dist/. "$release_dir/"

git -C "$release_dir" init --initial-branch=gh-pages --quiet
git -C "$release_dir" add .
git -C "$release_dir" \
  -c user.name="Kasper Junge" \
  -c user.email="kasperjunge@users.noreply.github.com" \
  commit --message="Deploy locally built Oldtidskort" --quiet
git -C "$release_dir" push --force "$(git remote get-url origin)" gh-pages

echo "GitHub Pages-buildet er publiceret fra gh-pages."
