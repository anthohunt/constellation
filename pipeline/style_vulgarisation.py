# -*- coding: utf-8 -*-
"""Controle C22 — le style de vulgarisation, mesure par mesure.

Le modele de style vit dans `veille-style` : huit
gestes, chacun avec son test. Regle generale de la pipeline, commune a tous les
owners. Quatre mesures, calees sur des essentiels reels et sur les tags que le
lecteur y a poses :

  1. GLOSE  — un terme d'architecture arrive nu, sans etre explique a sa premiere
              occurrence.
  2. DENSITE — l'essentiel introduit plus de trois notions techniques. C'est la
              mesure qui attrape les textes tagges « troptechnique » : ils
              glosent bien, ils en ont simplement six ou huit.
  3. CONTRASTE — le texte pose un fait sans le placer contre l'habitude
              (« d'ordinaire X, ici Y », « contre X auparavant »). C'est le
              geste le plus souvent rate, de loin.
  4. BORNAGE — le texte frappe fort (record, premier, jamais vu) sans dire
              ce que ca n'implique PAS.

CE QUE CE MODULE NE SAIT PAS FAIRE, ET POURQUOI C'EST ECRIT ICI.
« Trop technique » ne se lit pas dans un motif de surface. Deux mesures ont ete
essayees sur des essentiels reels et ecartees :
  - le lexique de jargon seul : precision parfaite mais rappel 2/7 — la moitie des
    essentiels juges trop techniques glosent chaque terme correctement
    (Langevin, laplacien, reservoir computing : tous gloses, tous tagges) ;
  - le comptage des gloses : ne separe rien du tout (moyenne 4,3 chez les tagges
    contre 3,2 chez les autres, et un finding classe « Excellent » en porte cinq).
Le lexique reste donc un filet grossier, volontairement peu bruyant. Le jugement
« est-ce que j'ai du avaler trop de notions ? » appartient a la relecture profane
(C17) : c'est un lecteur frais qui compte, pas une expression reguliere.

Les cinq gestes restants (definir par la fonction, entrer par la fausse impression,
enumerer du concret, repeter trois fois, l'anti-exemple) relevent de la meme
relecture : ils se jugent, ils ne se comptent pas.

Meme module pour l'etape 3 (essentiels) et l'etape 6 (digest, newsletter, resumes) :
un seul style, un seul controle.
"""

import re
import unicodedata

# ---------------------------------------------------------------- jargon connu
# Termes d'architecture / de methode qui exigent une glose a la premiere
# occurrence. La liste s'etend a chaque run ou un terme passe nu : c'est le
# journal des mots qui ont deja bloque un lecteur.
JARGON = [
    # architectures et methodes
    'VLA', 'GRPO', 'PPO', 'DPO', 'RLHF', 'RLAIF', 'MoE', 'mixture-of-experts',
    'JEPA', 'V-JEPA', 'world model', 'modele du monde', 'autoregressif',
    'autoregressive', 'diffusion', 'transformer diffusion', 'latent', 'espace latent',
    'distillation', 'quantification', 'quantization', 'fine-tuning', 'LoRA',
    'chain-of-thought', 'scaling law', 'loi d\'echelle', 'on-policy', 'off-policy',
    'dual-system', 'monolithique', 'end-to-end', 'sim-to-real', 'zero-shot',
    'few-shot', 'in-context', 'attention', 'tokenizer', 'context window',
    # robotique
    'GR00T', 'pi0', 'pi0.5', 'teleoperation', 'proprioception', 'policy',
    # hardware et compute
    'HBM', 'HBM3', 'HBM4', 'CoWoS', 'TF32', 'FP8', 'FP16', 'BF16', 'NVLink',
    'kernel CUDA', 'CUDA', 'interconnexion', 'H100-equivalent', 'petaflop',
    'exaflop', 'wafer', 'lithographie', 'nanometre', 'yield',
    # eval et securite
    'SWE-bench', 'MMLU', 'ARC-AGI', 'red-teaming', 'jailbreak', 'prompt injection',
    'sandbox', 'cache-poisoning', 'exfiltration', 'alignement', 'alignment',
    'interpretabilite', 'sparse autoencoder', 'steering', 'eval',
    # infra logicielle
    'vLLM', 'torchrun', 'inference', 'serving', 'harness', 'runtime', 'plugin',
    'MCP', 'RAG',
]

