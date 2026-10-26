# -*- coding: utf-8 -*-
"""Construit la constellation PUBLIEE, cumulative.

La publication ne montre pas la seule run qui vient de finir : elle montre toute la
bibliotheque du silo, livraison par livraison. C'est ce cumul qui fait la valeur — une fiche d'aujourd'hui n'a de sens
que rapportee a ce que la veille disait il y a trois semaines.

Usage : build_publie.py <workspace> <owner-dir> <watch> <dossier-de-sortie>
"""
import json, os, sys, pathlib, unicodedata, re, shutil


def slug(t):
    t = unicodedata.normalize('NFD', t or '')
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', t)).strip('-')[:52]


def charger_bibliotheque(owner_dir, watch):
    """Une fiche archivee par fichier ; la date de run les regroupe en livraisons."""
    d = pathlib.Path(owner_dir) / 'db' / 'findings' / watch
    out = []
    for f in sorted(d.glob('*.json')):
        try:
            out.append(json.loads(f.read_text(encoding='utf-8')))
        except Exception:
            continue
    return out


def sources_de(f):
    """Une fiche publiee porte les sources de son histoire, pas une seule adresse.
    Le tableau est toujours rempli : une histoire d'un seul finding y a une entree."""
    out = []
    for sc in (f.get('sources') or []):
        if not isinstance(sc, dict):
            continue
        url = (sc.get('url') or '').strip()
        if not url:
            continue
        out.append({'titre': (sc.get('titre') or '').strip(), 'url': url,
                    'date': (sc.get('date') or '').strip(),
                    'trouve_par': (sc.get('trouve_par') or '').strip(),
                    'fid': (sc.get('fid') or '').strip()})
    if not out and (f.get('url') or '').strip():
        out.append({'titre': (f.get('titre_fr') or f.get('titre') or '').strip(),
                    'url': f['url'].strip(), 'date': (f.get('date_fait') or '').strip(),
                    'trouve_par': '', 'fid': f.get('id', '')})
    return out


def construire(workspace, owner_dir, watch, sortie):
    fiches = charger_bibliotheque(owner_dir, watch)
    if not fiches:
        raise SystemExit('bibliotheque vide : rien a publier')

    dates = sorted({(f.get('run_date') or f.get('date_fait') or '?') for f in fiches})
    idx = {d: i for i, d in enumerate(dates)}
    nodes = []
    for f in fiches:
        ri = idx.get(f.get('run_date') or f.get('date_fait') or '?', 0)
        nodes.append({
            'id': f.get('id') or slug(f.get('titre') or ''),
            'run': ri, 'date': f.get('date_fait'), 'lane': len(nodes),
            'axe': f.get('axe') or 'Transverse',
            'headline': f.get('titre_fr') or f.get('titre'),
            'headline_fr': f.get('titre_fr') or f.get('titre'),
            'headline_en': f.get('titre_en'),
            'tier': f.get('tier') or 'Intéressant', 'tier_source': 'user',
            'tags': f.get('tags') or [],
            'fiche': {'essentiel': f.get('essentiel_fr'), 'essentiel_fr': f.get('essentiel_fr'),
                      'essentiel_en': f.get('essentiel_en'), 'url': f.get('url'),
                      'sources': sources_de(f),
                      'objets': f.get('objets') or []},
        })

    # de quoi juger la livraison, pas seulement la lire : ce qui a ete examine
    # a l'evaluation, et la part des classements de l'agent laisses tels quels
    try:
        import sys as _s, pathlib as _p
        _s.path.insert(0, str(_p.Path(__file__).parent))
        from perf_livraison import perf_par_livraison
        perf = perf_par_livraison(fiches, dates)
    except Exception as e:
        print('perf indisponible :', e)
        perf = {}

    bundle = {'watch': watch, 'owner': pathlib.Path(owner_dir).name,
              'theme': 'IA — toute la veille', 'theme_fr': 'IA — toute la veille',
              'theme_en': 'AI — the whole watch',
              'runs': dates, 'nlanes': len(nodes), 'mode': 'publish',
              'axes': sorted({n['axe'] for n in nodes}),
              'nodes': nodes, 'perf': perf}

    out = pathlib.Path(sortie)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'constellation-data.json').write_text(
        json.dumps(bundle, ensure_ascii=False, indent=1), encoding='utf-8')
    # le template de PUBLICATION, derive de celui d'evaluation : page de lecture,
    # sans parcours guide ni notation. Regenere a chaque publication pour ne jamais
    # diverger du template principal.
    base = pathlib.Path(os.environ.get('CONSTELLATION_DATA', 'data')) / 'shared'
    src, pub = base / 'constellation.html', base / 'constellation-publie.html'
    gen = pathlib.Path(__file__).parent / 'gen-template-publie.py'
    if src.exists() and gen.exists():
        import subprocess
        subprocess.run([sys.executable, str(gen), str(src), str(pub)], check=False)
    if pub.exists():
        shutil.copy(pub, out / 'constellation.html')
    elif src.exists():
        shutil.copy(src, out / 'constellation.html')
    vend = src.parent.parent / 'runs'
    for cand in vend.glob('*/vendor'):
        if not (out / 'vendor').exists():
            shutil.copytree(cand, out / 'vendor')
        break
    print('livraisons %d · fiches %d' % (len(dates), len(nodes)))
    return bundle


if __name__ == '__main__':
    if len(sys.argv) < 5:
        raise SystemExit(__doc__)
    construire(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
