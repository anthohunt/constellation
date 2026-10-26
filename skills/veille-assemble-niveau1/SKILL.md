---
name: veille-assemble-niveau1
description: Étape 3 de la pipeline. Le monteur reprend le vivier dédupliqué de l'étape 2, GROUPE les findings apparentés en HISTOIRES, fait écrire par des synthétiseurs l'ESSENTIEL NIVEAU 1 de chaque histoire depuis LES FICHES de ses findings (jamais depuis les pages), au niveau de `veille-style/reference-redaction.md` (aucun gabarit de paragraphes, aucun calibre : une notion par paragraphe, la longueur suit le sujet), reporte la tier posée à l'étape 2, assemble le bundle niveau 1 (un objet par histoire : titre + essentiel + axe + sources[] + tier, sans rapport de fond), construit et déploie la constellation d'évaluation RADIALE. Le montage ne retire ni n'ajoute aucun finding : il monte exactement le vivier de state/retenus.json, regroupé, et la tier est un point de départ que l'humain corrige à l'étape 5. PAS un skill invocable par l'utilisateur — le leader lit ce contenu et l'injecte dans le prompt du monteur.
---

# Veille — Assemblage niveau 1 (étape 3)

## Pourquoi cette étape existe

La **constellation est la surface de tri, et c'est le lecteur (étape 5) qui filtre à la main.** Cette étape assemble **TOUS** les passants vérifiés en une constellation **niveau 1**, en les regroupant en **histoires** — un objet de lecture peut porter plusieurs findings.

**Le niveau 1 = titre + ESSENTIEL + axe + source. Pas de rapport de fond.**

Tu es **Le monteur**. Tu reprends le vivier de l'étape 2, tu **groupes** les findings apparentés, tu fais **écrire l'essentiel** de chaque groupe (via des synthétiseurs que tu dispatches), tu **reportes** la tier posée à l'étape 2, tu assembles, tu déploies.

**Le volume ne se coupe pas, il se raconte.** Une file de soixante-dix faits isolés se survole ; les mêmes faits noués en une vingtaine d'histoires se lisent. C'est la raison d'être du groupage — pas une économie de tokens, une condition de lecture.

Le tri humain (étape 5) est un **classement en 6 tiers** que l'utilisateur **corrige** à partir des tiers posées à l'étape 2 (barème : `veille-launch-researcher` § La tier). **Rien n'est jeté**, pas de publication séparée : la constellation classée EST le livrable. Constellation **radiale** : axe = secteur, tier = distance au centre (Excellent au cœur → Inutile en périphérie).

## L'ESSENTIEL NIVEAU 1 — le point clé de cette étape

L'essentiel est **écrit à cette étape, directement depuis LES FICHES du chasseur** — jamais depuis les pages, que l'étape 2 a déjà attestées — (+ le dossier de capture). Ce n'est pas un pass-through de la capture brute — c'est une vraie rédaction, structurée.

**Le modèle d'écriture** : `veille-style/reference-redaction.md`, que chaque synthétiseur lit en
entier avant d'écrire. C'est un texte de vulgarisation réel sur un sujet technique — le niveau à
atteindre, pas une consigne à interpréter.

**Aucun gabarit de paragraphes, aucun calibre.** Le découpage suit les notions posées : **une idée
par phrase, une notion par paragraphe**. La longueur suit ce que le sujet demande pour être
compris — deux cents mots pour un signal simple, quatre cents pour un signal qui doit installer
une notion. On déplie, on ne compresse pas.

Ce que le texte doit avoir fait quand le lecteur le referme : il sait ce qui s'est passé, il a
compris le mécanisme, il voit quelle habitude ce fait rend intenable, il connaît la réserve, et il
sait ce qui change pour lui. L'ordre appartient au rédacteur ; c'est le résultat qui se juge — à la
vérification de l'étape, par comparaison à la référence.

**Orthographe et mise en évidence** : le français porte **tous ses accents**, capitales comprises. Dans l'essentiel, `__gras__` marque un fait ou un chiffre décisif (deux ou trois par essentiel), `*italique*` un nom propre ou un terme glosé. Cf. `veille-agent-synthetiseur` qui définit la règle.

**Voix : la DÉPÊCHE.** Registre informationnel-neutre : le fait ou le chiffre en tête, sujet-verbe-complément, une affirmation par phrase, zéro éditorialisation. On **rapporte**, on ne met pas en scène.

**Banlist « ton IA » (fautes dures)** : l'antithèse à négation « X, pas Y » ; le tiret correctif qui greffe une glose ; le tricolon décoratif ; l'insistance sur l'évident. Test : si une phrase pose une distinction puis la souligne, la réécrire en énoncé plat.

