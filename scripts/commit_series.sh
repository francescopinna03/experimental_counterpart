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
git rm -r -f -q --ignore-unmatch dossier/Protocollo_identificazione_dinamica.md dossier/Piano_analisi.md dossier/Istruzioni_partecipanti.md dossier/Quiz_e_copione.md dossier/Traccia_presentazione.md dossier/Revisioni_2_0.md dossier/LEGGIMI.md dossier/impaginazione.tex dossier/simulation_report.md
git rm -q --cached --ignore-unmatch documents/Nota_orientamento_progetto.tex documents/Nota_orientamento_progetto.pdf
step "English dossier, version 2.1" "Protocol and companion documents in English, with the calibrated likelihood-ratio test as primary for the first hypothesis." dossier .gitignore
step "Design document and slides aligned with the protocol" "Primary test of the first hypothesis updated in the design document and the project update deck." documents slides
step "README and commit script" "Repository description and commit helper." README.md scripts
git log --show-signature -3 --format='%h %G? %s' 2>/dev/null | cat
