---
name: veille-launch-researcher
description: Phase de chasse d'une run de veille. Lance le casting = 1 chasseur par AXE + 2 TRANSVERSAUX fixes (signal faible, contre-preuve) + 1 ECLAIREUR, chacun AMNESIQUE (agent frais a chaque tour). Le chasseur ne verifie pas son propre travail : la verification est un nœud separe du graphe, joue apres. Un chasseur ne differe des autres que par son axe et sa fraicheur : meme skill, memes outils, meme budget. Chaque chasseur = un MOTEUR de butinage commun + une TETE methodo selon son type (PIR pour l'axe, Ansoff pour le signal faible, ACH pour la contre-preuve). Plancher — un BUDGET D'EFFORT (sources ouvertes, formulations essayees), jamais un nombre de findings : zero finding sur un axe est valide. Max 5 allers-retours par chasseur. Chaque chasseur rend son transcript complet, conservé. Déclencheurs — "/veille-launch-researcher", "lance les chasseurs". Joué à l'étape 2, après la préparation. Étape suivante — la vérification de l'étape 2, puis le montage de la constellation.
---

# Veille — phase de chasse (chasseurs × vérificateurs, tous agents frais)

## ⚠️ Erreur de catégorie à éviter

**Ce skill décrit un WORKFLOW (chemin prédéterminé chasseur → vérificateur → boucle), pas un menu d'options.** Mais chargé dans le prompt d'un orchestrateur LLM autonome, il devient de fait *une suggestion que le LLM est libre d'ignorer* — workflows = predetermined paths, agents = LLM decides (Anthropic *Building Effective Agents*). Sous charge (post-fanout de N chasseurs, findings encaissés), l'orchestrateur collapse le composé « orchestrator-workers + evaluator-optimizer » vers le plus simple : orchestrator-workers seul, sans boucle vérificateur.

**Trois défauts structurels convergents** :
1. **Personne en aval pendant que l'orchestrateur tourne** — la vérification est un nœud séparé, jouée après ; pendant l'étape, *« looks done »* est le seul signal dont il dispose.
2. **Saturation post-fanout** — N sub-agents rentrent avec un rapport « done » ; la fonction de complétion converge vers « globalement done ».
3. **Skills advisory, pas déterministes** — un skill est du Markdown chargé une fois. Rien n'oblige à ré-invoquer le skill de vérification.

**Ce qui le neutralise** : le dispatch des vérificateurs est **hors du prompt de l'orchestrateur** — c'est un nœud du graphe, joué après celui-ci, par un runtime qui ne lui demande pas son avis. L'arête est statique (`add_edge` framework-enforced), pas une décision de LLM (`add_conditional_edges`). Toi, chef de chasse, tu ne vérifies rien : tu chasses, tu comptes, tu rends la main.

**Rappel opérationnel** : si tu n'as pas d'edge statique en aval, tu DOIS faire toi-même la boucle explicitement et cocher chaque tour. Ne fais jamais confiance à la relecture du skill au démarrage.

**Vérification rétroactive N'EST PAS un fix** — c'est un rapiéçage. Un run avec vérif rétroactive est biaisé (l'ordre normal = chasser et vérifier ensemble, jamais l'inverse). À signaler dans le rapport final.

---

## Ce que fait cette phase

Produit **des findings déjà validés**, pas des pistes brutes.

- **Le casting** = N chasseurs d'AXE (1 par axe du profil, couverture) + 2 chasseurs TRANSVERSAUX fixes (`signal-faible`, `contre-preuve`) qui balaient tout le sujet.
- **Chaque chasseur = moteur commun + tête méthodo**. Le moteur (comment fouiller) est identique ; la tête (quoi/où chercher) dépend du type.
- **Le chasseur persiste** : dispatché une fois, garde son contexte, reçoit le rapport du vérificateur, repart.
- **Le vérificateur est amnésique** : neuf à chaque tour, contexte vierge. Un juge qui accumule finit par valider ce qu'il a déjà vu ; réinstancié, il ne se lasse ni ne s'attache.
- **Le plancher porte sur l'EFFORT** — `budget_effort` en tête du casting : sources ouvertes, formulations essayées, pages atteintes sans passer par une liste de résultats, sources hors moteur généraliste. Infalsifiable par découpage ou remplissage, puisqu'il ne compte pas les sorties.
- **5 allers-retours max** par chasseur.
- **Le coût n'est pas un critère.**

Le chasseur qui apprend à plaire à son juge, **c'est l'objectif** — à la condition que les critères soient infalsifiables.

---

## Grille et règles injectées

**Grille unique** — 5 critères (Poids/affinité · Disruptivité · Delta · Matière · Contradiction), ancres dans `docs/criteres-juges.md`. Le vérificateur note une fois, la note voyage avec le finding.

**Règles apprises** : `owners/<owner>/preferences/selection-rules.md`, injecté aux chasseurs ET aux vérificateurs. Porte aussi les **consignes de chasse** (sujets/acteurs/angles/sources à creuser ou alléger, distillés du deck + commentaires-fond).

**Règles par axe** : `owners/<owner>/preferences/regles-axes.json` — pour TON axe, les règles
que le lecteur a validées, chacune avec ses mots-clés. Elles ne sont pas indicatives : le contrôle de
l'étape suivante confronte tes **requêtes journalisées** à ces mots-clés, et refuse l'étape si une
règle validée n'a été visée par aucune recherche. Formule donc au moins une requête par règle, et
dis dans ton journal laquelle tu vises.

**Deck de préférence** : `owners/<owner>/preferences/deck-<watch>.json`. Seuls les `adorés`
deviennent des pistes de recherche. Les `surcotés` (fiches que le lecteur a rétrogradées) sont
des **contre-exemples de calibration** : ne JAMAIS en faire des requêtes, sous peine de
rechercher exactement ce qui vient d'être sanctionné. Les `détestés` servent d'écartement.
Transforme les `adorés` en **requêtes concrètes** : sujets/acteurs/angles récurrents des adorés → nouvelles recherches ; détestés → anti-exemples.

**⚠️ Injection obligatoire dans le prompt du chasseur — la seule mention « s'il existe » ne suffit pas.** Le leader qui dispatche DOIT passer :
1. **Le deck complet** — les 5+5 brèves, pas juste leur existence.
2. **Les entités déjà introduites dans la veille** — extrait de `owners/<owner>/db/memory/<watch>.json` section `entities`. Sert au chasseur pour NE PAS ré-remonter un fait déjà rapporté (règle « déjà remonté ») et transmettre les gloses aux synthétiseurs.
3. **Les findings retenus des runs passés** — extrait de `owners/<owner>/db/findings/<watch>/*-retenus.json` : titres + axes + dates. Filtre anti-doublon.

Sans ces trois, le run est « à froid » et doit être marqué comme tel. `veille-start` s'assure qu'ils sont dans le workspace AVANT la chasse.

**ANTI-BULLE — c'est l'ÉCLAIREUR qui la porte**, pas un pourcentage réparti sur tout le monde : il cherche HORS de tous les axes et rend ses graines dans `state/axes-candidats.json`. Un chasseur d'axe reste sur son axe. Aucune piste n'est écartée au motif « hors préférence » : le classement range, il ne coupe pas.

