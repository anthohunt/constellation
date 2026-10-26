"""
Validateur étape 3 — CONSTELLATION (monteur + synthétiseur).

Contrats vérifiés (voir templates/brief-monteur.md et brief-synthetiseur.md) :
1. `findings.json` existe, JSON valide.
2. Chaque finding a: id, titre, axe, url, date_fait, essentiel, tier valide, tier_justification.
25. La tier reportee est celle posee a l'etape 2 : le monteur ne reclasse pas.
3. Chaque finding a `notes_chasse` non-défaut (< 5% de findings avec toutes-notes-à-0).
4. Anti-symétrie: pas de distribution tier identique sur ≥ 6 axes.
5. Chaque finding a `titre_a_revoir` renseigné, `verifier_pass_stamp` non vide.
6. Essentiel present et decoupe en paragraphes (>= 3). La longueur n'est pas un critere.
23. Style: chaque essentiel est passe par le juge de style (`verifications-style/<fid>.json`),
    qui le compare a `veille-style/reference-redaction.md` et rend conforme/refuse avec motif.
7. `constellation-bundle/constellation-data.json` déployé.
13. Intérêt: chaque finding est passé par `veille-verif-interet` (artefact `verifications-interet/<fid>.json`
    avec un « et alors ? » non vide et non générique) — un finding vrai mais sans intérêt ne doit pas atteindre le lecteur.
11. Layout aéré: `nlanes >= len(nodes)` et chaque node a un `lane` distinct (0 étoile empilée).
12. Tiers du bundle exclusivement dans le vocabulaire du viewer (`Excellent | Cool | Intéressant | Neutre | Bof | Inutile`) — tout autre libellé (EN ou tier non-supporté) rend les nodes concernés invisibles.

Retour : liste de strings, une par contrat cassé.
"""
import re, json, re, pathlib, collections

TIERS_VALIDES = {'Excellent', 'Cool', 'Intéressant', 'Neutre', 'Bof', 'Inutile'}
# TIERS_VIEWER = ceux que constellation.html sait rendre (const TIERS = [...] ligne ~948).
# Un tier hors de ce set fait chuter le node du filter mine.filter(d=>tierCourante(d)===t) → INVISIBLE.
TIERS_VIEWER = {'Excellent', 'Cool', 'Intéressant', 'Neutre', 'Bof', 'Inutile'}
# ordre canonique, du coeur vers la peripherie
TIERS_ORDRE = ['Excellent', 'Cool', 'Intéressant', 'Neutre', 'Bof', 'Inutile']

# Ce que juge le VERIFICATEUR, pas le monteur : la fidelite aux sources, la
# clarte, la lisibilite, la qualite du classement, et la trace de son propre
# passage. Le reste — structure des findings, bundle — appartient a celui qui
# fabrique. Le monteur REPORTE la tier posee a l'etape 2, il ne la pose pas :
# le juger sur la qualite d'un classement qu'il n'a pas fait serait le refuser
# pour une faute qu'il ne peut pas commettre.
PORTEE_VERIF = {'C4', 'C9', 'C10', 'C13', 'C14', 'C15', 'C16', 'C17', 'C19', 'C21', 'C23'}


def _code(err):
    m = re.match(r'\s*(C\d+)\s*[:.]', err or '')
    return m.group(1) if m else ''


def _filtrer_mode(errs, workspace):
    """Une collecte ramene des elements, pas des explications : les contrats qui
    jugent une explication redigee ne s'y appliquent pas."""
    try:
        import sys as _sm, os as _om
        _sm.path.insert(0, _om.path.dirname(_om.path.dirname(_om.path.abspath(__file__))))
        from mode_run import filtrer_redaction
    except Exception:
        return errs
    return filtrer_redaction(errs, workspace, _code)


def validate(workspace, portee='tout'):
    """portee : 'montage' (ce que produit le nœud 3), 'verification' (le nœud 3.5),
    ou 'tout'. Les contrats restent ici : un seul domicile, deux lectures."""
    errs = _filtrer_mode(_tous(workspace), workspace)
    if portee == 'montage':
        return [e for e in errs if _code(e) not in PORTEE_VERIF]
    if portee == 'verification':
        return [e for e in errs if _code(e) in PORTEE_VERIF]
    return errs