**VULGARISATION OBLIGATOIRE.** L'essentiel doit être compris par un lecteur intelligent mais NON spécialiste :
- chaque terme technique expliqué en clair dès sa 1ʳᵉ apparition (« un *jailbreak* = une astuce qui contourne les garde-fous d'une IA »)
- L'ouverture mène par le sens, pas par la mesure
- les chiffres rendus parlants (« perd 33 % de ses capacités », pas « 33,1 % de dégradation »)
- so-what saisissable par un profane
- **ton STANDARDISÉ** (le niveau technique du sujet ne rend pas l'essentiel plus dense — même accessibilité pour tous)
- encodage propre (pas de caractères exotiques ↔/−)

Détail + exemple de référence dans `veille-agent-synthetiseur` (« VULGARISATION OBLIGATOIRE »).

**Closed-world** : tout ce qu'affirme l'essentiel est ancré dans les sources de l'histoire. Le synthétiseur peut **ouvrir chaque source** (WebFetch) pour écrire le mécanisme et les réserves correctement, mais n'invente rien et ne sort pas du périmètre de ses findings — **le lien entre eux compris** : ce qui rapproche deux faits doit se lire dans les sources, jamais se déduire.

## ⚠️ En entrée — ne monter qu'un vivier déjà vérifié

**Le montage ne démarre pas tant que la vérification de l'étape 2 n'est pas verte.** Le runtime
le tient : `verifications/etape-2.md` est un livrable amont, et sans lui le nœud est bloqué à
l'entrée. Tu n'as donc pas à re-juger les pistes — mais tu dois savoir ce que la vérification a
conclu, parce que c'est ce qui décide de ce qui entre dans le bundle.

**Lis `verifications/etape-2.md` avant de commencer** :
- verdict **conforme** → tu montes le vivier tel quel.
- **failles bloquantes listées** → tu ne montes pas : l'étape 2 doit repasser. Monter sur un
  vivier refusé fabrique une constellation qu'il faudra démonter.

**Tu ne coupes ni n'ajoutes rien.** Le bundle porte exactement les findings de
`state/retenus.json` — la déduplication a eu lieu en fin d'étape 2, sur le vivier entier. Un
finding de plus ou de moins que cette liste est un écart : tu le signales, tu ne le rafistoles
pas. **Grouper n'est ni couper ni ajouter** : un finding qui entre dans une histoire y reste
entier, avec sa source et sa date. La tier RANGE les retenus, elle ne les coupe pas : c'est
le lecteur qui tranche à l'étape 5.

---

## Entrée / Sortie

**Entrée** :
- `state/retenus.json` — le vivier dédupliqué ENTIER. Par entrée : titre, capture d'essentiel brute, axe, source primaire + sources indépendantes, dossier de circulation, notes héritées, `date_fait`, tags de continuité, chasseur(s), `tier` + `tier_justification`, `fusion_de`.
- `state/passants-raw.jsonl` — le vivier avant dédup, et `state/ecartees.md` les doublons fondus. Tu les consultes seulement si une entrée manque à l'appel ; tu n'en montes rien de ton propre chef.
- `verifications/etape-2.md` — le verdict de la vérification amont.
- `subject.md` — thème + axes, pour l'ossature de la constellation.

**Sortie** :
1. **`state/groupes.json`** — les histoires candidates : par groupe, son identifiant, son axe, la liste des findings et ce qui les rapproche en une phrase.
2. **`findings.json`** — bundle niveau 1 : **un objet par histoire**, chacun `{id, titre, axe, sources, essentiel, date_fait, trouve_par, tags, tier, tier_source, tier_justification, notes}`. **Aucun `rapport`.**
3. **`constellation-data.json`** — via `deployer-eval.sh` (qui appelle le builder, déploie et contrôle).
4. **La constellation d'évaluation déployée** sous `/c/<run>-eval/`. Déployer ne prévient pas : le lecteur est invité par un nœud à part, après le feu vert de la vérification.

## Le protocole (4 tâches, dans l'ordre)

### 1. Reprendre le vivier

Lis **tout** `state/retenus.json` et pose chaque entrée dans `findings.json`, avec sa `tier`, sa `tier_justification` et son `fusion_de` recopiés à l'identique. C'est une recopie, pas un jugement : la fusion des doublons a eu lieu en fin d'étape 2, quand le vivier entier était sous les yeux d'un seul agent.

Compte ce que tu as posé et compare-le à la liste. Un écart se signale dans ton rapport — il ne se comble pas en repêchant depuis `passants-raw.jsonl`.

### 2. Grouper les findings apparentés en histoires

Un groupe rassemble **2 à 5 findings d'un même axe qui racontent la même chose** : trois travaux
sur la même architecture, deux mesures d'un même phénomène, une annonce et ce qu'elle a produit
trois semaines plus tard. Un finding qui ne se rattache à rien fait **un groupe d'un seul** — c'est
un cas normal, pas un échec.

**La parenté se repère au vocabulaire rare partagé** : des termes que deux fiches ont en commun et
qu'on ne trouve nulle part ailleurs dans la run. C'est un indice mécanique et bon marché, pas un
verdict — il propose les rapprochements, il ne les tranche pas.

**Chaque groupe porte une HYPOTHÈSE** : une phrase déclarative disant ce que ces faits racontent
ensemble — pas « ces trois travaux parlent de mémoire longue », mais « trois équipes butent sur la
même limite et l'attribuent chacune à une cause différente ». C'est elle qui part dans le dispatch,
et c'est elle que le synthétiseur va tester.

**Ton groupe est une PROPOSITION.** C'est le synthétiseur, sources ouvertes, qui dira si l'histoire
tient. Tu ne cherches donc pas la certitude avant de dispatcher : tu cherches le voisinage, et tu
écris l'hypothèse la plus intéressante qu'il rende possible — une hypothèse molle ne se teste pas.

**Ne jamais grouper à travers deux axes.** Un rapprochement qui traverse les axes brouille la
constellation, où l'axe est un secteur : le finding perdrait son secteur d'origine.

**Ne jamais forcer un groupe pour faire du chiffre.** Un groupe sans parenté produit une histoire
fausse, et une histoire fausse coûte plus cher au lecteur que dix objets isolés.

**Livrable** : `state/groupes.json` — par groupe, son identifiant (`G01`, `G02`…), son axe, la
liste des `id` de findings, **l'hypothèse** en une phrase, et — une fois l'écriture faite — ce que
le synthétiseur en a répondu : `verdict` (`tenue` · `corrigée` · `abandonnée`), l'hypothèse finale,
la **cause commune** qu'il a nommée, et les findings qu'il a `ecartes` avec leur motif.

C'est ce report qui rend la méthode vérifiable : sans lui, personne ne peut dire si le lien a été
testé ou simplement affirmé.

**Un groupe = un agent = un transcript.** C'est ce qui rend la vérification des traces tenable, et
juger par groupe coûte, à l'essentiel, environ quatre fois moins que juger un par un.

**Garde les groupes stables d'une passe à l'autre** : un finding reste dans son groupe, sinon les
verdicts acquis ne se rattachent plus à rien.

### 3. Faire écrire l'essentiel de chaque histoire (dispatch)

**Dispatche un synthétiseur par GROUPE** (skill `veille-agent-synthetiseur`) — jamais un agent
par finding. Chacun écrit **UN essentiel** qui relie les faits de son groupe, depuis les **sources
de chaque finding** + leurs captures, et **UNIQUEMENT l'essentiel**.

**Il est juge de ce qui fait histoire.** Ton groupe est une proposition ; lui a les sources
ouvertes. Trois issues, toutes légitimes :

- **l'histoire tient** → un essentiel, les findings du groupe en `sources` ;
- **un finding n'a rien à faire là** → il l'écarte du groupe, le dit dans son rendu, et tu le
  remontes en histoire à part ;
- **le groupe raconte deux choses** → il rend deux essentiels, et tu poses deux objets. Tu ne les
  recolles pas ;
- **aucune cause commune ne s'écrit** → il n'y a pas d'histoire. Tu poses chaque finding en objet
  seul, sans insister : un groupe forcé produit un texte faux, et le faux coûte plus cher au
  lecteur que dix objets isolés.

**Il ne dispose pas librement de la méthode** : hypothèse écrite avant l'ouverture des sources,
findings confrontés un à un, cause commune nommée avant l'écriture (`veille-agent-synthetiseur`
§ Composer une histoire). Tu n'as pas à la contrôler — la vérification de l'étape la lit dans son
transcript — mais tu reportes ce qu'il en dit dans `state/groupes.json`.

**Ce qu'il ne doit jamais faire : forcer un lien que les sources ne portent pas.** Deux faits mis
côte à côte ne font pas une suite, et une causalité inventée entre deux findings est une
affirmation fausse comme une autre — la vérification la refusera, à raison.

**Le texte de référence part dans CHAQUE dispatch**, en entier : `veille-style/reference-redaction.md`. Un synthétiseur qui ne l'a pas vu écrit au niveau qu'il croit attendu, et ce niveau est toujours plus bas.

*(Si budget/volume l'impose, tu peux écrire toi-même les essentiels les plus simples — mais le modèle d'écriture vaut pour toi comme pour eux.)*

**Coordination des gloses d'entités.** Une entité (organisme/produit/personne) doit être **présentée à sa 1ʳᵉ apparition dans le run** (glose de qui-c'est), **puis plus jamais re-glosée**. Comme les synthétiseurs sont amnésiques entre eux, **c'est TOI (le monteur) qui coordonnes** : tiens une liste des **entités déjà introduites** au fil des dispatches, et passe à chaque synthétiseur, dans son prompt, la liste des entités de SON groupe qui sont **déjà connues** (à ne pas re-gloser) vs **neuves** (à gloser). Ordonne les dispatches de façon stable (ex. par id) pour que « la première » soit déterministe. En cas de doute, gloser (mieux vaut une glose de trop).

