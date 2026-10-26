#!/usr/bin/env python3
"""filtrer-nouveautes.py <depuis-AAAAMMJJ> [archives.json] — garde le NEUF."""
import sys, json, os, re

depuis = sys.argv[1]
arch = sys.argv[2] if len(sys.argv) > 2 else ""
nu = lambda u: re.sub(r"^https?://(www\.)?", "", u.strip().rstrip("/"))

def moissonner(chemin, deja):
    """Les URL deja livrees, quel que soit le fichier qui les porte.

    On accepte un fichier OU un dossier : les archives d'une run sont un
    dossier, et exiger un fichier precis ferait echouer l'ecart en silence —
    la pire des pannes, puisque tout continue de tourner en doublonnant.
    """
    fichiers = []
    if os.path.isdir(chemin):
        for r, _, noms in os.walk(chemin):
            fichiers += [os.path.join(r, n) for n in noms if n.endswith(".json")]
    elif os.path.exists(chemin):
        fichiers = [chemin]
    for f in fichiers:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        pile = [d]
        while pile:
            o = pile.pop()
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("url", "url_nue", "lien") and isinstance(v, str) and v.startswith("http"):
                        deja.add(nu(v))
                    elif isinstance(v, (dict, list)):
                        pile.append(v)
            elif isinstance(o, list):
                pile += o

deja = set()
if arch:
    moissonner(arch, deja)

lignes = []
for l in sys.stdin.read().splitlines():
    p = l.split("\t")
    if len(p) < 2 or not p[0].isdigit() or p[0] < depuis:
        continue
    url = p[1] if p[1].startswith("http") else "https://www.youtube.com/watch?v=" + p[1]
    if nu(url) in deja:
        continue
    lignes.append((p[0], url, p[2] if len(p) > 2 else ""))

for d, u, t in sorted(lignes, reverse=True):
    print("%s-%s-%s\t%s\t%s" % (d[:4], d[4:6], d[6:], u, t))