def _tous(workspace):
    errs = []
    ws = pathlib.Path(workspace)

    # C1 — findings.json
    findings_file = ws / 'findings.json'
    if not findings_file.exists():
        errs.append("C1: `findings.json` absent à la racine du workspace")
        return errs
    try:
        F = json.loads(findings_file.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        errs.append(f"C1: `findings.json` JSON invalide: {e}")
        return errs

    # Un tableau nu est une variante d'emballage equivalente : on la ramene a la
    # forme dict des l'entree, le reste du validateur n'a pas a la connaitre.
    if isinstance(F, list):
        F = {'findings': F}
    findings = F.get('findings') if isinstance(F, dict) else None
    if not findings:
        errs.append("C1: `findings.json` ne contient aucun finding (attendu clé `findings` ou array)")
        return errs

    # C2 — champs obligatoires par finding
    zero_scored = 0
    axe_tier = collections.defaultdict(collections.Counter)
    for f in findings:
        fid = f.get('id', '?')
        for field in ('titre', 'axe', 'url', 'date_fait', 'essentiel'):
            if not f.get(field):
                errs.append(f"C2: finding `{fid}` — champ `{field}` manquant/vide")

        tier = f.get('tier')
        if tier not in TIERS_VALIDES:
            errs.append(f"C2: finding `{fid}` — tier invalide: {tier}")
        else:
            axe = f.get('axe', '?')
            axe_tier[axe][tier] += 1

        tj = (f.get('tier_justification') or '').strip()
        if not tj:
            errs.append(f"C2: finding `{fid}` — `tier_justification` manquant — elle vient "
                        f"du chasseur (etape 2), le monteur la reporte")

        if 'titre_a_revoir' not in f:
            errs.append(f"C5: finding `{fid}` — champ `titre_a_revoir` manquant")
        if not f.get('verifier_pass_stamp'):
            errs.append(f"C5: finding `{fid}` — `verifier_pass_stamp` absent (gate d'entrée cassé)")
        if not f.get('essentiel_verifie'):
            errs.append(f"C9: finding `{fid}` — essentiel non passé par `veille-verif-carte` (`essentiel_verifie` absent/faux)")
        elif not f.get('essentiel_verif_stamp'):
            errs.append(f"C9: finding `{fid}` — `essentiel_verifie: true` mais `essentiel_verif_stamp` absent (verdict non tracé)")
        else:
            # C9-dur : le booléen n'est PAS falsifiable à la main — il doit être adossé à un
            # artefact réel produit par la passe verif-carte (verifications-carte/<fid>.json).
            # Sans l'artefact, `essentiel_verifie:true` est un champ posé sans que la passe ait tourné.
            vc = ws / 'verifications-carte' / f'{fid}.json'
            if not vc.exists():
                errs.append(f"C9: finding `{fid}` — `essentiel_verifie:true` mais artefact de passe absent "
                            f"(`verifications-carte/{fid}.json`) : le champ n'est pas adossé à une vérification réelle")

        # C23 — le juge de style. Dernier des trois juges de 3.5 : on ne juge le grain
        # d'un texte qu'une fois qu'il est vrai (C9) et compris (C17). Il ne coche pas une
        # liste : il compare a `veille-style/reference-redaction.md` et dit si c'est le
        # meme niveau d'ecriture. La longueur n'entre pas dans son verdict.
        vs = ws / 'verifications-style' / f'{fid}.json'
        if not vs.exists():
            errs.append(f"C23: finding `{fid}` — pas de jugement de style "
                        f"(`verifications-style/{fid}.json` absent) : l'essentiel n'a pas ete "
                        f"compare a la reference de redaction")
        else:
            try:
                o = json.loads(vs.read_text(encoding='utf-8'))
            except Exception:
                o = {}
            verdict = str(o.get('verdict') or '').strip().lower()
            motif = (o.get('motif') or '').strip()
            if verdict not in ('conforme', 'refuse', 'refusé'):
                errs.append(f"C23: finding `{fid}` — verdict de style illisible ({verdict or 'vide'}), "
                            f"attendu `conforme` ou `refuse`")
            elif verdict != 'conforme':
                errs.append(f"C23: finding `{fid}` — essentiel refuse par le juge de style"
                            + (f" : {motif[:160]}" if motif else " (motif manquant)"))
            elif len(motif) < 30:
                errs.append(f"C23: finding `{fid}` — verdict `conforme` sans motif ecrit : "
                            f"un juge qui ne dit pas ce qui tient n'a pas juge")

        # C3 — scores non-défaut
        nc = f.get('notes_chasse') or f.get('notes') or {}
        vals = [nc.get(k, 0) for k in ('poids','disruptivite','delta','matiere','contradiction')]
        if all(v == 0 for v in vals):
            zero_scored += 1

        # C6 — l'essentiel existe et respire.
        # La longueur n'est PAS un critere : un essentiel s'allonge a proportion de ce
        # que le sujet demande pour etre compris. Ce qui se juge est la qualite d'ecriture,
        # et elle se juge par comparaison a la reference (C23), pas au caractere pres.
        # Ne restent ici que deux planchers de forme : le texte existe, et il est
        # decoupe en paragraphes — un bloc compact ne se lit pas, quelle que soit sa taille.
        e = (f.get('essentiel') or '').strip()
        paras = [p for p in e.split('\n\n') if p.strip()]
        if not e:
            errs.append(f"C6: finding `{fid}` — essentiel vide")
        elif len(paras) < 3:
            errs.append(f"C6: finding `{fid}` — essentiel en {len(paras)} paragraphe(s) : "
                        f"une notion par paragraphe, un bloc compact ne se lit pas")

    # C3 — ratio findings avec toutes notes à 0
    if findings and zero_scored / len(findings) > 0.05:
        pct = round(100 * zero_scored / len(findings), 1)
        errs.append(f"C3: {zero_scored}/{len(findings)} findings ({pct}%) ont notes_chasse={{0,0,0,0,0}} — les scores du vérificateur n'ont pas voyagé au monteur")

    # C25 — le report de tier est fidele. Le monteur ne classe pas : il reporte ce que
    # le chasseur a pose a l'etape 2. Une tier qui bouge entre les deux fichiers est un
    # classement clandestin — celui qui ecrit le texte ne decide pas de sa place.
    _brut = None
    for _c in (ws / 'state' / 'passants-raw.jsonl', ws / 'passants-raw.jsonl'):
        if _c.exists():
            _brut = _c
            break
    if _brut:
        _pose = {}
        for _l in _brut.read_text(encoding='utf-8', errors='replace').splitlines():
            _l = _l.strip()
            if not _l:
                continue
            try:
                _p = json.loads(_l)
            except json.JSONDecodeError:
                continue
            _t = (_p.get('tier') or _p.get('tier_proposee') or '').strip()
            if _p.get('id') and _t:
                _pose[_p['id']] = _t
        _derives = []
        for f in findings:
            _av = _pose.get(f.get('id'))
            if _av and (f.get('tier') or '').strip() != _av:
                _derives.append(f"{f.get('id')} : {_av} -> {f.get('tier')}")
        if _derives:
            errs.append(f"C25: {len(_derives)} tier(s) modifiee(s) entre la chasse et le montage "
                        f"({'; '.join(_derives[:5])}) — le monteur REPORTE la tier de l'etape 2. "
                        f"Une correction de classement appartient au lecteur (etape 4).")

    # C4 — anti-symétrie
    if len(axe_tier) >= 6:
        signatures = collections.Counter()
        for axe, counts in axe_tier.items():
            sig = tuple(sorted(counts.items()))
            signatures[sig] += 1
        for sig, n in signatures.items():
            if n >= 6:
                d = ', '.join(f'{t}={c}' for t, c in sig)
                errs.append(f"C4: {n} axes ont la même distribution tier ({d}) — remplissage mécanique, classement au feeling")

    # C10 — priorité de relecture (uncertainty sampling)
    prioritaires = [f for f in findings if f.get('priorite_relecture')]
    if findings:
        ratio = len(prioritaires) / len(findings)
        if ratio < 0.10 or ratio > 0.35:
            pct = round(100 * ratio, 1)
            errs.append(f"C10: {len(prioritaires)}/{len(findings)} findings ({pct}%) marqués `priorite_relecture: true` — hors cible [15%, 25%]")
    for f in prioritaires:
        if not (f.get('priorite_motif') or '').strip():
            errs.append(f"C10: finding `{f.get('id','?')}` prioritaire — `priorite_motif` manquant (le viewer l'affiche en tooltip)")

    # C8 — synthèses de fils (mode FIL du synthétiseur)
    fils = F.get('fils') or []
    for fil in fils:
        slug = fil.get('slug', '?')
        fc = fil.get('findings_courant') or []
        fp = fil.get('findings_passes') or []
        # Fil actif = ≥ 2 courants OU ≥ 1 courant + ≥ 2 passés
        actif = len(fc) >= 2 or (len(fc) >= 1 and len(fp) >= 2)
        if not actif:
            continue
        syn = (fil.get('synthese') or '').strip()
        if not syn:
            errs.append(f"C8: fil `{slug}` actif ({len(fc)} courants, {len(fp)} passés) — `synthese` manquante")
            continue
        L = len(syn)
        if L < 800 or L > 1500:
            errs.append(f"C8: fil `{slug}` — synthèse de {L} caractères, hors cible [800, 1500]")
        if '→' not in syn:
            errs.append(f"C8: fil `{slug}` — synthèse sans lecture actionnable (aucune flèche `→`)")
        # au moins 1 fid nommé
        fids_courants = set(fc)
        if not any(fid in syn for fid in fids_courants):
            errs.append(f"C8: fil `{slug}` — synthèse ne nomme aucun `fid` du fil")

    # C7 — constellation déployée
    cbundle = ws / 'constellation-bundle' / 'constellation-data.json'
    if not cbundle.exists():
        errs.append(f"C7: `constellation-bundle/constellation-data.json` absent (constellation d'éval non déployée)")
    else:
        # C13 — filet : tout finding retenu doit porter son artefact d'interet.
        # La QUALITE du « et alors ? » est jugee a l'etape 2.5, par le noeud qui le produit.
        for f in findings:
            fid = f.get('id', '?')
            if not (ws / 'verifications-interet' / f'{fid}.json').exists():
                errs.append(f"C13: finding `{fid}` — pas d'artefact d'interet "
                            f"(`verifications-interet/{fid}.json`) : entre dans la constellation "
                            f"sans etre passe par le test du « et alors ? »")

        # C11 — layout aéré : nlanes >= len(nodes) et pas de node empilé
        try:
            cdata = json.loads(cbundle.read_text(encoding='utf-8'))
            cnodes = cdata.get('nodes', [])
            nlanes = cdata.get('nlanes', 0)
            if cnodes:
                if nlanes < len(cnodes):
                    errs.append(f"C11: `nlanes`={nlanes} < len(nodes)={len(cnodes)} — layout empilé, attendu >= 1 lane par node (formule: nlanes = max(1, len(nodes)))")
                lane_counts = collections.Counter(n.get('lane') for n in cnodes)
                stacked = {lane: c for lane, c in lane_counts.items() if c > 1}
                if stacked:
                    worst_lane, worst_c = max(stacked.items(), key=lambda x: x[1])
                    errs.append(f"C11: {len(stacked)} lanes empilent plusieurs nodes (worst: lane {worst_lane} = {worst_c} nodes) — chaque node doit avoir un `lane` distinct, sorti de sorted(nodes, key=(axes.index(axe), stable))")

                # C12 — tiers du bundle dans le vocabulaire du viewer
                bad_tiers = collections.Counter()
                for node in cnodes:
                    t = node.get('tier')
                    if t and t not in TIERS_VIEWER:
                        bad_tiers[t] += 1
                if bad_tiers:
                    parts = ', '.join(f'{t}={n}' for t, n in sorted(bad_tiers.items(), key=lambda x:-x[1]))
                    total = sum(bad_tiers.values())
                    errs.append(f"C12: {total}/{len(cnodes)} nodes ont un `tier` hors vocabulaire viewer (rendus INVISIBLES): {parts}. Attendu: {sorted(TIERS_VIEWER)} — mapper EN→FR (Interesting→Intéressant, Useless→Inutile) et rabattre Cool/Neutre au build.")
        except (json.JSONDecodeError, OSError) as e:
            errs.append(f"C11: `constellation-bundle/constellation-data.json` illisible pour audit layout: {e}")

    # C14 — le francais s'ecrit avec ses accents. On ne juge plus sur une liste de
    # mots ecrite a la main : `accents_fr` connait le lexique complet et sait quels
    # mots non accentues sont legitimes (« marche », « cote »). Une passe automatique
    # corrige ces fautes avant ce controle ; ce qui subsiste ici est donc anormal.
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__)))))
        from accents_fr import suspects as _suspects
    except Exception:
        _suspects = None
    if _suspects:
        for f in findings:
            fid = f.get('id', '?')
            for champ in ('essentiel_fr', 'essentiel'):
                txt = (f.get(champ) or (f.get('fiche') or {}).get(champ) or '')
                if not isinstance(txt, str) or len(txt) < 200:
                    continue
                fautes = _suspects(txt)
                if fautes:
                    errs.append(f"C14: finding `{fid}` — `{champ}` : {len(fautes)} mot(s) "
                                f"ecrits sans accent ({', '.join(sorted(set(fautes))[:5])}). "
                                f"Le francais porte tous ses accents, capitales comprises.")
                break

    # C16 — clarte mesurable. Trois defauts qu'un lecteur non specialiste subit :
    # un sigle jamais developpe, une phrase interminable, une phrase faite de noms
    # abstraits sans personne dedans (« mecanismes de soutien cibles limites »).
    SIGLES_LIBRES = {'IA', 'AI', 'UE', 'EU', 'USA', 'US', 'PIB', 'GPU', 'CPU', 'API', 'PDG',
                     'ONU', 'OCDE', 'RGPD', 'PDF', 'URL', 'RAM', 'OS', 'IT', 'RH', 'CO2',
                     'GPT', 'PC', 'TV', 'SMS', 'ADN', 'QI', 'CEO', 'NASA', 'MIT'}
    ABSTRAIT = re.compile(r'\w+(?:tions?|ments?|it[ée]s?|ismes?|ances?|ences?)$', re.I)
    PONCT = ".,;:()«»’'\""
    MOTS_MAX = 34
    for f in findings:
        fid = f.get('id', '?')
        txt = (f.get('essentiel_fr') or (f.get('fiche') or {}).get('essentiel_fr')
               or f.get('essentiel') or (f.get('fiche') or {}).get('essentiel') or '')
        if not isinstance(txt, str) or len(txt) < 200:
            continue
        nu = re.sub(r'[*_`]', '', txt)

        # a. sigles jamais developpes (nom complet a cote, sous une forme ou l'autre)
        orphelins = []
        for sig in dict.fromkeys(re.findall(r'\b[A-Z]{2,6}\b', nu)):
            if sig in SIGLES_LIBRES:
                continue
            e = re.escape(sig)
            # glose acceptee sous toutes ses formes usuelles : parenthese, apposition,
            # tiret d'incise, « c'est-a-dire », « ou » de reformulation.
            if (re.search(e + r"\s*[(,—–-]", nu) or re.search(r"\(\s*" + e, nu)
                    or re.search(r"(?:ou|soit|c'est-à-dire|dit)\s+\W?" + e, nu, re.I)):
                continue
            orphelins.append(sig)
        if orphelins:
            errs.append(f"C16: finding `{fid}` — sigle(s) jamais developpe(s) : "
                        f"{', '.join(orphelins[:5])}. Nom complet a la premiere occurrence, "
                        f"ou pas de sigle du tout.")

        for phrase in re.split(r'(?<=[.!?])\s+', nu):
            mots = [w.strip(PONCT) for w in phrase.split() if len(w) > 2]
            if len(mots) < 10:
                continue
            if len(phrase.split()) > MOTS_MAX:
                errs.append(f"C16: finding `{fid}` — phrase de {len(phrase.split())} mots "
                            f"(max {MOTS_MAX}) : « {phrase[:70]}... ». Coupe-la en deux.")
            # les enumerations (deux-points + liste) sont denses mais lisibles
            if ':' in phrase and phrase.count(',') >= 2:
                continue
            dens = sum(1 for w in mots if ABSTRAIT.match(w)) / len(mots)
            if dens > 0.32:
                errs.append(f"C16: finding `{fid}` — phrase sans acteur concret "
                            f"({round(dens*100)}% de noms abstraits) : « {phrase[:70]}... ». "
                            f"Dis qui fait quoi.")

    # C17 — relecture profane : un agent frais, qui n'a pas ecrit le texte et n'a pas lu la
    # source, redit chaque fait avec ses mots. Un redacteur relit toujours son texte comme clair.
    dossier_clarte = ws / 'state' / 'clarte'
    if not dossier_clarte.exists():
        dossier_clarte = ws / 'clarte'
    if not dossier_clarte.exists():
        errs.append("C17: aucune relecture profane (`state/clarte/<fid>.json` absent). "
                    "Chaque essentiel doit etre relu par un agent frais qui le reformule.")
    else:
        vus, a_reecrire = set(), []
        for j in dossier_clarte.glob('*.json'):
            try:
                o = json.loads(j.read_text(encoding='utf-8'))
            except Exception:
                continue
            fid = o.get('fid') or j.stem
            reformule = (o.get('reformulation') or '').strip()
            verdict = (o.get('verdict') or '').strip().lower()
            if verdict.replace('à', 'a').replace('é', 'e') in ('a_reecrire', 'a reecrire', 'illisible'):
                a_reecrire.append(fid)
            elif len(reformule) >= 40 or o.get('compris') is True:
                vus.add(fid)
        manquants = [f.get('id') for f in findings if f.get('id') not in vus]
        if manquants:
            errs.append(f"C17: {len(manquants)} finding(s) sans relecture profane exploitable "
                        f"(ex. {', '.join(str(m) for m in manquants[:3])}).")
        # notions a retenir : le plafond est le meme que celui de C22-densite, mais
        # ici c'est un lecteur qui compte, pas un lexique — il attrape les notions
        # qu'aucune liste ne contient (Langevin, laplacien, reservoir computing).
        trop_dense = []
        for j in dossier_clarte.glob('*.json'):
            try:
                o = json.loads(j.read_text(encoding='utf-8'))
            except Exception:
                continue
            fid = o.get('fid') or j.stem
            n = o.get('notions_avalees')
            if isinstance(n, int) and n > 3:
                trop_dense.append('%s (%d)' % (fid, n))
        if trop_dense:
            errs.append("C17: %d finding(s) ou le relecteur a du retenir plus de trois notions "
                        "nouvelles (%s). Gloser chaque terme ne suffit pas : garde trois briques, "
                        "descends le reste dans le rapport de fond."
                        % (len(trop_dense), ', '.join(trop_dense[:4])))
        if a_reecrire:
            errs.append(f"C17: {len(a_reecrire)} finding(s) encore marques « a reecrire » par le "
                        f"relecteur (ex. {', '.join(a_reecrire[:3])}). Reecris-les avant de sortir.")

    # C18 — le pre-classement suit l'echelle courante, pas une echelle abandonnee.
    # Pas de quota : on ne demande pas une part de chaque niveau, seulement que les
    # niveaux intermediaires aient ete envisages quand le vivier est assez grand.
    INTERMEDIAIRES = {'Cool', 'Neutre'}
    if len(findings) >= 25:
        poses = {(f.get('tier') or '').strip() for f in findings}
        if not (poses & INTERMEDIAIRES):
            comptes = {}
            for f in findings:
                t = (f.get('tier') or '?').strip()
                comptes[t] = comptes.get(t, 0) + 1
            detail = ', '.join(f'{k} {v}' for k, v in sorted(comptes.items(), key=lambda x: -x[1]))
            errs.append(
                f"C18: sur {len(findings)} findings, aucun n'est classe dans un niveau "
                f"intermediaire ({' ni '.join(sorted(INTERMEDIAIRES))}) — reparti : {detail}. "
                f"L'echelle en compte SIX : {' > '.join(TIERS_ORDRE)}. Reprends le pre-classement "
                f"sur les six niveaux, au merite et relativement aux autres findings du meme axe.")

    # C19 — un chiffre ne voyage jamais seul. Deux defauts distincts :
    # (a) un banc d'essai nomme sans dire ce qu'il mesure — c'est du jargon ;
    # (b) un essentiel qui empile les variations chiffrees sans jamais les traduire.
    BANCS = re.compile(r'\b(SWE-?bench|MMLU|ARC-?AGI|LIBERO|HumanEval|GSM8K|BIG-?bench|HELM|'
                       r'ImageNet|COCO|GPQA|AIME|LiveBench|Chatbot Arena|MT-?Bench)\b', re.I)
    TRADUIT = re.compile(r"c'est-à-dire|autrement dit|en pratique|concrètement|soit\b|"
                         r"revient à|ce qui veut dire|ce qui signifie|équivaut|en clair|"
                         r"au quotidien|c'est le niveau|contre\b", re.I)
    CHIFFRE = re.compile(r'\d+[,.]?\d*\s*(?:%|pts?\b|points?\b|×|fois\b)')
    for f in findings:
        fid = f.get('id', '?')
        txt = (f.get('essentiel_fr') or (f.get('fiche') or {}).get('essentiel_fr')
               or f.get('essentiel') or (f.get('fiche') or {}).get('essentiel') or '')
        if not isinstance(txt, str) or len(txt) < 200:
            continue
        nu = re.sub(r'[*_`]', '', txt)
        nus = []
        for b in dict.fromkeys(m.group(0) for m in BANCS.finditer(nu)):
            e = re.escape(b)
            # presente = suivi d'une apposition/parenthese, ou introduit par « sur le test … »
            if re.search(e + r'\s*[(,]', nu) or re.search(r'\(\s*' + e, nu):
                continue
            if re.search(r'(?:test|banc|batterie|epreuve|épreuve|jeu d.essai)[^.]{0,40}' + e, nu, re.I):
                continue
            nus.append(b)
        if nus:
            errs.append(f"C19: finding `{fid}` — banc(s) d'essai cite(s) sans dire ce qu'ils "
                        f"mesurent : {', '.join(nus[:4])}. Un nom de benchmark nu est du jargon.")
        phrases_chiffrees = [ph for ph in re.split(r'(?<=[.!?])\s+', nu) if CHIFFRE.search(ph)]
        if len(phrases_chiffrees) >= 2 and not TRADUIT.search(nu):
            errs.append(f"C19: finding `{fid}` — {len(phrases_chiffrees)} phrases chiffrees et "
                        f"aucune traduction en effet concret. Dis ce que ces chiffres changent, "
                        f"ou retire-les.")

    # C20 — les findings apparentes portent un lien. Ni fusionnes ni relies, ils
    # obligent le lecteur a decouvrir lui-meme qu'il lit deux fois la meme histoire.
    import math as _math, collections as _coll
    STOP_LIENS = set(('les des une pour dans avec sur que qui plus sans leur sont est ont '
                      'cette entre elle comme deux trois selon mais aussi tout tous fait '
                      'faire dont chez alors ainsi donc lors leurs publie publient chercheurs '
                      'equipe etude papier travail resultat resultats modele modeles').split())
    def _sac(x):
        t = ' '.join([(x.get('headline_fr') or x.get('headline') or ''),
                      ((x.get('fiche') or {}).get('essentiel_fr') or x.get('essentiel_fr') or '')])
        return set(w for w in re.findall(r'[A-Za-zÀ-ÿ]{5,}', t.lower()) if w not in STOP_LIENS)
    cn = findings
    if len(cn) >= 12:
        sacs = [_sac(x) for x in cn]
        df = _coll.Counter()
        for sa in sacs: df.update(sa)
        NB = len(cn)
        def _liens_de(x):
            l = x.get('rel') or x.get('liens') or x.get('fil') or []
            if isinstance(l, str): l = [l]
            return {str(v) for v in l if v}
        manquants = []
        for i in range(NB):
            for j in range(i + 1, NB):
                communs = [w for w in (sacs[i] & sacs[j]) if df[w] <= 6]
                score = sum(_math.log(NB / df[w]) for w in communs)
                if score < 18: continue
                a, b = cn[i], cn[j]
                ida, idb = str(a.get('id')), str(b.get('id'))
                if idb in _liens_de(a) or ida in _liens_de(b): continue
                manquants.append((ida, idb, sorted(communs, key=lambda w: -df[w])[:3]))
        if manquants:
            ex = '; '.join('%s <-> %s (%s)' % (m[0][:22], m[1][:22], ', '.join(m[2])) for m in manquants[:4])
            errs.append("C20: %d paire(s) de findings traitent visiblement du meme sujet sans etre "
                        "reliees : %s. Fusionne-les, ou pose le lien (`rel`) pour que le lecteur "
                        "sache qu'il lit la suite de la meme histoire." % (len(manquants), ex))

    # C21 — lisibilite mesuree (Kandel-Moles, adaptation francaise de Flesch) :
    # 207 - 1,015 x mots/phrase - 73,6 x syllabes/mot. 100 = tres facile, 60-70 =
    # presse grand public, 30 = texte savant. Plancher a 50 : un lecteur non
    # specialiste doit suivre sans relire.
    def _syllabes(mot):
        return max(1, len(re.findall(r'[aeiouyàâäéèêëîïôöùûüœ]+', mot.lower())))
    for f in findings:
        fid = f.get('id', '?')
        txt = (f.get('essentiel_fr') or (f.get('fiche') or {}).get('essentiel_fr')
               or f.get('essentiel') or (f.get('fiche') or {}).get('essentiel') or '')
        if not isinstance(txt, str) or len(txt) < 200:
            continue
        nu = re.sub(r'[*_`]', '', txt)
        phrases = [x for x in re.split(r'(?<=[.!?])\s+', nu) if len(x.split()) > 2]
        mots = re.findall(r"[A-Za-zÀ-ÿ']+", nu)
        if not phrases or not mots:
            continue
        mpp = len(mots) / len(phrases)
        spm = sum(_syllabes(m) for m in mots) / len(mots)
        score = 207 - 1.015 * mpp - 73.6 * spm
        if score < 50:
            longs = sorted({m for m in mots if _syllabes(m) >= 4}, key=len, reverse=True)[:5]
            errs.append("C21: finding `%s` — lisibilite %.0f/100 (plancher 50) : le texte demande "
                        "un effort de lecture. Les phrases font %.0f mots, ce n'est pas la, c'est le "
                        "vocabulaire — mots savants a remplacer par leur equivalent courant : %s."
                        % (fid, score, mpp, ', '.join(longs) if longs else 'voir les mots longs'))

    # C15 — mise en evidence : le lecteur doit pouvoir lire en diagonale.
    # __gras__ pour un fait ou un chiffre, *italique* pour un nom ou un terme.
    sans_relief = []
    for f in findings:
        txt = (f.get('essentiel_fr') or f.get('essentiel')
               or (f.get('fiche') or {}).get('essentiel') or '')
        if not isinstance(txt, str) or len(txt) < 200:
            continue
        gras = len(re.findall(r'__[^_\n]{2,}__', txt))
        ital = len(re.findall(r'(?<![\*\w])\*[^\*\n]{2,}?\*(?!\*)', txt))
        if gras + ital == 0:
            sans_relief.append(f.get('id', '?'))
    if findings and len(sans_relief) > len(findings) * 0.25:
        errs.append(f"C15: {len(sans_relief)}/{len(findings)} essentiels sans aucune mise en "
                    f"evidence (`__gras__` pour un fait ou un chiffre, `*italique*` pour un nom "
                    f"ou un terme). Sans relief, tout se lit au meme poids et rien ne ressort.")

        # C22 - le style de vulgarisation, mesure par mesure. Le modele vit dans les
    # modele de style de la pipeline (veille-style) : huit gestes,
    # dont quatre se mesurent (glose, densite de notions, contraste, bornage).
    # Meme module a l'etape 6 : un seul style pour les essentiels et la publication.
    try:
        import sys as _s22, os as _o22
        _s22.path.insert(0, _o22.path.dirname(_o22.path.dirname(_o22.path.abspath(__file__))))
        from style_vulgarisation import controler as _c22
        from style_vulgarisation import MOTS_MAX_ESSENTIEL as _max22
    except Exception:
        _c22 = None
    if _c22:
        for f in findings:
            txt = (f.get('essentiel_fr') or (f.get('fiche') or {}).get('essentiel_fr')
                   or f.get('essentiel') or '')
            errs.extend(_c22(txt, etiquette="finding " + str(f.get('id', '?'))))

    return errs
