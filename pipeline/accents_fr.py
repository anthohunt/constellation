# -*- coding: utf-8 -*-
"""Correcteur d'accents francais, deterministe.

Pourquoi : les modeles ecrivent par intermittence « modele » au lieu de la forme
accentuee. Redire la consigne ne tient que quelques messages (bug connu Claude Code
#65127 / #32886). On corrige donc apres coup, mecaniquement.

Deux sources, deux roles :
  - le lexique aspell-fr dit quels mots existent VRAIMENT sans accent
    (« marche », « montre », « cote ») : ceux-la ne sont jamais touches ;
  - wordfreq departage quand plusieurs formes accentuees existent
    (« modele » -> le nom commun, pas le participe passe « modele »).

Un mot n'est corrige que si sa forme accentuee est franchement plus courante que
ses concurrentes ; dans le doute, on ne touche pas.
"""
import os, re, subprocess, unicodedata, json, sys

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.lexique-fr.json')
ECART_MIN = 0.7     # en zipf : la gagnante doit etre ~5x plus frequente
ZIPF_MIN  = 2.3     # sous ce seuil, le mot est trop rare pour trancher

try:
    from wordfreq import zipf_frequency
except ImportError:
    zipf_frequency = None

# Marques et mots anglais qui ressemblent a des mots francais desaccentues.
# Sans cette liste, « Meta » deviendrait « Meta » accentue et « The » un breuvage.
MARQUES = {'meta','the','helix','omega','alpha','beta','delta','sigma','gemma','gemini',
           'nova','vera','sora','opus','sonnet','ultra','mistral','cohere','claude','genie',
           'era','ego','elan','echo','ideal','tempo','sierra','aurora','atlas','orion'}

def _nu(mot):
    return ''.join(c for c in unicodedata.normalize('NFD', mot)
                   if unicodedata.category(c) != 'Mn')

def _construire():
    dump = subprocess.run(['aspell','-d','fr','--encoding=utf-8','dump','master'],
                          capture_output=True, text=True, check=True).stdout
    exp = subprocess.run(['aspell','-l','fr','--encoding=utf-8','expand'],
                         input=dump, capture_output=True, text=True, check=True).stdout
    formes = {m.strip() for ligne in exp.split('\n') for m in ligne.split(' ') if m.strip()}
    sans = {m.lower() for m in formes if _nu(m) == m}
    cand = {}
    for m in formes:
        if _nu(m) != m:
            cand.setdefault(_nu(m).lower(), set()).add(m.lower())
    table = {}
    for cle, formes_acc in cand.items():
        if cle in sans:            # le mot sans accent existe deja : ambigu, on s'abstient
            continue
        formes_acc = sorted(formes_acc)
        if len(formes_acc) == 1:
            table[cle] = formes_acc[0]; continue
        if not zipf_frequency:     # sans arbitre, on s'abstient
            continue
        scores = sorted(((zipf_frequency(f, 'fr'), f) for f in formes_acc), reverse=True)
        if scores[0][0] >= ZIPF_MIN and scores[0][0] - scores[1][0] >= ECART_MIN:
            table[cle] = scores[0][1]
    return {'table': table}

def lexique(rebuild=False):
    if not rebuild and os.path.exists(CACHE):
        try: return json.load(open(CACHE, encoding='utf-8'))
        except Exception: pass
    lex = _construire()
    json.dump(lex, open(CACHE, 'w', encoding='utf-8'))
    return lex

_MOT = re.compile(r'[A-Za-zÀ-ɏ]{3,}')
# Zones ou l'on ne touche a rien : mise en valeur, code, URL, et CITATIONS.
# Une citation est verbatim par definition : accentuer le titre de commit
# « ... semantic-layer and theme endpoints » en « thème endpoints » falsifie la source.
_PROTEGE = re.compile(r'\*\*?[^\*\n]{1,80}\*\*?|`[^`\n]{1,120}`|https?://\S+'
                      r'|«[^»\n]{1,300}»|"[^"\n]{1,300}"|“[^”\n]{1,300}”')

def _casse(src, cible):
    if src.isupper(): return cible.upper()
    if src[:1].isupper(): return cible[:1].upper() + cible[1:]
    return cible

def corriger(texte, lex=None):
    """Retourne (texte_corrige, [(avant, apres), ...])."""
    lex = lex or lexique(); table = lex['table']; corr = []
    zones = [(m.start(), m.end()) for m in _PROTEGE.finditer(texte)]
    def rempl(m):
        mot = m.group(0); i = m.start()
        if _nu(mot) != mot: return mot                     # deja accentue
        if mot.isupper(): return mot                       # sigle : HELIX reste HELIX
        if mot.lower() in MARQUES: return mot
        if any(a <= i < b for a, b in zones): return mot   # entite mise en valeur, code, URL
        if mot[:1].isupper():
            # un mot capitalise au fil de la phrase est presque toujours un nom propre :
            # on ne corrige qu'en tete de phrase.
            avant = texte[:i].rstrip()
            if avant and avant[-1] not in '.!?:;\n—«“(':
                return mot
        cible = table.get(mot.lower())
        if not cible: return mot
        out = _casse(mot, cible); corr.append((mot, out)); return out
    return _MOT.sub(rempl, texte), corr

def suspects(texte, lex=None):
    """Mots que la passe corrigerait : sert de controle qualite en validation."""
    _out, corr = corriger(texte, lex)
    return [a for a, _b in corr]

if __name__ == '__main__':
    if '--rebuild' in sys.argv:
        lex = lexique(rebuild=True); print('lexique : %d entrees' % len(lex['table'])); raise SystemExit
    src = sys.stdin.read(); out, corr = corriger(src)
    sys.stdout.write(out)
    if corr:
        sys.stderr.write('%d correction(s) : %s\n' % (len(corr),
            ', '.join(sorted({'%s->%s' % c for c in corr}))))
