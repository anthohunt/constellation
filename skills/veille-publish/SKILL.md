---
name: veille-publish
description: Sert DEUX étapes de la pipeline. Étape 4 — prévenir le lecteur : où trouver son adresse, l'URL de sa run, et le POST /api/notify-ready, une fois la vérification de l'étape 3 verte. Étape 7 — publier : livrables pilotés par le profil owner, archivage des gardés, constellation publiée en lecture seule, carnet de sources et mémoire du domaine. Déclencheurs — « /veille-publish <watch> », « publie la veille X », « préviens le lecteur ».
---

# Veille publish — étapes 4 et 7

Ce skill sert **deux nœuds du graphe** :

- **Étape 4 — Prévenir le lecteur** : l'inviter sur sa constellation d'évaluation (§ ci-dessous).
- **Étape 7 — Publier** : livrables, archivage, constellation publiée, carnet de sources, mémoire
  du domaine (tout le reste du skill).

---

## Étape 4 — Prévenir le lecteur

**Un lecteur prévenu trop tôt note un travail refusé.** Rien ne part tant que la vérification de
l'étape 3 n'est pas verte — c'est tout l'objet de ce nœud.

**Où trouver l'adresse du lecteur** : le profil de l'owner, `owners/<owner>/profile.md` (ou
`run-config.json`), rapatrié dans le workspace à l'étape 1. L'owner se lit dans `WORKSPACE.txt`.

**L'URL** : celle déployée en 3.4 — `$CONSTELLATION_BASE_URL/c/<run>-eval/`. **Jamais
un serveur local.**

**L'envoi** :

```bash
sudo -n /usr/local/bin/flux-inviter --workspace <workspace>
```

**Le destinataire n'est pas un argument.** Tu désignes une run ; le wrapper lit lui-même l'adresse
du lecteur dans le profil de son owner. C'est ce qui permet d'ouvrir cette commande à un agent :
elle ne peut écrire qu'au lecteur de la veille qu'il monte, jamais à une adresse qu'il aurait
choisie. Le secret admin de l'endpoint reste côté root, tu ne le vois pas.

L'URL est déduite du nom de la run (`/c/<run>-eval/`) — `--url` ne sert qu'à en servir une autre,
et elle doit rester sous `/c/`.

La commande répond `invite <adresse> -> <url> — http 200`. **Sans cette ligne, l'invitation n'est
pas partie** : écris-le dans ton livrable plutôt que de le supposer, et n'insiste pas — deux
tentatives suffisent à établir qu'un canal est cassé.

## Étape 7 — Publier


Après le tri humain de l'étape 5 et le feedback (étape 6), ce skill :
2. **Produit les livrables** selon le profil owner (`run-config.json`).
3. **Archive** les gardés dans `publish/gardes.json` + `owners/<owner>/db/findings/<watch>/` (+ miroir Notion). Lu par l'étape 1.7 de la run suivante.
4. **Referme la boucle d'apprentissage** : règles per-rôle consolidées + mémoire de domaine mise à jour.

**Deux constellations à ne pas confondre** :
- Constellation d'**ÉVALUATION** (niveau 1, tous les findings) — assemblée+déployée à l'**étape 3** sous `/c/<run>-eval/`.
- Constellation **PUBLIÉE** (GARDÉS seulement, **lecture seule** `mode:'publish'`) — déployée **ici** sous `/c/<run>-publie/`.

Un publish n'est « fait » que quand livrables + archive + boucle d'apprentissage + **mémoire de domaine (5.5)** + màj `watch-feedback-status` sont TOUS constatés. Pas d'extra optionnel.

## Why

Une fois que le lecteur a classé la constellation via `/veille-feedback`, ce skill produit les livrables polis, met à jour la KB de l'owner et referme la boucle d'apprentissage — **tout siloed sous `owners/<owner>/`** pour qu'un run client ne pollue jamais le profil de l'owner.

## Pipeline position

```
... → /veille-assemble-niveau1 → [Le lecteur classe sur la constellation] → /veille-feedback
→ /veille-publish  ⟵ YOU ARE HERE (last step)
```

