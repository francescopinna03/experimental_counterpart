#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
verify() {
  git verify-commit HEAD >/dev/null 2>&1 || { echo "signature not verified on HEAD, stopping"; exit 1; }
  echo "verified: $(git log -1 --format='%h %s')"
}
step() {
  local title="$1"; local description="$2"; shift 2
  git add -A -- "$@"
  if git diff --cached --quiet; then echo "no changes for: $title"; return; fi
  git commit -S -m "$title" -m "$description" >/dev/null
  verify
}
git rm -r -f -q --ignore-unmatch dossier/select_K_battery.py dossier/design_data/K_battery.csv dossier/design_data/K_selection.json dossier/design_data/fisher_K_benchmark.csv dossier/design_data/template_computer.csv dossier/design_data/checks_v2.json dossier/figures/prices_and_power_v2.png
step "Design checks for the present design" "Benchmark prices under the two rules, trial templates, calendars and the check of the comparison between partners." dossier/design_checks.py dossier/partner_comparison_check.py dossier/design_data dossier/figures
git rm -f -q --ignore-unmatch dossier/Presentation_outline.md
step "Protocol and extracts on the present design" "Protocol, analysis plan, instructions, quiz and script, revision log and layout header." dossier
step "Explanatory note and design document" "Explanatory note on the experimental apparatus and design document aligned with the protocol." documents
step "README and commit script" "Repository description and commit helper." README.md scripts
git log --show-signature -4 --format='%h %G? %s' 2>/dev/null | cat