**UNE VIDÉO OU UN PODCAST SE LIT PAR SON TRANSCRIPT, JAMAIS PAR SA PAGE.** Une page YouTube porte
un titre et une description — pas ce qui est dit. En juger revient à rapporter le résumé de
l'auteur, et une affirmation tirée de là n'est adossée à rien.

```bash
veille-transcript <url>      # rend le texte, sans horodatage
```

**Elle marche pour YouTube comme pour un podcast**, et se débrouille seule : elle demande à YouTube
quelles pistes existent et prend celle **dans la langue de la vidéo** ; si aucune n'est utilisable
elle télécharge le son et le transcrit sur la machine, puis l'efface. Tu n'as ni langue à choisir,
ni option à passer.

*Ce que ça t'évite de refaire : demander « le français » sur une vidéo anglaise déclenche une
traduction à la volée, et c'est la seule chose que YouTube limite — la même récupération coûte
351 s de réessais par cette voie contre 6 s par la piste d'origine.*

**Code 3 ou 4 : tu le CONSIGNES et tu passes.** Une source qu'on n'a pas pu lire ne devient pas une
fiche : écrire depuis le titre fabriquerait un fait que rien ne soutient. Note-la « non lisible »
dans ton compte-rendu — c'est un constat, pas un échec de ton budget d'effort.

**UNE SOURCE TENUE NE SE CONSULTE PAS, ELLE S'ÉNUMÈRE.** Ouvrir la page d'accueil d'une chaîne, c'est
regarder ce que l'algorithme y met ce jour-là et rater ce qui est sorti la veille. Trois gestes, dans
cet ordre, pour chaque source de ta ligne de casting :

```bash
veille-source-nouveautes <url> <fraîcheur-de-ton-axe> archives/
```

- **① Elle liste** ce que la source a publié, avec la date — par le flux de la chaîne, pas par sa page.
- **② Elle coupe à ta fraîcheur** : ton axe dit 48 h, tu ne vois que les deux derniers jours.
- **③ Elle écarte ce qui a déjà été livré**, en comparant aux archives de la veille.

Elle rend une ligne par publication neuve — `date`, `url`, `titre` — la plus récente d'abord. Tu
prends chacune, tu en lis le texte par `veille-transcript`, et tu juges. **Une sortie vide est un
résultat valide** : la source n'a rien publié de neuf dans ta fenêtre, tu le notes et tu passes à la
chasse ordinaire.

*Sans le geste ③, chaque run reprend les mêmes vidéos et le lecteur relit les mêmes histoires en
croyant que rien n'a bougé. Sans le ②, une chaîne active noie ton axe sous un mois d'archives.*

**LES SOURCES QUE LE LECTEUR T'A NOMMÉES — tu les ouvres AVANT d'ouvrir un moteur.** Ta ligne de
`casting.json` porte `sources` : celles tenues sur ton axe, plus celles que le profil tient pour
tous. Ce sont des adresses à atteindre à la main, pas des mots-clés à taper — un site, une chaîne,
un compte, une revue, une personne. Tu les épuises d'abord, puis tu chasses normalement.
*Le lecteur les a nommées parce qu'il leur fait confiance : arriver sur son axe sans les avoir
ouvertes, c'est lui rendre ce qu'un moteur aurait trouvé sans lui.* Elles ne remplacent aucun
plancher d'effort : une source nommée ne dispense ni des formulations, ni des pages atteintes hors
liste de résultats. Champ vide = rien de tenu sur cet axe, tu chasses normalement.

**Directives dures** : `state/directives.md` si présent (ex. « ≥8/20 findings à source primaire scientifique »). Honorées activement, jamais par remplissage.

---

## La fiche — la définition CLOSE de ce que tu rends

Une piste, c'est un titre et **neuf champs**, dans cet ordre. **Liste close** : pas un champ de
plus, pas un de moins. C'est contre elle que ton lot sera vérifié, champ par champ.

```markdown
## P<n> — <titre : l'affirmation elle-même, pas un sujet>
- **URL** : <l'adresse exacte de la page ouverte>
- **Date du fait** : <la date que porte la source ; « consulté <date> » si elle n'en donne aucune>
- **Source** : <hôte> — primaire | secondaire | agrégateur <qualification si et seulement si la page la dit>
- **Sources indépendantes** : <celles qui disent la même chose, ou « <hôte> uniquement — à corroborer »>
- **Essentiel** : <ce que la source établit — fait, mécanisme, chiffres, réserve>
- **Ce que ça déplace** : <ce que le lecteur change dans SON matériau, nommément>
- **Pertinence pour le lecteur** : <pourquoi lui, pourquoi maintenant>
- **Tier** : <Excellent | Cool | Intéressant | Neutre | Bof | Inutile>
- **tier_justification** : <pourquoi celle-là et pas la voisine, nommée>
```

**Cinq de ces champs sont ADOSSÉS À LA SOURCE** — `URL`, `Date du fait`, `Source`,
`Sources indépendantes`, `Essentiel`. Tout ce qu'ils affirment doit se lire dans une page que **tu
as réellement ouverte** : chaque chiffre, chaque nom propre, chaque affiliation, chaque
qualification d'éditeur. **Ce que tu sais par ailleurs ne compte pas.** Si la page donne trois
noms d'auteurs sans leur institution, tu écris les trois noms et rien d'autre — même si tu sais où
ils travaillent. Le vérificateur cherchera la chaîne dans tes `tool_result` ; absente, c'est une
faille, et ta piste repart en correction.

**Les quatre autres sont TIENS** — `Ce que ça déplace`, `Pertinence pour le lecteur`, `Tier`,
`tier_justification`. C'est ton jugement, il n'a pas à être dans une source : il a à être justifié.

**Le doute se lève en ouvrant une page, jamais en écrivant moins.** Une affiliation utile et non
donnée par la page se va chercher sur une seconde page, qui devient une source indépendante.

## La tier — le chasseur classe sa propre trouvaille

**Chaque piste sort de la chasse avec sa tier.** Elle vit dans la fiche
(`pistes-<chasseur>-T<n>.md`) et voyage dans `state/passants-raw.jsonl`. Le monteur la
**reporte** telle quelle à l'étape 3 ; le lecteur la corrige à l'étape 4.

**Les six tiers**, du plus proche du centre de la constellation au plus lointain :

```
Excellent · Cool · Intéressant · Neutre · Bof · Inutile
```

C'est ici que le barème est défini. Partout ailleurs on y renvoie.

- **Toi, tu classes ; tu ne coupes pas.** Aucune piste ne se jette en chasse : une piste
  `Inutile` sort quand même avec sa fiche. Le vivier monte entier (§ La déduplication) — un
  chasseur qui couperait le ferait sans voir les autres axes.
- **Contre les règles de TON axe et le deck**, pas contre ton goût : proximité aux `adorés`,
  distance aux `détestés`, et les `surcotés` disent où tu places ta barre trop haut — une
  piste qui ressemble à un `surcoté` mérite la tier que le lecteur avait choisie, pas celle
  que tu allais lui donner.
