"""
Validateur étape 2.5 — VÉRIFICATION DE CHASSE.

Les vérificateurs sont des agents frais, lancés par le runtime (jamais par le chef
de chasse) : ils notent chaque piste sur les 5 critères, posent les éliminatoires,
puis passent le test d'intérêt.

Contrats vérifiés :
2. Pour chaque chasseur qui a produit des pistes, un `notes-<chasseur>-T<n>.json`
   existe avec le format exact du vérificateur.
3. Chaque piste PASSANTE a ses 5 notes complètes (pas 0 par défaut sans justification).
4. Chaque piste PASSANTE a `titre_a_revoir` renseigné.
5. Un `verifier_pass_stamp-<chasseur>-T<n>` par lot vérifié.

Retour : liste de strings, une par contrat cassé, ou [] si tout va bien.
"""
import json, re, pathlib



def _couverture_regles(ws, errs):
    # C6 — les regles d'axe validees par le lecteur ont-elles guide les recherches ?
    regles_f = None
    for cand in (ws / 'state' / 'regles-axes.json', ws / 'regles-axes.json'):
        if cand.exists():
            regles_f = cand; break
    if regles_f:
        try:
            R = json.loads(regles_f.read_text(encoding='utf-8'))
        except Exception as e:
            errs.append("C6: `regles-axes.json` illisible: %s" % e)
            R = None
        effort = None
        for cand in (ws / 'state' / 'effort-chasse.json', ws / 'effort-chasse.json'):
            if cand.exists():
                try: effort = json.loads(cand.read_text(encoding='utf-8'))
                except Exception: effort = None
                break
        if R and effort:
            # les requetes, tous chasseurs confondus et par chasseur
            par_chasseur = {}
            for c in (effort.get('par_chasseur') or []):
                nom = (c.get('chasseur') or '').lower()
                par_chasseur.setdefault(nom, []).extend(c.get('requetes') or [])
            toutes = [q.lower() for qs in par_chasseur.values() for q in qs]
            for axe, regles in (R.get('axes') or {}).items():
                for r in (regles or []):
                    if (r.get('statut') or '') != 'validee':
                        continue
                    cles = [str(k).lower() for k in (r.get('mots_cles') or []) if k]
                    if not cles:
                        errs.append("C6: la regle validee de l'axe `%s` n'a pas de `mots_cles` — "
                                    "sans eux on ne peut pas verifier qu'elle a servi." % axe)
                        continue
                    vise = [q for q in toutes if any(k in q for k in cles)]
                    if not vise:
                        errs.append("C6: axe `%s` — aucune requete ne vise la regle validee "
                                    "« %s » (mots-cles : %s). Elle n'a pas guide la chasse."
                                    % (axe, (r.get('regle') or '')[:70], ', '.join(cles[:4])))



