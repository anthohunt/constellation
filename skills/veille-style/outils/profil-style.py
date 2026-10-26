#!/usr/bin/env python3
"""profil-style.py — mesure les traits objectivables d'un texte.

    profil-style.py <fichier.md> [--corps-apres-tirets]

Sert deux fois, avec le meme code des deux cotes : il a produit le profil GELE
de la reference de redaction (`veille-style/profil-mesure.md`), et le juge de
style le lance sur l'essentiel qu'il doit noter. Un ecart se lit alors comme un
ecart de mesure, pas comme une impression.

Rend du JSON sur stdout.
"""
import re, sys, json, statistics as st, collections

def corps(t, apres_tirets=False):
    if apres_tirets:
        i = t.find('\n---\n')
        if i > 0:
            t = t[i+5:]
    return re.sub(r'^#{1,6} .*$', '', t, flags=re.M)

def phrases(p):
    p = re.sub(r'\s+', ' ', p)
    return [s.strip() for s in re.split(r'(?<=[.!?…])\s+(?=[A-ZÀ-ÜÇ«*])', p) if s.strip()]

CONNECTEURS = r"(Mais|Donc|Or\b|Et |Ça|C'est|Il faut|Concrètement|D'habitude|Sur le papier|Pour qui|Autrement dit|Résultat)"

def profil(texte):
    b = texte
    paras = [p.strip() for p in b.split('\n\n') if p.strip()]
    ph = [s for p in paras for s in phrases(p)]
    if not ph:
        return {}
    mots = [len(s.split()) for s in ph]
    pp = [len(phrases(p)) for p in paras]
    rep = collections.Counter()
    for m in mots:
        rep['<=8' if m <= 8 else '9-15' if m <= 15 else '16-25' if m <= 25 else '>25'] += 1
    n = len(ph)
    c = lambda rx: len(re.findall(rx, b, flags=re.I))
    return {
        'paragraphes': len(paras),
        'phrases': n,
        'mots_par_phrase': {'mediane': st.median(mots), 'moyenne': round(st.mean(mots), 1),
                            'min': min(mots), 'max': max(mots)},
        'repartition_longueur_pct': {k: round(100 * v / n) for k, v in rep.items()},
        'phrases_par_paragraphe': {'mediane': st.median(pp), 'min': min(pp), 'max': max(pp)},
        'deux_points_pct': round(100 * c(r"\s:\s") / n),
        'ouverture_connecteur_pct': round(100 * len([s for s in ph if re.match(CONNECTEURS, s)]) / n),
        'gras_par_paragraphe': round(c(r"\*\*[^*]+\*\*") / len(paras), 2),
        'questions': c(r"\?"),
        'antithese_negation': c(r",\s(?:pas|jamais|non)\s") + c(r"n'(?:est|était) pas[^.]{0,60}c'est"),
        'vous': c(r"\bvous\b"), 'on': c(r"\bon\b"), 'je': c(r"\bje\b"),
    }

if __name__ == '__main__':
    src = sys.argv[1]
    apres = '--corps-apres-tirets' in sys.argv
    print(json.dumps(profil(corps(open(src, encoding='utf-8').read(), apres)),
                     ensure_ascii=False, indent=2))
