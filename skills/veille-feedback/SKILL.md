---
name: veille-feedback
description: Étape 6 — traitement AUTONOME de la notation du lecteur : lit ses classements, ses commentaires et ses avis, en induit les règles par axe (écrites seulement si elles retrouvent ses classements), reconstruit le deck et les consignes de chasse. AUCUN dialogue : le rapport de fin d'étape dit ce qui a été écrit et avec quel score. Déclencheurs — « /veille-feedback <veille> », « j'ai fini la veille X », enchaînement automatique après l'étape 5.
---

# Veille feedback — étape 6

## Où tout s'écrit

**Deux magasins, et les deux comptent.**

- **Le workspace de la run** — c'est là que le graphe attend les livrables, et le nœud de
  vérification qui suit ne démarre pas tant qu'il en manque un.
- **Le silo de l'owner** (`owners/<owner>/`, owner lu depuis `WORKSPACE.txt`) — c'est ce qui
  **survit à la run**. Le workspace disparaît ; le deck, les règles et les ratings doivent être
  là au démarrage de la run suivante.

Ce qui s'écrit aux deux endroits — d'abord le workspace, puis recopié dans le silo :

| Livrable | Workspace (le graphe le lit) | Silo (la run suivante le lit) |
|---|---|---|
| non-ouverts | `analyse-non-ouverts.md` | — |
| règles proposées | `regles-proposees.md` | — |
| écarts de tier | `state/ecarts-tier.md` | — |
| règles par axe | `state/regles-axes.json` | `preferences/regles-axes.json` |
| deck | `state/deck-<watch>.json` | `preferences/deck-<watch>.json` |
| profil suivant | `profil-prochaine-run.json` | `preferences/profil-prochaine-run.json` |
| ratings | `ratings/<watch>-ratings.jsonl` | `preferences/ratings/<watch>-ratings.jsonl` |
| rapport de session | `db/feedback-reports/<run-id>.md` | `db/feedback-reports/<run-id>.md` |

Les trois premiers sont le **raisonnement** de l'étape : ils justifient ce qui a été écrit
ailleurs, et c'est sur eux que la vérification travaille. Ils ne partent pas au silo.

**Chemins sans accents** — ce sont des noms de fichiers, pas du texte.

## Le modèle DECK — 3 leviers pour la prochaine run

**Le tri de l'étape 5 est un classement en 6 tiers** — **Excellent · Cool · Intéressant · Neutre · Bof · Inutile** — que le lecteur **corrige** à partir des tiers posées par les chasseurs à l'étape 2. **Rien n'est jeté, pas de publication séparée** : la constellation classée EST le livrable. La notation exporte par finding sa **tier finale** (+ `tier_source` agent/user), pas un score /10.

Ce skill (étape 6) part de `notation-terminee.json` (schéma tiers) et produit **3 leviers** pour la prochaine run :

**1. DECK DE PRÉFÉRENCE** — ~5 findings adorés + ~5 détestés + les **surcotés**

**La polarité se lit sur le tier FINAL posé par le lecteur, jamais sur le fait qu'il ait touché
la fiche.** Une fiche qu'il a RÉTROGRADÉE n'est pas une fiche qu'il aime : c'est une fiche que
l'agent avait surestimée. La confondre avec un « adoré » enseigne au juge suivant de refaire
l'erreur, et fait chercher aux chasseurs davantage du même sujet.

- `adorés` — tier final **Excellent ou Cool**. Rien d'autre n'y entre. S'il n'y en a aucun,
  la liste est VIDE : mieux vaut aucun exemple qu'un exemple faux.
- `détestés` — tier final **Bof ou Inutile**.
- `surcotés` — les corrections **à la baisse** : `{titre, tier_agent, tier_anthony, motif}`.
  Ce sont des **contre-exemples de calibration**, pas des sujets à chercher. Le juge les lit
  pour savoir où il place la barre trop haut ; les chasseurs ne les transforment JAMAIS en
  requêtes.

