---
name: veille-analyse-etape
description: Use when the operator wants to analyze / post-mortem ONE step of a veille run — "analyse l'étape N", "post-mortem de l'étape chasse", "/veille-analyse-etape", "on analyse l'étape 2". Reads the WHOLE transcripts of ALL agents of that step + the step's skill(s) + its node in the flux graph + the deliverables, and produces a two-faced report — (1) audit d'exécution (livrables livrés ? comportement de l'IA vs protocole ? temps perdu ?) and (2) critique de la spec (le skill / le nœud du graphe sont-ils clairs et complets, ou induisent-ils les dérives ?). Diagnostic ONLY — hands concrete fixes to `adjust-pipeline`. UNE étape à la fois. Formalise l'étape 8 du graphe de flux `veille`.
---

# veille-analyse-etape — post-mortem d'UNE étape d'une run de veille

## Le budget d'effort se juge ICI, et nulle part ailleurs

**Aucune vérification ne relit un transcript pendant une run** — elle juge le livrable contre sa
définition close et ses sources contre les pages. Le comptage d'effort d'un producteur — pages
réellement ouvertes, formulations essayées, hôtes distincts, pages atteintes sans passer par une
liste de résultats — n'est donc mesuré nulle part tant que la run tourne.

**C'est le post-mortem qui le fait**, à froid, sur les transcripts conservés, quand le constat ne
bloque plus une étape. Pour chaque producteur de l'étape analysée : ce qu'il a réellement ouvert
contre le plancher de son casting, et l'écart s'il y en a un. Un plancher franchi ne se répare pas
rétroactivement : il devient une consigne pour la run suivante.


## À quoi sert ce skill

Après une run, on veut savoir **comment chaque étape s'est réellement passée** — pas « ça a produit un fichier », mais : l'IA a-t-elle suivi le protocole, s'est-elle bien conduite, a-t-elle perdu du temps, et — tout aussi important — **le skill et le nœud du graphe eux-mêmes sont-ils bons**, ou est-ce la spec qui induit les dérives observées.

**Principe cardinal : deux faces.** Une déviation constatée dans un transcript a deux causes possibles — soit l'agent s'est mal comporté (audit d'exécution), soit la spec était ambiguë/incomplète et l'a mal guidé (critique de la spec). **Le fix est souvent dans le skill ou le nœud du graphe, pas dans l'agent.** Un post-mortem qui ne regarde que l'exécution rate la moitié des corrections.

**Une étape à la fois.** On ne « note pas la run » d'un bloc.

**⚠️ Suggérer systématiquement l'enchaînement étape par étape.** Quand le lecteur demande « on analyse la run », ne pas rendre une analyse globale résumée — proposer un **balayage étape par étape** dans l'ordre chronologique (1 → 2 → 3 → …). À la fin de chaque étape, produire son Dashboard KPI + Dimensions + Actions, appliquer les fixes validés, puis demander explicitement « on passe à l'étape N+1 ? ». Tenir en tête un **tableau récap qui se remplit** au fil du balayage :

```
| Étape | Verdict | Drifts fixés | Restants |
|:-:|:-:|:-:|:-:|
| 1 Setup       | ✅ | 2 | 0 |
| 2 Chasse      | ✅ | 3 | 0 |
| 3 Constellation | 🟡 | 1 | 1 |
| 4 Éval        | — | — | — |
```

Motif : une analyse « globale » masque les chaînages (un drift de l'étape N vient souvent de l'étape N-1). Analyser dans l'ordre force la reconstitution du fil et la responsabilité au bon endroit.

**Diagnostic seul.** Ce skill ne corrige rien. Il produit un rapport avec des écarts nommés, pièces à l'appui, et pointe chaque fix vers `adjust-pipeline` (qui, lui, propage). Ne jamais éditer un skill, le graphe ou une config depuis ce skill.

## Invocation

`/veille-analyse-etape <run> <N>` — `<run>` = id ou chemin du workspace ; `<N>` = numéro d'étape (1-8), ou `<N>-verification` pour son contrôle. Sans `<run>`, prendre le workspace actif (le plus récent sous `~/veille-runs` — ou le cwd — contenant `state/comptes-chasse.json`).

## Ce qu'on analyse — trois faces

**Face A — audit d'exécution** (le transcript + les livrables) :
1. **Livrables vs critères de réussite.** Chaque livrable attendu (les `livrables` du nœud, et ceux que le nœud suivant réclame en entrée) existe, **non vide**, au **bon format**. Le verdict qualité = les critères « réussi quand… » sont-ils remplis, **pièces à l'appui**.
2. **Comportement de l'IA.** L'agent s'est-il **bien conduit** ? Repérer flail (essais répétés sans info neuve), boucles, re-lectures inutiles, dérive de sujet, outils tâtonnés, sous-agents mal briefés. Répondre avec des extraits.
3. **Conformité au protocole.** Le transcript suit-il les sous-étapes du nœud **dans l'ordre**, sans en **sauter** ni en **inventer** ? Toute incohérence est nommée avec la ligne du skill concernée + l'extrait du transcript.
4. **Temps / valeur / COÛT.** Chronométrie + tokens par passe/action — lire d'abord `<base>/metrics/substeps-etape-N.md` (durée + outils + tokens par sous-étape) et `<base>/metrics/tokens-run.md` (tokens par étape + total RUN). Repérer les **passes longues à faible rendement** — une passe de 25 min qui rend 1 piste, un vérificateur qui gonfle en tokens pour peu de valeur. Pas juste la durée brute — le **ratio temps/résultat**.

**Face B — critique de la spec** (le skill + la fiche, comme objets) :
5. **Le skill lui-même** — clair, complet, non ambigu ? Une consigne floue, une sous-étape sous-spécifiée, un critère non mesurable, un ordre implicite → est-ce **elle** qui a produit la déviation de la face A ? **Le nœud du graphe** — cohérent avec le skill, objectif et livrables bien posés, branchements `si_succes`/`si_echec` justes, cartes agent à jour ?

Pour chaque écart de la face A, trancher la **cause probable** : *agent* (a mal fait ce qui était clair) vs *spec* (a bien suivi une consigne mauvaise/ambiguë).

**Face C — Comparaison cross-runs** :
6. **Cette exécution vs les mêmes étapes des runs précédents.** Un post-mortem isolé rate les tendances : ce qui s'améliore (les fixes précédents ont-ils tenu ?), ce qui régresse (une bonne pratique s'est perdue ?), ce qui traîne comme drift récurrent, et l'évolution des chiffres. Sans référentiel, un post-mortem ne raconte qu'un moment.

**Où on trouve les post-mortems passés** : `owners/<owner>/db/post-mortems/<watch>-etape<N>-<run-id>.md` (silo owner, écrit par ce skill à la fin de chaque analyse). Le leader liste les fichiers du même `(watch, étape)` triés par date, extrait les métriques comparables (Verdict / chrono / drifts nommés / écarts par cause) et les met en regard de l'analyse courante. Si aucun post-mortem passé : le noter, produire Face C avec « base de référence — ce run est la 1re mesure ».

**Fixes qui n'ont pas tenu** : pour chaque écart de la Face A, croiser avec les post-mortems passés — si le même écart y figurait déjà avec un fix acté vers `adjust-pipeline`, signaler que **le fix précédent n'a pas tenu** (régression ou fix mal propagé) et en faire une entrée prioritaire côté Face B.

## Comment ça tourne (architecture)

Les transcripts font 0,5–1 Mo chacun, plusieurs par étape → **jamais tout charger dans le contexte principal**.

**0. Résoudre le contexte.** Workspace ; numéro d'étape → skills / nœud du graphe / transcripts / livrables via le mapping ci-dessous ; **découvrir** les transcripts réels (lister `<workspace>/transcripts/`, + le transcript principal de la session `-p` et son dossier `subagents/` si présents).

**1. Le leader lit la petite matière** (lui-même) : le(s) skill(s) de l'étape, la fiche (objet `STEP` : `in`/`out`/`tasks`/`success`), la liste des livrables attendus et **vérifie leur existence + non-vacuité + format**. Il en tire déjà la face « livrables » et prépare le protocole de référence à injecter.

**2. Un sous-analyste par transcript d'agent** (dispatché, contexte frais). Chacun reçoit UN transcript + le protocole de référence et **ÉCRIT** son JSON structuré dans `analyse-etape<N>/<agent>.json` : conformité (écarts + citations + ligne de skill + cause_probable `agent|spec`), comportement (flail/boucle/dérive, extraits), chronométrie (par passe/action, deltas relatifs), passes à faible rendement, preuves de livraison, 3 points saillants. Un sous-analyste **ne voit qu'un transcript**.

> **⚠️ Collecte par FICHIER, pas par message.** Le livrable de chaque sous-analyste **DOIT** être un fichier écrit (outil Write) — pas un texte renvoyé. Un agent qui « répond » en texte : son output est **invisible** au leader. Consigne explicite dans son prompt : « écris ton JSON dans `analyse-etape<N>/<agent>.json` via Write, puis confirme ». Le leader lit ensuite les fichiers.

**3. Le leader synthétise** les retours : recoupe les écarts, tranche agent vs spec, écrit le rapport en trois faces. Il ajoute la critique de la spec (face B) en corrélant les écarts récurrents aux passages faibles du skill/de la fiche qu'il a lus en 1.

## Mapping étape → skills · transcripts · livrables

Le **graphe de flux** (`pipeline/workflows/veille.json`) est la référence : c'est lui qui
a composé le brief de chaque agent, donc c'est contre lui qu'on juge l'exécution. Les skills sous
`~/.claude/skills/veille-*/`.

| N | Étape | Protocole d'étape | Transcripts | Livrables clés |
|---|---|---|---|---|
| 1 | Préparer la run | `veille-start` | le préparateur | `state/prevol/`, `subject.md`, `profile.md`, `run-config.json`, `casting.json`, `archives/`, `state/comptes-chasse.json` |
| 2 | Chasse | `veille-launch-researcher` + `veille-chasse-tableau` | chef de chasse + un par chasseur | `pistes-*-T*.md`, `state/passants-raw.jsonl`, `state/retenus.json`, `state/ecartees.md`, `state/axes-candidats.json` |
| 3 | Monter la constellation | `veille-assemble-niveau1` + `veille-agent-synthetiseur` | monteur + synthétiseurs | `findings.json`, `constellation-bundle/constellation-data.json`, `/c/<run>-eval/` déployée |
| 4 | Prévenir le lecteur | `veille-publish` | le messager | `state/notification-envoyee.json` |
| 5 | Ta notation | (barrière humaine) | — | `constellation-bundle/notation-terminee.json` |
| 6 | Feedback | `veille-feedback` | session feedback | `analyse-non-ouverts.md`, `regles-proposees.md`, `state/ecarts-tier.md`, `state/regles-axes.json`, `state/deck-*.json`, `profil-prochaine-run.json`, `ratings/*.jsonl`, `db/feedback-reports/` |
| 7 | Publier | `veille-publish` | chef de publication + publieur | `publish/`, `publish/gardes.json`, `state/memory-*.json`, `publish/carnet-sources.md`, `/c/<run>-publie/` |
| 8 | Bilan | ce skill | — | `post-mortem.md`, `metrics/tokens-run.md` |

Le socle `veille-pipeline` accompagne tous les nœuds producteurs — il n'est pas répété dans la
colonne « protocole d'étape ». Les nœuds de vérification portent `veille-verif-etape`.

**Chaque étape est suivie de sa vérification**, qui porte son rang (`<N>-verification`) et écrit
`verifications/etape-<N>/` + `verifications/etape-<N>.md`. **L'étape 5 n'en a pas** : barrière
humaine, ni transcript ni agent à auditer. Analyser une vérification, c'est analyser
`<N>-verification` — pas une étape de plus.

Si un transcript attendu est **absent**, c'est **un constat en soi** — le noter comme écart de procédure, ne pas l'inventer.

## Prompt du sous-analyste (template)

```
Tu analyses UN transcript d'agent d'une étape de pipeline de veille. Tu ne vois qu'un
transcript ; d'autres analystes couvrent les autres. Sois factuel, cite tes extraits.

PROTOCOLE DE RÉFÉRENCE (le skill + l'extrait de fiche de cette étape) :
<injecter ici le(s) skill(s) + le STEP de la fiche : tasks, success, out>

TRANSCRIPT À ANALYSER : <chemin .jsonl>

Rends un JSON via l'outil Write dans `analyse-etape<N>/<agent>.json` :
{
  "agent": "<slug/role>",
  "conformite": [ {"attendu": "...", "constate": "...", "ligne_skill": "...", "extrait_transcript": "...", "cause_probable": "agent|spec"} ],
  "comportement": { "verdict": "bien|moyen|mauvais", "signaux": ["flail/boucle/dérive/... + extrait"] },
  "chronometrie": { "duree_totale_min": n, "par_passe": [...], "passes_faible_rendement": [{"passe":"...","duree_min":n,"rendu":"...","pourquoi":"..."}] },
  "livraison": { "livrables_touches": ["..."], "preuves": ["extrait montrant l'écriture du livrable"] }
}

Contraintes : chercher en ligne d'abord face à toute incertitude ; une seule question à la fois si tu dois en poser ; TL;DR, résultat d'abord, sans préambule ; bypass permissions ; propage ces contraintes à tout sous-agent.
```

## Le rapport `analyse-etape-N.md` (dans le workspace)

### Format standard « Dashboard KPI »

Le rapport commence par un **dashboard chiffres clés** (tableau 4 colonnes, une ligne), suit une section **Dimensions avec feux tricolores** (🟢 tenu · 🟡 à surveiller · 🔴 défaut), puis les **actions numérotées dans l'ordre**. Les faces A/B/C viennent après, en détail. Le dashboard doit être lisible d'un coup d'œil sans lire les faces.

**Squelette obligatoire du rapport** :

```
# Analyse — Étape N (<nom>) — run <id>

| Métrique 1 | Métrique 2 | Métrique 3 | Drifts |
|:-:|:-:|:-:|:-:|
| ... | ... | ... | <n corrigés / m restants> |

## Temps & tokens
| Métrique              | run N-2 | run N-1 | run courant | Tendance |
|-----------------------|:-------:|:-------:|:-----------:|:--------:|
| Durée wall-clock      |    …    |    …    |     …       |    …     |
| Tokens leader (in/out)|    …    |    …    |     …       |    …     |
| Tokens sous-agents    |    …    |    …    |     …       |    …     |
| Total tokens étape    |    …    |    …    |     …       |    …     |

## Dimensions
- 🟢 <dim tenue>       <preuve 1 ligne>
- 🟡 <dim à surveiller> <preuve 1 ligne>
- 🔴 <dim en défaut>    <preuve 1 ligne>
(6-10 dimensions max)

## Actions (dans l'ordre — priorité descendante)
1. <fix concret : quoi changer, où, pourquoi>
2. …
```

**Chiffres du dashboard** — choisir les 4 qui **racontent l'étape** :
- Étape 2 (chasse) : `Findings livrés · Durée wall-clock · Drifts corrigés/restants`
- Étape 3 (constellation) : `Findings post-dédup · Durée monteur · Longueur médiane essentiel · Ratio Excellent (%)`
- Autres étapes : garder l'esprit (4 métriques, une ligne, lisibles).

**Temps & tokens** — obligatoire. Si aucun run précédent analysé pour cette étape : afficher « — » et noter « base de référence, aucun comparatif possible ». Chiffres depuis les transcripts (`usage.duration_ms`, `usage.subagent_tokens`, notifications de tâches). **Toujours en tokens bruts** — pas de conversion en dollars (les tokens sont l'unité qui compte, la conversion en $ change avec les tarifs).

**Feux tricolores** : 🟢 tenue avec preuve · 🟡 passable, à surveiller · 🔴 défaut manifeste. Une dimension par ligne, verbe court, chiffre juste après le libellé.

**Actions numérotées** : chaque action = **quoi changer + où + pourquoi**, dans l'ordre de priorité. Prioriser les fixes qui n'ont pas tenu (Face C les signale).

**Ordre du rapport** : dashboard → dimensions → actions → **puis** Face A (exécution détaillée) → Face B (critique spec) → Face C (cross-runs).

**⚠️ Vocabulaire du dashboard — MOTS ORDINAIRES, PAS DE JARGON INTERNE.** Le dashboard est destiné au lecteur, pas à un agent. Interdits : « slugs », « drift », « pattern », « pipeline », « spec », « MACH », « GATES », « meta », « delta », « ratio SUITE », noms de fichiers .md/.py. Les mêmes idées avec des mots ordinaires :
- « drift chasse à froid » → « la chasse est partie à l'aveugle »
- « pattern 1/2/2/1 » → « mêmes proportions dans tous les axes, comme si l'IA remplissait des cases »
- « répartition trop mécanique » → « classement pas au mérite »
- « fix qui n'a pas tenu » → « la correction précédente n'a pas marché »

Test : chaque dimension et chaque action doit être lisible par quelqu'un qui n'a jamais lu un skill.

### Faces détaillées (après le dashboard)

```
## Face A — Exécution
### Livrables vs critères de réussite
<par livrable : présent/vide/format ; par critère « réussi quand » : rempli ? preuve>
### Comportement de l'IA
<bien conduit ? flail/boucle/dérive, avec extraits>
### Conformité au protocole
<écarts vs sous-étapes du skill, chacun : ligne skill + extrait transcript + cause (agent|spec)>
### Temps / valeur
<chronométrie ; passes longues à faible rendement, chiffrées>

## Face B — Critique de la spec
### Le skill
<passages flous/incomplets/non mesurables qui ont induit les écarts>
### La fiche
<STEP cohérent ? success bien posés ? MACH/GATES/out justes ?>

## Face C — Comparaison cross-runs
### Post-mortems passés lus (mêmes owner + watch + étape)
<liste : `<run-id>` (date) — verdict, drifts saillants ; ou « aucun — cet run est la base de référence »>
### Évolution des métriques
<table : durée totale · tokens · nb dédups · ratios tiers — colonne par run, tendance>
### Ce qui s'améliore
<fixes précédents qui ont tenu, drifts éliminés, bonnes pratiques stabilisées>
### Ce qui régresse ou stagne
<drifts qui reviennent, fixes qui n'ont pas tenu, bonnes pratiques perdues>
### Verdict cross-runs
<1-2 lignes : ce run est-il meilleur/moins bon que le précédent, sur quels axes précis>

## Fixes proposés → adjust-pipeline
<liste ordonnée : chaque fix = quoi changer, où, pourquoi. Prioriser les fixes qui n'ont pas tenu.>
```

**Persistance** : le rapport `analyse-etape-N.md` du workspace est aussi **copié dans le silo owner** à `owners/<owner>/db/post-mortems/<watch>-etape<N>-<run-id>.md` — c'est ce que le prochain post-mortem lira pour sa Face C.

## Gotchas

- **Timing** : les timestamps internes des `.jsonl` peuvent être décalés (~2 h) → pour l'absolu, se fier aux **mtimes filesystem** (`find -mmin`, `ls -la`) ; pour le détail intra-transcript, les **deltas relatifs** entre events restent justes.
- **Ne pas confondre livrable réel et intermédiaire** : le vrai livrable de l'étape 3 = le bundle `findings.json` + constellation déployée, pas les essentiels individuels.
- **Transcript absent ≠ étape ratée** : un lot assumé vide sans vérificateur instancié est un **écart de procédure à noter**, pas un trou à combler.
- **Ne jamais corriger depuis ce skill** — diagnostic seul ; les fixes partent en `adjust-pipeline`.

## Après

Le rapport liste les fixes. Pour les appliquer (skill / fiche / config / gates), **invoquer `adjust-pipeline`** — c'est lui qui propage sans divergence. Ce skill formalise l'étape 8 du graphe de flux `veille`.
