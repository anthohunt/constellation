"""
Validateur étape 5 — FEEDBACK.

Gate de sortie : le deck de préférence a-t-il été produit/mis à jour à partir de
la notation de l'étape 4 ? C'est ce qui rend la prochaine run plus juste.

Contrats :
1. Un deck `deck-*.json` (state/ ou racine) présent, JSON valide.
2. Le deck porte au moins une des sorties attendues du feedback :
   règles de chasse, règles de forme, ou consignes pour la prochaine run.
3. Le deck a été RÉÉCRIT PENDANT CETTE RUN (mtime > WORKSPACE.txt). Le deck d'entrée
   est copié depuis les préférences de l'owner à l'étape 1 : sans ce contrat, l'étape 5
   passe au vert sans avoir rien produit — c'est le trou par lequel la boucle
   d'apprentissage ne s'est jamais fermée sur la run 2026-08-13.
4. Les NON-OUVERTS sont traités comme des rejets : `analyse-non-ouverts.md` existe et
   n'est pas un stub. Un finding non ouvert par le lecteur est un rejet prononcé sur le
   seul titre — le signal le plus abondant de la run, et le seul qui juge la porte
   d'entrée. La pipeline le jetait silencieusement.
"""
import json, glob, os, pathlib

def _run_start(ws):
    """Horodatage de départ de la run = mtime de WORKSPACE.txt (posé à l'étape 1)."""
    w = ws / 'WORKSPACE.txt'
    return w.stat().st_mtime if w.exists() else None


TIERS_HAUT = {'Excellent', 'Cool'}
TIERS_BAS = {'Bof', 'Inutile'}

def _polarite(deck, errs):
    """Un deck ne peut pas presenter comme aime ce que le lecteur a rejete ou rabaisse.

    C'est le defaut qui rend la boucle contre-productive : les exemples sont relus par
    le juge de la run suivante ET transformes en requetes par les chasseurs.
    """
    adores = deck.get('adorés') or deck.get('adores') or []
    detestes = deck.get('détestés') or deck.get('detestes') or []
    faux = [a for a in adores
            if isinstance(a, dict) and (a.get('tier') or '').strip() not in TIERS_HAUT]
    if faux:
        exemples = ', '.join('%s (%s)' % ((a.get('titre') or '?')[:40], a.get('tier')) for a in faux[:3])
        errs.append("C5: %d entree(s) de `adorés` ne portent pas un tier haut (Excellent/Cool) : %s. "
                    "La polarite se lit sur le tier FINAL du lecteur, pas sur le fait qu'il ait touche "
                    "la fiche — une fiche retrogradee va dans `surcotés`, jamais dans `adorés`."
                    % (len(faux), exemples))
    fauxb = [a for a in detestes
             if isinstance(a, dict) and (a.get('tier') or '').strip() not in TIERS_BAS]
    if fauxb:
        errs.append("C5: %d entree(s) de `détestés` ne portent pas un tier bas (Bof/Inutile)." % len(fauxb))

def _regles_axes(ws, errs):
    """Le fichier de regles par axe : produit, teste, et honnete sur son statut."""
    f = None
    for cand in (ws / 'state' / 'regles-axes.json', ws / 'regles-axes.json'):
        if cand.exists():
            f = cand; break
    if not f:
        errs.append("C6: `regles-axes.json` absent — le feedback n'a induit aucune regle par axe. "
                    "C'est le seul artefact qui dit au chasseur OU chercher pour cet axe.")
        return
    try:
        R = json.loads(f.read_text(encoding='utf-8'))
    except Exception as e:
        errs.append("C6: `regles-axes.json` illisible: %s" % e); return
    axes = R.get('axes') or {}
    if not axes:
        errs.append("C6: `regles-axes.json` ne contient aucun axe — si la matiere ne permettait "
                    "d'induire aucune regle, ecris-le explicitement (axe: []), ne laisse pas vide.")
        return
    for axe, regles in axes.items():
        for r in (regles or []):
            if not isinstance(r, dict): continue
            titre = (r.get('regle') or '?')[:50]
            pr = r.get('preuve') or {}
            if not isinstance(pr, dict) or pr.get('total') in (None, 0):
                errs.append("C6: axe `%s`, regle « %s » — aucune preuve chiffree. Une regle se "
                            "teste sur les classements deja poses avant d'etre proposee." % (axe, titre))
                continue
            retrouve, total = pr.get('retrouve') or 0, pr.get('total') or 0
            if total and retrouve / total < 0.66 and (r.get('statut') or '') == 'validee':
                errs.append("C6: axe `%s`, regle « %s » marquee `validee` alors qu'elle ne retrouve "
                            "que %s classements sur %s." % (axe, titre, retrouve, total))
            if (r.get('statut') or '') == 'validee' and not (r.get('mots_cles') or []):
                errs.append("C6: axe `%s`, regle « %s » validee sans `mots_cles` — inapplicable : "
                            "c'est par eux que la chasse prouve qu'elle a cherche la." % (axe, titre))