### La tier d'une histoire

Chaque finding entre dans cette étape avec sa `tier`, posée à l'étape 2 par les juges qui avaient
les sources ouvertes et le contexte des préférences du lecteur. **Tu ne la reposes pas et tu ne la
discutes pas** : tu la reportes dans le bundle.

**Une histoire prend la PLUS HAUTE tier de ses findings**, avec la `tier_justification` qui va
avec. C'est mécanique, sans jugement : une histoire vaut au moins son meilleur signal, et les
findings d'appui l'enrichissent sans la dégrader. Les tiers des autres findings restent lisibles
dans `sources`.

Cette étape RÉDIGE et MONTE. Elle ne juge pas.

### Fusionner, grouper, séparer — trois gestes distincts

- **Fusionner** (étape 2, pas ici) : deux fiches portent le **même fait**. Une seule survit, l'autre
  est citée dans son `fusion_de`. Ce geste a eu lieu avant que tu reçoives le vivier.
- **Grouper** (ici) : deux findings portent des **faits différents qui racontent la même chose**.
  Les deux vivent, dans le même objet, et l'essentiel les relie. Chacun garde sa source et sa date
  dans `sources`.
- **Séparer** : rien ne les rapproche. Chacun fait un objet.

Le doute se tranche toujours vers **séparer** : une redite se voit à la lecture, une histoire fondue
par erreur ne se retrouve pas.

