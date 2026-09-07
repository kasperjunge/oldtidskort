---
name: deploy-oldtidskort
description: Deploy or dry-run the local Oldtidskort GitHub Pages release, including repository preflight, fresh source data, tests, build validation, gh-pages publication, and live verification. Use for release, publication, deployment, or deployment diagnosis of kasperjunge/oldtidskort; do not use for ordinary application development.
---

# Deploy Oldtidskort

Work in `/Users/kasperjunge/Agent/code/kasperjunge/public/oldtidskort`. Treat
`scripts/deploy_pages.sh` as the single source of truth for deployment mechanics;
do not reproduce its build or git commands manually.

## Choose the operation

- If the user asks to inspect, prepare, test, or check a deployment, run
  `./scripts/deploy_pages.sh --dry-run`. This may download fresh public source
  data but must not update `gh-pages`.
- If the user explicitly asks to deploy, publish, release, or make the current
  version live, run `./scripts/deploy_pages.sh`. That request authorizes the
  script's force-push of its generated, temporary `gh-pages` branch only.
- If intent is ambiguous about publication, use dry-run and report that no push
  occurred. Do not infer permission to deploy from a request to diagnose.

Do not run dry-run immediately before a real deployment unless the user asks;
the real command already performs the same preflight, refresh, tests, and
validation, and repeating it needlessly redownloads the sources.

## Handle results

Before running, inspect `git status --short --branch` and report relevant local
changes without modifying them. Let the script enforce branch and remote-state
requirements.

On success, report the validated counts and the live URL shown by the script.
On failure, identify the failed phase from its output. Do not bypass failed
tests or data validation, and do not manually force-push. If the push succeeded
but live verification timed out, say that publication may still be processing
and inspect GitHub Pages status read-only before proposing another deployment.
