#!/usr/bin/env python3
"""questionnaire.py — le questionnaire FIGÉ d'une étape, extrait de ses livrables.

**La question vient du LIVRABLE, la réponse se cherche dans la SOURCE.**

Le contrôle disait au vérificateur « énumère tout ce qui est vérifiable ». Le
vérificateur décidait donc lui-même COMBIEN de choses il y avait à vérifier — et
ce nombre a varié du simple au triple d'une passe à l'autre sur le même texte
(lots de 18,0 / 15,5 / 51,7 Ko, consigne identique au md5 près). Le score qui en
sortait ne mesurait pas la qualité de la fiche : il mesurait la profondeur de
lecture du jour, et il baissait quand un modèle plus fort prenait la main.

Ici le nombre de questions ne dépend plus du lecteur. Il est extrait une fois,
écrit dans le registre, et **gelé pour toute la run** : d'une passe à l'autre on
compare deux fois la même chose.

    questionnaire.py extraire <pistes-*.md>...   -> le questionnaire, en JSON
    questionnaire.py extraire --resume <...>     -> ce qu'il contient, en clair

Ce que ce programme ne fait PAS : il ne juge rien. Il pose les questions ; les
réponses viennent d'ailleurs (un grep dans la page pour les unes, un agent pour
les autres).
"""
import argparse, json, hashlib, pathlib, re, sys

# --------------------------------------------------------------- LES CHAMPS
# Seuls les champs qui ATTESTENT quelque chose entrent au questionnaire. Ce que
# le chasseur interprète — « ce que ça déplace », « pertinence », la
# justification du classement — dit ce qu'il PENSE, pas ce que la source porte :
# le juger contre une page n'a pas de sens, et c'est ce qui gonflait la liste.
CHAMPS_ATTESTANTS = ('titre', 'URL', 'Date du fait', 'Source',
                     'Sources indépendantes', 'Essentiel')

# --------------------------------------------------------- LES DÉCLENCHEURS
# Un déclencheur = un motif dans le texte de la fiche qui fait naître UNE
# question. Ils sont volontairement larges : mieux vaut une question de trop,
# qui se répondra « oui » d'un grep, qu'une faute qu'aucune question ne vise.

# Un nombre porteur de sens : pourcentage, facteur, montant, ordre de grandeur,
# durée, fréquence. Le « 1 » de « en 1 an » compte ; le « 3 » de « P3 » non.
RX_CHIFFRE = re.compile(
    r'(?<![\w./-])'
    r'(\d[\d\s .,]*)\s*'
    r'(%|×|x\b|fois|\$|€|Md\b|M\b|k\b|milliards?|millions?|milliers?|'
    r'heures?|h\b|min\b|jours?|semaines?|mois|ans?|années?|Hz\b|points?|'
    r'tokens?|paramètres?|Go\b|To\b)',
    re.I)

# « selon X », « d'après X », « X affirme » — une attribution nommée.
RX_ATTRIBUTION = re.compile(
    r'(selon\s+[A-ZÉÈÀ][\w.\-&\' ]{1,40}'
    r'|d[\'’]après\s+[A-ZÉÈÀ][\w.\-&\' ]{1,40}'
    r'|[A-ZÉÈÀ][\w.\-&\']{2,30}\s+'
    r'(?:affirme|annonce|rapporte|mesure|revendique|déclare|indique|estime|cite))')

# Un verbe qui dit un projet, une promesse ou une revendication — pas un fait.
RX_MODALITE = re.compile(
    r'\b(annonc\w+|prévu\w*|prévoit|vise\s+à|revendiqu\w+|devrait\w*|'
    r'ambitionne|promet|se présente comme|affirme être|serait|pourrait)\b', re.I)

# Un titre ou un rang accolé à quelqu\'un ou quelque chose.
RX_QUALIF = re.compile(
    r'\b(PDG|CEO|CTO|directeur\w*|directrice|Senior Director|Lead\b|'
    r'mainteneur\w*|fondateur\w*|fondatrice|chercheur\w*|président\w*|'
    r'premier\w*|première|leader|numéro un|n°\s*1|pionnier\w*)\b', re.I)

# Une date, absolue ou relative.
RX_DATE = re.compile(
    r'(\d{4}-\d{2}-\d{2}'
    r'|\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|'
    r'septembre|octobre|novembre|décembre)\b'
    r'|\b(?:en\s+moins\s+de|il\s+y\s+a|depuis|dans)\s+\d+\s*'
    r'(?:h|heures?|jours?|semaines?|mois|ans?)\b)', re.I)

