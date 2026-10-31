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
git rm -r -f -q --ignore-unmatch dossier/simulazione_completa.py dossier/verifica_disegno_v2.py dossier/seleziona_batteria_K.py dossier/crea_facsimile.py dossier/impagina_word.py dossier/dati_disegno dossier/figure scripts/commit_serie.sh
rm -rf dossier/dati_disegno dossier/figure
step "English programs and certifying simulation" "Programs, data files and figures in English, with the full-replication results and a calibrated critical value." dossier/*.py dossier/design_data dossier/figures .gitignore
step "Simulation report and updated documents" "Report of the certifying run, updated protocol section, design document and slides." dossier/*.md documents slides
step "README and commit script" "Reproduction instructions and commit helper." README.md requirements.txt scripts
git log --show-signature -3 --format='%h %G? %s' 2>/dev/null | cat