## Contraintes critiques

- **Max 5 agents en parallèle** (hard limit machine).
- **Sub-agents ne peuvent pas spawn d'agents** — le leader (main conversation) spawne tout.
- **Isolation per-owner** — lire/écrire uniquement sous `owners/<owner>/`, jamais cross silos.
- **Monde clos** — le Publisher n'invente rien : sa seule matière, ce sont les essentiels gardés.
- **Gardés = tiers Excellent + Intéressant** (par défaut) déplacés/confirmés par le lecteur ; owner peut ajuster la barre.

## Pre-conditions

Avant de tourner, vérifier :
1. `/veille-feedback <watch>` a tourné pour ce run (règles NEXT écrites, deck produit).
2. Le workspace `WORKSPACE.txt` nomme l'**owner** de ce run (gelé au `/veille-start`).
3. `notation-terminee.json` du run existe.

Si owner manquant/inconnu → demander lequel avant de continuer (jamais supposer un owner en silence).

Si feedback n'a pas tourné → répondre :
> *« Publish impossible : lance d'abord `/veille-feedback <watch>` pour que je sache quoi garder et que les règles NEXT soient posées. »*

## Step 0 — Resolve owner + run config

1. Lire `WORKSPACE.txt` → owner, watch, workspace path.
2. Sync le silo owner depuis serveur : `owners/<owner>/profile.md`, `run-config.json`, `preferences/`, existing `db/`.
3. Lire `run-config.json` → quels **formats** (livrables) et **médiums** ce run doit produire. Un run peut produire plusieurs livrables (ex. newsletter perso + rapport consulting client) — un Publisher agent par livrable.

## Step 1 — Collecte des GARDÉS