def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)
    _couverture_regles(ws, errs)   # independant du format des lots : evalue d'emblee

    # les lots à vérifier sont ceux que la chasse a rendus
    pistes_files = sorted(ws.glob('pistes-*-T*.md')) + sorted((ws / 'notes').glob('pistes-*-T*.md'))
    chasseurs_tours = set()
    for f in pistes_files:
        m = re.match(r'pistes-(.+)-T(\d+)\.md$', f.name)
        if m:
            chasseurs_tours.add((m.group(1), int(m.group(2))))
    passants = set()
    if not chasseurs_tours:
        errs.append("C2: aucun lot de pistes à vérifier — la chasse n'a rien rendu au format "
                    "`pistes-<chasseur>-T<n>.md`, il n'y a rien à noter.")
        return errs

    # C2 — notes-<chasseur>-T<n>.json
    for chasseur, tour in sorted(chasseurs_tours):
        # le lot peut vivre a la racine du workspace ou sous state/ : c'est le
        # meme livrable, l'emplacement n'est pas un critere de qualite
        notes_file = next((c for c in (ws / f'notes-{chasseur}-T{tour}.json',
                                       ws / 'state' / f'notes-{chasseur}-T{tour}.json')
                           if c.exists()), ws / f'notes-{chasseur}-T{tour}.json')
        if not notes_file.exists():
            errs.append(f"C2: `notes-{chasseur}-T{tour}.json` absent — le vérificateur n'a pas livré au bon format")
            continue
        try:
            n = json.loads(notes_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            errs.append(f"C2: `notes-{chasseur}-T{tour}.json` JSON invalide: {e}")
            continue
        pistes = n if isinstance(n, list) else next(
                (n[k] for k in ('pistes', 'lot', 'findings', 'notes', 'notes_par_finding', 'evaluations')
                 if isinstance(n.get(k), list)), [])
        if not pistes:
            errs.append(f"C2: `notes-{chasseur}-T{tour}.json` n'a aucune piste")
            continue
        for p in pistes:
            if not isinstance(p, dict):
                errs.append(f"C2: `notes-{chasseur}-T{tour}.json` — entree qui n'est pas une piste")
                continue
            pid = p.get('id') or p.get('fid') or '?'

            # verdict : explicite, ou deduit des eliminatoires + du passage de barre
            verdict = p.get('verdict')
            if verdict is None:
                elim = p.get('elim') or {}
                rate = any(v is False for k, v in elim.items() if k != 'motif')
                verdict = 'ÉLIMINÉ' if rate else ('PASSANT' if p.get('passe_barre') else 'SOUS-BARRE')
            if verdict not in ('PASSANT', 'SOUS-BARRE', 'ÉLIMINÉ'):
                errs.append(f"C2: piste `{pid}` — verdict invalide: {verdict}")

            if verdict != 'PASSANT':
                continue
            passants.add(pid)

            # C3 — les 5 notes, chacune chiffree ET justifiee
            notes = p.get('notes') or {}
            justif_a_part = p.get('justifications') or {}
            valeurs = {}
            for k in ('poids', 'disruptivite', 'delta', 'matiere', 'contradiction'):
                brut = notes.get(k)
                v = brut.get('n') if isinstance(brut, dict) else brut
                valeurs[k] = v
                if v is None:
                    errs.append(f"C3: piste `{pid}` PASSANT — note `{k}` absente")
                elif not isinstance(v, int) or v < 0 or v > 3:
                    errs.append(f"C3: piste `{pid}` — note `{k}={v}` hors [0..3]")
                just = (brut.get('justif') or brut.get('obj')) if isinstance(brut, dict) else justif_a_part.get(k)
                if not (just if isinstance(just, str) else '').strip():
                    errs.append(f"C3: piste `{pid}` — justification `{k}` manquante")
            if all(valeurs.get(k) == 0 for k in ('poids', 'disruptivite', 'delta', 'matiere', 'contradiction')):
                errs.append(f"C3: piste `{pid}` PASSANT — les 5 notes sont a 0 "
                            f"(placeholder par defaut, scores non joints)")

            # C4 — le titre doit avoir ete rejuge
            if not any(k in p for k in ('titre_a_revoir', 'titre_revu', 'titre_propose')):
                errs.append(f"C4: piste `{pid}` PASSANT — aucun avis sur le titre "
                            f"(`titre_a_revoir` attendu)")

        # C5 — verifier_pass_stamp
        stamp = next((c for c in (ws / 'state' / f'verifier_pass_stamp-{chasseur}-T{tour}',
                                  ws / f'verifier_pass_stamp-{chasseur}-T{tour}',
                                  ws / 'state' / f'verifier_pass_stamp-{chasseur}',
                                  ws / f'verifier_pass_stamp-{chasseur}')
                      if c.exists()), None)
        if stamp is None:
            errs.append(f"C5: `state/verifier_pass_stamp-{chasseur}-T{tour}` absent — lot non estampillé")


    # C13 — test d'interet : le « et alors ? » de chaque piste qui passe la barre.
    # Distinct de la notation : celle-ci dit si c'est VRAI, celui-la si ca CHANGE QUELQUE CHOSE.
    et_alors_vus = {}
    for fid in sorted(passants):
        vi = ws / 'verifications-interet' / f'{fid}.json'
        if not vi.exists():
            errs.append(f"C13: piste `{fid}` PASSANTE — pas passee par le test d'interet "
                        f"(artefact `verifications-interet/{fid}.json` absent)")
            continue
        try:
            d = json.loads(vi.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            errs.append(f"C13: `verifications-interet/{fid}.json` JSON invalide: {e}")
            continue
        ea = str(d.get('et_alors') or '').strip()
        verdict = d.get('verdict')
        if verdict == 'INTÉRESSANT':
            if not ea:
                errs.append(f"C13: piste `{fid}` — verdict INTERESSANT sans « et alors ? » : "
                            f"un finding qu'on ne sait pas justifier ne passe pas")
            elif len(ea.split()) < 6:
                errs.append(f"C13: piste `{fid}` — « et alors ? » trop court "
                            f"({len(ea.split())} mots), probablement generique")
            else:
                k = ' '.join(ea.lower().split())
                if k in et_alors_vus:
                    errs.append(f"C13: pistes `{et_alors_vus[k]}` et `{fid}` ont le MEME "
                                f"« et alors ? » — au moins l'un des deux est generique")
                else:
                    et_alors_vus[k] = fid
        elif verdict == 'SANS INTÉRÊT' and not d.get('motif'):
            errs.append(f"C13: piste `{fid}` — ecartee sans motif (deja-su / sans-consequence / "
                        f"hors-prisme / generique)")
    return errs