# Un passage donné comme cité mot pour mot.
RX_CITATION = re.compile(r'«\s*([^»]{8,300})\s*»|"([^"\n]{8,300})"')

RX_URL = re.compile(r'https?://[^\s,;)»\]]+')

# ------------------------------------------------------------ LES QUESTIONS
# `mecanique: True` = la réponse se trouve par programme (chercher la chaîne
# dans la page téléchargée). Aucune de celles-là ne coûte un jeton de modèle.
TYPES = {
    'chiffre':   dict(n=1, mecanique=True,
                      libelle="« {extrait} » figure-t-il dans la page, sous cette forme ou une "
                              "forme arithmétiquement équivalente ?"),
    'reserve':   dict(n=2, mecanique=False,
                      libelle="La page encadre-t-elle « {extrait} » d'une réserve — « jusqu'à », "
                              "« environ », « près de », « selon les estimations », « rapporté, "
                              "non vérifié » — que la fiche ne reprend pas ?"),
    'attribution': dict(n=3, mecanique=False,
                      libelle="Pour « {extrait} » : la page est-elle bien de cette source (ou la "
                              "cite-t-elle), et cette source soutient-elle bien cette affirmation ?"),
    'modalite':  dict(n=4, mecanique=False,
                      libelle="La page dit-elle « annoncé / prévu / revendiqué » là où la fiche "
                              "écrit « {extrait} » comme un fait accompli ?"),
    'qualification': dict(n=5, mecanique=False,
                      libelle="Le titre ou le rang « {extrait} » est-il écrit dans la page pour "
                              "cette personne ou cette entité ?"),
    'date':      dict(n=6, mecanique=True,
                      libelle="La date ou la durée « {extrait} » figure-t-elle dans la page ?"),
    'citation':  dict(n=7, mecanique=True,
                      libelle="Le passage « {extrait} » est-il dans la page, mot pour mot ?"),
    'lien':      dict(n=8, mecanique=True,
                      libelle="L'URL {extrait} répond-elle, et la page porte-t-elle ce que la "
                              "fiche lui prête ?"),
    'sens':      dict(n=9, mecanique=False,
                      libelle="La conclusion que la fiche tire de cette source est-elle celle que "
                              "la source elle-même tire ?"),
}

# CE QUI EST CALIBRE, ET CE QUI NE L'EST PAS.
#
# Un type de question n'est un CRITERE que si deux lecteurs frais, sur le meme
# texte inchange, en tirent la meme reponse. Sinon ce n'est pas un critere,
# c'est une opinion — et une opinion qui bloque une etape fait boucler la
# verification sans fin.
#
# Calibration du 2026-09-04, 45 questions jugees, 5 fiches, deux verificateurs
# frais et aveugles l'un a l'autre. Accord global 44/45 = 98 %, la ou un juge
# LLM libre plafonne a 91-94 % dans la litterature :
#
#     reserve        32 questions   100 %   RETENU
#     modalite        4 questions   100 %   RETENU
#     qualification   2 questions   100 %   RETENU
#     attribution     2 questions   100 %   RETENU
#     sens            5 questions    80 %   NON RETENU comme bloquant
#
# Les quatre premiers sont quasi binaires : « la page porte-t-elle cette
# chaine, oui ou non ». Le cinquieme demande de resumer ce qu'une source
# CONCLUT — les deux lecteurs ont diverge sur une progression de score
# (P4.Q18). Il se consigne donc, il ne refuse rien.
#
# A REFAIRE A CHAQUE CHANGEMENT DE MODELE : c'est precisement une bascule de
# modele non enregistree qui avait fait passer un score de 93 a 84 sans qu'une
# ligne de texte ait bouge.
NON_CALIBREE = ('sens',)


def _bornes(t, m):
    """La phrase qui porte l'occurrence — le juge a besoin du contexte, pas du mot nu."""
    a = t.rfind('.', 0, m.start()) + 1
    b = t.find('.', m.end())
    b = len(t) if b < 0 else b + 1
    return t[a:b].strip()[:400]