# Ceux-la restent en anglais par convention — les traduire ajoute une friction la
# ou il n'y en avait pas. Jamais reclames en glose.
JARGON_DISPENSE = {
    'benchmark', 'transformer', 'embedding', 'rag', 'agent', 'token', 'prompt',
    'attention', 'inference', 'eval', 'policy',
}

# Marqueurs qui, autour du terme, valent glose.
GLOSE_OUVRANTE = r'[(\[—–,:]|\bc\'est-à-dire\b|\bautrement dit\b|\bsoit\b|\bune?\s'

# ------------------------------------------------------------------ contraste
CONTRASTE = [
    "d'ordinaire", 'd’ordinaire', "d'habitude", 'jusqu\'ici', 'jusqu’ici',
    'jusque-là', 'jusque-la', 'auparavant', 'avant cela', 'là où', 'la ou',
    'alors que', 'tandis que', 'désormais', 'desormais', 'au lieu de',
    'contre les', 'contre le ', 'contre la ', 'contre ses', 'contre son ',
    'pour la première fois', 'pour la premiere fois', 'à la place de',
    'par rapport à', 'par rapport a', 'comparé à', 'compare a',
    'plus que', 'moins que', 'deux fois', 'trois fois', 'le précédent',
    'la génération précédente', 'la generation precedente', 'reste loin de',
]

# -------------------------------------------------------------------- bornage
FORT = [
    'record', 'jamais vu', 'inédit', 'inedit', 'première fois', 'premiere fois',
    'le plus grand', 'le plus puissant', 'le plus rapide', 'le premier',
    'double tous les', 'triple', 'multiplié par', 'multiplie par', 'bat tous',
    'dépasse tous', 'depasse tous', 'sans précédent', 'sans precedent',
    'révolution', 'revolution', 'change tout', 'écrase', 'ecrase',
]
BORNE = [
    'ne veut pas dire', 'ne signifie pas', 'n\'implique pas', 'ne prouve pas',
    'ne garantit pas', 'en revanche', 'toutefois', 'cependant', 'néanmoins',
    'neanmoins', 'reste à', 'reste a ', 'reste loin', 'sous réserve',
    'sous reserve', 'estimation', 'estimé', 'estime', 'à confirmer',
    'a confirmer', 'limite', 'limites', 'prudence', 'pas encore',
    'ne dit rien', 'ne mesure pas', 'non reproduit', 'non vérifié',
    'non verifie', 'annonce non', 'déclaratif', 'declaratif',
]


def _plat(s):
    """minuscules sans accents — pour chercher un motif sans se battre avec l'orthographe."""
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower().replace('’', "'")


def _sans_balises(txt):
    return re.sub(r'[*_`#>]', '', txt or '')


def jargon_nu(txt, jargon=None):
    """Termes d'architecture employes sans glose a leur premiere occurrence."""
    nu = _sans_balises(txt)
    plat = _plat(nu)
    fautifs = []
    for terme in (jargon or JARGON):
        if terme.lower() in JARGON_DISPENSE:
            continue
        tp = _plat(terme)
        # premiere occurrence, en mot entier
        m = re.search(r'(?<![\w-])' + re.escape(tp) + r'(?![\w-])', plat)
        if not m:
            continue
        i, j = m.start(), m.end()
        # fenetre de glose : ce qui suit immediatement, ou l'apposition qui precede
        apres = nu[j:j + 90]
        avant = nu[max(0, i - 90):i]
        glose = (re.match(r'\s*' + GLOSE_OUVRANTE, apres, re.I)
                 or re.search(GLOSE_OUVRANTE + r'[^.]{0,60}$', avant, re.I))
        if not glose:
            fautifs.append(terme)
    return fautifs


def notions_techniques(txt, jargon=None):
    """Termes techniques distincts introduits par le texte, glosés ou non."""
    plat = _plat(_sans_balises(txt))
    vus = []
    for terme in (jargon or JARGON):
        if terme.lower() in JARGON_DISPENSE:
            continue
        if re.search(r'(?<![\w-])' + re.escape(_plat(terme)) + r'(?![\w-])', plat):
            vus.append(terme)
    return vus


# Plafond de notions par essentiel. Cale sur des essentiels reels : au-dessus de
# trois, les textes concernes sont exactement ceux que le lecteur a tagges
# « troptechnique », sans faux positif. Le plafond descendra a deux si les runs
# montrent que deux notions suffisent a bloquer la lecture.
NOTIONS_MAX = 3


