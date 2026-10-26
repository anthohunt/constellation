#!/usr/bin/env python3
"""etat-run.py — l'inventaire d'une run, en UN appel.

Pourquoi cet outil existe : sur une run complete, 153 des 452 commandes des trois
gros nœuds etaient des scripts Python jetables, reecrits a chaque fois pour
recompter les memes choses — combien de findings, quels champs manquent, quelle
longueur fait cet essentiel, quel est le md5 de ce fichier. Un tour de parole par
question, et chaque tour renvoie tout l'historique au modele.

Il rend en UNE fois ce que ces scripts recalculaient : les comptes, les champs
presents et manquants, les longueurs, les empreintes. L'agent lit, il n'ecrit plus.

    etat-run.py <workspace> [--json] [--seulement findings|retenus|essentiels|fichiers]
    etat-run.py <workspace> --element G01        # tout ce qu'on sait d'un element
    etat-run.py <workspace> --champs essentiel_fr,titre_en   # qui les porte, qui non
"""
import argparse, collections, datetime, hashlib, json, os, pathlib, sys


def charger(p):
    try:
        d = json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:
        return None
    if isinstance(d, list):
        return d
    for c in ('findings', 'retenus', 'items', 'pistes'):
        if isinstance(d.get(c), list):
            return d[c]
    return d


def md5(p):
    try:
        return hashlib.md5(pathlib.Path(p).read_bytes()).hexdigest()
    except Exception:
        return None


def mots(s):
    return len((s or '').split())


