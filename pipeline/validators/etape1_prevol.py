"""
Validateur étape 1 — PRÉ-VOL / PRÉPARATION.

Gate de sortie de l'étape 1 : le terrain est-il monté et prêt pour la chasse ?
Ne teste pas les conditions machine (moteur/mémoire/agents) — celles-là sont
vérifiées EN VIVO au moment de l'étape 1, pas a posteriori. Ici on vérifie que
les livrables de setup existent et sont cohérents.

Contrats :
1. WORKSPACE.txt présent (owner + subject gelés).
2. subject.md, profile.md, run-config.json, casting.json présents et non vides.
3. state/comptes-chasse.json présent (le tableau de comptage vierge).
4. run-config.json est un JSON valide portant des axes.
5. casting.json est un JSON valide non vide (au moins 1 chasseur).
6. casting.json contient un ÉCLAIREUR — un agent dont le mandat est de chercher HORS
   des axes définis (rôle/persona « éclaireur » ou axe « Découverte »). C'est le seul
   agent qui peut faire naître un nouvel axe ; sans lui la veille ne peut que confirmer
   ce qu'on lui a commandé. Trou constaté sur les runs 07-29, 08-01 et 08-13 : le quota
   d'exploration existait dans les skills mais aucun casting ne l'a jamais instancié.
7. `run-config.json` APPLIQUE le profil décidé au feedback précédent
   (`preferences/profil-prochaine-run.json`) : chaque axe ajouté a son entrée, et le
   volume par axe/global reste nul quand le profil a basculé en BUDGET D'EFFORT.
   Trou constaté run 4 (2026-08-17) : l'étape 1 a rechargé le profil du wizard et perdu
   les décisions de la veille — axes ajoutés absents, "volume cible 20" ressuscité.
"""
import json, os, pathlib, re

def _owner(ws):
    """owner de la run, lu dans WORKSPACE.txt (sinon déduit du nom de dossier)."""
    f = ws / 'WORKSPACE.txt'
    if f.exists():
        for l in f.read_text(encoding='utf-8', errors='replace').splitlines():
            if l.startswith('owner:'):
                return l.split(':', 1)[1].strip()
    return ''

