#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
verifica() {
  git verify-commit HEAD >/dev/null 2>&1 || { echo "firma non verificata su HEAD, interrompo"; exit 1; }
  echo "verificato: $(git log -1 --format='%h %s')"
}
passo() {
  local titolo="$1"; local descrizione="$2"; shift 2
  git add -- "$@"
  if git diff --cached --quiet; then echo "nessuna modifica per: $titolo"; return; fi
  git commit -S -m "$titolo" -m "$descrizione" >/dev/null
  verifica
}
passo "Repository structure" "README, requirements, gitignore and commit script." README.md requirements.txt .gitignore scripts/commit_serie.sh
passo "Experimental dossier 2.0" "Protocol, instructions, analysis plan, revision log, layout files, design data and figures." dossier/LEGGIMI.md dossier/Protocollo_identificazione_dinamica.md dossier/Piano_analisi.md dossier/Istruzioni_partecipanti.md dossier/Quiz_e_copione.md dossier/Traccia_presentazione.md dossier/Revisioni_2_0.md dossier/impaginazione.tex dossier/figure dossier/dati_disegno
passo "Verification and simulation programs" "Design checks, depth battery selection and full simulation of the analysis procedure." dossier/verifica_disegno_v2.py dossier/seleziona_batteria_K.py dossier/simulazione_completa.py dossier/crea_facsimile.py dossier/impagina_word.py
passo "Design document and orientation note" "English design document and Italian orientation note, with sources." documents
passo "Presentation decks" "First presentation and project update decks." slides
git log --show-signature -5 --format='%h %G? %s' 2>/dev/null | cat
