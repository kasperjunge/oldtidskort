#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"

dry_run=false
verify_timeout=180

usage() {
  printf '%s\n' \
    "Brug: ./scripts/deploy_pages.sh [--dry-run] [--verify-timeout SEKUNDER]" \
    "" \
    "  --dry-run                  Hent, test og byg uden at pushe." \
    "  --verify-timeout SEKUNDER  Ventetid på live-sitet efter push (standard: 180)."
}

while (($#)); do
  case "$1" in
    --dry-run)
      dry_run=true
      shift
      ;;
    --verify-timeout)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      verify_timeout="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Ukendt argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ "$verify_timeout" =~ ^[0-9]+$ ]] || {
  printf '%s\n' "--verify-timeout skal være et helt antal sekunder." >&2
  exit 2
}

for command in git uv curl shasum; do
  command -v "$command" >/dev/null || {
    printf 'Mangler kommandoen: %s\n' "$command" >&2
    exit 1
  }
done

branch="$(git branch --show-current)"
[[ "$branch" == "main" ]] || {
  printf 'Deploy skal køres fra main; nuværende branch er %s.\n' "${branch:-detached HEAD}" >&2
  exit 1
}

origin_url="$(git remote get-url origin)"
git fetch --quiet origin main gh-pages
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || {
  printf '%s\n' "Lokale main er ikke identisk med origin/main. Commit/push eller pull først." >&2
  exit 1
}

if [[ -n "$(git status --short)" ]]; then
  printf '%s\n' "Bemærk: worktree indeholder lokale ændringer; de indgår i buildet."
fi

printf '%s\n' "Kører tests ..."
uv run --extra dev python -m pytest

printf '%s\n' "Henter friske kildedata ..."
uv run oldtidskort build fund_og_fortidsminder --refresh
uv run python scripts/build_runestone_research.py --refresh

printf '%s\n' "Bygger og validerer GitHub Pages-sitet ..."
uv run python scripts/build_static_site.py
summary="$(uv run python - <<'PY'
import json
from collections import Counter
from pathlib import Path

path = Path('.pages-dist/data/lokaliteter.json')
payload = json.loads(path.read_text(encoding='utf-8'))
if payload.get('format') != 'oldtidskort-v2':
    raise SystemExit('Uventet dataformat i lokaliteter.json')
counts = Counter(row[3] for row in payload.get('features', []))
required = ('gravhoej', 'runesten')
missing = [kind for kind in required if counts[kind] == 0]
if missing:
    raise SystemExit(f'Mangler punkter af typen: {", ".join(missing)}')
print(
    f'{sum(counts.values()):,} punkter '
    f'(gravminder: {counts["gravhoej"]:,}, runesten: {counts["runesten"]:,}); '
    f'{path.stat().st_size / 1_000_000:.1f} MB'
)
PY
)"
printf 'Valideret: %s\n' "$summary"

if [[ "$dry_run" == true ]]; then
  printf '%s\n' "Dry-run færdig: intet blev pushet."
  exit 0
fi

release_dir="$(mktemp -d)"
trap 'rm -rf "$release_dir"' EXIT
cp -R .pages-dist/. "$release_dir/"

git -C "$release_dir" init --initial-branch=gh-pages --quiet
git -C "$release_dir" add .
git -C "$release_dir" \
  -c user.name="Kasper Junge" \
  -c user.email="kasperjunge@users.noreply.github.com" \
  commit --message="Deploy Oldtidskort from $(git rev-parse --short HEAD)" --quiet

expected_hash="$(shasum -a 256 "$release_dir/data/lokaliteter.json" | awk '{print $1}')"
git -C "$release_dir" push --force "$origin_url" gh-pages

printf '%s\n' "Venter på at den nye datafil bliver synlig på GitHub Pages ..."
deadline=$((SECONDS + verify_timeout))
live_url="https://kasperjunge.github.io/oldtidskort/data/lokaliteter.json"
while ((SECONDS <= deadline)); do
  cache_buster="$(date +%s)"
  live_hash="$(curl --fail --silent --show-error "${live_url}?deploy=${cache_buster}" | shasum -a 256 | awk '{print $1}' || true)"
  if [[ "$live_hash" == "$expected_hash" ]]; then
    printf 'Deployment verificeret: %s\n' "$live_url"
    exit 0
  fi
  sleep 5
done

printf '%s\n' \
  "Push lykkedes, men live-sitet viste ikke det nye build inden for ${verify_timeout} sekunder." \
  "Se Pages-status: https://github.com/kasperjunge/oldtidskort/actions" >&2
exit 1
