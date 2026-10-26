"""
Validateur étape 2 — CHASSE.

Contrats vérifiés (voir templates/brief-chasseur.md et brief-verificateur.md) :
1. `passants-raw.jsonl` existe, chaque ligne a les champs obligatoires du chasseur.
   Les notes du vérificateur (`notes-*`, stamps) ne sont PAS jugées ici : elles
   appartiennent à l'étape de vérification, qui est un nœud séparé — un chasseur
   ne se juge pas lui-même, il ne peut donc pas être bloqué sur le travail d'un autre.
6. Aucun titre à énigme non signalé (heuristique).
7. EFFORT: chaque chasseur a tenu le plancher d'effort (>=15 sources ouvertes, >=8 requetes,
   >=5 hors premiere page, >=3 hors moteur) — l'effort est impose, la sortie est libre.
   Un chasseur qui rend < 3 pistes doit avoir écrit son motif.
9. TIER: chaque piste porte la tier posee par son chasseur, dans le bareme des six, avec
   la phrase qui dit pourquoi celle-la et pas la voisine. Le monteur la REPORTE (etape 3).
8. EXPLORATION: `state/axes-candidats.json` existe et porte au moins une graine hors axes
   définis, rapportée par l'éclaireur. C'est le quota d'exploration (15-20 %, anti-bulle)
   de `veille-launch-researcher` — écrit dans les skills depuis toujours, jamais exécuté
   sur les runs 07-29, 08-01 et 08-13. Sans ce fichier, la veille ne peut que confirmer
   les axes qu'on lui a commandés, et aucun nouvel axe ne peut naître.

Retour : liste de strings, une par contrat cassé, ou [] si tout va bien.
"""
import json, os, re, pathlib, unicodedata

TITRE_ENIGME_PREFIX = ('ceux qui', 'un truc qui', 'une chose qui', 'ce qui ')

# Le barème des tiers, du plus proche du centre au plus lointain. Comparé sans
# accents ni casse : l'emballage n'est pas un critère de qualité.
TIERS_AFFICHAGE = ('Excellent', 'Cool', 'Intéressant', 'Neutre', 'Bof', 'Inutile')

def _tier_clef(v):
    s = unicodedata.normalize('NFKD', str(v).strip().lower())
    return ''.join(c for c in s if not unicodedata.combining(c))

TIERS = {_tier_clef(t) for t in TIERS_AFFICHAGE}