def sans_contraste(txt):
    """True si le texte ne place jamais son fait contre une reference connue."""
    plat = _plat(_sans_balises(txt))
    return not any(_plat(m) in plat for m in CONTRASTE)


def fort_sans_borne(txt):
    """Renvoie le marqueur d'affirmation forte laisse sans phrase de limite, ou None."""
    plat = _plat(_sans_balises(txt))
    trouve = next((m for m in FORT if _plat(m) in plat), None)
    if not trouve:
        return None
    if any(_plat(b) in plat for b in BORNE):
        return None
    return trouve


# Plafond de longueur d'un essentiel, en mots. L'enveloppe habituelle de la veille
# est serree (181-213 mots) : les huit gestes s'y logent, ils ne l'agrandissent pas. Ce qu'on gagne en supprimant les
# termes a expliquer paie l'entree par la fausse impression. Le plafond ne
# s'applique QU'AUX essentiels (etape 3) : une section de digest a sa propre taille.
# Pas de plafond de longueur : ce qui se juge est la lecture, pas le compte.
# Conserve a zero pour les appelants qui l'importent encore.
MOTS_MAX_ESSENTIEL = 0

# Les chevilles d'articulation : une par texte. Deux, et le lecteur entend le
# gabarit ; trois, il repose le texte.
CHEVILLES = ('il faut bien voir', 'il faut voir', 'a noter', 'à noter',
             'concretement', 'concrètement', 'en clair', 'autrement dit',
             'ceci dit', 'cela dit', 'en pratique', 'du coup')


def chevilles_repetees(txt):
    """Une meme formule d'articulation employee plusieurs fois."""
    bas = (txt or '').lower()
    out = []
    for c in CHEVILLES:
        n = bas.count(c)
        if n > 1:
            out.append((c, n))
    return out


_MOIS = (r'janvier|f\u00e9vrier|mars|avril|mai|juin|juillet|ao\u00fbt|septembre|'
         r'octobre|novembre|d\u00e9cembre')

# Au-dela de ce seuil, le lecteur retient plus de noms qu'il ne suit d'idees.
# Mesure : le texte de reference se tient a 3,0 ; un essentiel compresse monte a 14.
DENSITE_MAX = 5.0


def densite_faits(txt):
    """Faits nommes pour cent mots : noms propres, chiffres, dates, references."""
    import re as _re
    t = _sans_balises(txt or '')
    mots = t.split()
    if len(mots) < 40:
        return 0.0
    n = len(_re.findall(r'\b\d+[\d ,.]*\s*%', t))
    n += len(_re.findall(r'\barXiv\s*\d', t, _re.I))
    n += len(_re.findall(r'\b\d{1,2}\s+(?:' + _MOIS + r')', t, _re.I))
    n += len(_re.findall(r'(?<![.!?]\s)(?<!^)\b[A-Z\u00c9\u00c8][a-z\u00e9\u00e8\u00ea\u00e0\u00ef\u00ee]+'
                         r'(?:\s+[A-Z\u00c9\u00c8][a-z\u00e9\u00e8\u00ea\u00e0\u00ef\u00ee]+)*', t))
    n += len(_re.findall(r'\b[A-Z]{2,}\b', t))
    return round(100.0 * n / len(mots), 1)


def ouverture_chargee(txt):
    """La premiere phrase porte-t-elle l'etat civil avant le sujet ?"""
    import re as _re
    t = _sans_balises(txt or '').strip()
    if not t:
        return False
    p1 = _re.split(r'(?<=[.!?])\s+', t)[0]
    return bool(_re.search(r'\b\d{1,2}\s+(?:' + _MOIS + r')|\barXiv|\b\d+\s*%', p1, _re.I))


