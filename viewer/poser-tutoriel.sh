#!/usr/bin/env bash
# poser-tutoriel.sh — installe la constellation d'exemple sous /c/tutoriel/.
#
# A la premiere visite d'une vraie veille, la page ouvre un parcours guide dans un
# cadre pointant sur /c/tutoriel/ : on y apprend a noter sans toucher aux vraies
# donnees. Une installation neuve n'a pas cette run ; ce script la pose a partir
# d'une run construite (par defaut l'exemple fictif du depot).
#
#   CONSTELLATION_DATA=<data du site> poser-tutoriel.sh [<workspace construit>]
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="${1:-$ICI/../examples/demo-run}"
DATA="${CONSTELLATION_DATA:?CONSTELLATION_DATA non defini (dossier data/ du site)}"
SRC="$WS/constellation/constellation-data.json"
[ -f "$SRC" ] || python3 "$ICI/build_constellation.py" "$WS"
DEST="${DATA%/}/runs/tutoriel"
mkdir -p "$DEST"
cp "$ICI/constellation.template.html" "$DEST/constellation.html"
cp -r "$ICI/vendor" "$DEST/"
python3 - "$SRC" "$DEST/constellation-data.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
d["watch"] = "tutoriel"          # la page joue le parcours guide sur cette veille-la
json.dump(d, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
PY
echo "tutoriel pose : $DEST"
