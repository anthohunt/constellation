---
name: veille-start
description: Prépare une run de veille quand le lecteur invoque `/veille-start <veille>` ou `/veille-start --owner=<x>`. Résout D'ABORD l'owner puis son sujet, vérifie la concurrence, crée un workspace neuf, synchronise sujet/état/archives/préférences depuis le serveur, applique le profil décidé au feedback précédent et déduit le casting des axes (1 par axe + 2 transversaux + 1 éclaireur). Le profil est CHARGÉ, jamais créé : un profil incomplet arrête la run. Aucun dialogue, aucun agent lancé — il prépare le contexte et écrit les traces de pré-vol sous `state/prevol/`. Étape suivante — la chasse. Déclencheurs — "/veille-start ai-watch", "lance une run sur health-watch", "déclenche immersive-watch maintenant".
---

# Veille start — context setup

## Why

The watch pipeline runs locally as Claude Code agents. Before any agent can start, the leader (the main conversation) needs a workspace with subject file, state, archives, and freshly-built preferences synced from serveur.

This skill does **only setup**. It does not launch any agent. After setup, the leader calls `/veille-launch-researcher` to begin sourcing.

## CRITICAL architecture rules

- **YOU (main conversation) are the leader.** Sub-agents cannot spawn other agents.
- **Plafond de simultanéité : ~10 agents actifs pendant la phase de chasse** (au-delà : mode décalé par vagues de ~5). Partout ailleurs, la limite reste 5.
- **Each pipeline phase = separate skill**: split-by-phase architecture pour robustesse — si une étape est interrompue, la suivante détecte l'état du workspace et reprend au bon endroit.

## When to invoke

- User types `/veille-start <name>` or `/veille-start <name> --owner=<owner>`
- User types `/veille-start` **alone** → interactive menu (list veilles + owners, let le lecteur pick)
- User says equivalent in French/English: "lance une run sur X", "déclenche X maintenant", "re-run X"

## Owner model

Every run belongs to an **owner** = a reader profile. The owner determines downstream: which preferences/rules condition the agents, and the deliverable format/médiums at `/veille-publish`. Owners are isolated silos `owners/<owner>/` on serveur (`profile.md`, `run-config.json`, `preferences/`, `db/`). A client run never touches another owner's silo. See [[project-veille-publish-architecture]].

## On part du lecteur, pas d'une liste de sujets

On choisit un **owner**, et son sujet vient avec — depuis `run-config.json` (`subject_default`) ou depuis les sujets déjà couverts par son silo.

Le cas « un même sujet, plusieurs lecteurs » reste possible (un sujet, deux lentilles, deux livrables). C'est **l'exception explicite**, plus le point de départ.

## How to invoke

### Step 1 — Resolve owner first, then subject

**Un seul silo de profils** :
```bash
ssh $VEILLE_SERVER "ls -d $VEILLE_OWNERS_DIR/*/ 2>/dev/null | xargs -n1 basename"
```

- **Silo** : `$VEILLE_OWNERS_DIR/<owner>/`. Le wizard web (`$CONSTELLATION_BASE_URL`) y écrit directement, à chaque enregistrement de profil : `profile.json`, `run-config.json`, `profile.md`, `subject.md` et `preferences/regles-axes.json`. Rien à importer, rien à recopier.
- Le slug d'un owner créé au wizard dérive de son **e-mail** (`jane.doe@example.org` → `jane-doe-example-org`).
- Le silo ne porte PAS le casting : il se déduit des axes au pré-vol.

**Ordre de résolution** :

1. **Owner.** `--owner=<x>` donné et existant → l'utiliser. Sinon → afficher la liste + `+ nouveau profil` et demander. **Ne jamais supposer un owner en silence** si d'autres owners existent.
2. **Sujet, dérivé de l'owner.** Lire `subject_default` dans son `run-config.json`, et lister les sujets déjà couverts (`ls ${ODIR}/db/findings/`).
   - Un seul candidat → le prendre, l'annoncer, ne pas demander.
   - Plusieurs → les proposer, **ceux de cet owner uniquement**.
   - Aucun → demander lequel surveiller, et proposer les sujets partagés (`ls $VEILLE_SUBJECTS_DIR/*.md`) comme choix possible, pas comme menu imposé.
