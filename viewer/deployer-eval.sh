#!/usr/bin/env bash
# deployer-eval.sh — construit le JSON de la constellation d'evaluation et le deploie.
#
# Remplace la sequence que le monteur faisait a la main : retrouver le script de build,
# retrouver le chemin de destination, sauvegarder, copier, verifier en HTTP. Un appel,
# un tour d'agent.
#
#   deployer-eval.sh <workspace>
#
# Sortie : une ligne par etape, puis un RESUME. Code 0 si la page et son JSON repondent
# 200 et que le md5 servi est celui du livrable local ; non nul sinon.
#
# N'appelle PAS corriger_accents_run.py : run-node.py le passe deja en fin de noeud.

set -uo pipefail

WS="${1:?usage: deployer-eval.sh <workspace>}"
WS="${WS%/}"
[ -d "$WS" ] || { echo "workspace introuvable : $WS" >&2; exit 2; }

SLUG="$(basename "$WS")"
# Reglages : CONSTELLATION_DATA = dossier data/ du site (monte dans son conteneur),
# CONSTELLATION_BASE_URL = adresse publique du site.
DATA="${CONSTELLATION_DATA:?CONSTELLATION_DATA non defini (dossier data/ du site)}"
DEST="${DATA%/}/runs/${SLUG}-eval"
BASEURL="${CONSTELLATION_BASE_URL:-http://localhost:8080}/c/${SLUG}-eval"
ASSETS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="$WS/constellation-bundle/_build"
LIVRABLE="$WS/constellation-bundle/constellation-data.json"
STAMP="$(date +%Y%m%d-%H%M%S)"

echo "workspace : $WS"
echo "destination : $DEST"

# 1. construire le JSON depuis findings.json
[ -f "$WS/findings.json" ] || { echo "findings.json absent — rien a construire" >&2; exit 2; }

# findings.json doit etre lisible ET non vide : le builder avale un JSON casse en silence
# et produit une constellation a 0 signal, qui se deploierait comme un succes.
N_IN=$(python3 - "$WS/findings.json" <<'PY' 2>/dev/null
import json,sys
b=json.load(open(sys.argv[1],encoding="utf-8"))
print(len(b if isinstance(b,list) else b.get("findings",[])))
PY
) || { echo "findings.json illisible — le builder produirait une constellation vide" >&2; exit 2; }
[ -n "${N_IN:-}" ] || { echo "findings.json illisible — le builder produirait une constellation vide" >&2; exit 2; }
[ "$N_IN" -gt 0 ] || { echo "findings.json ne porte aucun finding — rien a deployer" >&2; exit 2; }
echo "-- entree : $N_IN findings"
mkdir -p "$BUILD"
cp "$WS/findings.json" "$BUILD/findings.json"
for f in run-config.json subject.md; do
  [ -f "$WS/$f" ] && cp "$WS/$f" "$BUILD/$f"
done
echo "-- build"
python3 "$ASSETS/build_constellation.py" "$BUILD" || { echo "build en echec" >&2; exit 1; }

PRODUIT="$BUILD/constellation/constellation-data.json"
[ -s "$PRODUIT" ] || { echo "le build n'a produit aucun JSON" >&2; exit 1; }

N_OUT=$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1],encoding='utf-8'))['nodes']))" "$PRODUIT" 2>/dev/null || echo 0)
[ "$N_OUT" -gt 0 ] || { echo "le build a rendu 0 signal pour $N_IN findings — rien n'est deploye" >&2; exit 1; }
if [ "$N_OUT" != "$N_IN" ]; then
  echo "!! ecart entree/sortie : $N_IN findings -> $N_OUT signaux" >&2
fi

# 2. poser le livrable du noeud
[ -f "$LIVRABLE" ] && cp "$LIVRABLE" "$WS/state/constellation-data.json.bak-$STAMP" 2>/dev/null
mkdir -p "$(dirname "$LIVRABLE")"
cp "$PRODUIT" "$LIVRABLE"
echo "-- livrable : $LIVRABLE ($(stat -c%s "$LIVRABLE") o)"

# 3. premier deploiement : la page et ses assets, une seule fois
if [ ! -d "$DEST" ]; then
  echo "-- premier deploiement : creation de $DEST"
  mkdir -p "$DEST"
  cp "$ASSETS/constellation.template.html" "$DEST/constellation.html"
  [ -d "$ASSETS/vendor" ] && cp -r "$ASSETS/vendor" "$DEST/vendor"
else
  cp "$DEST/constellation-data.json" "$DEST/constellation-data.json.bak-$STAMP" 2>/dev/null
fi

# 4. deployer les donnees
cp "$LIVRABLE" "$DEST/constellation-data.json"
echo "-- deploye"

# 5. constater
RC=0
for u in "/" "/constellation-data.json" "/vendor/three.module.js"; do
  CODE=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "$BASEURL$u")
  printf "   %-28s %s\n" "$u" "$CODE"
  [ "$CODE" = "200" ] || RC=1
done

MD5_LOCAL=$(md5sum "$LIVRABLE" | cut -d' ' -f1)
MD5_SERVI=$(curl -s -m 40 "$BASEURL/constellation-data.json" | md5sum | cut -d' ' -f1)
NODES=$(python3 -c "import json;print(len(json.load(open('$LIVRABLE'))['nodes']))" 2>/dev/null || echo '?')

if [ "$MD5_LOCAL" = "$MD5_SERVI" ]; then
  echo "RESUME : $NODES signaux servis, md5 conforme — $BASEURL/"
else
  echo "RESUME : md5 DIFFERENT entre le livrable et ce qui est servi (local=$MD5_LOCAL servi=$MD5_SERVI)" >&2
  RC=1
fi
exit $RC
