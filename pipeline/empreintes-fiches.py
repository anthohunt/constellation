#!/usr/bin/env python3
"""Empreinte md5 de chaque ELEMENT d'un livrable, quelle que soit sa forme.

A quoi ca sert : l'acquis d'une verification se compte au grain de l'ELEMENT — la
plus petite chose qui porte un verdict (une fiche de chasse, un essentiel, une
entree). Un element conforme dont le texte n'a pas bouge ne se rejuge pas, meme si
le fichier qui le porte a ete reecrit ailleurs. Sans empreinte par element, la
moindre correction fait repasser tout le lot au programme — et verifier une
reparation coute alors plus cher que verifier le travail d'origine.

La meme commande sert a toutes les etapes, parce que la verification a la meme
forme partout. Elle reconnait quatre formes de source :

  <fichier>.md      -> une section `## <id> …` par element (l'id est le premier mot)
  <dossier>/        -> un fichier par element (l'id est le nom sans extension)
  <fichier>.json    -> un objet ou une liste ; l'id est la cle, ou le champ id/fid/pid
  <fichier>.jsonl   -> une ligne par element ; l'id est le champ id/fid/pid

Usage :
  empreintes-fiches.py <source> [<source> ...]          -> tableau lisible
  empreintes-fiches.py --json <source> [...]            -> {"<source>": {"<id>": "<md5>"}}
  empreintes-fiches.py --diff <registre.json> <source> [...]
        -> les id A JUGER : jamais vus, ou empreinte differente du registre
"""
import sys, os, re, json, hashlib

TITRE_MD = re.compile(r'^##\s+([^\s—:]+)')
CLES_ID = ('id', 'fid', 'pid', 'uid')


def md5(texte):
    return hashlib.md5(texte.encode('utf-8')).hexdigest()


def norm(texte):
    return '\n'.join(l.rstrip() for l in texte.splitlines()).strip() + '\n'


def _id_de(obj, defaut):
    if isinstance(obj, dict):
        for k in CLES_ID:
            if obj.get(k):
                return str(obj[k])
    return defaut


def elements_md(chemin):
    out, eid, buf = {}, None, []
    for ligne in open(chemin, encoding='utf-8', errors='replace'):
        m = TITRE_MD.match(ligne)
        if m:
            if eid:
                out[eid] = md5(norm(''.join(buf)))
            eid, buf = m.group(1), [ligne]
        elif eid:
            buf.append(ligne)
    if eid:
        out[eid] = md5(norm(''.join(buf)))
    return out


def elements_dossier(chemin):
    out = {}
    for nom in sorted(os.listdir(chemin)):
        p = os.path.join(chemin, nom)
        if os.path.isfile(p) and not nom.startswith('_'):
            out[os.path.splitext(nom)[0]] = md5(norm(open(p, encoding='utf-8', errors='replace').read()))
    return out


def _collection(d):
    """La collection d'elements d'un JSON, sous l'entete qui la porte.

    Un livrable de pipeline est presque toujours un objet a entete : `run`,
    `date`, `totaux`... puis UNE liste (ou UN objet) qui porte les elements.
    Hacher les cles de premier niveau donnerait une empreinte pour `date` et
    aucune pour les fiches — et le perimetre d'une passe se calculerait sur du
    vide sans que rien ne le signale.
    """
    if isinstance(d, list):
        return d
    if not isinstance(d, dict):
        return None
    # une liste d'objets qui portent un id : c'est elle
    for v in d.values():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v) \
           and any(_id_de(x, None) for x in v):
            return v
    # un objet dont TOUTES les valeurs sont des objets : les cles sont les id
    if d and all(isinstance(v, dict) for v in d.values()):
        return d
    # sinon on prend l'objet tel quel : c'est le cas d'un registre a plat
    return d


def elements_json(chemin):
    d = _collection(json.load(open(chemin, encoding='utf-8')))
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out[str(k)] = md5(json.dumps(v, ensure_ascii=False, sort_keys=True))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out[_id_de(v, str(i))] = md5(json.dumps(v, ensure_ascii=False, sort_keys=True))
    return out


def elements_jsonl(chemin):
    out = {}
    for i, ligne in enumerate(open(chemin, encoding='utf-8', errors='replace')):
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            v = json.loads(ligne)
        except Exception:
            continue
        out[_id_de(v, str(i))] = md5(json.dumps(v, ensure_ascii=False, sort_keys=True))
    return out


def elements(source):
    if os.path.isdir(source):
        return elements_dossier(source)
    ext = os.path.splitext(source)[1].lower()
    if ext == '.md':
        return elements_md(source)
    if ext == '.jsonl':
        return elements_jsonl(source)
    if ext == '.json':
        return elements_json(source)
    return {os.path.basename(source): md5(norm(open(source, encoding='utf-8', errors='replace').read()))}