3. **Sujet passé en argument** (`/veille-start ai-watch`) → le respecter tel quel. Vérifier seulement qu'il existe.

**`+ nouveau profil`** → **déléguer à `/veille-profile <new>`** (skill canonique). Ne PAS refaire le dialogue ici. Une fois créé, revenir à `/veille-start`.

**Profil créé au wizard** : il est déjà dans le silo, axes et fraîcheur par axe compris — ne pas rappeler `/veille-axes`. Seul le casting reste à dériver (Step 4bis).

### Step 2 — Garde de concurrence

La sonde vit dans `veille-preflight.sh` (Step 4), section `===CONCURRENCE_TMUX===` : elle lit
l'état des runs flux (`flux/state/<wf>/<workspace>/`), ne garde que les sessions tmux **encore
vivantes**, et ne compare que le préfixe `<veille>-<owner>-`.

- **Deux veilles différentes en parallèle est autorisé**, et deux owners aussi.
- **Le doublon, c'est la même veille pour le même owner** → ne pas démarrer : reprendre la run
  existante, ou l'arrêter par PID avant de relancer.

### Step 3 — Create local workspace

**JAMAIS dans `%TEMP%`** — Windows peut nettoyer le dossier sans prévenir.

```powershell
$SUBJECT = "<from-arg>"
$OWNER = "<from-arg>"
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd-HHmmss"
$LOCAL_BASE = "$env:USERPROFILE\veille-runs\$SUBJECT-$OWNER-$TIMESTAMP"
New-Item -ItemType Directory -Force -Path "$LOCAL_BASE\state", "$LOCAL_BASE\archives", "$LOCAL_BASE\verifications", "$LOCAL_BASE\transcripts", "$LOCAL_BASE\rapports", "$LOCAL_BASE\cartes", "$LOCAL_BASE\fils"
```

**Miroir serveur obligatoire dès la fin de la phase de chasse** — deux copies valent mieux qu'une :

```bash
R="$FLUX_RUNS_HOME/veille-runs/${SUBJECT}-${OWNER}-${TIMESTAMP}"
ssh $VEILLE_SERVER "mkdir -p $R/transcripts $R/verifications $R/state"
# puis scp des candidats, WORKSPACE.txt, contexte, index de transcripts
```

**Ne jamais mirrorer les JSONL bruts** (500-700 Ko chacun) : les index suffisent au serveur.

### Step 4 — Sync from serveur (single bash call)

**D'ABORD un seul appel de diagnostic — `veille-preflight.sh`** (une connexion, ~5 s). Ne PAS ouvrir des ssh réactifs un par un (chaque ssh repaie sa poignée de main — 8 connexions = ~2 min 45 mesurées).

```bash
ssh $VEILLE_SERVER "bash $CONSTELLATION_HOME/skills/veille-start/veille-preflight.sh <owner> <subject-slug>" > "$BASE/state/preflight.out"
```

Sortie balisée `===SECTION===` : `SILO_DIR` · `SILO_RUNCONFIG` · `WIZARD_RUNCONFIG` · `SILO_CASTING` · `SELECTION_RULES` · `MEMORY_BRIEF` · `WATCH_PREFERENCES` · `CONCURRENCE_TMUX` · `ARCHIVES_WIZARD`. Lis-la en entier AVANT tout autre ssh. Les `scp` ci-dessous rapatrient les fichiers, pas pour diagnostiquer.

Subject + dedup archives sont **partagés** ; **preferences/rules sont lues depuis le silo OWNER** (`owners/<owner>/preferences/`), pas depuis un chemin global.

