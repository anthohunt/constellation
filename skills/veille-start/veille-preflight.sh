#!/bin/bash
# veille-preflight.sh <owner> <subject-slug>
# Dump COMPLET de l'etat du serveur necessaire au demarrage d'une run, en UNE session ssh.
# Remplace les ~7 aller-retours ssh du preparateur : il appelle ce script UNE fois,
# puis raisonne en local sur la sortie. Lecture + setup idempotent (scaffold/preferences).
# Sortie = sections balisees ===SECTION=== que le preparateur parse.
set -u
O="${1:?usage: veille-preflight.sh <owner> <subject-slug>}"
S="${2:?usage: veille-preflight.sh <owner> <subject-slug>}"
# Reglages (voir .env.example) :
#   VEILLE_OWNERS_DIR  silo des profils, partage avec le site (defaut ~/veille-owners)
#   CONSTELLATION_DATA dossier data/ du site
#   VEILLE_SCRIPTS     dossier des scripts de memoire facultatifs (veille-memory.py, build-watch-preferences.py)
#   FLUX_STATE_DIR     etat du moteur flux
OWNERS="${VEILLE_OWNERS_DIR:-$HOME/veille-owners}"
DATA="${CONSTELLATION_DATA:-./data}"
SCRIPTS="${VEILLE_SCRIPTS:-}"
FSTATE="${FLUX_STATE_DIR:-$HOME/flux/state}"
SILO="$OWNERS/$O"
WIZ="$DATA/owners/$O"

echo "===PREFLIGHT=== owner=$O subject=$S host=$(hostname) date=$(date -u +%FT%TZ)"

printf "
===SILO_DIR===
"
ls -la "$SILO" 2>/dev/null || echo "ABSENT"
echo "--- preferences ---"; ls -la "$SILO/preferences" 2>/dev/null || echo "ABSENT"
echo "--- db/findings/$S ---"; ls -1 "$SILO/db/findings/$S" 2>/dev/null | head -40 || echo "ABSENT"
echo "--- db/findings/$S count ---"; ls -1 "$SILO/db/findings/$S" 2>/dev/null | wc -l

printf "
===SILO_RUNCONFIG===
"
cat "$SILO/run-config.json" 2>/dev/null || echo "ABSENT"

printf "
===WIZARD_RUNCONFIG===
"   # la version a jour vit cote wizard (pont wizard->pipeline non auto)
cat "$WIZ/run-config.json" 2>/dev/null || echo "ABSENT"

printf "
===SILO_CASTING===
"
cat "$SILO/casting.json" 2>/dev/null || echo "ABSENT"

printf "
===SELECTION_RULES===
"
find "$SILO" -name 'selection-rules*' -o -name '*criteres-juges*' 2>/dev/null | head -20

printf "
===MEMORY_BRIEF===
"       # scaffold idempotent puis brief (0 run = memoire vide)
if [ -n "$SCRIPTS" ] && [ -f "$SCRIPTS/veille-memory.py" ]; then
  python3 "$SCRIPTS/veille-memory.py" scaffold "$O" "$S" >/dev/null 2>&1
  python3 "$SCRIPTS/veille-memory.py" brief "$O" "$S" 2>&1 | head -60
else echo "ABSENT (VEILLE_SCRIPTS non defini)"; fi

printf "
===WATCH_PREFERENCES===
"  # regenere le pad de preferences apprises
if [ -n "$SCRIPTS" ] && [ -f "$SCRIPTS/build-watch-preferences.py" ]; then
  python3 "$SCRIPTS/build-watch-preferences.py" "$S" --owner "$O" 2>&1 | tail -20
else echo "ABSENT (VEILLE_SCRIPTS non defini)"; fi

printf "
===CONCURRENCE_TMUX===
"   # Une run tourne-t-elle DEJA sur cette veille pour cet owner ?
# Deux veilles differentes en parallele est autorise, et deux owners aussi.
# Le doublon, c'est le meme couple veille+owner. La session flux est nommee
# flux-<workflow>-<noeud>-p<n> : elle ne dit pas quelle run, donc on lit l'etat
# par run (flux/state/<wf>/<workspace>/) et on ne garde que les sessions vivantes.
VIVANTES="$(tmux ls -F '#{session_name}' 2>/dev/null)"
TROUVE=0
for ST in "$FSTATE"/*/*/; do
  WSNAME="$(basename "$ST")"
  case "$WSNAME" in "${S}-${O}-"*) ;; *) continue ;; esac
  for J in "$ST"*.json; do
    [ -f "$J" ] || continue
    SESS="$(python3 -c "import json,sys;d=json.load(open(sys.argv[1]));p=(d.get('passages') or [{}])[-1];print(p.get('session') or d.get('tmux') or '')" "$J" 2>/dev/null)"
    [ -n "$SESS" ] || continue
    if printf '%s\n' "$VIVANTES" | grep -qx "$SESS"; then
      echo "DOUBLON veille=${S} owner=${O} workspace=${WSNAME} noeud=$(basename "$J" .json) session=${SESS}"
      TROUVE=1
    fi
  done
done
[ "$TROUVE" -eq 0 ] && echo "AUCUNE_RUN_CONCURRENTE veille=${S} owner=${O}"

printf "
===ARCHIVES_WIZARD===
"    # constellations livrees cote wizard (recompte)
ls -1dt "$DATA"/runs/${S}-* 2>/dev/null | head -5
for R in $(ls -1dt "$DATA"/runs/${S}-* 2>/dev/null | head -3); do
  C="$R/constellation-data.json"
  if [ -f "$C" ]; then
    N=$(python3 -c "import json,sys;print(len(json.load(open('$C')).get('nodes',[])))" 2>/dev/null)
    echo "$R -> nodes=$N"
  fi
done

printf "
===PREFLIGHT_END===
"