def _slug_source(src):
    """Le nom de lot que porte un nom de fichier : `pistes-signal-faible-T1.md` -> `signal-faible`."""
    b = os.path.splitext(os.path.basename(os.path.normpath(src)))[0]
    return re.sub(r'^(pistes|lot)-|-T\d+$', '', b)


def _slug(uid):
    """Le nom de lot que porte l'id d'une unite : `lot-signal-faible` -> `signal-faible`."""
    return re.sub(r'^(\d+(\.\d+)*-)?(lot-)?', '', uid or '')


def acquis_du_registre(registre, source):
    """Les empreintes deja conformes pour cette source, {id: md5}.

    Deux appariements a faire, et rater l'un des deux vide silencieusement
    l'acquis — tout repasse au programme sans qu'aucun message ne le dise.

    1. L'UNITE. Son champ `source` est ecrit par un agent : c'est une phrase
       (« pistes-x-T1.md + state/retenus.json (fiches de x) »), pas un chemin.
       On cherche donc le nom du fichier DANS la phrase, et a defaut le nom de
       lot de son id dans le nom du fichier. Toutes les unites qui repondent
       comptent, pas seulement la premiere : deux peuvent porter le meme lot.

    2. L'ELEMENT. Le registre nomme une fiche par son lot (`signal-faible:P3`)
       parce qu'il couvre toute l'etape ; le fichier, lui, ne connait que `P3`.
       On apparie donc sur l'id exact ET sur ce qui suit le dernier « : ».
    """
    base = os.path.basename(os.path.normpath(source))
    unites = registre.get('unites') if isinstance(registre, dict) else registre
    out = {}
    for u in unites or []:
        if not isinstance(u, dict):
            continue
        dit = u.get('source') or u.get('lot') or ''
        slug = _slug(u.get('id'))
        if base not in dit and not (slug and slug in base):
            continue
        for i, e in (u.get('elements') or u.get('fiches') or {}).items():
            if e.get('verdict') != 'conforme':
                continue
            out[i] = e.get('empreinte')
            court = i.rsplit(':', 1)[-1]
            out.setdefault(court, e.get('empreinte'))
    return out


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)

    if args[0] == '--tamponner':
        # Le registre porte le verdict ET l'empreinte de l'element au moment ou
        # il a ete juge. Ecrit a la main, l'empreinte se perd — et sans elle
        # l'acquis ne peut PLUS jamais s'apparier : tout repasse au programme a
        # chaque passe, en silence, comme si rien n'avait jamais ete valide.
        # Le chef ne l'ecrit donc pas : il la fait tamponner.
        if len(args) < 3:
            sys.exit('usage: --tamponner <registre.json> <source> [...]')
        chemin = args[1]
        registre = json.load(open(chemin, encoding='utf-8'))
        courant = {}
        for src in args[2:]:
            for i, h in elements(src).items():
                courant[i] = h
                courant.setdefault(_slug_source(src) + ':' + i, h)
        pose = manque = 0
        for u in (registre.get('unites') if isinstance(registre, dict) else registre) or []:
            if not isinstance(u, dict):
                continue
            for i, e in (u.get('elements') or u.get('fiches') or {}).items():
                h = courant.get(i) or courant.get(i.rsplit(':', 1)[-1])
                if h:
                    e['empreinte'] = h
                    pose += 1
                else:
                    manque += 1
        json.dump(registre, open(chemin, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('%s : %d empreintes posees, %d elements sans source correspondante'
              % (os.path.basename(chemin), pose, manque))
        if manque:
            print('  -> un element sans empreinte ne sera JAMAIS acquis : nomme sa source')
        return

    if args[0] == '--diff':
        if len(args) < 3:
            sys.exit('usage: --diff <registre.json> <source> [...]')
        registre = json.load(open(args[1], encoding='utf-8'))
        for src in args[2:]:
            acquis = acquis_du_registre(registre, src)
            courant = elements(src)
            a_juger = [i for i, h in courant.items() if acquis.get(i) != h]
            print('%s : %d elements, %d a juger -> %s'
                  % (os.path.basename(os.path.normpath(src)), len(courant), len(a_juger),
                     ' '.join(a_juger) if a_juger else '(aucun)'))
        return

    json_mode = args[0] == '--json'
    sources = args[1:] if json_mode else args
    res = {os.path.basename(os.path.normpath(s)): elements(s) for s in sources}
    if json_mode:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for src, e in res.items():
            print(f'{src} — {len(e)} elements')
            for i, h in e.items():
                print(f'  {i:<12} {h}')


if __name__ == '__main__':
    main()