```bash
BASE="/tmp/veille-run/<subject>-<owner>-<timestamp>"
OWNER="<owner>"
ODIR="$VEILLE_OWNERS_DIR/${OWNER}"

# Subject (shared across owners)
scp $VEILLE_SERVER:$VEILLE_SUBJECTS_DIR/${SUBJECT}.md "$BASE/subject.md"

# Owner profile + run-config (drives publish + agent conditioning)
scp $VEILLE_SERVER:${ODIR}/profile.md "$BASE/profile.md"
scp $VEILLE_SERVER:${ODIR}/run-config.json "$BASE/run-config.json"

# Règles PAR AXE — ce que chaque chasseur doit viser. Sans elles, la vérification de la chasse refuse l'étape.
scp $VEILLE_SERVER:${ODIR}/preferences/regles-axes.json "$BASE/state/regles-axes.json"

# Owner per-role rules
ssh $VEILLE_SERVER "ls ${ODIR}/preferences/*-rules.md ${ODIR}/preferences/model-status.json 2>/dev/null" \
  | while read f; do scp "$VEILLE_SERVER:$f" "$BASE/state/"; done

# Directives DURES apprises des feedbacks (best-effort, jamais de remplissage)
scp $VEILLE_SERVER:${ODIR}/preferences/directives.md "$BASE/state/directives.md" 2>/dev/null || echo "(pas de directives dures pour cet owner — OK)"

# Owner-specific archives of this watch (for dedup)
ssh $VEILLE_SERVER "ls -t ${ODIR}/db/findings/${SUBJECT}/*.md 2>/dev/null | head -20" \
  | while read f; do scp "$VEILLE_SERVER:$f" "$BASE/archives/"; done

# Build fresh preferences pad
ssh $VEILLE_SERVER "python3 $VEILLE_SCRIPTS/build-watch-preferences.py ${SUBJECT} --owner ${OWNER}"
scp $VEILLE_SERVER:${ODIR}/preferences/${SUBJECT}-preferences.md "$BASE/state/"

# Carnet de sources (owner-aware, best-effort)
SRC="${ODIR}/sources/${SUBJECT}-sources.json"
scp "$VEILLE_SERVER:$SRC" "$BASE/state/${SUBJECT}-sources.json" 2>/dev/null || echo "(pas encore de carnet de sources — 1er run)"

# DECK de préférence + MÉMOIRE DE DOMAINE + FINDINGS retenus — obligatoires pour le launcher-researcher
scp "$VEILLE_SERVER:${ODIR}/preferences/deck-${SUBJECT}.json" "$BASE/state/" 2>/dev/null || echo "(pas de deck — 1er run)"
ssh $VEILLE_SERVER "python3 $VEILLE_SCRIPTS/veille-memory.py scaffold ${OWNER} ${SUBJECT} >/dev/null 2>&1; python3 $VEILLE_SCRIPTS/veille-memory.py brief ${OWNER} ${SUBJECT}" > "$BASE/state/domain-brief.md" 2>/dev/null || echo "(pas de mémoire de domaine — 1er run)"
scp "$VEILLE_SERVER:${ODIR}/db/memory/${SUBJECT}.json" "$BASE/state/memory-${SUBJECT}.json" 2>/dev/null || true
ssh $VEILLE_SERVER "ls ${ODIR}/db/findings/${SUBJECT}/*-retenus.json 2>/dev/null" \
  | while read f; do scp "$VEILLE_SERVER:$f" "$BASE/state/"; done
```

**Le `state/domain-brief.md`** est l'état accumulé du domaine : lu par `/veille-launch-researcher` (chasseurs suivent/creusent le connu + promotions de watchlist) et par les vérificateurs (score la vraie NOUVEAUTÉ contre le connu). Réécrit en fin de cycle par le **memory-updater** (`/veille-publish`). C'est ce qui rend chaque run **cumulatif**.

**Le deck + la mémoire + les findings retenus sont OBLIGATOIRES** pour l'étape de chasse : `veille-launch-researcher` doit les injecter dans le prompt de chaque chasseur (voir sa section « Injection obligatoire »).

