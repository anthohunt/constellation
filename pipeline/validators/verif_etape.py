"""
Validateur GENERIQUE des nœuds « Etape N — Verification ».

La verification a la meme forme a toutes les etapes : recenser le perimetre,
fouiller chaque livrable contre le transcript qui l'a produit, agreger les
failles. Le contrat est donc unique — il est parametre par le numero d'etape.

Ce qu'il juge, et rien d'autre :

V1. `verifications/etape-<N>/perimetre.md` existe et liste des sous-etapes.
V2. Au moins un rapport par transcript sous `verifications/etape-<N>/`, hors
    perimetre.md — un seul rapport pour dix agents veut dire qu'on n'a pas
    dispatche.
V3. Chaque rapport porte la colonne « transcript » remplie : un `conforme`
    sans trace citee est un rapport invalide, pas un rapport optimiste.
V4. `verifications/etape-<N>.md` existe, porte un verdict lisible, et agrege
    (il cite les rapports, il ne les remplace pas).
V5. Verdict conforme mais des failles bloquantes listees = incoherence.

Zero faille EST un resultat valide : on ne verifie jamais qu'il y a des
failles, seulement que la fouille a eu lieu et qu'elle est tracee.

Retour : liste de strings, une par contrat casse.
"""
import re, pathlib

# Marqueurs acceptes pour la colonne « ce que le transcript montre ». On accepte
# les variantes d'emballage : ce qui compte est qu'une trace soit citee, pas le
# libelle exact de l'en-tete.
_TRACE = re.compile(r'transcript|session|jsonl|outil|WebFetch|WebSearch|Read|Write|Bash|appel',
                    re.IGNORECASE)
_VERDICT = re.compile(r'\b(conforme|faille|refus|bloquant|verdict)\b', re.IGNORECASE)


def _num(etape):
    """« 2-verification » -> « 2 ». Le nœud de verification porte le numero de
    l'etape qu'il juge : il n'a pas de rang a lui."""
    return str(etape).split('-')[0].split('.')[0]


# Les contrats de CONTENU d'une etape verifiee vivent dans leur propre module —
# ils jugent ce que la fouille doit constater (fidelite aux sources, clarte,
# style, notes par piste), la ou V1-V5 jugent que la fouille a eu lieu. Le
# generique les appelle en plus des siens : un seul gate, deux natures de
# contrat, aucune regle recopiee.
# Toutes les etapes n'y figurent pas, et c'est voulu : un contrat de contenu de
# VERIFICATION n'existe que la ou la fouille doit juger autre chose que ce que le gate
# du producteur juge deja. Pour les etapes 1, 6 et 7, leurs contrats jugent le
# producteur — les rejouer ici ne dirait rien de neuf, et ferait rougir la verification
# pour une faute qui n'est pas la sienne. V1-V5 y suffisent : ils etablissent que la
# fouille a eu lieu et qu'elle est tracee.
_CONTENU = {
    '2': ('etape2_5_verification', None),
    '3': ('etape3_constellation', 'verification'),
    '4': ('etape4_notification', None),
}


def _contrats_de_contenu(workspace, n):
    ref = _CONTENU.get(n)
    if not ref:
        return []
    nom, portee = ref
    f = pathlib.Path(__file__).parent / f'{nom}.py'
    if not f.exists():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location(nom, f)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return mod.validate(workspace, portee) if portee else mod.validate(workspace)
    except Exception as e:
        return [f"V0: contrats de contenu de l'etape {n} illisibles ({type(e).__name__}: {e})"]


def validate(workspace, etape=None, portee='tout'):
    errs = []
    ws = pathlib.Path(workspace)
    n = _num(etape if etape is not None else 1)
    errs.extend(_contrats_de_contenu(workspace, n))

    dossier = ws / 'verifications' / f'etape-{n}'
    rapport = ws / 'verifications' / f'etape-{n}.md'

    # ── V1 : le perimetre
    per = dossier / 'perimetre.md'
    if not dossier.exists():
        errs.append(f"V1: `verifications/etape-{n}/` absent — la verification n'a pas tourne")
        return errs
    if not per.exists() or per.stat().st_size == 0:
        errs.append(f"V1: `verifications/etape-{n}/perimetre.md` absent ou vide — le perimetre "
                    f"doit etre fixe AVANT de juger, sinon on regarde ce qui est facile a regarder")
    else:
        txt = per.read_text(encoding='utf-8', errors='replace')
        if len(txt.strip()) < 120:
            errs.append(f"V1: `perimetre.md` trop court ({len(txt.strip())} car) — il liste toutes "
                        f"les sous-etapes avec leur livrable, et tous les transcripts")

    # ── V2 : un rapport par transcript
    rapports = [f for f in dossier.glob('*.md') if f.name != 'perimetre.md']
    if not rapports:
        errs.append(f"V2: aucun rapport sous `verifications/etape-{n}/` — un verificateur FRAIS "
                    f"par transcript, chacun ecrit le sien")
        return errs

    # ── V3 : chaque rapport cite des traces
    muets = []
    for f in rapports:
        t = f.read_text(encoding='utf-8', errors='replace')
        if not _TRACE.search(t):
            muets.append(f.name)
        elif len(t.strip()) < 150:
            muets.append(f.name)
    if muets:
        errs.append(f"V3: {len(muets)} rapport(s) sans trace citee ({', '.join(muets[:4])}) — "
                    f"un « conforme » sans la colonne transcript remplie est un rapport invalide")

    # ── V4/V5 : le rapport d'etape
    if not rapport.exists() or rapport.stat().st_size == 0:
        errs.append(f"V4: `verifications/etape-{n}.md` absent — le chef agrege les rapports en un "
                    f"verdict d'etape")
        return errs
    agg = rapport.read_text(encoding='utf-8', errors='replace')
    if not _VERDICT.search(agg):
        errs.append(f"V4: `verifications/etape-{n}.md` ne porte aucun verdict lisible "
                    f"(conforme / faille / bloquant)")
    if len(agg.strip()) < 200:
        errs.append(f"V4: `verifications/etape-{n}.md` trop court ({len(agg.strip())} car) pour "
                    f"agreger {len(rapports)} rapport(s)")
    bloquant = re.search(r'bloquant', agg, re.IGNORECASE)
    conforme = re.search(r'verdict\s*[:\-–]?\s*conforme', agg, re.IGNORECASE)
    if bloquant and conforme:
        errs.append("V5: le rapport d'etape annonce un verdict conforme ET liste des failles "
                    "bloquantes — l'un des deux est faux")
    return errs