def inventaire_liste(elems, nom):
    """Comptes, champs, longueurs — ce que les scripts jetables recalculaient."""
    if not elems:
        return None
    champs = collections.Counter()
    for e in elems:
        if isinstance(e, dict):
            champs.update(k for k, v in e.items() if v not in (None, '', [], {}))
    n = len(elems)
    tous = [k for k, v in champs.items() if v == n]
    partiels = {k: v for k, v in champs.items() if v < n}
    out = {'nom': nom, 'n': n,
           'champs_sur_tous': sorted(tous),
           'champs_partiels': dict(sorted(partiels.items(), key=lambda x: -x[1]))}
    # On ne repartit que des valeurs SCALAIRES : compter des dictionnaires rend une
    # ligne par element, ce qui deverse le fichier au lieu de le resumer.
    for cle in ('tier', 'axe', 'role', 'freshness', 'verdict', 'lien', 'tour'):
        c = collections.Counter(
            str(e.get(cle)) for e in elems
            if isinstance(e, dict) and isinstance(e.get(cle), (str, int, float, bool)))
        if c:
            out.setdefault('repartitions', {})[cle] = dict(c.most_common())
    longueurs = {}
    for cle in ('essentiel', 'essentiel_fr', 'essentiel_en', 'titre', 'titre_fr', 'titre_en'):
        v = [mots(e.get(cle)) for e in elems if isinstance(e, dict) and e.get(cle)]
        if v:
            v.sort()
            longueurs[cle] = {'n': len(v), 'min': v[0], 'median': v[len(v)//2], 'max': v[-1]}
    if longueurs:
        out['longueurs_en_mots'] = longueurs
    ids = [e.get('id') or e.get('gid') for e in elems if isinstance(e, dict)]
    ids = [i for i in ids if i]
    if ids:
        out['ids'] = ids
        dbl = [k for k, v in collections.Counter(ids).items() if v > 1]
        if dbl:
            out['ids_en_double'] = dbl
    return out


def fichiers_du_ws(ws):
    """Les livrables et leur empreinte — sans descendre dans ce qui n'est pas juge."""
    skip = {'transcripts', 'archives', '.git', '_build', 'scripts', 'preuves-p5'}
    out = {}
    for r, ds, fs in os.walk(ws):
        ds[:] = [d for d in ds if d not in skip and not d.startswith('.')]
        for f in sorted(fs):
            if not f.endswith(('.md', '.json', '.jsonl', '.out')):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, ws)
            try:
                st = os.stat(p)
            except OSError:
                continue
            out[rel] = {'octets': st.st_size, 'md5': md5(p),
                        'mtime': datetime.datetime.fromtimestamp(
                            st.st_mtime, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('workspace')
    ap.add_argument('--json', action='store_true', help='sortie machine')
    ap.add_argument('--seulement', help='findings|retenus|essentiels|fichiers')
    ap.add_argument('--element', help="tout ce que la run sait d'un id (G01, R42…)")
    ap.add_argument('--champs', help='liste de champs : qui les porte, qui ne les porte pas')
    a = ap.parse_args()

    ws = a.workspace.rstrip('/')
    if not os.path.isdir(ws):
        print(f'workspace introuvable : {ws}', file=sys.stderr)
        return 2

    src = {
        'findings': charger(os.path.join(ws, 'findings.json')),
        'retenus': charger(os.path.join(ws, 'state', 'retenus.json')),
    }
    ess_dir = os.path.join(ws, 'state', 'essentiels')
    if os.path.isdir(ess_dir):
        ess = []
        for f in sorted(os.listdir(ess_dir)):
            if f.endswith('.json'):
                d = charger(os.path.join(ess_dir, f))
                if isinstance(d, dict):
                    ess.append(d)
        src['essentiels'] = ess

    # --element : tout ce qu'on sait d'un id, d'un coup
    if a.element:
        trouve = {}
        for nom, elems in src.items():
            if not isinstance(elems, list):
                continue
            for e in elems:
                if isinstance(e, dict) and (e.get('id') == a.element or e.get('gid') == a.element):
                    trouve[nom] = e
        print(json.dumps(trouve, ensure_ascii=False, indent=1) if trouve
              else f'aucun element « {a.element} »')
        return 0 if trouve else 1

    # --champs : qui porte quoi
    if a.champs:
        cibles = [c.strip() for c in a.champs.split(',') if c.strip()]
        rap = {}
        for nom, elems in src.items():
            if not isinstance(elems, list):
                continue
            for c in cibles:
                porte, manque = [], []
                for e in elems:
                    if not isinstance(e, dict):
                        continue
                    i = e.get('id') or e.get('gid')
                    (porte if e.get(c) not in (None, '', [], {}) else manque).append(i)
                if porte or manque:
                    rap.setdefault(nom, {})[c] = {'porte': len(porte), 'manque': manque}
        print(json.dumps(rap, ensure_ascii=False, indent=1))
        return 0

    rap = {'workspace': ws}
    for nom, elems in src.items():
        if a.seulement and a.seulement != nom:
            continue
        if isinstance(elems, list):
            inv = inventaire_liste(elems, nom)
            if inv:
                rap[nom] = inv
    if not a.seulement or a.seulement == 'fichiers':
        rap['fichiers'] = fichiers_du_ws(ws)

    if a.json:
        print(json.dumps(rap, ensure_ascii=False, indent=1))
        return 0

    # sortie lisible : ce qu'on veut voir sans deplier un JSON
    for nom in ('findings', 'retenus', 'essentiels'):
        b = rap.get(nom)
        if not b:
            continue
        print(f"\n== {nom} — {b['n']} elements")
        if b.get('ids_en_double'):
            print(f"   !! ids en double : {b['ids_en_double']}")
        if b.get('champs_partiels'):
            print("   champs incomplets : " + ', '.join(
                f"{k} ({v}/{b['n']})" for k, v in list(b['champs_partiels'].items())[:8]))
        for cle, d in (b.get('repartitions') or {}).items():
            print(f"   {cle} : " + ' · '.join(f"{k}={v}" for k, v in d.items()))
        for cle, d in (b.get('longueurs_en_mots') or {}).items():
            print(f"   {cle} (mots) : min={d['min']} median={d['median']} max={d['max']} sur {d['n']}")
    fich = rap.get('fichiers')
    if fich:
        print(f"\n== fichiers juges — {len(fich)}")
        for rel, d in list(fich.items())[:200]:
            print(f"   {d['md5'][:8]}  {d['octets']:>9}  {d['mtime']}  {rel}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
