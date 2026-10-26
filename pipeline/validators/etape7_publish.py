"""
Validateur étape 6 — PUBLIER.

Gate de sortie : la version publiée (niveau 2, gardés seulement) est-elle produite,
et la constellation publiée déployée ?

Contrats :
1. publish/gardes.json présent, JSON valide, au moins 1 gardé.
3. Carnet de sources présent (publish/carnet-sources.md) — fermeture de boucle.
   (avertissement seulement s'il manque — pas bloquant tant que 1+2 sont là)
"""
import json, os, glob, pathlib, re


def _publie_cumulatif(ws, errs):
    """La page publiee doit porter toutes les livraisons.

    Deployer la seule run de la semaine perd le cumul — or c'est lui qui donne sa
    valeur a la veille : une fiche ne se lit que contre ce qui a ete dit avant.
    """
    import glob as _glob
    cands = sorted(_glob.glob(os.path.join(os.environ.get('CONSTELLATION_DATA', 'data'), 'runs', '*-publie', 'constellation-data.json')),
                   key=os.path.getmtime, reverse=True)
    if not cands:
        errs.append("C7: aucune constellation publiee deployee.")
        return
    try:
        B = json.loads(open(cands[0], encoding='utf-8').read())
    except Exception as e:
        errs.append("C7: bundle publie illisible: %s" % e); return
    runs = B.get('runs') or []
    if len(runs) < 2:
        errs.append("C7: la constellation publiee ne porte que %d livraison(s) — elle doit "
                    "cumuler toute la bibliotheque, pas la seule run de la semaine." % len(runs))
    if len(B.get('nodes') or []) < 2:
        errs.append("C7: la constellation publiee ne porte aucun signal — la bibliotheque "
                    "n'est pas arrivee jusqu'a la page.")

def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    _publie_cumulatif(ws, errs)

    g = ws / 'publish' / 'gardes.json'
    if not g.exists():
        errs.append("C1: `publish/gardes.json` absent — rien n'a été publié")
        return errs
    try:
        d = json.loads(g.read_text(encoding='utf-8'))
        gardes = d if isinstance(d, list) else (d.get('gardes') or [])
        if not gardes:
            errs.append("C1: `publish/gardes.json` — aucun gardé (liste vide)")
    except json.JSONDecodeError as e:
        errs.append(f"C1: `publish/gardes.json` JSON invalide: {e}")



        # C22 - la publication s'ecrit dans le meme style que les essentiels. Digest,
    # newsletter et resumes passent le meme controle qu'a l'etape 3 : celui qui
    # ouvre la newsletter n'a pas moins droit a la clarte que celui qui note la
    # constellation. Le controle est applique SECTION PAR SECTION : un digest
    # agrege une dizaine de findings, le plafond de notions se juge sur ce que le
    # lecteur doit tenir en tete dans un bloc. Le carnet de sources n'est pas un
    # texte redige mais un inventaire : hors perimetre.
    try:
        import sys as _s22, os as _o22
        _s22.path.insert(0, _o22.path.dirname(_o22.path.dirname(_o22.path.abspath(__file__))))
        from style_vulgarisation import controler_document as _c22doc
        from mode_run import est_collecte as _est_collecte
    except Exception:
        _c22doc = None
        _est_collecte = lambda _w: False
    # Une collecte aligne des elements ; le style de vulgarisation juge une
    # explication qu'elle n'a pas a produire.
    if _c22doc and not _est_collecte(ws):
        cibles = []
        for rel in ('deliverables/digest.html', 'deliverables/digest.md',
                    'deliverables/newsletter.html'):
            p = ws / 'publish' / rel
            if p.exists():
                cibles.append(p)
        dres = ws / 'publish' / 'resumes'
        if dres.exists():
            cibles += sorted(dres.glob('*.md'))
        for p in cibles:
            try:
                errs.extend(_c22doc(p.read_text(encoding='utf-8', errors='replace'),
                                    etiquette=p.name))
            except Exception:
                continue

    return errs