**⚠️ La tier ne se repose pas ici.** Elle arrive de l'étape 2 avec sa `tier_justification` : tu la **recopies** dans le bundle, à l'identique. Un classement modifié entre la chasse et le montage est une faille — celui qui écrit le texte ne décide pas de sa place. Une tier qui te paraît fausse se signale dans tes notes ; elle se corrige à l'étape 5, par le lecteur.

### Tu ne fais juger aucun essentiel

**Tu écris, tu rends.** Le jugement des essentiels appartient au nœud de vérification qui suit —
agents frais, skill `veille-verif-carte`, trois questions : compris, vrai, bien écrit. Tu ne
dispatches aucun vérificateur, tu ne poses aucun champ de verdict sur un finding, et tu n'attends
aucun feu vert pour assembler.

*Motif : un juge posté à l'intérieur de l'étape ne prévient pas les refus du juge qui suit — il
corrige un texte que l'autre refuse ensuite sur d'autres critères, et son verdict est de toute façon
périmé dès que tu réécris. Le contrôle est un nœud, pas une sous-étape.*

**Ce que tu fais quand un rapport de vérification te revient** : tu corriges ce qu'il prescrit, et
rien d'autre. La correction **recopie la source**, elle ne rédige pas ; quand aucune recopie ne peut
réparer, elle retire l'affirmation fautive.

### Le bundle niveau 1 — sa forme

Pour **chaque histoire** (zéro filtre — toutes entrent), écris une entrée dans `findings.json` :

```json
{
  "id": "<id stable>",
  "titre": "<headline de l'histoire, compréhensible seule>",
  "axe": "<axe de l'histoire, ou 'Transverse' pour signal-faible/contre-preuve>",
  "sources": [
    {"titre": "<titre du finding>", "url": "<URL réelle>", "date": "<AAAA-MM-JJ>",
     "trouve_par": "<chasseur>", "fid": "<id du finding d'origine>"}
  ],
  "url": "<source primaire de l'histoire — la première de `sources`>",
  "essentiel": "<les paragraphes de l'essentiel, séparés par une ligne vide>",
  "date_fait": "<AAAA-MM-JJ — la PLUS RÉCENTE des sources>",
  "trouve_par": ["<chasseur1>", "..."],
  "tags": ["NEW" | "SUITE:<entité>" | "PROMEUT:<signal>"],
  "tier": "Excellent | Cool | Intéressant | Neutre | Bof | Inutile",
  "tier_source": "agent",
  "tier_justification": "<1 phrase courte>",
  "titre_a_revoir": true|false,
  "notes": {"poids": 0, "disruptivite": 0, "delta": 0, "matiere": 0, "contradiction": 0}
}
```