def lire_fiches(chemin):
    """Découpe un livrable de chasse en fiches. Une fiche = « ## P<n> — <titre> »."""
    txt = pathlib.Path(chemin).read_text(encoding='utf-8')
    out = []
    blocs = re.split(r'\n(?=##\s+P\d+\s+—)', txt)
    for b in blocs:
        m = re.match(r'##\s+(P\d+)\s+—\s*(.+?)\n', b)
        if not m:
            continue
        champs = {'titre': m.group(2).strip()}
        for c in re.finditer(r'^-\s+\*\*(.+?)\*\*\s*:\s*(.*?)(?=\n-\s+\*\*|\n##|\Z)',
                             b, re.S | re.M):
            champs[c.group(1).strip()] = c.group(2).strip()
        out.append({'id': m.group(1), 'champs': champs})
    return out


def questions_du_champ(nom, texte):
    """Toutes les questions que ce champ fait naître, dans l'ordre du texte."""
    q = []
    vus = set()

    def pose(t, extrait, ancre):
        cle = (t, extrait[:120])
        if cle in vus or not extrait.strip():
            return
        vus.add(cle)
        q.append({'type': t, 'champ': nom, 'extrait': extrait.strip()[:300],
                  'ancre': ancre[:400]})

    for m in RX_CHIFFRE.finditer(texte):
        ex, an = m.group(0).strip(), _bornes(texte, m)
        pose('chiffre', ex, an)
        pose('reserve', ex, an)          # toujours en doublure : c'est la plus rentable
    for rx, t in ((RX_ATTRIBUTION, 'attribution'), (RX_MODALITE, 'modalite'),
                  (RX_QUALIF, 'qualification'), (RX_DATE, 'date')):
        for m in rx.finditer(texte):
            pose(t, m.group(0), _bornes(texte, m))
    for m in RX_CITATION.finditer(texte):
        pose('citation', m.group(1) or m.group(2) or '', _bornes(texte, m))
    for m in RX_URL.finditer(texte):
        pose('lien', m.group(0), _bornes(texte, m))
    return q


def questionnaire(fiche, source_fichier):
    """Le questionnaire figé d'UNE fiche."""
    qs = []
    for nom in CHAMPS_ATTESTANTS:
        v = fiche['champs'].get(nom)
        if v:
            qs += questions_du_champ(nom, v)
    if fiche['champs'].get('Essentiel'):
        qs.append({'type': 'sens', 'champ': 'Essentiel',
                   'extrait': fiche['champs']['Essentiel'].strip()[-300:],
                   'ancre': ''})
    for i, q in enumerate(qs, 1):
        d = TYPES[q['type']]
        q['id'] = '%s.Q%d' % (fiche['id'], i)
        q['numero_type'] = d['n']
        q['mecanique'] = d['mecanique']
        q['bloquante'] = q['type'] not in NON_CALIBREE
        q['question'] = d['libelle'].format(extrait=q['extrait'])
    return {'element': fiche['id'], 'fichier': source_fichier,
            'titre': fiche['champs'].get('titre', ''),
            'questions': qs, 'total': len(qs)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('action', choices=['extraire'])
    ap.add_argument('fichiers', nargs='+')
    ap.add_argument('--resume', action='store_true', help='en clair, pas en JSON')
    a = ap.parse_args()

    elements = []
    for f in a.fichiers:
        for fiche in lire_fiches(f):
            elements.append(questionnaire(fiche, pathlib.Path(f).name))

    total = sum(e['total'] for e in elements)
    meca = sum(1 for e in elements for q in e['questions'] if q['mecanique'])
    corps = json.dumps(elements, ensure_ascii=False, sort_keys=True)
    d = {'elements': elements, 'total_questions': total,
         'mecaniques': meca, 'jugees': total - meca,
         'empreinte': hashlib.md5(corps.encode('utf-8')).hexdigest()}

    if not a.resume:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0

    print('%d élément(s) · %d questions · %d mécaniques (%d %%) · %d à juger'
          % (len(elements), total, meca, round(100 * meca / max(total, 1)), total - meca))
    print('empreinte du questionnaire : %s' % d['empreinte'])
    par_type = {}
    for e in elements:
        for q in e['questions']:
            par_type[q['type']] = par_type.get(q['type'], 0) + 1
    print('\npar type :')
    for t, n in sorted(par_type.items(), key=lambda x: -x[1]):
        print('  %-14s %4d  %s' % (t, n, 'mécanique' if TYPES[t]['mecanique'] else 'jugée'))
    print('\npar élément :')
    for e in elements:
        print('  %-6s %3d questions   %s' % (e['element'], e['total'], e['titre'][:70]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
