---
name: veille-pipeline
description: SOCLE d'une run de veille — la carte des 8 étapes, les invariants vrais partout, la forme de la vérification, ce qu'on ne fait jamais. Le protocole détaillé d'une étape vit dans le skill de cette étape, injecté avec celui-ci. Déclencheurs — "/veille-pipeline", "lance une veille", "on attaque la veille", "étape suivante de la veille".
---

# Veille — le socle

## Ce que tu as sous les yeux

Ce document porte **ce qui est vrai à toutes les étapes**. Le protocole de ton étape vit dans le
skill de cette étape — injecté avec celui-ci, dans le même prompt : tu n'as rien à aller chercher,
et tu ne lis le protocole d'aucune étape que tu ne joues pas.

**Le graphe de flux (`pipeline/workflows/veille.json`) est la vérité exécutable** : c'est
lui qui compose ton brief et fixe tes sous-étapes. Ce socle ne redéfinit aucune règle métier — une
barre écrite à deux endroits divergera : il renvoie plutôt qu'il n'écrit.

---

## La pipeline en un coup d'œil

| # | Étape | Ce qu'elle produit | Protocole |
|---|---|---|---|
| 1 | Préparer la run | terrain de travail, casting, contexte du lecteur | `veille-start` |
| 2 | Chasse | les passants trouvés et classés par tier, puis dédupliqués — le vivier monte entier (`veille-launch-researcher`, § La déduplication) | `veille-launch-researcher` |
| 3 | Monter la constellation | les findings apparentés groupés en histoires, un essentiel par histoire, bundle assemblé, constellation d'éval déployée | `veille-assemble-niveau1` |
| 4 | Prévenir le lecteur | l'invitation envoyée, une fois la vérification verte | `veille-publish` |
| 5 | Notation | **barrière humaine** — Le lecteur corrige les tiers, commente, fait évoluer les axes | aucun agent |
| 6 | Feedback | les règles par axe, le deck, le profil de la run suivante | `veille-feedback` |
| 7 | Publier | les livrables du profil, la constellation publiée, la mémoire du domaine | `veille-publish` |
| 8 | Bilan | ce que la run a coûté, ce qui doit remonter dans les skills | `veille-analyse-etape` |

Chaque étape est suivie de **sa vérification**, qui porte le rang de l'étape qu'elle juge.
L'étape 5 n'en a pas : ni transcript ni agent à auditer.

**Le chaînage est bloquant** : rien ne monte avant que la vérification de la chasse soit verte,
personne n'est invité avant que celle des essentiels le soit.

---

## Les invariants — vrais partout