def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)

    if not (ws / 'WORKSPACE.txt').exists():
        errs.append("C1: `WORKSPACE.txt` absent — owner/subject non gelés pour la run")

    for f in ('subject.md', 'profile.md', 'run-config.json', 'casting.json'):
        p = ws / f
        if not p.exists() or p.stat().st_size == 0:
            errs.append(f"C2: `{f}` absent/vide — setup incomplet")

    cc = ws / 'state' / 'comptes-chasse.json'
    if not cc.exists():
        errs.append("C3: `state/comptes-chasse.json` absent — tableau de comptage non créé")

    rc = ws / 'run-config.json'
    if rc.exists() and rc.stat().st_size:
        try:
            d = json.loads(rc.read_text(encoding='utf-8'))
            if not (d.get('axes')):
                errs.append("C4: `run-config.json` sans axes — la chasse partirait à l'aveugle")
        except json.JSONDecodeError as e:
            errs.append(f"C4: `run-config.json` JSON invalide: {e}")

    cast = ws / 'casting.json'
    if cast.exists() and cast.stat().st_size:
        try:
            d = json.loads(cast.read_text(encoding='utf-8'))
            n = len(d) if isinstance(d, list) else len(d.get('chasseurs') or d.get('agents') or [])
            if n == 0:
                errs.append("C5: `casting.json` sans chasseur — aucun agent à lancer")
            else:
                agents = d if isinstance(d, list) else (d.get('agents') or d.get('chasseurs') or [])
                def _is_eclaireur(a):
                    blob = ' '.join(str(a.get(k, '')) for k in
                                    ('persona', 'role', 'rôle', 'axe', 'subterrain', 'mandat')).lower()
                    return 'eclaireur' in blob or 'éclaireur' in blob or 'découverte' in blob or 'decouverte' in blob
                if not any(_is_eclaireur(a) for a in agents if isinstance(a, dict)):
                    noms = ', '.join(str(a.get('axe') or a.get('role') or a.get('persona') or '?')
                                     for a in agents if isinstance(a, dict))
                    errs.append(
                        f"C6: `casting.json` sans ÉCLAIREUR — aucun agent avec mandat hors-axes "
                        f"(persona/rôle « éclaireur » ou axe « Découverte »). Casting actuel : {noms}. "
                        f"Sans lui, le quota d'exploration (15-20 %, cf. veille-launch-researcher) "
                        f"n'a personne pour l'exécuter et la veille ne peut que confirmer les axes commandés.")
                # C6-bis : sans freshness, l'anti-doublon ne sait pas si un finding
                # archive peut encore ressortir — il copie tout au lieu de ce qui compte.
                sans = [str(a.get('axe') or a.get('role') or '?')
                        for a in agents if isinstance(a, dict) and not a.get('freshness')]
                if sans:
                    errs.append(
                        f"C6: {len(sans)} chasseur(s) sans `freshness` ({', '.join(sans[:5])}). "
                        f"Chaque chasseur en porte une, transversaux et eclaireur compris "
                        f"(defaut `mois`) : elle decide quels findings archives peuvent encore ressortir.")
        except json.JSONDecodeError as e:
            errs.append(f"C5: `casting.json` JSON invalide: {e}")

    # ── C9 : la run applique-t-elle le profil decide au feedback precedent ?
    prof = pathlib.Path(os.path.expanduser(os.environ.get('VEILLE_OWNERS_DIR', '~/veille-owners'))) / _owner(ws) / 'preferences' / 'profil-prochaine-run.json'
    if rc.exists() and rc.stat().st_size and prof.exists():
        try:
            d = json.loads(rc.read_text(encoding='utf-8'))
            pr = json.loads(prof.read_text(encoding='utf-8'))
            subj = ws / 'subject.md'
            txt = subj.read_text(encoding='utf-8', errors='replace') if subj.exists() else ''
            cfg = json.dumps(d, ensure_ascii=False)

            # a. les axes ajoutes au feedback existent bien dans la run
            noms = ' | '.join(str(a.get('name') or a.get('titre') or '')
                              for a in (d.get('axes') or [])).lower()
            manquants = []
            for aj in (pr.get('ajouts') or []):
                t = str(aj.get('name') or aj.get('titre') or '').strip()
                if t and t.split(' ')[0].lower().strip('\u00b7,') not in noms:
                    manquants.append(t)
            if manquants:
                errs.append(
                    "C9: `run-config.json` n'applique pas le profil decide au feedback precedent \u2014 "
                    "axe(s) absent(s) : " + ' ; '.join(manquants) +
                    ". Ces axes ont ete valides par le lecteur ; une run qui les ignore ne teste pas "
                    "ce qui a ete decide.")

            # b. le MODE de la run (ex. veille scientifique) est porte par le terrain
            mode = str(pr.get('mode') or '').strip()
            if mode and mode.lower() not in (txt + cfg).lower():
                errs.append(
                    "C9: la run ne porte pas le MODE decide au feedback precedent (" + mode + "). "
                    "Ni `subject.md` ni `run-config.json` ne le mentionnent : les chasseurs "
                    "repartiraient sur le perimetre de sources de la run precedente. "
                    "Cf. `mode_note` dans profil-prochaine-run.json.")

            # c. aucun quota de sortie ne survit quand le profil est passe en budget d'effort
            if pr.get('volume', 'absent') is None:
                if re.search(r'"(volume|volume_cible|target_volume|findings_cible)"\s*:\s*[0-9]',
                             cfg, re.I) or re.search(r'volume\s+(cible|par\s+axe)\s*:?\s*[0-9]', txt, re.I):
                    errs.append(
                        "C9: la run porte encore un QUOTA DE SORTIE chiffre alors que le profil est "
                        "passe en BUDGET D'EFFORT (volume: null). C'est exactement le quota qui "
                        "fabrique du remplissage : zero finding sur un axe est un resultat valide.")
        except (json.JSONDecodeError, OSError):
            pass

    return errs