**`sources` est obligatoire, même pour une histoire à un seul finding** — une entrée. C'est ce
tableau que la carte de la constellation affiche ; `url` reste rempli pour les lecteurs qui n'en
lisent qu'une, et vaut toujours la première entrée de `sources`.

**`notes`** = le vecteur des 5 critères que le vérificateur de chasse a posé. Pour une histoire à
plusieurs findings, le monteur recopie le vecteur du finding dont la tier a été retenue (il ne
renote ni ne moyenne). Sert à l'**affichage de la note IA dans la carte** du viewer.

Règle dure : **AUCUN `rapport`**. **Axe `Transverse`** = axe à part entière, ne jamais le rabattre. L'axe Transverse doit exister dans la liste d'axes du `constellation-data.json` (l'ajouter s'il manque, sinon les nodes transverses n'ont pas de hub).

**⚠️ Passe explicite de vérification des titres.** Pour CHAQUE finding, réponds explicitement à la question **« ce titre est-il compréhensible seul, sujet nommé + fait concret ? »** — pose la question dans ton raisonnement, réponds oui/non, THEN pose `titre_a_revoir:true|false`. **Un titre à énigme est TOUJOURS à revoir.**

Test automatique — si le titre commence par « Ceux qui », « Un truc qui », « Une nouveauté qui », « La chose que », « Le fait que », « C'est ce que », « Voici pourquoi » → `titre_a_revoir:true` sans discussion. Si le titre parle d'un fait précis sans nommer le sujet (« bat », « double », « chute » sans QUI/QUOI en tête) → `titre_a_revoir:true`.

Ne jamais jeter un finding pour son titre, ne pas le réécrire toi-même — mais LE SIGNALER est obligatoire. Un `0/N` signalé sur un run réel = présomption de non-vérification.

### 4. Construire et déployer la constellation d'évaluation

**UNE commande fait tout** — build, pose du livrable, déploiement, contrôle HTTP :

```bash
$CONSTELLATION_HOME/viewer/deployer-eval.sh <workspace>
```

Elle construit `constellation-data.json` depuis `findings.json`, le pose comme livrable du nœud,
le déploie sous `/c/<run>-eval/`, puis constate : la page, le JSON et un asset en HTTP 200, et le
md5 servi comparé au livrable local. Elle sort en code non nul si l'un des trois manque, et son
`RESUME` dit lequel. Elle sauvegarde l'existant avant d'écraser.

**Elle refuse de déployer plutôt que de déployer du vide** : `findings.json` illisible ou sans
aucun finding, ou build qui rend zéro signal, et rien ne part. *Le builder avale un JSON cassé en
silence et produit une constellation à 0 signal — sans ce garde-fou, une page vide se déploie en
annonçant un succès, et le lecteur y est invité.*

**Ne refais aucun de ces gestes à la main.** Chercher le script, retrouver le chemin de
destination, empiler les `cp` et les `curl` de contrôle, c'est une vingtaine d'allers-retours pour
ce qu'une commande fait en moins d'une seconde.

**La page HTML ne se reconstruit pas.** Le template racine (`constellation.template.html`) est
copié tel quel au premier déploiement, avec ses assets ; seul le JSON change ensuite. Le script
s'en charge, ne le recopie pas toi-même.

**Deux contrats que le builder doit respecter** — les vérifier dans le JSON produit, jamais les
écrire à la main :

- **Bilingue** : chaque node porte `headline`/`headline_fr`/`headline_en`, `lead`/`lead_fr`/`lead_en`,
  et dans `fiche` : `essentiel`/`essentiel_fr`/`essentiel_en` ; à la racine, `axes` + `axes_fr` +
  `axes_en`, alignés par index. Sans eux, le bouton EN du viewer ne s'affiche pas ou affiche du faux.
- **Layout** : `nlanes = max(1, len(nodes))` — une lane par node — et chaque node porte un `lane`
  distinct dans `[0, nlanes-1]`, attribué en triant par index d'axe puis ordre stable. Un `nlanes`
  plus petit empile les étoiles au lieu de les aérer.

**Déployer ne prévient pas** : le lecteur n'est invité qu'après le feu vert de la vérification.