- **I1. Nommage explicite** : `chasseur-3-praticien-p2`, `verif-praticien-p2`. Une liste d'agents anonymes devient illisible.
- **I2. Écriture au fil de l'eau, jamais en fin.** Un agent coupé qui garde tout en mémoire perd tout.
- **I3. Un agent long ne lance pas de sous-agent.**
- **I4. Ne conclure « mort » qu'après vérification** (`TaskOutput` + relire le fichier). Un watchdog signale une absence, pas une mort.
- **I5. Tout agent est FRAIS.** Chaque lancement, à chaque tour, instancie un agent neuf, à contexte vierge — producteurs comme vérificateurs. Aucun `SendMessage` pour reprendre un agent avec son contexte. Ce qu'un agent sait du tour précédent, il le **lit** : ses propres livrables et le rapport qui lui est remis dans son brief. Motif : un contexte d'agent ne se relit pas, ne survit ni à une coupure ni à un résumé de contexte, et rend l'exécution non rejouable. L'état de la run vit dans les livrables du workspace — inspectables, versionnés, et c'est sur eux que la vérification travaille.
- **I5 bis. Un seul style d'écriture, pour tous les owners.** Tout texte destiné à un lecteur — essentiel monté à l'étape 3, digest, newsletter, résumé — suit `veille-style` : huit gestes et un exemple de référence complet, que tout agent qui écrit reçoit avant d'écrire. Pas de plafond de longueur — une idée par phrase, une notion par paragraphe, et on déplie plutôt que de compresser. C'est une règle de la pipeline, pas une préférence de silo : un owner apporte ses règles de sélection et son ton, jamais son propre niveau de langue. Jugé à la vérification de l'étape 3, par le juge unique de chaque essentiel.
- **I6. Paralléliser dès que les lots ne se parlent pas.** Le seul travail global est la dédup.
- **I7. Deux agents n'écrivent jamais dans le même fichier.**
- **I8. Fin d'étape : lister les agents, arrêter ce qui traîne.**
- **I9. Les mesures se font sur les transcripts, pas sur les déclarations d'agents — mais au POST-MORTEM, jamais pendant une run.** Une vérification ne relit aucun transcript : elle juge le livrable.
- **I10. Un écart se signale, il ne se rafistole pas.** Un compte rafistolé contamine tout l'aval.
- **I11. Rapport de run auto — à CHAQUE fin de nœud.** `run-node.py` régénère le bundle self-contained (`<workspace>/run-report-bundle/`) et le déploie sous `/c/<slug>-eval/report.html` (route `report.html` à ajouter à la liste blanche de `/c/<id>/` dans `server/server.js` : elle n'y est pas encore). URL vivante à chaque étape : entonnoir des chiffres, timing, liens vers les livrables. C'est LA page à ouvrir pour voir « où en est le run / pourquoi ça plante ».

---

## La vérification — même forme après chaque étape

**La vérification n'est pas une étape de plus.** Elle porte le rang de l'étape qu'elle juge et
n'a pas de rang à elle : dans le graphe, `verification: true` ; ses tâches s'écrivent
`<N>-verification.1`, `.2`, `.3`.

**C'est le SEUL juge du travail.** Aucun programme ne note le contenu d'un livrable : le runtime
ne contrôle que leur PRÉSENCE — le nœud suivant ne démarre pas tant qu'il en manque un. Tout ce
qui relève du jugement — l'effort tenu, la fidélité aux sources, la clarté, l'écriture, l'intérêt
— appartient à des agents frais qui lisent les transcripts. Une règle qu'on veut voir appliquée
s'écrit donc dans la liste « ce qu'on regarde à cette étape », jamais dans un contrôle mécanique.

**Trois sous-étapes, jamais plus** — recenser le périmètre et former les lots · fouiller chaque
livrable **contre sa définition close, et ses sources contre les pages téléchargées** · agréger les
failles. **Aucun transcript ne se relit pendant une run.** Seule varie la liste « ce qu'on regarde à cette
étape », injectée dans le détail de `.2`. Un vérificateur FRAIS par LOT de livrables, en parallèle, plus
un chef qui recense et agrège. Skill : `veille-verif-etape`.

**Ce qu'elle attrape** : l'écart entre ce qu'un agent *dit* avoir fait et ce que sa session
montre. Le runtime constate que les fichiers existent ; le vérificateur établit qu'ils ont été
**gagnés**.

**Zéro faille est un résultat valide** s'il est adossé aux traces. On impose l'effort, jamais le
résultat.

---

## Ce qu'on ne fait jamais

- Monter la constellation avant que la vérification de la chasse soit verte.
- Filtrer automatiquement le vivier des passants — le tri est humain (étape 5).
- Rembourrer un lot pour atteindre un seuil — le budget porte sur l'effort, pas sur la sortie.
- Sérialiser un travail dont les lots ne se parlent pas.
- Tuer un agent sans avoir vérifié son état réel.
- Laisser deux agents écrire dans le même fichier.
- Combler un écart de comptage — le signaler.
- Lancer les chasseurs sans avoir vérifié le moteur de recherche.
- **Dispatcher deux fois le même chasseur d'axe.** Un chasseur = UN dispatch, un `agentId` conservé.
- **Renommer le livrable de pistes** : reste `pistes-<chasseur>-T<n>.md`, du chasseur à la vérification.
- **Geler un transcript en cours de passe** : geler seulement en fin de passe.

## Garde-fous d'orchestration

- **Étape 1 — non-identité des fichiers de contexte** : deux fichiers censés porter des contenus distincts (`selection-rules.md`, `regles-axes.json`, `subject.md`) doivent réellement différer. Identiques, ils neutralisent en silence la règle qu'ils étaient censés porter.
- **Étape 2 — traçabilité** : conserver les `agentId` de tous les chasseurs, 2ᵉ vague comprise. Les comptes de `state/comptes-chasse.json` se déduisent des lots de pistes — un écart entre un compte et le lot qui le porte se signale, il ne se comble pas. L'effort, lui, ne se déclare pas : il se lit dans le transcript du chasseur.
- **Outils partagés** : ne PAS corriger un script de skill depuis une run en cours (hors périmètre) — écrire la variante dans `scripts/` du workspace ET porter la correction au skill au post-mortem.