Chaque entrée reste la brève elle-même (titre + essentiel + axe + source), **les brèves elles-mêmes** (titre + essentiel + axe + source), pas des scores. Chaque entrée porte sa **tier** + le **commentaire « pourquoi »** si présent. **Poids « non consulté » = IGNORÉ** (MNAR : pas vu ≠ rejeté), jamais négatif : n'entrent au deck que les findings **vu (`vu`) OU déplacés (`tier_source=='user'`)**. Injecté **en few-shot au JUGE** du prochain run + ancre le **rerank/trim final**. Écrit dans `state/deck-<watch>.json`, recopié dans `owners/<owner>/preferences/deck-<watch>.json`.

**1 bis. RÈGLES PAR AXE — induites, testées, puis validées**

Le lecteur ne peut pas dire à l'avance ce qui fait qu'un finding est Excellent : c'est en classant
qu'il le découvre, et le critère change avec le sujet de la run. On ne le lui demande donc pas —
on l'**induit de ses gestes**, puis on **vérifie que la règle retrouve ses corrections** avant de
la lui proposer.

Pour **chaque axe** ayant au moins 3 findings classés :

1. **Observer** — ce qu'il a monté, ce qu'il a descendu, ses commentaires, ses avis
   (`trop technique`, `pas clair`, `déjà vu`…), et ce qu'il n'a pas ouvert.
2. **Formuler 2 ou 3 règles candidates**, courtes, au présent, propres à cet axe :
   « en Robotique, ce qui monte est ce qui sort du labo ; un banc d'essai de plus tombe ».
3. **Tester chaque candidate sur les findings DÉJÀ CLASSÉS de cet axe** : combien de ses
   classements la règle retrouve-t-elle, combien manque-t-elle ? Une règle qui ne retrouve pas
   au moins les deux tiers est jetée sans être proposée — elle décrit une intuition, pas ses gestes.