1. Lire `notation-terminee.json` + `constellation-data.json` du run.
2. Garder les findings avec **tier Excellent + Intéressant** (par défaut ; ajustable via `run-config.json:threshold_tier` si l'owner veut monter la barre).
3. Assembler le set des gardés = liste `{id, titre, axe, essentiel, source, tier, tier_source, notes}`. C'est le **seul** matériau du Publisher — closed world.

Si 0 gardé → dire au lecteur, stopper (rien à publier).

**Owner CUMULATIF (`accumulation: "cumulative"` dans `run-config.json`) — collecte élargie au STACK.** Pour un profil cumulatif (les runs s'empilent), le livrable de synthèse périodique ne parle PAS que de la run courante : il puise dans le **corpus accumulé** `owners/<owner>/db/findings/<watch>/` (toutes les runs passées) UNION les gardés du run courant. Le **roundup** (cadence `share_cadence`) synthétise le stack. Les livrables « courants » (digest de la semaine) restent limités au run.

## Step 2 — Déployer la constellation PUBLIÉE, cumulative

La page publiée ne montre pas la seule run qui vient de finir : elle montre **toute la
bibliothèque** du silo, livraison par livraison en profondeur. Une fiche d'aujourd'hui ne vaut
que rapportée à ce que la veille disait il y a trois semaines — publier la run seule perd
exactement cela.

```bash
python3 $CONSTELLATION_HOME/viewer/build_publie.py \n  <workspace> <owner-dir> <watch> $CONSTELLATION_DATA/runs/<run>-publie
```

L'outil lit la bibliothèque (`owners/<owner>/db/findings/<watch>/`) et en fait une livraison par
date de run, empilées en profondeur. Le lecteur navigue d'une livraison à l'autre ; **la page ne
relie pas les findings entre eux** — le nombre de rapprochements possibles est ouvert, et rien ne
distingue celui qui apprend quelque chose de celui qui remplit.

Vérifier ensuite que la page annonce bien le compte attendu — « N signaux · M livraisons ».

## Step 3 — Livrables (Publisher agents)

### Ce que porte chaque Publisher — la règle du monde clos

**Sa SEULE matière, ce sont les gardés qu'on lui remet.** Il n'invente rien : aucun fait, aucun
chiffre, aucune affirmation qui ne soit déjà dans un essentiel vérifié à l'étape 3. Il peut
reformuler, regrouper, hiérarchiser, tirer un motif transverse — depuis ce que les essentiels
disent déjà. **Une phrase de synthèse qui aurait besoin d'un fait absent se supprime, elle ne se
fabrique pas.** Les essentiels ont passé la vérification ; ce qu'on ajoute après contourne ce
contrôle.

**Il ne choisit pas ce qui est publié** — les gardés sont déjà arrêtés. Il assemble, réangle,
synthétise pour le lecteur décrit dans le profil.

### Le registre — il se lit dans le profil

Le profil de l'owner est du texte libre. En déduire le registre le plus proche ; s'il en nomme un,
le suivre.

**newsletter** — grand public, non technique. Léger, vivant, « à retenir » en tête de chaque item,
zéro jargon non expliqué, phrases courtes. Accroche → 3 à 6 items courts → mot de la fin. Ni
pyramide stratégique ni implications business lourdes.

**consulting (Minto + SCQA)** — client industriel, décideur. **La réponse d'abord** : l'exec
summary délivre la conclusion en tête, pas en fin. Entrée SCQA — Situation (l'état connu) →
Complication (ce qui a changé) → Question → Answer. **Exactement 3 messages-clés**, chacun
soutenu par des findings comme preuves. Sections : exec summary (1 p.) → SCQA → 3 messages →
tendances transverses → ce que ça implique pour le lecteur → conclusion → annexe sources. Les
findings sont des munitions, pas des vedettes. **Réanglage** : le « pour toi » d'un essentiel,
ancré sur l'owner, devient « implications pour le client » cadré sur SA situation ; un essentiel
trop spécifique et non transposable reste en preuve factuelle, sans son angle perso.

**expert / analyste** — audience experte interne. Neutre, équilibré : état des lieux → lecture
d'expert → signaux faibles → scénarios. Pas de recommandation unique imposée ; on éclaire, le
lecteur tranche. Sourcing visible, comparatifs, nuances.

**Dans tous les registres** : la langue et le ton du profil (tutoiement/vouvoiement, FR/EN,
formalité) · anti-jargon proportionnel au lecteur · chaque affirmation pointe son finding source
(les essentiels portent leurs URLs — les réutiliser) · longueur : newsletter 2-3 p., consulting
8-10 p., expert selon la matière · branding du profil s'il en spécifie un.

### Relecture avant de rendre

1. **Chaque chiffre et chaque affirmation remonte-t-il à un essentiel ?** Sinon : retirer ou
   corriger pour coller à l'essentiel.
2. **Aucun superlatif banni** (`révolutionnaire`, `game-changer`, `disruptif`…).
3. **Le registre correspond-il au lecteur ?** Un client ne veut pas d'une newsletter bavarde ; un
   amateur ne veut pas de SCQA.
4. **Le réanglage est-il fait ?** Aucun « pour toi » résiduel adressé à l'owner dans un livrable client.

**Tout gardé inutilisable se signale** dans le compte rendu de l'agent, avec son motif — jamais
écarté en silence.

**Règles accumulées** : si `owners/<owner>/preferences/publisher-rules.md` existe, l'appliquer en
plus de la ligne de base.

### Les médiums — le chef de publication convertit, pas le Publisher

Le Publisher produit **du markdown**. La conversion suit :
- **Notion** → MCP `notion-create-pages` sous l'arbre de l'owner
- **DOCX** → `pandoc <md> -o <docx>`
- **PDF** → `pandoc <md> -t html5 --css <style> -o <html>` puis `chrome --headless --print-to-pdf`

**Même style qu'à l'évaluation.** Chaque prompt de Publisher embarque
`veille-style` — le modèle d'écriture de la veille, huit gestes, commun à
tous les owners. Celui qui ouvre la newsletter n'a pas moins droit à la clarté que celui qui note
la constellation : le niveau de langue ne change pas entre les deux moments. Le juge de style
(glose, densité de notions, contraste, bornage) tourne sur le digest, la newsletter et les résumés
**section par section** — un digest agrège une dizaine de findings, le plafond de trois notions se
juge sur ce que le lecteur tient dans un bloc, pas sur le fichier entier.

Pour chaque deliverable dans `run-config` (`digest`, `newsletter`, `mindmap`, `roundup`…) :
- Build prompt = `[cette section] + [veille-style en entier] + [owner profile.md] + [gardés] + [run metadata] + [format visé + son gabarit] + [output path] + [médiums] + [owner publisher-rules.md si existe]`
- Le Publisher **projette** les gardés selon le format (closed world : ne sort que ce qui est dans les gardés).
- Spawn 1 Publisher par livrable (`mode: bypassPermissions`, `run_in_background: true`). Max 5 en parallèle.

Chaque Publisher écrit `deliverables/<owner>-<format>.md` (source markdown) et reporte findings utilisés / skipped.

### Les livrables — projections des GARDÉS

Un seul matériau (les gardés), plusieurs sorties. **Aucune ne réécrit le fond** — elles projettent à une profondeur + un médium.

1. **La mindmap / constellation publiée** — HTML hébergé sous `/c/<run>-publie/` (lecture seule, `mode:'publish'`). C'est la constellation d'évaluation filtrée aux gardés.

2. **Digest (1 page)** — pour chaque gardé, l'essentiel (P1-P3) + l'axe + date + **source primaire en hyperlien cliquable**, classés par tier. **EXACTEMENT 1 page ET qui REMPLIT la page** : pas seulement « ≤1 page » — occuper toute la hauteur (flex colonne + `justify-content:space-between`, `html,body{height:100%}`). Trop petit + blanc en bas = à corriger. Sources = `<a href>` réel (Chrome `--print-to-pdf` conserve les liens dans le PDF).

3. **Newsletter (push email)** — **ASSEMBLÉE, jamais rédigée.** Les essentiels ont été écrits et vérifiés à l'étape 3 : la newsletter les MONTE, elle ne les réécrit pas. Ce que l'agent compose, ce sont les **liants** : le regroupement par thème, l'ordre, les transitions, une ouverture qui dit ce que la livraison a de commun. **Le texte de chaque finding est son essentiel, en entier** — jamais tronqué par « … », jamais reformulé. Langue + ton du profil owner.

4. **Rapport de feedback (LIVRABLE)** — le rapport de session produit par `/veille-feedback` (Step 8.0), format Notion standard. À inclure dans le bundle final : copier `owners/<owner>/db/feedback-reports/<run-id>.html` (+ le `.md`) dans `deliverables/`. Ce n'est PAS une projection des gardés (c'est la trace de la boucle HITL : NEXT appris + deck produit + thermomètre) — l'agent vérificateur ne lui applique pas la checklist des projections, seulement : fichier présent, stats cohérentes, zéro emoji.

5. **Roundup cumulatif** (owners `accumulation: "cumulative"`) — livrable de synthèse périodique qui puise dans le **stack accumulé** (db owner, toutes runs) et non le seul run courant. Présente le meilleur du corpus depuis le dernier partage. Closed-world sur la db archivée.

## La grille des livrables — appliquée par la vérification de l'étape

**Ce n'est pas une sous-étape de la publication** : le nœud de vérification qui suit l'étape 7 applique cette grille, avec un agent frais qui n'a produit aucun des livrables qu'il juge. Il audite CHAQUE livrable. Il ne corrige pas le fond — il **valide ou renvoie au Publisher**. Spawn 1 vérificateur par livrable (`mode: bypassPermissions`), tier différent du Publisher.

**Checklist binaire** :
- [ ] **Digest = EXACTEMENT 1 page ET remplit la page**. Vérif déterministe : `pypdf.PdfReader(path).pages` → doit valoir 1. Aussi : ne pas laisser une demi-page blanche. *Piège : un PDF ouvert dans un viewer est verrouillé → Chrome n'écrase pas et tu re-mesures l'ancien fichier ; écris sous un nom neuf ou vérifie le mtime.*
- [ ] **Sources cliquables** : chaque référence de source est un hyperlien (`<a href>` avec URL réelle), jamais du texte mort. Dans le PDF, vérifier la présence d'annotations liens.
- [ ] **Closed-world** : tout chiffre/claim du livrable existe dans un gardé (aucune invention au publishing). Échantillonner 5 claims et les retrouver. Hors-gardé = FAIL.
- [ ] **Mindmap/constellation publiée hébergée** : `$CONSTELLATION_BASE_URL/c/<run>-publie/` répond **HTTP 200**, `constellation-data.json` charge (N gardés), l'UI est en lecture seule (`mode:'publish'`), les encarts d'évaluation sont masqués.
- [ ] **Newsletter = montée, pas rédigée** : chaque finding y porte **son essentiel entier**, tel qu'il a été vérifié à l'étape 3 — un texte réécrit au montage est **FAIL**, il contourne la vérification de l'étape 3. Ce qui est jugé ici, c'est le liant : regroupement par thème, ordre, transitions, ouverture. **Zéro phrase tronquée par « … »**.
- [ ] **Style de vulgarisation** : lancer
      `python3 pipeline/style_vulgarisation.py <livrable>` — zéro défaut de densité
      (max trois notions techniques par section), phrase de contraste présente, affirmation forte
      bornée, jargon d'architecture glosé à sa première occurrence. Un livrable exact mais plat ou
      surchargé de notions repart au Publisher.
- [ ] **Format** : zéro emoji · langue conforme au profil owner · titres présents · dates affichées.
- [ ] **Le livrable est bien passé PAR ce vérificateur** — ne jamais produire un livrable « à la main » et le shipper sans l'auditer.
- [ ] **Médiums** : chaque fichier annoncé existe + non vide ; chaque page Notion créée.

Verdict par livrable : **OK** (passe) ou **FAIL + raison précise** → re-spawn le Publisher avec la correction demandée (max 2 itérations), puis re-vérifier. **Ne JAMAIS livrer un digest >1 page ni un claim hors-gardé.**

## Step 4 — Archive des gardés (siloed)

1. Écrire chaque gardé (forme finale) → `owners/<owner>/db/findings/<watch>/<date>-<slug>.json` + métadonnées. (Garder aussi la projection markdown `.md` à côté pour relecture humaine.)
2. Update `owners/<owner>/db/index.jsonl`.
3. Mirror to Notion sous l'arbre `DB findings` de l'owner.

Les non-gardés restent dans `state/passants-raw.jsonl` du workspace — réutilisables au run suivant sans re-vérification.

## Step 5 — Boucle d'apprentissage (siloed + gated)

1. **Consolider les règles per-rôle** : merger les règles NEXT du feedback dans `owners/<owner>/preferences/<role>-rules.md` (synthetiseur / publisher / selection). Lues au prochain `/veille-start`.

2. **Carnet de sources** — apprend QUELLES sources donnent des findings aimés. Pré-requis : `findings-sources.json` du run + ratings synced.
   ```bash
   scp "<BASE>/findings-sources.json" $VEILLE_SERVER:/tmp/veille-fs-<watch>.json
   ssh $VEILLE_SERVER "python3 $VEILLE_SCRIPTS/build-source-ledger.py <watch> --owner <owner> --run-dir /tmp/srcled-<watch> --run-id <run-id>"
   ```
   Note ≥7 (ou tier Excellent/Cool) → la source monte (`trusted` quand yield≥3) ; ≤4 (ou Bof/Inutile) → descend ; décroissance des sources muettes. Récap 1 ligne : « Carnet sources <watch> : +X promues, −Y rétrogradées, Z trusted. »

## Step 5.5 — Mettre à jour la MÉMOIRE DE DOMAINE (memory-updater)

**C'est le pas qui rend la veille cumulative** (ferme la boucle lue en `/veille-start`). Un agent **memory-updater** réécrit l'état distillé du domaine à partir de CE run.

**Entrées** (toutes siloed owner) :
- Mémoire actuelle : `owners/<owner>/db/memory/<watch>.json` (via `veille-memory.py show <owner> <watch>`).
- Les **gardés** de ce run + leurs **tags de continuité** (`NEW`/`MÀJ`/`SUITE`/`PROMEUT`).
- Les **verdicts de feedback** de ce run : tiers + commentaires (depuis le rapport `db/feedback-reports/<run-id>.md`).

**Ce que l'agent écrit** (réécrit le JSON entier, schéma dans `veille-memory.py` → `SCHEMA`) :
- **entities** : ajoute/actualise les acteurs récurrents (state à jour, facts, last_run) ; passe en `dormant` ceux qu'aucun run récent n'a touchés.
- **watchlist** : les commentaires qui indiquent des sujets à creuser plus tard atterrissent ici (signal `building`/`seed`). Un signal existant re-vu ce run → `times_seen++` et maturité qui monte. Un signal **matérialisé** (finding `PROMEUT:` publié) → `status: promoted`. Un signal mort/périmé → `dead`.
- **covered** : append les findings de ce run avec `{title, run, tier, comment}` (anti-répétition + lignée pour les « suite/màj » futurs).

**Exécution** :
1. Spawn 1 agent memory-updater (`mode: bypassPermissions`), modèle tier ≠ Publisher. Il lit les entrées, réécrit `owners/<owner>/db/memory/<watch>.json`, **compact** (ne gonfle pas : fusionne, élague les entités mortes au-delà de ~20).
2. Bookkeeping déterministe : `ssh … "python3 $VEILLE_SCRIPTS/veille-memory.py note-run <owner> <watch> --run <run-id> && python3 $VEILLE_SCRIPTS/veille-memory.py validate <owner> <watch> && python3 $VEILLE_SCRIPTS/veille-memory.py brief <owner> <watch>"`.
3. Le `validate` doit dire VALID ; sinon renvoyer l'agent corriger. Le brief rendu = ce que le PROCHAIN run lira.

**Récap 1 ligne** au lecteur : « Mémoire domaine <watch> : <±E> entités, watchlist <open/promoted/dead>, <C> covered ajoutés. »

## Step 6 — Cleanup

- Update `watch-feedback-status.json` (marquer ce run `published+archived`).

## Step 7 — Report to the operator

```
**Veille `<watch>` publiée + archivée — owner `<owner>`.**

**Livrables** (<N>) :
- <format> → <médiums> : <chemins / URL Notion>
...

**Archive** : <X> findings gardés → owners/<owner>/db/findings/<watch>/ + Notion mirror
**Apprentissage** : <R> règles per-rôle consolidées · carnet sources : +<X> promues, -<Y> rétrogradées
**Mémoire de domaine** : <±E> entités · watchlist <O open / P promoted / D dead> · <C> covered
**Cleanup** : status `published+archived`

Pipeline `<watch>` terminé.
```

## Hard rules

- **NEVER** cross owner silos (read/write only `owners/<owner>/`).
- **NEVER** let the Publisher invent — closed world : toute projection ne sort QUE des faits présents dans les gardés ; un claim hors-gardé = reject + re-spawn.
- **TOUTES les sorties sont des projections des mêmes gardés** — ne jamais réécrire le fond au publishing.
- **NEVER** claim un médium produit sans vérifier que le fichier existe / la page Notion est créée.
- **TOUJOURS faire passer chaque livrable par l'agent vérificateur (Step 3.5) avant de l'annoncer** — digest **exactement 1 page**, closed-world, URL 200, zéro emoji. FAIL → re-spawn Publisher (max 2 iter).
- **Vérificateur ≠ modèle du Publisher** (anti self-preference).
- **ALWAYS** injecter la section « Ce que porte chaque Publisher » + `veille-style` en entier dans chaque dispatch.
- **ALWAYS** mettre à jour la mémoire de domaine (Step 5.5) avant le cleanup — un run publié sans màj mémoire = accumulation perdue. `validate` doit dire VALID.

## What this skill does NOT do

- Ne classe pas les findings (c'est `/veille-feedback` sur la constellation d'éval).
- Ne re-source pas et ne re-écrit pas les niveau 1 (étapes 1-3).
- Ne touche pas les silos d'autres owners.