def controler(txt, etiquette='texte', seuil_longueur=200, mots_max=None):
    """Les quatre mesures de C22 sur un texte. Renvoie une liste de defauts."""
    if not isinstance(txt, str) or len(txt.strip()) < seuil_longueur:
        return []
    defauts = []

    d = densite_faits(txt)
    if d > DENSITE_MAX:
        defauts.append(
            f"C22-densite: {etiquette} — {d} faits nommés pour 100 mots (plafond "
            f"{DENSITE_MAX}). Le lecteur retient plus de noms qu'il ne suit d'idées : "
            f"déplie, ne compresse pas."
        )
    if ouverture_chargee(txt):
        defauts.append(
            f"C22-ouverture: {etiquette} — la première phrase porte déjà une date, un "
            f"chiffre ou une référence. On ouvre sur la question du lecteur ; l'état "
            f"civil du travail cité vient après."
        )
    for c, n in chevilles_repetees(txt):
        defauts.append(
            f"C22-cheville: {etiquette} — « {c} » revient {n} fois. Une articulation "
            f"ne se répète pas : deux paragraphes qui s'ouvrent pareil s'entendent."
        )

    nus = jargon_nu(txt)
    if nus:
        defauts.append(
            f"C22-glose: {etiquette} — terme(s) d'architecture employé(s) sans "
            f"explication à la première occurrence : {', '.join(nus[:6])}. "
            f"Une incise de 4 à 8 mots qui dit ce que ça FAIT, pas ce que c'est."
        )

    notions = notions_techniques(txt)
    if len(notions) > NOTIONS_MAX:
        defauts.append(
            f"C22-densité: {etiquette} — {len(notions)} notions techniques dans un seul "
            f"texte (plafond {NOTIONS_MAX}) : {', '.join(notions[:8])}. Gloser chacune ne "
            f"suffit pas : le lecteur doit toutes les retenir. Garde trois briques, "
            f"descends le reste dans le rapport de fond."
        )

    if sans_contraste(txt):
        defauts.append(
            f"C22-contraste: {etiquette} — le fait n'est jamais placé contre "
            f"l'habitude ni contre l'état d'avant. Ajoute la phrase de contraste "
            f"(« d'ordinaire… ici… », « contre X auparavant »)."
        )

    fort = fort_sans_borne(txt)
    if fort:
        defauts.append(
            f"C22-bornage: {etiquette} — affirmation forte (« {fort} ») laissée sans "
            f"sa limite. Dis juste après ce que ça n'implique pas."
        )

    return defauts


def controler_document(brut, etiquette='document', seuil_longueur=200):
    """Meme controle, applique SECTION PAR SECTION a un document redige.

    Un digest ou une newsletter agrege une dizaine de findings : mesurer la
    densite de notions sur le fichier entier n'a pas de sens, le plafond y serait
    depasse par construction. Ce qui compte, c'est ce que le lecteur doit tenir en
    tete dans UN bloc. On decoupe donc sur les titres, et chaque section est jugee
    comme un essentiel.
    """
    txt = brut or ''
    # decoupe sur les titres HTML puis markdown, avant de retirer les balises
    morceaux = re.split(r'(?i)<h[1-4][^>]*>|\n#{2,4}\s', txt)
    if len(morceaux) < 2:
        morceaux = re.split(r'\n\s*\n\s*\n', txt)
    defauts = []
    for n, bloc in enumerate(morceaux, 1):
        propre = re.sub(r'<[^>]+>', ' ', bloc)
        propre = re.sub(r'[ \t]+', ' ', propre)
        if len(propre.strip()) < seuil_longueur:
            continue
        titre = re.sub(r'\s+', ' ', propre.strip())[:38]
        defauts.extend(controler(propre, etiquette='%s § %s...' % (etiquette, titre),
                                 seuil_longueur=seuil_longueur))
    return defauts


# --------------------------------------------------------------------- CLI
if __name__ == '__main__':
    import json
    import sys

    if len(sys.argv) < 2:
        print("usage: style_vulgarisation.py <findings.json | fichier.md|html> [...]")
        raise SystemExit(2)

    total, touches, examines = 0, 0, 0
    for chemin in sys.argv[1:]:
        if chemin.endswith('.json'):
            data = json.load(open(chemin, encoding='utf-8'))
            fs = data if isinstance(data, list) else data.get('findings', [])
            for f in fs:
                txt = (f.get('essentiel_fr') or f.get('essentiel')
                       or (f.get('fiche') or {}).get('essentiel_fr') or '')
                d = controler(txt, etiquette=f"finding `{f.get('id', '?')}`")
                examines += 1
                if d:
                    touches += 1
                    total += len(d)
                    for m in d:
                        print(m)
        else:
            txt = open(chemin, encoding='utf-8', errors='replace').read()
            txt = re.sub(r'<[^>]+>', ' ', txt)
            d = controler(txt, etiquette=chemin.split('/')[-1])
            examines += 1
            if d:
                touches += 1
                total += len(d)
                for m in d:
                    print(m)

    print(f"\n-- C22 : {total} défaut(s) sur {touches}/{examines} texte(s) examiné(s).")