4. **Écrire directement celles qui passent le seuil** dans `state/regles-axes.json` (recopié
   dans `owners/<owner>/preferences/regles-axes.json`), statut `validee`, **score inscrit à côté**, avec
   3 à 6 **mots-clés** (les termes qu'une recherche visant cette règle contiendrait). Sans
   mots-clés, la règle est inapplicable : c'est par eux que l'étape de chasse prouve qu'elle a
   cherché là où la règle demande.
5. **Seuil d'écriture** : au moins **3 classements testés** dans l'axe **et au moins deux tiers
   retrouvés**. En dessous, la règle est consignée en `piste` dans le même fichier — visible,
   jamais appliquée, réexaminée à la run suivante avec plus de matière.

**Pas de dialogue de validation.** La preuve chiffrée remplace l'accord oral : une règle qui ne
retrouve pas les classements du lecteur ne s'écrit pas, et une règle qui les retrouve n'a pas
besoin qu'on la lui fasse confirmer. Le rapport de fin d'étape liste ce qui a été écrit, avec les
scores — il peut le contester après coup, comme n'importe quel livrable.

**2. CONSIGNES DE CHASSE** — un mini-agent « profileur » fond le deck + les commentaires-**FOND** en instructions de recherche concrètes (sujets/acteurs/angles/sources à **creuser** ou **alléger**), écrites dans `owners/<owner>/preferences/selection-rules.md` (+ `subject.md` pour le cadrage axes) — ces deux-là vivent dans le silo seulement : elles sont lues par la run suivante, pas par le graphe. Les chasseurs les transforment en **requêtes réelles**. Le carnet de sources devient une **suggestion validée**, jamais une promo/rétro auto.

**3. RÈGLES DE FORME** — les commentaires-**FORME** → règle dans le fichier du rôle qui écrit (`synthetiseur-rules.md`). Le **NEXT se scinde** : **fond → chasse** (levier 2), **forme → rôle** (levier 3).

**OBJECTIF** : la prochaine run vise **couverture + surprise + quelques vrais hits Excellent**, PAS « maximiser la proportion de ce que le lecteur aime déjà » (l'optimiser fabrique une bulle de filtre — la valeur d'une veille est l'angle mort, pas le confort).

**ANTI-BULLE — l'ÉCLAIREUR.** Un chasseur du casting a pour mandat de chercher hors de tous les axes et rend ses graines dans `state/axes-candidats.json` ; le lecteur les tranche à l'étape 5. Un finding d'exploration noté Excellent devient une graine d'axe. Ces pistes sont **exclues de toute optimisation « proportion likée »**.

**Puis** écrire `axes_prochaine_run` + `profil-prochaine-run.json` (`{fraicheur, decisions, ajouts}`).

## Principes de lecture

- **Un commentaire = quelque chose l'a dérangé.** Chaque commentaire et chaque avis produit une
  règle, dans le fichier du rôle concerné. Rien ne se perd, rien ne se discute.
- **Une règle ne s'écrit que si elle se vérifie** sur les classements de la run — le score
  l'accompagne, toujours.
- **Le rapport de fin d'étape liste ce qui a été écrit**, avec les scores. Le lecteur le lit après
  coup et conteste ce qu'il veut, comme n'importe quel livrable.

## When to invoke

- `/veille-feedback <watch>` ou « j'ai fini la veille X », « on traite mes feedbacks X »
- Après que le lecteur a classé les findings sur la constellation

## Input source

`data/runs/<id>/notation-terminee.json` sur le serveur — porte, par node-id : `tier`, `tier_source` (agent/user), `vu` (bool), `comment` (optionnel), `tags` (optionnel, ex. `dejavu`), commentaire de forme (optionnel).

## Le protocole — 7 sous-étapes, dans cet ordre

**Aucun dialogue.** On ne demande rien, on n'annonce rien, on ne fait valider aucune règle : on
lit, on teste, on écrit, et le rapport de fin d'étape dit ce qui a été écrit et avec quel score.
Le lecteur le lit après coup et conteste ce qu'il veut, comme n'importe quel livrable.

**Charger d'abord** `notation-terminee.json` de la run + le `constellation-data.json` associé
(pour mapper node-id → titre / axe / essentiel).

### 6.1 — Lire les non-ouverts comme des rejets

**Livrable : `analyse-non-ouverts.md`.**

Un finding **non ouvert** est un rejet prononcé sur le seul **TITRE** — c'est le seul signal qui
juge la porte d'entrée, et rien d'autre ne le donne.

- Séparer les findings `vu` des `non vu`, par axe et par tier posée par l'agent.
- Chercher **ce que les titres ouverts ont et que les autres n'ont pas** : forme du verbe, présence
  d'un chiffre, nom d'acteur connu, promesse de révélation contre annonce de lancement.
- Écrire ce qu'on trouve, et **ce qu'on ne trouve pas** — un motif absent est un résultat.
- **Si le signal de clic n'a pas voyagé** (aucun champ `vu`, ou tous à `false`) : l'écrire
  franchement dans l'analyse. Ne JAMAIS traiter tous les non-ouverts comme des rejets par défaut.

### 6.2 — Traiter les commentaires un par un

**Livrable : `regles-proposees.md`** — chaque commentaire, ce qu'il change, et où.

Un commentaire = quelque chose l'a dérangé. Chacun produit une règle, aucun ne reste sans suite.

**Trancher NOW ou NEXT** pour chaque :
- **NOW** — appliqué à la prochaine run : la règle part tout de suite dans le fichier de rôle.
- **NEXT** — mis en attente : consigné dans `regles-proposees.md`, réexaminé à la run suivante
  avec plus de matière. Un commentaire isolé qui ne se recoupe avec rien va en NEXT.

**Le fichier de rôle**, dans le silo (`owners/<owner>/preferences/`) :

| La plainte porte sur | Fichier |
|---|---|
| « ne me remonte plus ça » / déjà vu / hors sujet / pas assez important | `selection-rules.md` |
| la carte : trop longue, essentiel qui n'accroche pas, nature du système pas dite d'emblée | `synthetiseur-rules.md` |
| le rendu, le registre, le format du livrable | `publisher-rules.md` |
| le scope, un axe | `subject.md` (proposer la modif) |

Le tri décisif : la plainte porte-t-elle sur **ce qu'on lui a remonté** (→ sélection) ou sur **la
façon dont c'était traité** (→ rédaction) ?

**Un commentaire incompris se pose tel quel en question ouverte** dans `regles-proposees.md`. On ne
l'interprète jamais.

**Forme de la règle écrite** : une phrase impérative, mots ordinaires, max 2 lignes. Pas de
« Diagnostic : … », pas de reprise du finding, pas de jargon de spec (« bascule d'un acteur »,
« poser le poids », « ancrer »). Si elle a besoin d'un exemple, UNE incise entre parenthèses
(« ex `sf6` — K3 fermé »), pas un paragraphe.

### 6.3 — Traiter les écarts de tier

**Livrable : `state/ecarts-tier.md`** — par axe : ce qui a été monté, ce qui a été descendu, de
combien de crans.

Chaque déplacement dit où l'agent s'est trompé :
- un finding **monté** dit ce que l'agent **sous-estime** ;
- un finding **descendu** dit ce qu'il **surestime** ;
- les **SURCOTÉS** (montés par l'agent, rabaissés par le lecteur) sont le signal le plus net : ils
  disent où sa barre est trop haute.

**Regrouper par axe** — c'est là que les régularités apparaissent. **Aucun écart est un résultat**,
pas une étape vide : l'agent a visé juste, on l'écrit.

### 6.4 — Induire les règles par axe et les tester

**Livrable : `state/regles-axes.json`** (+ miroir silo) — par axe : la règle, son sens, ses
mots-clés, son score de preuve.

Les candidates sortent des **trois sources précédentes** : les non-ouverts (6.1), les commentaires
(6.2), les écarts de tier (6.3). Protocole et seuil : § « RÈGLES PAR AXE » ci-dessus.

**Les mots explicites du lecteur (6.2) passent AVANT ce qu'on déduit de ses gestes** : une règle
induite qui contredit un commentaire est une règle fausse — elle ne s'écrit pas.

Sous le seuil, la règle ne se grave pas : elle va en `piste` dans `regles-axes.json` ET dans
`regles-proposees.md`.

### 6.5 — Reconstruire le deck de préférence

**Livrable : `state/deck-<watch>.json`** (+ miroir silo). Format et règles : § « Construire le
DECK » ci-dessous.

**Moins de findings notés que le deck n'en demande** : le construire plus court. Jamais le
compléter avec du non-noté.

### 6.6 — Écrire l'évolution des axes

**Livrable : `profil-prochaine-run.json`** (+ miroir silo) — axes gardés, faits évoluer, retirés,
ajoutés. Détail : § « Évolution des axes » ci-dessous.

**À partir des SEULES règles validées en 6.4**, jamais d'une intuition. **Aucune décision d'axe** :
recopier le profil courant — un fichier absent fait repartir la run suivante à l'aveugle.

### 6.7 — Ranger les notes et écrire le rapport de session

**Livrables : `ratings/<watch>-ratings.jsonl`** (+ miroir silo) **et `db/feedback-reports/<run-id>.md`.**

Une ligne JSON par finding noté : `{title, tier, tier_source, vu, agent (axe), comment, tags,
section_id (node-id), run, ts}`. **Sans `section_id` distinct par finding, les notes dédupliquent
en une seule ; sans `agent`, les scripts consommateurs crashent.**

C'est le magasin où le deck ira piocher ses exemplaires. Gabarit du rapport : § « Rapport de
session » ci-dessous.

**Si le rapport ne s'écrit pas** : les notes rangées suffisent à sauver la run, le rapport se
refait après.

---

## Construire le DECK

`state/deck-<watch>.json`, recopié dans `owners/<owner>/preferences/deck-<watch>.json` :

```json
{
  "watch": "<watch>",
  "run_source": "<run-id>",
  "generated_at": "YYYY-MM-DD",
  "adorés": [
    {"tier": "Excellent", "titre": "...", "essentiel": "...", "axe": "...", "source": "...", "pourquoi": "<commentaire ou raison brève>"},
    ...
  ],
  "détestés": [
    {"tier": "Bof|Inutile", "titre": "...", "essentiel": "...", "axe": "...", "source": "...", "pourquoi": "<commentaire ou raison brève>"},
    ...
  ],
  "surcotés": [
    {"titre": "...", "tier_agent": "Excellent", "tier_anthony": "Neutre", "axe": "...", "motif": "<pourquoi l'agent l'a surestimé>"},
    ...
  ]
}
```

Règles :
- **~5 adorés + ~5 détestés** (pas plus, pas moins — le juge du prochain run les lit en few-shot, dépasser 10-12 dilue).
- **Findings vu OU déplacés seulement.** Un finding jamais consulté = poids 0, exclu.
- **Le `pourquoi`** : commentaire du lecteur si présent, sinon 1-2 mots (« angle disruptif chiffré », « annonce vide »).

## Consignes de chasse (levier 2)

Traiter les commentaires **FOND** :
- Sujets/acteurs à **creuser** → append dans `selection-rules.md` (« le lecteur a aimé les findings sur X → chasseur cherche plus dans cette famille »).
- Sujets/acteurs à **alléger** → append dans `selection-rules.md` (« le lecteur a détesté les findings sur Y → chasseur évite ce motif »).
- Ajustements de scope/axe → proposer une modif de `subject.md`.

## Règles de forme (levier 3)

Traiter les commentaires **FORME** :
- Défaut d'essentiel/carte → `synthetiseur-rules.md`
- Défaut de rendu → `publisher-rules.md`

## Évolution des axes

Analyser les tiers de la session :
- Axe avec beaucoup de Bof/Inutile → recentrer.
- Axe scoré haut → élargir.
- Suggestions d'axes (Volet B — `constellation/suggestions-axes.json` si présent) → présenter, valider/rejeter.

Écrire `axes_prochaine_run` (`{decisions:{<axe>:{choix, vers}}, ajouts:[{titre}]}`) et `profil-prochaine-run.json` (`{fraicheur, decisions, ajouts}`) à la racine du workspace, puis recopier dans `owners/<owner>/preferences/`.

## Thermomètre dejavu (bon état de la veille)

**Motif** : le tag `dejavu` posé par le lecteur est un signal de **novelty** (dimension orthogonale à la qualité — Castells et al. 2011), pas un signal de qualité. Il ne va donc PAS dans le deck de préférence (contamine le juge — preference leakage, arXiv 2502.01534) ni dans les règles chasseur (fabrique une bulle de filtre). Il alimente **uniquement** un thermomètre de bon état de la veille, consulté au démarrage du run suivant.

**Action à la clôture** : compter les findings taggés `dejavu` dans `notation-terminee.json` et append une ligne dans `state/veille-health-<watch>.json`, recopié dans `owners/<owner>/preferences/veille-health-<watch>.json` :
```json
{
  "watch": "<watch>",
  "runs": [
    {"run": "<run-id>", "date": "YYYY-MM-DD", "total_notes": N, "dejavu_count": D, "ratio": D/N},
    ...
  ]
}
```

**Interprétation (lue par `veille-start` au run suivant)** — moyenne des 3 derniers ratios :
- **< 10 %** → rien à signaler
- **10-20 %** → simple note dans le rapport ; pas de bruit au lecteur
- **> 20 %** → au démarrage du run suivant, alerter le lecteur : *« ratio dejavu à X %, la chasse dérive vers le mainstream. Tu veux qu'on regarde la stratégie chasseur (sources, longue traîne) avant de partir ? »*

**Interdits** :
- **Ne JAMAIS** ajouter un dejavu au deck « détestés ».
- **Ne JAMAIS** baisser la tier d'un finding parce qu'il porte le tag dejavu (2 dimensions orthogonales — 2/3 des dejavu sont notés Intéressant/Excellent).
- **Pas de correctif automatique** : le thermomètre est reporté dans le rapport de fin d'étape, il ne déclenche jamais de filtrage ou une réécriture de règles par la pipeline seule.

## Rapport de session (OBLIGATOIRE, à CHAQUE run)

Avant la clôture, écrire un **rapport de feedback durable** qui consigne TOUT ce qui a été décidé — règles NOW écrites, règles NEXT mises en attente, scores à l'appui. Trace d'audit de la boucle d'apprentissage — produite à **chaque run, sans exception**.

**Où** : `db/feedback-reports/<run-id>.md` dans le workspace, recopié dans `owners/<owner>/db/feedback-reports/<run-id>.md`. Créer les dossiers si absents. Un fichier par run-id.

**Gabarit** :
```
# Rapport feedback — <watch> / owner <owner> — run <run-id>
Date : YYYY-MM-DD · Relecteurs : <noms> (N findings notés)

## Répartition tiers
- Excellent : <N> · Cool : <N> · Intéressant : <N> · Neutre : <N> · Bof : <N> · Inutile : <N>
- Désaccords notables (pré-classement agent vs classement final) : <fids>

## Points discutés (NEXT)
### <fid> — <tier finale>
- Commentaire : <verbatim court>
- NEXT : <règle ajoutée + fichier cible>
...

## Règles NEXT ajoutées (récap par fichier)
- selection-rules.md : <n> · synthetiseur-rules.md : <n> · publisher-rules.md : <n> · subject : <n>

## Deck produit
- Adorés : <N> · Détestés : <N> → deck-<watch>.json

## Thermomètre dejavu
- Ratio ce run : <D>/<N> = <X %> · Moyenne 3 derniers : <Y %>

## Suggestions d'axes
- <si applicable>
```

**Format standard — deux sorties** :
1. **`.md`** (gabarit ci-dessus) — dans `db/feedback-reports/<run-id>.md`, aux deux endroits.
2. **`.html` style Notion** — version lisible/partageable, à partir de `assets/feedback-report-template.html` (CSS Notion embarqué, s'ouvre seul dans un navigateur). Écrire à côté du `.md`.

Le rapport est la **mémoire de la boucle** : au run suivant, `/veille-start` peut le relire pour vérifier que les règles ont bien été appliquées.

## Clôture

> **Feedback `<watch>` terminé.**
> - <P> points discutés : <N> règles ajoutées (selection:x / synthetiseur:y / publisher:z / subject:u)
> - Deck : <A> adorés · <B> détestés → `deck-<watch>.json`
> - Thermomètre dejavu : <ratio ce run> (moyenne 3 derniers : <Y %>) → <sain / à surveiller / alerte>
> - Suggestions d'axes : <si applicable>
> - **Rapport de session : `owners/<owner>/db/feedback-reports/<run-id>.md`**
>
> **Prochaine étape : `/veille-publish <watch>`** — écrit le niveau 2 des gardés, produit le(s) livrable(s), archive, referme la boucle.

Le nœud de vérification de l'étape 6 prend la main ensuite ; il n'y a rien à annoncer ni à lancer.

## Hard rules

- **AUCUN dialogue** : ni annonce, ni question, ni validation demandée. Le rapport de fin d'étape est la seule sortie.
- **Une carte notée sans commentaire ne se discute pas** : sa tier compte pour l'induction, rien de plus.
- Chaque commentaire est tranché **NOW** (règle écrite tout de suite dans le fichier de rôle) ou **NEXT** (consigné dans `regles-proposees.md`, réexaminé à la run suivante). Aucun ne reste sans suite.
- Les règles écrites alimentent les fichiers de rôle que les chasseurs et les synthétiseurs lisent au run suivant.
- **Les sept livrables du graphe s'écrivent tous** : sans eux, la vérification de l'étape ne démarre pas.
- **TOUJOURS** écrire le rapport de session avant la clôture — un run sans rapport = boucle d'apprentissage non tracée
- **Deck** : ~5+5 max, findings vu-ou-déplacés seulement, poids « non consulté » ignoré
- **Dejavu** : jamais dans le deck détesté, jamais utilisé pour baisser une tier automatiquement
- **Une règle écrite** : max 2 lignes, mots ordinaires, pas de jargon de spec