def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)

    # C1 — passants-raw.jsonl
    passants_raw = ws / 'state' / 'passants-raw.jsonl'
    if not passants_raw.exists():
        # fallback : à la racine
        passants_raw = ws / 'passants-raw.jsonl'
    if not passants_raw.exists():
        errs.append("C1: `passants-raw.jsonl` absent (attendu à `<ws>/state/` ou `<ws>/`)")
        return errs

    passants = []
    for lineno, line in enumerate(passants_raw.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line: continue
        try:
            p = json.loads(line)
            passants.append(p)
        except json.JSONDecodeError as e:
            errs.append(f"C1: `passants-raw.jsonl` ligne {lineno} JSON invalide: {e}")
            continue
        for field in ('id', 'titre', 'date_fait'):
            if not p.get(field):
                errs.append(f"C1: passant `{p.get('id','?')}` ligne {lineno} — champ `{field}` manquant/vide")
        # url primaire : soit `url` top-level, soit sources[0].url ou sources[0] (si string)
        has_url = bool(p.get('url'))
        if not has_url:
            src = p.get('sources') or []
            if src:
                first = src[0]
                if isinstance(first, str):
                    has_url = bool(first.strip())
                elif isinstance(first, dict):
                    has_url = bool(first.get('url'))
        if not has_url:
            errs.append(f"C1: passant `{p.get('id','?')}` ligne {lineno} — pas d'URL primaire (ni `url` top-level ni `sources[0]`)")
        # titre à énigme
        t = (p.get('titre') or '').lower().strip()
        for pref in TITRE_ENIGME_PREFIX:
            if t.startswith(pref):
                errs.append(f"C6: passant `{p.get('id','?')}` — titre à énigme non réécrit: « {p.get('titre')[:80]} »")
                break

    if not passants:
        errs.append("C1: `passants-raw.jsonl` vide — aucune piste retenue")
        return errs

    # Chasseurs uniques (extraits de l'id — préfixe avant chiffre)
    # Ex: "cc5-…" → chasseur "cognition-creation" via casting, mais on peut passer
    # par les fichiers pistes-*.md à la racine.
    pistes_files = sorted(ws.glob('pistes-*-T*.md')) + sorted((ws/'notes').glob('pistes-*-T*.md'))
    if not pistes_files:
        errs.append("C1: aucun fichier `pistes-<chasseur>-T<n>.md` trouvé")

    chasseurs_tours = set()
    for f in pistes_files:
        m = re.match(r'pistes-(.+)-T(\d+)\.md$', f.name)
        if m:
            chasseurs_tours.add((m.group(1), int(m.group(2))))

    if not chasseurs_tours:
        errs.append("C1: aucun (chasseur, tour) extractible depuis les fichiers pistes")

    # C7 — budget d'effort (remplace le quota de sortie)
    ef = ws / 'state' / 'effort-chasse.json'
    if not ef.exists():
        errs.append("C7: `state/effort-chasse.json` absent — l'effort de chasse n'est pas journalisé, "
                    "impossible de vérifier que les chasseurs ont réellement fouillé")
    else:
        try:
            raw = ef.read_text(encoding='utf-8').strip()
            entries = []
            if raw.startswith('['):
                entries = json.loads(raw)
            elif raw.startswith('{'):
                try:
                    d7 = json.loads(raw)
                    for k in ('par_chasseur', 'chasseurs', 'effort', 'entries'):
                        if isinstance(d7.get(k), list):
                            entries = d7[k]; break
                    else:
                        entries = [d7]
                except json.JSONDecodeError:
                    for line in raw.splitlines():
                        line = line.strip()
                        if line:
                            entries.append(json.loads(line))
            else:
                for line in raw.splitlines():
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            errs.append(f"C7: `state/effort-chasse.json` illisible: {e}")
            entries = []
        PLANCHERS = {'sources_ouvertes': 15, 'requetes': 8, 'hors_premiere_page': 5, 'hors_moteur': 3}
        for e in entries:
            who = e.get('chasseur', '?')
            for champ, mini in PLANCHERS.items():
                v = e.get(champ)
                n = len(v) if isinstance(v, list) else (v or 0)
                if n < mini:
                    errs.append(f"C7: chasseur `{who}` — {champ}={n} < {mini} : effort sous le plancher "
                                f"(l'agent s'est arrêté trop tôt)")
            if (e.get('pistes_rendues') or 0) < 3 and not (e.get('motif_si_peu') or '').strip():
                errs.append(f"C7: chasseur `{who}` — moins de 3 pistes rendues sans motif écrit "
                            f"(rendre peu est valide, ne pas l'expliquer ne l'est pas)")

    # C9 — la tier est posée par le CHASSEUR, contre les règles de son axe.
    # Elle n'est pas un jugement de qualité de la fouille (c'est le rôle de la
    # vérification) : c'est ce que le chasseur dit de sa propre trouvaille, et
    # ce que le lecteur corrigera à l'étape 4. Le monteur la REPORTE, il ne la pose pas.
    sans_tier, sans_motif, hors_bareme = [], [], []
    for p_ in passants:
        pid = p_.get('id', '?')
        brut = p_.get('tier') or p_.get('tier_proposee') or p_.get('rang')
        if not brut or not str(brut).strip():
            sans_tier.append(pid)
            continue
        if _tier_clef(brut) not in TIERS:
            hors_bareme.append(f"{pid} (« {brut} »)")
        motif = (p_.get('tier_justification') or p_.get('justification')
                 or p_.get('pourquoi_cette_tier') or '')
        if len(str(motif).strip()) < 15:
            sans_motif.append(pid)
    if sans_tier:
        errs.append(f"C9: {len(sans_tier)} piste(s) sans `tier` ({', '.join(sans_tier[:5])}) — "
                    f"le chasseur pose la tier de chaque piste contre les règles de son axe ; "
                    f"une piste sans tier arrive au montage sans point de départ à corriger.")
    if hors_bareme:
        errs.append(f"C9: tier hors barème sur {', '.join(hors_bareme[:5])} — "
                    f"les six tiers sont : {' · '.join(TIERS_AFFICHAGE)}.")
    if sans_motif:
        errs.append(f"C9: {len(sans_motif)} piste(s) sans justification de tier "
                    f"({', '.join(sans_motif[:5])}) — une tier dit pourquoi celle-là et pas la "
                    f"voisine, sinon elle n'est pas relisable.")

    # C8 — quota d'exploration : les graines d'axes hors périmètre commandé
    ac = ws / 'state' / 'axes-candidats.json'
    if not ac.exists():
        errs.append("C8: `state/axes-candidats.json` absent — le quota d'exploration (15-20 %, "
                    "cf. veille-launch-researcher § QUOTA D'EXPLORATION) n'a pas tourné. "
                    "Sans éclaireur qui rapporte hors axes, aucun nouvel axe ne peut naître "
                    "et la veille ne fait que confirmer ce qu'on lui a commandé.")
    else:
        try:
            d = json.loads(ac.read_text(encoding='utf-8'))
            graines = d if isinstance(d, list) else next(
                (d[k] for k in ('candidats', 'graines', 'seeds', 'axes_candidats', 'axes')
                 if isinstance(d.get(k), list) and d[k]), [])
        except json.JSONDecodeError as e:
            errs.append(f"C8: `state/axes-candidats.json` JSON invalide: {e}")
            graines = []
        if not graines:
            errs.append("C8: `state/axes-candidats.json` ne contient aucune graine — "
                        "l'éclaireur n'a rien rapporté hors axes définis. Un lot vide est possible, "
                        "mais il doit être motivé, pas silencieux.")
        # axes déjà commandés : une graine qui retombe dedans n'est pas une exploration
        axes_connus = set()
        rc = ws / 'run-config.json'
        if rc.exists():
            try:
                axes_connus = {str(a.get('name') if isinstance(a, dict) else a).strip().lower()
                               for a in (json.loads(rc.read_text(encoding='utf-8')).get('axes') or [])}
            except json.JSONDecodeError:
                pass
        for g in graines:
            if not isinstance(g, dict):
                continue
            nom = str(g.get('sujet') or g.get('axe') or g.get('nom') or g.get('axe_propose') or g.get('titre') or '?')
            if nom.strip().lower() in axes_connus:
                errs.append(f"C8: graine `{nom}` retombe dans un axe déjà commandé — "
                            f"ce n'est pas de l'exploration.")
            if not (g.get('pourquoi_hors_axes') or g.get('pourquoi') or '').strip():
                errs.append(f"C8: graine `{nom}` sans `pourquoi_hors_axes` — "
                            f"une graine doit dire en quoi elle n'entre dans aucun axe existant.")
            if not any(g.get(k) for k in ('source', 'url', 'preuves', 'sources', 'refs', 'liens')):
                errs.append(f"C8: graine `{nom}` sans source — non vérifiable.")

    return errs