- **Une phrase de justification par piste** (`tier_justification`) : elle dit **pourquoi
  celle-là et pas la voisine**. Sans elle, la tier n'est pas relisable — et le contrôle de
  l'étape refuse la piste.
- **Étaler.** Tout un axe rangé dans la même tier n'est pas un classement, c'est un
  remplissage de cases. À égalité réelle, préférer la tier du milieu plutôt que gonfler
  `Excellent`.
- **Tu classes ta trouvaille, tu ne juges pas ta fouille.** La qualité de ta chasse est
  jugée au nœud de vérification, par un agent frais qui n'y a pas participé.

---

## La déduplication — ce qui monte

**Le vivier monte entier.** La chasse ratisse large et rend tout ce qui a passé la vérification :
aucun plafond, aucun quota, aucune réserve. Ce qui tient la lecture n'est pas une coupe mais le
regroupement des findings en **histoires**, à l'étape 3 — le lecteur y trouve moins d'objets à lire
sans qu'on ait jeté une seule trouvaille.

**Le seul geste de fin de chasse est la déduplication**, tenue par le chef de chasse une fois
`state/passants-raw.jsonl` figé. Deux fiches qui portent le même fait fusionnent : la meilleure
reste, la seconde est citée dans son `fusion_de`, et `state/ecartees.md` garde une ligne par
doublon fondu (titre, URL, axe, l'entrée qui l'a absorbé).

**Dans le doute, on ne fusionne pas.** Deux pistes voisines mais distinctes se laissent séparées :
le rapprochement se juge à l'étape 3, sources ouvertes, par celui qui écrit. Une redite se voit à
la lecture ; une fusion abusive ne se retrouve pas.

**Livrable** : `state/retenus.json` — le vivier dédupliqué entier, chaque entrée avec sa `tier`,
sa `tier_justification` et son `fusion_de`.

---

## Ce que le lecteur a demandé d'écarter

Quatre sources, quand elles existent. **Toutes absentes = première run** — c'est l'état normal
d'un premier tour, pas une dégradation.

| Ce qu'elle apporte | Où elle vit |
|---|---|
| Ce que le lecteur a **explicitement demandé d'écarter**, validé par lui | `state/selection-rules.md` |
| Ce qu'il a **adoré, détesté, surcoté** — avec son pourquoi | `state/deck-<veille>.json` |
| Ce qu'on lui a **déjà livré**, pour couper la redite | `state/memory-<sujet>.json` |
| Ce que chaque axe doit viser | `state/regles-axes.json` |

Deux priorités, sans lesquelles ces sources se contredisent :

- **Une règle d'écartement SORT la piste.** Elle a été validée en langage naturel par le lecteur :
  elle vaut plus que ton classement. C'est le seul motif qui retire une trouvaille du vivier.
- **Le deck ne commande pas.** Il montre à quoi ressemble ce qui a compté pour lui — c'est du
  montrer-par-l'exemple. Une piste qui ressemble à un détesté te fait chercher ce qui la
  sauverait ; elle ne meurt pas de la ressemblance. Elle pèse sur la tier, jamais sur la présence.

## L'ampleur d'exploration — mesurée, pas imposée