### Step 4bis — Appliquer le profil décidé au feedback précédent

**Le profil est posé en amont par le wizard : on le CHARGE, on ne le crée pas.** Ce skill ne
propose aucun axe, n'arbitre aucun casting et ne fait rien valider — le graphe ne prévoit ni
dialogue ni décision à l'étape 1.

**Appliquer les réglages « prochaine run ».** Si `owners/<owner>/preferences/profil-prochaine-run.json`
existe (écrit à l'étape 6 : `{fraicheur, decisions, ajouts}`), l'appliquer au `run-config.json` /
`subject.md` : `fraicheur` → fenêtre par défaut ; `decisions` (garder / évoluer-vers / retirer, par
axe) + `ajouts` → la liste d'axes. **Ces décisions ont déjà été prises et tracées à l'étape 6** :
on les applique, on ne les rejoue pas. Le fichier est absent → le profil courant tient tel quel.

**Le casting se DÉDUIT des axes, rien à arbitrer** : un chasseur par axe, plus 2 transversaux fixes
(`Signal faible`, `Contre-preuve`) et 1 **éclaireur** (axe `Découverte`). Tous portent une
fraîcheur, défaut `mois`. Écrire `casting.json`.

**LES SOURCES TENUES D'UN AXE PARTENT AVEC SON CHASSEUR.** Un axe peut porter un champ `sources`
— un site, une chaîne, un compte, un journal, une personne, une par ligne. Recopie-le **tel quel**
dans la ligne du chasseur de cet axe (`casting.json`, clé `sources`), et recopie `sources.free` du
profil dans la ligne de **chacun** : ce qui ne sert aucun axe en particulier sert tout le monde.
*Sans ce report, la personne a nommé les sources auxquelles elle tient et aucun chasseur ne les
voit — elles dorment dans le silo pendant que la chasse part au hasard du moteur.* Un axe sans
sources garde le champ vide : c'est un cas normal, pas un manque.

**Ce qui manque n'est pas à inventer** :

```bash
grep -q "À GÉNÉRER" "$BASE/subject.md" && echo "AXES_MANQUANTS"
ssh $VEILLE_SERVER "test -f ${ODIR}/casting.json && echo CASTING_OK || echo CASTING_MANQUANT"
```

- **Axes absents** → **STOP**. Le profil est incomplet : le dire au lecteur et s'arrêter. Les axes
  se posent hors run (wizard, ou `veille-axes`), jamais au démarrage d'une chasse.
- **Owner introuvable ou profil absent** → **STOP**, même raison.

**Check du thermomètre dejavu.** Si `owners/<owner>/preferences/veille-health-<watch>.json` existe,
lire la moyenne des 3 derniers ratios `dejavu_count / total_notes` : **< 10 %** rien à signaler ·
**10-20 %** une note dans le rapport de pré-vol · **> 20 %** le signaler dans
`state/prevol/1.4-lecteur.md` — la chasse dérive vers le mainstream. **Jamais de correctif
automatique**, et pas de question posée : c'est un constat écrit, que le lecteur lit au rapport de run.

### Step 4ter — Écrire les traces de pré-vol

Chaque contrôle de l'étape 1 laisse son fichier sous `state/prevol/` — c'est ce qui rend le pré-vol
vérifiable après coup :

| Fichier | Ce qu'il contient |
|---|---|
| `state/prevol/1.1-recherche.md` | la requête de test, un extrait des résultats, le verdict |
| `state/prevol/1.2-memoire.md` | la mémoire libre relevée, le mode de lancement retenu |
| `state/prevol/1.3-concurrence.md` | les runs en vie, leur veille et leur owner, le verdict |
| `state/prevol/1.4-lecteur.md` | l'owner résolu, le chemin de son silo, les axes de son profil |

Un contrôle sans son fichier est une faille que la vérification de l'étape relèvera.

### Step 5 — Persist workspace path

Écrire `<base>/WORKSPACE.txt` :
- Subject name
- **Owner** (CRITICAL — lu par `veille-feedback` et `veille-publish` pour savoir de quel silo la run relève)
- Timestamp
- Absolute Windows base path
- Date de création

Ce fichier est lu par les nœuds aval (`veille-launch-researcher`, `veille-feedback`, `veille-publish`) et sert de repère de fraîcheur. L'owner est **gelé** ici pour toute la run.

### Step 5 bis — Poser le moteur de la run

Écrire `<base>/state/moteur` avec la seule ligne `perso`.

C'est le compte qui fera tourner tous les nœuds de la run. Son dossier de
configuration (`moteurs.json` → `perso` = `$CLAUDE_CONFIG_DIR`) ne charge ni
les plugins, ni la liste des skills personnelles, ni le CLAUDE.md du serveur : le
**contexte de départ** d'un agent y pèse 36,7k jetons au lieu de 50,0k.
Chaque agent traîne ce socle à CHAQUE tour de parole : un chasseur qui prend la
parole 95 fois paie l'écart 95 fois. Sur la seule étape de chasse d'une run
mesurée (7 chasseurs, 676 tours), l'écart valait ~11 M de jetons sur 62,7 M.

Sans ce fichier, la run retombe sur le moteur `defaut` de `moteurs.json` et perd
ce gain sans le dire.

### Step 6 — Report to user

```
Workspace prêt : <local-base-path>
- Veille: <subject> · Owner: <owner>
- Subject: <subject>.md (<size> chars)
- Profil owner: <registre> · médiums <…>
- State files: <N> synced · Archives: <N> for dedup
- Preferences: <N> ratings built into preferences pad · algo <actif/sommeil>
- Deck: <présent | absent 1er run>  · Mémoire de domaine: <N entités · K watchlist open>  · Findings retenus: <N runs passés>

Prochaine étape : /veille-launch-researcher
```

## What this skill does NOT do

- Ne lance AUCUN agent (c'est `veille-launch-researcher`)
- Ne vérifie AUCUN candidat — la vérification est un nœud séparé du graphe
- N'assemble AUCUN finding, ne lance aucun auditeur, n'écrit aucun rapport (phases aval)

## Hard rules

- **NEVER** réutiliser un ancien workspace — toujours fresh timestamp dir
- **NEVER** modifier les prompts veille / subject file dans ce skill, sauf pour appliquer `profil-prochaine-run.json` (utiliser `veille-modify` hors run)
- **NEVER** exécuter la pipeline en SSH sur serveur — elle tourne en local
- Toujours inclure le timestamp dans le nom du dir pour traçabilité
- **Deck + mémoire du domaine + carnet de sources + archives DOIVENT être rapatriés** avant la chasse — sans quoi le run part « à froid »
- **Aucune question au lecteur à l'étape 1** : ce qui manque au profil arrête la run, il ne se complète pas ici
- **`CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION=1000` dans `~/.claude/settings.json`** — le défaut de 200 est calibré pour du dev, pas pour dix agents qui constatent une circulation en ligne
- **Le pré-vol est bloquant** : sans moteur de recherche, la chasse part à l'aveugle

## Reprise / multi-run (pause puis retour)

Le pipeline est **résumable par conception** : chaque phase écrit ses artefacts dans le workspace et la phase suivante **détecte ce qui est déjà fait** et reprend là où ça s'est arrêté. On peut donc **lancer plusieurs runs (owners différents) séquentiellement, faire une pause, et revenir**.

**Workspace owner-tagué** : `<subject>-<owner>-<timestamp>` → les runs de plusieurs owners sur le même subject **ne se mélangent pas**.

**Pour reprendre** : la console du moteur flux liste chaque run en cours (owner · subject · âge · étape atteinte · **prochaine étape**). Puis appeler le skill de phase indiqué **avec le bon owner** — il saute automatiquement le travail déjà fait. Pour une pause longue, mirrorer le workspace sur le serveur `owners/<owner>/runs/` (durable).
