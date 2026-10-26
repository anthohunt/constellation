"""
Validateur étape 4 — TA NOTATION (barrière humaine).

Gate de sortie : Le lecteur a-t-il réellement terminé sa notation sur la constellation ?
Cette étape est humaine — le validateur vérifie seulement que l'artefact de clôture
existe et est complet, pas la qualité des choix (ce sont les siens).

Contrats :
1. constellation-bundle/notation-terminee.json présent, JSON valide.
2. `done: true` — la notation est explicitement close (pas un brouillon).
3. `notes` non vide — au moins des tiers/commentaires ont été posés.
"""
import json, pathlib

def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    p = ws / 'constellation-bundle' / 'notation-terminee.json'

    if not p.exists():
        errs.append("C1: `constellation-bundle/notation-terminee.json` absent — notation non clôturée")
        return errs
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        errs.append(f"C1: `notation-terminee.json` JSON invalide: {e}")
        return errs

    if not d.get('done'):
        errs.append("C2: `notation-terminee.json` — `done` n'est pas true (notation en cours, pas close)")

    notes = d.get('notes')
    if not notes:
        errs.append("C3: `notation-terminee.json` — aucune note posée (`notes` vide)")

    return errs