Pas de quota d'URL. La largeur vient du **moteur** :
- **critère de parcelle** (lâcher un filon qui s'épuise)
- **diversification** (angles différents + une requête oblique)
- **requête vivante** (la recherche évolue, ne stagne pas sur q0)

Le compte se fait par extraction du transcript, jamais déclaré par l'agent. Le **nombre d'hôtes distincts** est reporté au rapport de méthode : un chasseur resté sur 3 hôtes est **signalé** — non pour un quota raté, mais parce que le critère de parcelle n'a pas joué. Non bloquant.

**Piège d'extraction** : un chasseur qui script ses appels d'API construit ses URL dynamiquement, l'extraction mécanique le sous-compte massivement (mesuré : 2 requêtes comptées pour 25 réelles). Avant de conclure qu'un chasseur a peu exploré, reconstituer le compte réel dans le brut.

---

## Le casting

Dérivé du profil owner par `/veille-start`, stocké dans `casting.json`.

**Les chasseurs ne diffèrent que par deux choses : l'axe qu'ils couvrent, et la fenêtre de
fraîcheur de cet axe.** Même skill, mêmes outils, même budget pour tous. Il n'y a ni persona, ni
spécialité, ni style propre à un chasseur — rien de tel n'est lu nulle part.

| Chasseur | Combien | Ce qu'il couvre |
|---|---|---|
| **d'axe** | 1 par axe du profil, illimité | son axe, et lui seul |
| **transversal** | 2, fixes | `Signal faible` et `Contre-preuve` balaient tout le sujet |
| **éclaireur** | 1, obligatoire | HORS de tous les axes — le seul qui peut faire naître un axe |

```json
{ "axe": "Robotique", "freshness": "mois", "consigne": "alléger fortement" }
{ "axe": "Découverte", "role": "eclaireur" }
```

`consigne` n'apparaît que si le feedback en a produit une pour cet axe.

**Chaque chasseur porte une `freshness`, transversaux et éclaireur compris.** Sans elle on ne
peut pas dire si un finding archivé peut encore ressortir, et l'anti-doublon copie tout ce qui
existe au lieu de ce qui compte. Défaut pour les trois non-axés (`Signal faible`,
`Contre-preuve`, `Découverte`) : `mois`.

**Le plancher de chaque chasseur est un budget d'EFFORT, pas un nombre de findings** :
`budget_effort` en tête du casting — ≥15 sources ouvertes, ≥8 formulations de requête, **≥5 pages
atteintes sans passer par une liste de résultats**, ≥3 hors moteur généraliste.

**« Sans passer par une liste de résultats »** = adresse construite à la main, lien suivi depuis
une page déjà ouverte, moteur interne ou archive d'un site. *Le moteur du harnais ne rend qu'**une**
page de résultats et n'offre aucune pagination : « au-delà de la 1re page » n'est pas un geste
qu'un chasseur puisse poser, et chaque juge en inventait sa propre lecture — l'un déclaré conforme
à 13, l'autre recalé à 1, pour un travail comparable.* **Zéro finding sur un axe est un résultat valide.** Un
chasseur qui remplit pour atteindre un nombre fabrique du bruit, et c'est le bruit qu'on lit
ensuite.

Casting absent → le dériver des axes du profil, et le signaler.

**Pourquoi ce modèle** : l'AXE dit *quoi couvrir*, l'ANGLE dit *comment chercher* — deux dimensions orthogonales. Découper la chasse uniquement par axe supprime le signal faible et la contre-preuve, qui sont transverses.

### Le recouvrement — bon ou mauvais selon lequel

- **Converger sur un même finding** (deux chasseurs partis d'angles différents tombent sur le même fait) → **Bon.** Confirmation indépendante, le finding gagne du poids et porte l'étiquette « trouvé par N chasseurs ».
- **Dérouler les mêmes requêtes** (deux chasseurs lancent des recherches identiques et lisent les mêmes pages) → **Gaspillage.** On paie deux fois le même travail et la convergence est fausse.

On garantit donc **la non-duplication des chemins**, pas la disjonction des terrains :
- L'axe (et pour un transversal, son angle) est un **point de départ**, pas une clôture.
- **Tableau de requêtes partagé** `<base>/queries-board.md` : chaque chasseur y ajoute ses requêtes et hôtes à chaque tour. Avant son tour suivant, il le lit et **ne relance pas une requête déjà lancée** — il reformule ou change d'angle. Alimenté par extraction du transcript, pas par déclaration.
- La **convergence est comptée, jamais fusionnée en silence** : à la fusion, un finding trouvé par plusieurs chasseurs conserve `trouve_par: N` et la liste des chemins distincts. Si deux chasseurs ont pris la même requête, N retombe à 1.

---

## Le moteur de butinage — couche commune à TOUS les chasseurs

Injecté à l'identique dans le prompt de chaque chasseur. **Comment on fouille**, indépendamment de ce qu'on cherche. Quatre gestes + un critère d'arrêt.

**1. L'odeur — juger avant d'ouvrir** (Information Foraging : *information scent*). Score l'odeur de chaque résultat sur ce qu'il voit — titre, extrait, domaine, date. N'ouvre que les plus prometteurs. Log un `scent` bref (fort/moyen/faible) sur ce qu'il choisit d'ouvrir.

**2. La requête vivante — évoluer à chaque trouvaille** (Berrypicking + PRF/Rocchio). Interdit de rejouer la même requête. Tient un **état de requête** mis à jour après chaque trouvaille **validée** : extraire termes neufs, construire la suivante avec. Garde-fou anti-dérive : n'enrichit qu'à partir des trouvailles validées, jamais à partir de pages brutes. Sa trajectoire q0→q1→q2… se lit dans sa session, requête après requête — un agent bloqué sur q0 s'y voit, sans qu'il ait à la recopier ailleurs.

**3. Le snowballing — chaque trouvaille en engendre deux** (Wohlin, backward/forward). Après chaque trouvaille validée :
- **backward** — suivre les sources citées **dans** la page pour remonter au document d'origine (communiqué, papier, dépôt, changelog). On cite la source primaire, jamais un écho.
- **forward** — chercher **qui reprend, adopte, conteste ou réagit** à cette trouvaille après elle. Patron : `"<entité/claim>" (alternative OR migration OR critique OR retour) after:<date>`.

Déroulé tant que ça ramène du neuf, arrêt sur saturation.

**4. Diversification + sérendipité — pas de clones, une piste au hasard** (MMR/DPP + Erdelez). Évite de rapporter plusieurs trouvailles qui disent la même chose. Réserve **au moins une requête délibérément oblique** par passe (angle adjacent, source atypique, terme contre-intuitif).

**Critère d'arrêt interne — quitter un filon qui s'épuise** (théorème de la parcelle). Tient un **rendement courant** = trouvailles retenues / pages ouvertes. Quand le rendement d'un filon tombe nettement sous ce qu'il obtenait juste avant, il **pivote** — nouvel angle, nouvel hôte — au lieu de gratter le même puits.

---

## Les trois têtes méthodologiques — couche propre à CHAQUE type

Greffée sur le moteur. **Quoi chercher et où.**

### Tête AXE → Collection Planning / PIR

1. Éclater l'axe en **questions de couverture**.
2. Éclater chaque question en **indicateurs observables** — signes concrets qu'il saurait reconnaître (ex. axe « prix/dispo » → baisse annoncée, pénurie, nouvel entrant).
3. Tenir une **matrice de couverture** : quels indicateurs ont déjà une trouvaille, lesquels sont vides.
4. **Chasser les indicateurs vides**, pas re-fouiller au hasard. Fin = tous les indicateurs couverts ou constatés introuvables.

Sourcing : structurer en **secondaire** (largeur : actu, agrégateurs) puis **primaire** (profondeur : communiqué, papier, dépôt). Ne jamais s'arrêter au secondaire. Selon la nature de l'axe : axe scientifique → preprints/sources primaires ; axe outillage → dépôts, changelogs, SDK ; axe matériel → bancs, self-host.

### Tête SIGNAL-FAIBLE → signaux faibles d'Ansoff / horizon scanning

Cherche **l'important-mais-peu-relayé, ce qui rend une pratique obsolète sans être annoncé**. Un signal faible n'est jamais dans les canaux d'annonce.
- **Chercher hors mainstream** : preprints, dépôts, changelogs, notes de dépréciation, fils d'issues, forums de praticiens, niches, non-anglophone.
- **Chasser l'effet, pas l'annonce** — les *traces de bascule* : qui **abandonne** ce qui est adopté, qui **adopte** ce qui est abandonné, qui **contourne** par un fork, quel flag/défaut change sans communication. Le témoin se cherche dans le **mouvement parallèle**, pas dans la plainte.
- Patrons : `"we replaced X with"`, `"deprecating"`, `"migration away from"`, `"no longer need"`, `"removed dependency on"`, `"stopped using"`, et équivalents dans les langues du terrain.
- **Sélection = surprise × déconnexion du dominant**, jamais le volume de citations.
- Pour chaque trouvaille, **nommer la pratique établie qu'elle rend obsolète** avec un fait daté. Tagger la **trajectoire** (émergent / en amplification).

### Tête CONTRE-PREUVE → ACH de Heuer + red team

**Falsification-only** : ne rapporte jamais de positif.
- **Pre-mortem** systématique sur chaque promesse/hype : « dans 12 mois, cette promesse a échoué — quelle preuve datée l'annonce **déjà** ? »
- Poser l'**hypothèse concurrente** « c'est faux / surévalué » et chercher la **preuve qui réfute** : benchmark rejoué et démonté, réplication ratée, condition cachée, promesse non tenue, retour de terrain qui contredit le communiqué.
- **Sélection sur diagnosticité** — une preuve qui *départage vraiment*, pas une opinion critique.
- La contre-preuve vient souvent du **primaire** (post-mortem d'ingénieur, thread de praticien) qui contredit le secondaire optimiste : mandat explicite d'aller chercher la parole de terrain.

### Règles transverses aux N+2

- **Triangulation** : viser ≥2 sources indépendantes avant de proposer un finding. Le signal-faible, non corroboré par nature, **flag** « source neuve non corroborée » au lieu de jeter.
- **Pivoting** : partir d'un point exposé (nom, dépôt, auteur) pour dérouler les entités liées — utile signal-faible et contre-preuve.

---

## Le transcript du chasseur

**Le chasseur rend son transcript complet**, pas un compte rendu rédigé. Un agent qui rédige son propre journal peut l'enjoliver ; le transcript ne ment pas.

### Où vit le transcript

Chaque sous-agent lancé par `Agent` écrit un JSONL dans :
```
~/.claude/projects/<slug>/<session-id>/subagents/agent-<agentId>.jsonl
agent-<agentId>.meta.json   → {agentType, description, toolUseId, parentAgentId, spawnDepth}
```
Chaque ligne = événement `user`/`assistant` avec ses blocs `tool_use` et `tool_result` — les requêtes WebSearch littérales, les URLs ouvertes, le raisonnement intermédiaire.

### Pour qu'il soit adressable

1. **Nommer chaque chasseur** au dispatch (`name: "chasseur-axe-<slug>"`). L'`agentId` reprend le nom, le fichier est retrouvable par glob.
2. **Tu n'as rien à copier.** Le runtime rend les transcripts — le tien et celui de chacun de tes
   chasseurs — dans `<base>/transcripts/` à la fin de chaque passe, sans que tu le demandes.
   *C'est le runtime et pas toi parce qu'un sous-agent ignore son propre identifiant, et parce
   qu'une trace produite par celui qu'elle sert à juger n'est plus une preuve.*
3. **Extraire un index par tour** `<base>/transcripts/chasseur-<slug>-round<k>.index.md`, produit par grep (jamais par le chasseur) :
   - requêtes lancées, mot pour mot, dans l'ordre
   - hôtes et URLs effectivement ouverts
   - rejets explicites et leur motif
   - compteurs : requêtes distinctes, doublons, pages ouvertes, profondeur maximale d'une chaîne source

### Comment le vérificateur le lit

Volume : ~20 recherches par chasseur, × pages ouvertes, × jusqu'à 5 tours. Personne ne lit linéairement.

Le vérificateur reçoit **l'index** (obligatoire, en entier) + **le JSONL brut** en accès ciblé (chemin fourni, grep possible). Premier réflexe : vérifier que l'index colle au brut sur 2-3 points au hasard. Si l'index a été fabriqué au lieu d'être extrait, ça se voit.

**Séparation des rôles** : le jugement de la **méthode** (transcript) et le jugement des **findings** (grille) sont deux prompts distincts, dans le même vérificateur amnésique mais en deux passes séquentielles, méthode d'abord. Sinon le coût de lecture du transcript écrase la vérification factuelle.

---

## Les deux jugements du vérificateur

### A. Jugement de la CONVERSATION (score séparé)

On juge la **méthode**, pas les trouvailles. Ce score **ne décide pas du sort des findings** — il déclenche une relance motivée et remonte au rapport de phase.

- Diversité réelle des recherches (questions différentes vs dix reformulations)
- Volume d'exploration (pages réellement ouvertes, pas seulement listées)
- Profondeur (suivi des sources citées ou arrêt au premier résultat)
- Remontée aux sources d'origine (primaire vs articles qui en parlent)
- Rejets motivés
- Couverture du terrain (tous les angles ou seulement les faciles)
- Auto-excuses (« pas trouvé », « source inaccessible » : vrai obstacle ou abandon)
- Taux de survie de ses pistes vs autres chasseurs
- Recouvrement avec les autres — **information, pas sanction**

### B. Jugement de CHAQUE FINDING (grille partagée)

**Éliminatoires** — binaire, un « non » et le finding tombe :
- le fait est vrai
- la source existe et est vérifiable
- les sources sont indépendantes (trois articles citant le même communiqué = **une** source)
- le plancher de conséquence est franchi

**Notés** — grille 5 critères, échelles 0-3, un critère = un appel séparé, **nommer sinon zéro**, ancres du document de référence.

**Étiquettes** — ni bonus ni malus, informent le lecteur :
- auto-déclaré ou mesuré par un tiers (une annonce d'éditeur *est* auto-déclarée — étiqueter, pas pénaliser, sinon on élimine mécaniquement les annonces produit)
- date réelle du fait, distincte de la date de l'article
- nombre de chasseurs y étant arrivés par des **chemins distincts**

### La barre de passage

Définie une seule fois dans `docs/criteres-juges.md`, section « La barre de passage ». Ne pas la redéfinir ici.

En résumé : tous les éliminatoires passés, **et** `delta ≥ 1`, **et** `matière ≥ 1`, **et** au moins une de : `disruptivité ≥ 1` · `matière = 2` · `contradiction ≥ 1`.

**Le poids ne conditionne pas le passage.** Si un finding devait être fortement relayé pour passer, la chasse éliminerait mécaniquement le peu-relayé-mais-disruptif — exactement ce qu'une veille est censée apporter.
- Le **poids** est constaté et étiqueté, hors barre. Constaté **en ligne**, jamais dans la fiche (un juge qui note le poids d'après les sources listées mesure la qualité du sourcing, pas la circulation).
- L'**affinité** (goûts appris) est étiquetée de même. Sert à la distillation, pas au passage.

Un finding qui ne passe pas est renvoyé au chasseur **avec le motif par critère et l'ancre manquée**, pas avec un score global.

---

## Le signal faible — pourquoi un chasseur transversal dédié

L'angle rare perd toujours l'arbitrage contre l'évident quand il est distribué à tous les chasseurs. Le protocole le confie à un **chasseur transversal dédié** dont c'est l'unique fonction, sur tout le sujet, avec la **tête Ansoff**.

Cas de référence : vLLM supprime PagedAttention, aucune plainte publique nulle part, la recherche est vide — mais trois organisations l'implémentent dans la même fenêtre (Layr-Labs, HF, Intel/OpenVINO), et un utilisateur en aval change de backend pour l'obtenir. Le finding passe par le **mouvement inverse**, pas par un mécontent.

**Instrumenter le lot rejeté** : tout finding écarté est logué avec sa case (poids, disruptivité) dans `<base>/rejected.md`, avec son motif. Rien ne disparaît en silence. Cette règle vaut aussi pour le pré-filtre de préférences.

---

## Concurrence — ~10 agents actifs, garde-fou

Plafond de simultanéité : **~10 agents actifs**. Un tour mobilise 2×(N+2) agents (chasseurs + vérificateurs). Au-delà de ~10 : **mode décalé** par vagues de ~5 (chasseurs → leurs vérificateurs → vague suivante). Le plafond réel retombe à ~5, la structure de la boucle est intacte, on ne perd que du temps de mur (qui n'est pas un critère).

Signes de saturation à surveiller :
- réponse d'agent tronquée ou agent qui ne rend jamais la main
- harnais qui met plus d'une minute à répondre
- mémoire disponible sous ~2 Go ou machine qui swappe

Bascule en mode décalé : **le dire dans le rapport de phase**.

---

## Note technique — tout agent est FRAIS

**Aucun agent de la pipeline ne garde de contexte d'un lancement au suivant.** Chaque tour de chasse instancie un chasseur neuf (`Agent`, jamais `SendMessage` à un agent nommé), exactement comme le vérificateur. Ce qu'un chasseur sait du tour précédent, il le sait parce qu'il l'a **écrit** : son fichier de pistes, ses graines d'axes, et le rapport du vérificateur qui lui est remis dans son brief.

**Motif** : un contexte d'agent n'est pas un magasin d'état fiable. Il ne survit ni à une coupure, ni à une reprise, ni à un résumé de contexte en cours de run, et il rend l'exécution non rejouable — deux lancements du même tour ne partent pas du même point. L'état de la run vit dans les livrables du workspace, qui eux sont inspectables, versionnés et vérifiés par les gates.

**Conséquences pratiques** :
1. Le brief d'un chasseur au tour N porte **tout ce dont il a besoin** : son mandat, son plancher d'effort, ses livrables du tour N-1 et le rapport de vérification à traiter. Rien n'est supposé « déjà su ».
2. Un tour interrompu se reprend sans perte : on relit les livrables, on relance un agent frais.
3. **Règle leader** : conserver les `agentId` retournés au lancement (pour les transcripts et `TaskStop`), et vérifier en fin de phase qu'aucun sous-agent n'est resté actif.

---

## Déroulé

### Étape 0 — Contrôle pré-vol : le moteur de recherche

**Obligatoire, avant tout dispatch.** Un chasseur sans moteur de recherche ne peut pas faire son travail, et le dispositif ne s'en aperçoit pas.

Émettre un `WebSearch` d'essai trivial. Si le retour porte *« this session has used its web search budget »*, **la run est bloquée** — ne pas lancer les chasseurs, ouvrir une nouvelle session.

Pourquoi c'est un blocage : le critère `matière` demande de constater **si un travail indépendant existe sur le même objet**. C'est une recherche de moteur ; sans moteur, ce critère mesure une panne d'infrastructure, pas la trouvaille.

### Étape 1 — Localiser le workspace

Lire `$FLUX_RUNS_HOME/veille-runs/<subject>-<owner>-*/WORKSPACE.txt` de l'**owner actif** (pas le plus récent — les workspaces sont owner-tagués).

### Étape 2 — Charger le contexte partagé (une fois, pour tous)

- `subject.md`
- `profile.md` de l'owner (audience, périmètre, ton, `reader_level`)
- `selection-rules.md` de l'owner (règles de sélection apprises)
- `state/directives.md` si présent
- `current-stack` (règles apprises en dépendent : « pas de delta réel contre son montage »)
- 3 archives — déduplication dure
- **carnet de sources** `<base>/state/<subject>-sources.json` si présent : extraire les sources `status: trusted`, triées par `yield`
- **mémoire de domaine** `<base>/state/domain-brief.md` si présent — état accumulé cross-run
- **casting** `owners/<owner>/casting.json`
- **grille** `docs/criteres-juges.md` — injectée telle quelle **aux vérificateurs uniquement**

**Coût — n'injecte pas la grille complète aux chasseurs** (levier coût majeur). Le chasseur a besoin de la **barre de passage** et du **plancher de valeur**, pas des ancres de notation (~43k tokens) qui ne servent qu'à noter — c'est le travail du vérificateur. Extraire la section « La barre de passage » pour les chasseurs ; réserver le document entier aux vérificateurs.

Créer `<base>/transcripts/` et `<base>/queries-board.md` (vide).

### Étape 3 — Tour 1 : dispatcher les N+2 chasseurs

**En un seul message** (ou vagues de ~5 en mode décalé), `mode: "bypassPermissions"`, `run_in_background: true`, chacun nommé : `chasseur-axe-<slug>` par axe, `chasseur-tv-signalfaible` et `chasseur-tv-contrepreuve` pour les transversaux.

**Modèle : Opus par défaut.** La chasse fait du raisonnement fin (note de réouverture, jugement `matière`/`contradiction`). Le gain d'un passage en Sonnet est trop faible (~1.7× sur le coût) pour justifier le risque qualité. Garder Opus. Le vrai levier coût est l'élagage du contexte (étape 2), pas le modèle.

**Garde-fou temps/tokens par chasseur** : plafond souple par tour ≈ 25 min wall-clock ou ~120 appels d'outil. Au-delà, le leader interrompt par `SendMessage` (« rends ce que tu as, on arrête ce tour »). Un chasseur qui dépasse largement la médiane des autres est le signal à surveiller.

**Le chasseur est ÉQUIPÉ par le flux — tu ne lui recopies AUCUN protocole.** Dispatche-le avec `subagent_type: "flux-chasse-chasseur"` : il démarre avec ce skill entier en consigne permanente, moteur de butinage et têtes méthodo compris. Recopier la méthode par-dessus la double, la fait diverger d'un dispatch à l'autre, et coûte le double du contexte pour rien.

**Ton prompt ne porte donc que ce qui lui est PROPRE** — ce que lui seul doit savoir et que ce fichier ne peut pas contenir :

- **Ton mandat** : couvrir ton axe en tenant ton **budget d'effort** (le leader te le passe en clair depuis `casting.json`) — tant de sources ouvertes, tant de formulations essayées, tant atteintes sans passer par une liste de résultats. Tu rapportes ce qui tient, et **rien ne t'oblige à rapporter quelque chose** : zéro finding est un résultat valide, du remplissage ne l'est pas. Un vérificateur te dira lesquels passent. Tu as **5 tours max**.
- **Ton périmètre** : chasseur d'AXE → tu couvres **ton axe et lui seul**, via la tête PIR. Chasseur TRANSVERSAL → tu balaies **tout le sujet** sous ton angle.
- **Ne relance pas une requête déjà dans `queries-board.md`** — reformule ou change d'angle. Tu peux converger sur le même *finding* qu'un autre (bon) ; ne refais pas son *chemin*.
- **Plancher de valeur** : capacité nouvelle · limite réelle levée · saut coût/perf d'un ordre de grandeur · deadline qui oblige à agir. « X passe en version Y » sans l'un de ces deltas = bruit.
- **Exploite la mémoire de domaine** — promeut la watchlist, et cherche le vraiment nouveau hors du déjà-couvert.
- **Capture par finding** : titre **compréhensible seul** (FR, sans jargon, sujet nommé + fait concret en tête, jamais d'accroche à énigme) · URL réelle · **date vérifiée du fait + âge en jours** — **âge ≤ fenêtre de fraîcheur de ton axe** (casting `freshness` : 48h / semaine / mois). Au-delà : ne rends pas la piste, SAUF si `MÀJ`/`SUITE` d'un fil suivi (un fait daté rouvre un fil). Fraîcheur = couperet de capture, jamais critère de note. · domaine source · sources indépendantes listées séparément · 1 ligne de pertinence pour l'owner · tag de continuité `NEW` | `MÀJ:<fil>` | `SUITE:<entité>` | `PROMEUT:<signal>` · pour candidats disruptifs : **ce qui est bousculé, nommé, avec son fait daté**.
- **Gestes obligatoires (éliminatoires de méthode)** :
  - Ne JAMAIS écrire « je ne l'ai pas trouvé » / « aucune reprise » sans la requête qui le prouve. Une absence affirmée non cherchée est le défaut n°1.
  - Avant d'abandonner une source sur 403/429/404, essayer au moins un miroir : API publique du régulateur, `web.archive.org`, communiqué de presse correspondant, `r.jina.ai`. Deux chemins bloqués ne prouvent pas qu'une source est inaccessible.
  - **Muter l'ENTITÉ après deux reformulations** d'une même requête. Sept requêtes par le même chemin ≠ diversité.
- **Liste ORDONNÉE**, meilleur en premier (nécessaire à la fusion RRF).
- Sortie : `<base>/pistes-<chasseur>-T<n>.md`, numérotée avec préfixe unique. **NOM FIGÉ** — le leader ne renomme JAMAIS ce fichier (les outils de mesure en dépendent).
- Chaque piste de la fiche porte sa `tier` et sa `tier_justification` (cf. § La tier).

Carnet : chasseurs d'axe balaient en priorité les sources `trusted` de leur terrain ; transversaux sont poussés **hors carnet** — le signal faible et la contre-preuve ne vivent pas dans les sources déjà de confiance.

### Étape 4 — Après chaque tour : figer + vérifier

Pour chaque chasseur qui a rendu :

1. Copier `agent-<agentId>.jsonl` → `<base>/transcripts/chasseur-<n>-round<k>.jsonl`
2. Produire l'index par extraction (grep, jamais l'agent) → `.index.md`
3. Alimenter `queries-board.md` depuis l'index
4. Lancer un **vérificateur neuf** (`Agent`, jamais `SendMessage`), nommé `verif-<n>-round<k>`, avec :
   - grille complète et ancres
   - `selection-rules.md` + directives dures
   - archives (pour Delta — il doit **citer l'entrée comparée**)
   - candidats du tour
   - index de transcript + chemin du JSONL brut
   - consigne en deux passes : **méthode d'abord** (score conversation), **findings ensuite** (grille, un critère = un appel séparé)

Sortie du vérificateur → `<base>/verif-<n>-round<k>.md` :
- liste des findings qui passent (notes par critère, étiquettes)
- liste des recalés, **avec le motif par critère et l'ancre manquée**
- score de méthode + ce qui devrait changer au tour suivant
- compte courant : combien validés cumulés

5. Loguer les recalés définitifs dans `<base>/rejected.md` avec leur case (poids, disruptivité).

### Étape 5 — Relance ou arrêt

#### Le tour de correction doit ÉLARGIR, pas creuser

Mécanisme structurel : le vérificateur signale un manque **sur un finding**, le chasseur retourne **sur ce finding**, et un finding vit sur les sources où on l'a trouvé. **La boucle de correction concentre au lieu d'ouvrir**, sans que personne l'ait voulu. Un plancher chiffré (« touche N hôtes neufs ») ne réglerait rien — il serait coché comme une case. Ce qui manque est un **raisonnement**, rendu obligatoire et écrit.

#### La note de réouverture — obligatoire avant toute nouvelle requête

À chaque tour de correction, le chasseur écrit **d'abord**, dans `<base>/reouvertures/chasseur-<n>-round<k>.md`, et **avant d'émettre la moindre requête** :

1. **Pourquoi je n'ai pas trouvé au tour précédent.** Une phrase par finding rejeté. Deux réponses admises :
   - *« la chose n'existe pas »* → le finding est abandonné maintenant
   - *« je n'ai pas cherché là »* → la suite est obligatoire
2. **Où je n'ai pas regardé.** Liste des surfaces non touchées, nommées. Pas « ailleurs » : des hôtes, des interfaces, des types de sources.
3. **Ce que je vais tenter et qui n'est pas une variante de ce que j'ai déjà fait.** Reformuler une requête n'est pas élargir.

Le leader **injecte l'index du tour précédent** dans le prompt de relance — le chasseur voit noir sur blanc les hôtes qu'il a touchés.

**Le vérificateur du tour suivant lit cette note en premier** et la confronte au transcript : les surfaces annoncées ont-elles été réellement touchées ? Une note de réouverture non suivie d'effet est un manquement de méthode.

#### Rapport de vérification — au-delà des corrections

En plus du finding par finding :
- **les surfaces que le chasseur n'a pas touchées** et qui auraient pu porter la réponse
- **une question ouverte** plutôt qu'une seule liste de tâches : « qu'est-ce qui, dans ton terrain, n'a produit aucun candidat, et pourquoi ? »

Un terrain qui n'a rien donné est une information — invisible si on ne la demande pas.

#### Décision par chasseur

- **< son findings propre validés cumulés et < 5 tours** → relancer un chasseur **neuf** (`Agent`) sur le même mandat, avec dans son brief : le rapport du vérificateur, l'index du tour écoulé, ses pistes déjà rendues et les requêtes que le vérificateur a relevées dans sa session du tour écoulé. Il commence par sa note de réouverture.
- **≥ son findings propre validés** → il s'arrête. Ne pas le relancer pour du volume.
- **5 tours atteints sans le plancher** → **on le signale et on avance avec ce qui est passé.** Pas de 6e tour. Noter au rapport : chasseur, nombre atteint, score de méthode, lecture — terrain mince, ou chasse faible.

**GARDE-FOU** : les DEUX seules conditions d'arrêt d'un chasseur sont ci-dessus. Il n'y en a pas de troisième. Aucun plafond de livrable — le seul volume est `axes[i].findings` par chasseur. Ne jamais arrêter un chasseur sous son plancher avant ses 5 tours sous prétexte que « le pool total suffit », « rendement décroissant », ou « on a assez ». La cible de la phase est la somme des `findings` de tous les chasseurs validés ; un pool abondant n'est pas une raison de couper — il sert la diversité et le poids par convergence.

### Étape 6 — Fusion

Fusionner les listes validées par **Reciprocal Rank Fusion (k = 60)**. Score = Σ 1/(60 + rang) sur les listes où l'item apparaît.

- Quasi-doublons (même URL, titre très proche) fusionnés en une entrée.
- **`trouve_par: N` conservé** — mais N ne compte que les chasseurs y étant arrivés par des **chemins distincts** (vérifiable via `queries-board.md`). Deux chasseurs, même requête = 1.
- Les **notes du vérificateur voyagent avec le finding**. La distillation hérite et **ne renote pas**.

Sortie : `<base>/candidates.md`, renuméroté C1..CN, tags chasseur + score RRF + notes + étiquettes conservés.

### Étape 7 — Pré-filtre préférences (si modèle owner actif)

Le modèle tourne sur les titres du pool fusionné. Sortie : ligne JSON par candidat — `{title, p_liked, p_not_liked, active, drop}`. Si toutes les lignes portent `active:false` (ou `no_model`) → le modèle dort, ne rien changer.

**Le pré-filtre étiquette, il ne supprime pas.** Les candidats avec `drop:true` (P(pas aimé) > 75 %) sont **marqués `prefilter-doute`** dans `candidates.md` et listés dans `<base>/prefilter-flagged.md`, mais **restent dans le pool**. Motif : la conformité aux goûts appris est déjà notée par le vérificateur ; supprimer en plus pénalise deux fois la même dimension et referme la veille sur ce que le lecteur aime déjà.

### Étape 8 — Rapport de phase

```
Phase de chasse terminée — <owner> / <subject>

Chasseurs (N axes + 2 transversaux) :
  chasseur-axe-<slug> — <n> validés en 3 tours — méthode <score>
  chasseur-tv-signalfaible — <n> validés, 5 tours atteints — méthode <score>
  chasseur-tv-contrepreuve — <n> validés — méthode <score>
  ...
Total validés : <N>   (rejetés logués : <M> dans rejected.md)
Convergence : <k> findings trouvés par ≥2 chasseurs par chemins distincts
Concurrence : <N+2 chasseurs | mode décalé par vagues de ~5 — motif>
Transcripts : <base>/transcripts/ (<N> fichiers + index)
Requêtes : <N> distinctes, <M> doublons évités via queries-board
Pré-filtre préférences : <actif — N marqués prefilter-doute | en sommeil>

Étape suivante : la vérification de l'étape 2, puis le montage de la constellation.
Les findings arrivent déjà validés et notés. Ne pas re-vérifier, ne pas renoter.
```

---

## Règles dures

- **Le budget d'effort tenu**, par chasseur : sources ouvertes, formulations essayées, pages hors liste de résultats, hors moteur généraliste. Pas un nombre de findings. **Il se constate dans le transcript, jamais dans une déclaration du chasseur.** Le décompte est strict — les pages de résultats de recherche n'en font pas partie — et il n'y a pas de verdict indéterminé : sous le plancher, le chasseur repart.
- **5 allers-retours maximum.** Au-delà : signaler et avancer.
- **Deux conditions d'arrêt d'un chasseur, pas trois** : `≥ findings propre validés` OU `5 tours atteints`. Interdit de couper sous plancher avant 5 tours au motif « pool suffit / rendement décroissant / on a assez ».
- **Chasseur et vérificateur sont neufs à chaque tour** (`Agent`, jamais `SendMessage`). Ce qui passe d'un tour au suivant passe par des fichiers, jamais par un contexte d'agent.
- **Le transcript est copié par le leader**, brut et complet. Jamais un compte rendu rédigé par le chasseur. Il n'est pas indexé : le vérificateur le lit en entier, il ne le sonde pas.
- **Le poids ne conditionne pas le passage.** Constaté en ligne, étiqueté.
- **Le signal faible est porté par le chasseur transversal dédié** (tête Ansoff), plus par quota distribué.
- **Le recouvrement de findings est bon, le recouvrement de requêtes ne l'est pas.** `queries-board.md` avant chaque tour.
- **Récence = poids, pas filtre.** Capturer l'âge, ne pas exclure sur la date.
- **Jamais de findings déjà livrés** — déduplication dure contre les 3 archives ; le critère Delta l'impose aussi (0 = exclut).
- **Rien ne disparaît en silence** — tout écarté logué avec son motif et sa case.
- **Plafond ~10 agents actifs, avec garde-fou.** Au-delà : mode décalé par vagues de ~5, et le dire.
- **La largeur vient du moteur** (odeur + parcelle + diversification + requête oblique). Nombre d'hôtes distincts mesuré et reporté, non bloquant.
- **Le coût n'est pas un critère.** Ni le temps, ni les tokens.
- **Une page se TÉLÉCHARGE et se lit ; `WebFetch` rend un résumé, pas la page.** Toute affirmation que tu poses dans une fiche doit venir d'un texte que tu as lu toi-même — voir « Lire une page » ci-dessous. Une reformulation depuis un résumé produit une faute grave au contrôle, qui juge sur la page téléchargée.

## Lire une page — télécharge-la, ne la fais pas résumer

**`WebFetch` ne te rend PAS la page.** Il la fait lire par un **petit modèle** qui répond à la question posée : ce qu'il n'a pas recopié n'existe plus pour toi, et tu ne sauras jamais ce qu'il a omis. Une durée, un chiffre, une réserve — c'est exactement ce qui saute au résumé, et exactement ce qu'une fiche affirme.

**Ta voie par défaut est donc le téléchargement**, et tu lis toi-même :

```bash
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "<url>" -o /tmp/p.html
```

puis `Grep` / `Read` dessus. **Un `403` de `WebFetch` ne dit rien du site** : les mêmes URL répondent `200` en téléchargement avec cet en-tête de navigateur — ne renonce jamais à une source sur ce seul signal.

**Si le téléchargement échoue vraiment** : `https://r.jina.ai/<url>` (rend le texte complet), puis `web.archive.org`. **`WebFetch` en tout dernier recours** — et ce que tu en tires, tu l'écris dans la fiche **comme venant d'un résumé**, jamais comme une citation de la page.

**Une page de résultats de recherche n'est jamais une source.** Son résumé non plus : il est écrit par le moteur, il n'atteste rien.

*Ce que ça change concrètement : le contrôle de l'étape télécharge la page et y cherche ta chaîne. Une phrase reformulée depuis un résumé — « deux mois » là où la page écrit « in its first month » — n'y est pas, et c'est une faute grave qui renvoie ton lot en réparation.*

## Budget d'EFFORT (remplace le quota de sortie)

Ce qui est imposé, c'est **combien tu cherches**, pas **combien tu rends**. Un agent libre de s'arrêter quand il veut satisfait trop vite : il prend les 3 premiers résultats et s'arrête. Un quota de sortie, lui, fabrique du remplissage — tu rends 5 pistes même quand il n'y en a qu'une de valable.

**Plancher d'effort, par chasseur et par tour (non négociable)** :
- **≥ 15 sources distinctes réellement ouvertes.** Une source ouverte est une **page que tu as TÉLÉCHARGÉE et lue toi-même** — `curl` puis `Grep`/`Read`, ou `gh api`. **Une recherche n'ouvre rien** : `WebSearch` rend des titres et des URL, et son résumé, si étoffé soit-il, n'est attribuable à aucune page. **`WebFetch` n'ouvre rien non plus** — il rend le résumé d'un petit modèle, pas la page (cf. « Lire une page » ci-dessous) : une page dont tu n'as lu que le résumé ne compte pas dans ce plancher.
- **≥ 8 requêtes** de formulations différentes — pas 8 variantes du même mot-clé : varie l'angle (nom de l'acteur, nom du mécanisme, chiffre attendu, formulation d'un sceptique, terme en anglais et en français).
- **≥ 5 sources hors première page** de résultats — c'est là que vit ce que tout le monde rate.
- **≥ 3 sources hors moteur généraliste** : site d'un acteur, papier, changelog, forum, archive du domaine.

**Sortie LIBRE** : tu rends autant de pistes que tu en as trouvé qui tiennent — **zéro compris**. Rendre zéro piste après un effort complet est un résultat valide et utile ; rendre du remplissage ne l'est pas.

**Si tu rends moins de 3 pistes**, écris en une phrase pourquoi : rien de neuf sur la période, sujet saturé, ou signaux tous déjà livrés. Cette phrase vaut mieux que trois findings tièdes.

**Tu ne tiens aucun journal d'effort.** Ton effort se lit dans ta session : chaque requête, chaque
page ouverte, chaque hôte y figure déjà, horodatés et dans l'ordre. La vérification de l'étape les
compte là, et nulle part ailleurs — un effort sous le plancher fait repartir le chasseur, quel que
soit le nombre de pistes rendues. Écrire une deuxième fois ce que la session montre déjà ne prouve
rien de plus et se paie cher.