def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    decks = glob.glob(str(ws / 'state' / 'deck-*.json')) + glob.glob(str(ws / 'deck-*.json'))
    if not decks:
        errs.append("C1: aucun `deck-*.json` — le feedback n'a rien produit")
        return errs

    deck_path = decks[0]
    try:
        d = json.loads(open(deck_path, encoding='utf-8').read())
    except json.JSONDecodeError as e:
        errs.append(f"C1: `{os.path.basename(deck_path)}` JSON invalide: {e}")
        return errs

    _polarite(d, errs)
    _regles_axes(ws, errs)

    # Le format canonique du deck utilise des clés ACCENTUÉES (`adorés`/`détestés`) —
    # cf. owners/<owner>/preferences/deck-<watch>.json. Les variantes non accentuées
    # sont tolérées. Ce contrat cherchait `adores`/`detestes` et déclarait donc rouge
    # un deck parfaitement valide.
    keys = ('regles_chasse', 'regles_forme', 'consignes_prochaine_run',
            'adorés', 'détestés', 'adores', 'detestes', 'consignes')
    if not any(d.get(k) for k in keys):
        errs.append(f"C2: `{os.path.basename(deck_path)}` — aucune sortie de feedback "
                    f"(ni règles de chasse/forme, ni consignes prochaine run, ni exemples adorés/détestés)")

    # C3 — le deck doit avoir été produit DANS cette run, pas hérité de l'étape 1
    t0 = _run_start(ws)
    if t0 is not None and os.path.getmtime(deck_path) <= t0:
        errs.append(f"C3: `{os.path.basename(deck_path)}` n'a pas été réécrit pendant cette run "
                    f"(mtime antérieur à WORKSPACE.txt) — c'est le deck d'ENTRÉE copié à l'étape 1, "
                    f"pas une sortie de feedback. L'étape 5 n'a rien produit.")

    # C4 — les non-ouverts sont un signal, pas un trou
    ano = ws / 'analyse-non-ouverts.md'
    if not ano.exists():
        errs.append("C4: `analyse-non-ouverts.md` absent — les findings non ouverts par le lecteur "
                    "sont des REJETS prononcés sur le seul titre, pas des données manquantes. "
                    "L'étape 5 doit les analyser avant tout le reste.")
    else:
        txt = ano.read_text(encoding='utf-8').strip()
        if len(txt) < 600:
            errs.append(f"C4: `analyse-non-ouverts.md` fait {len(txt)} caractères — stub. "
                        f"Attendu : ce que les titres rejetés ont en commun, ce que les titres "
                        f"ouverts ont en commun, et la différence opérationnelle entre les deux.")

    # C4b — la notation doit porter la distinction ouvert/non-ouvert
    fj = ws / 'findings.json'
    if fj.exists():
        try:
            F = json.loads(fj.read_text(encoding='utf-8'))
            findings = F.get('findings', F if isinstance(F, list) else [])
            sans_flag = [f.get('id', '?') for f in findings if 'ouvert' not in f]
            if sans_flag:
                errs.append(f"C4: {len(sans_flag)} findings sans champ `ouvert` "
                            f"(ex. {', '.join(sans_flag[:5])}) — le signal de clic n'a pas été "
                            f"fusionné depuis `notation-terminee.json`.")
        except json.JSONDecodeError:
            pass

    return errs
