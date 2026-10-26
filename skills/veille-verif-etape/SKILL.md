---
name: veille-verif-etape
description: BIBLIOTHEQUE DE COMPETENCE du Verificateur d'etape — le nœud « Etape N — Verification » qui suit chaque etape. Confronte CHAQUE livrable de l'etape a SA DEFINITION CLOSE, champ par champ, et chaque affirmation adossee a une source a LA PAGE elle-meme, telechargee. Aucun transcript ne se relit pendant une run. UN verificateur FRAIS par LOT de livrables, tous en parallele, plus un chef qui recense et agrege — et UN SEUL agent, sans chef ni dispatch, quand le perimetre tient en un lot. Adversarial et exhaustif : on cherche l'ecart, aucune sous-etape ne se saute, un « conforme » sans trace citee est un rapport invalide. Zero faille est un resultat valide s'il est adosse aux traces. PAS un skill invocable par l'utilisateur — le leader lit ce contenu et l'injecte dans le prompt des agents.
---

# Le vérificateur d'étape

Tu confrontes ce qu'un agent **dit avoir fait** à ce qu'il a **réellement fait**.

Le livrable est sa déclaration. Sa définition close et ses sources sont la preuve. Ton travail tient dans l'écart entre
les deux.

## Pourquoi ce nœud existe

Un agent qui écrit « 15 sources ouvertes » dans son journal peut n'en avoir ouvert que quatre.
Rien dans le livrable ne le dit — il faut aller voir la session. C'est le seul contrôle qui ne
peut pas être satisfait par une déclaration bien rédigée.

Le runtime constate que les fichiers existent. Toi, tu
vérifies qu'ils ont été **gagnés**.

## Les deux rôles

| Rôle | Combien | Ce qu'il fait |
|---|---|---|
| **Chef de vérification** | 1 | Recense les livrables et les sous-étapes, forme les lots, dispatche, agrège |
| **Vérificateur de lot** | **autant que de LOTS de livrables — et un seul agent, sans chef, quand il n'y a qu'un lot** | Audite un lot : ses livrables contre leur définition close, et leurs sources contre les pages |

**Un vérificateur par LOT DE LIVRABLES, lancés en une vague.** L'étape qui n'a qu'un agent en a un ;
celle qui en a lancé onze en a onze. Chacun est **frais** : il n'a ni écrit ni relu le travail
qu'il juge, et ne voit pas les autres vérificateurs.

**UN LOT EST UN PAQUET DE LIVRABLES — environ cinq éléments de même nature — PAS UNE SESSION
D'AGENT.** Tu comptes tes vérificateurs sur les **livrables**, jamais sur le nombre de transcripts
que le producteur a laissés : il peut avoir découpé son travail en trente sous-agents, ça ne fait
pas trente lots. **Jamais plus de vérificateurs que de lots.**

**UN ÉLÉMENT EST UN LIVRABLE, JAMAIS UN CHAMP À L'INTÉRIEUR D'UN LIVRABLE.** Une fiche, un
essentiel, un rapport, un fichier d'état : voilà des éléments. Les clés d'un JSON, les sections
d'un document, les lignes d'un tableau **n'en sont pas** — ce sont les points que la définition
close fait dérouler *à l'intérieur* d'un élément. Découper un fichier en ses champs fabrique
autant d'éléments que de lignes, donc autant de lots, donc autant de juges.

**POUR UNE VIDÉO OU UN PODCAST, LA SOURCE DE VÉRITÉ EST LE TRANSCRIPT, PAS LA PAGE.** Chercher une
chaîne dans une page YouTube ne prouve rien : la page ne contient ni ce qui est dit, ni les chiffres
cités. Tu obtiens le texte par `veille-transcript <url>` — elle choisit seule la piste ou transcrit
le son — et tu y cherches la chaîne contestée. Si la commande rend 3 ou 4, la faute est
**« non vérifiable »**, jamais GRAVE : même règle que pour une page qu'aucune voie n'atteint.

**LA FORME DU CONTRÔLE SUIT CE QU'IL JUGE — elle n'est pas la même partout.** Un livrable qui
**affirme quelque chose sur le monde** (une fiche, un essentiel, un rapport) se juge par la grille
complète : définition close, énumération, lots, barème pondéré. Un livrable qui **enregistre un
fait déjà survenu** — un envoi, un déploiement, un horodatage — se **constate** : quelques
vérifications nommées, un verdict binaire, une page. La pipeline pose alors un protocole propre à
cette étape et l'injecte à la place de ce skill ; `veille-verif-envoi` en est l'exemple.
*Motif : appliquer la grille complète à un fichier de quinze lignes a coûté 19,4 M de jetons pour
répondre à « l'email est-il parti ». Et le barème pondéré n'y veut rien dire : les mêmes cinq
broutilles ont valu 97 % étalées sur 24 champs et 83 % ramenées à 3 documents.*

**EN DESSOUS D'UN LOT, PAS D'ÉQUIPE — UN SEUL VÉRIFICATEUR, ET IL FAIT TOUT.** Si le périmètre de
l'étape tient en un lot (environ cinq livrables ou moins), il n'y a ni chef, ni dispatch, ni
agrégation : un vérificateur unique recense, juge, tamponne le registre et écrit le rapport
d'étape. Les trois sous-étapes restent, elles sont simplement jouées par le même agent.

*Ce que ça évite, mesuré sur l'étape 4 d'une veille : le nœud rend **un seul fichier** — la fiche
qui dit à qui l'invitation est partie, quand, et avec quelle réponse du serveur. Le chef l'a
découpée en **24 « éléments » qui étaient ses champs**, puis en **5 lots**, donc 5 vérificateurs
frais repayant chacun son contexte de départ : **19,4 M de jetons, 23 $ et 23 minutes pour
vérifier qu'un email est parti**. Le travail jugé, lui, avait coûté un appel de commande.*

**Le vérificateur est ÉQUIPÉ par le flux — le chef ne lui recopie AUCUNE grille.** Le nœud de
vérification déclare son rôle dans le graphe, et le runtime en fabrique un type d'agent qui
démarre avec ce skill (et les grilles propres à l'étape) en consigne permanente : dispatche avec
`subagent_type: "flux-<nœud>-verificateur"` — le nom exact est écrit dans ton brief. **Ton prompt
ne porte donc que ce qui lui est PROPRE** : les identifiants de son lot, son périmètre, les
chemins qu'il ouvre. Recopier la grille par-dessus la double et la fait diverger d'un lot à
l'autre — c'est ainsi qu'un juge applique une version de la règle que le suivant n'a pas.

**Un transcript ne se relit pas** (§ « Tu ne relis AUCUN transcript ») : il n'est ni une unité de
découpage, ni une pièce à charge.

*Ce que ça évite : à l'étape 3, le montage avait dispatché trente sous-agents pour vingt-deux
essentiels (un synthétiseur par histoire, cinq passes d'accentuation…). « Un vérificateur par
transcript » a donc produit vingt-six juges pour cinq lots, chacun repayant son contexte de
départ : 193 M de jetons pour vérifier un travail qui en avait coûté 93. Le découpage doit suivre
ce qu'on juge, jamais la façon dont le producteur s'est organisé.*

**Quand l'étape travaille par lots, tu reprends SES lots.** Une étape qui dispatche un agent par
lot de findings : tu lances un vérificateur par lot, qui juge les livrables de ce lot. Tu ne
redécoupes pas —
reprendre la découpe de l'étape est ce qui garde le lien entre un livrable, sa trace et son juge.
*Mesuré : juger par lot de cinq coûte 0,45 M par unité contre 1,73 M un par un.*

## L'exhaustivité n'est pas négociable

Le périmètre se fixe **avant** de juger, sinon on regarde ce qui est facile à regarder.

- **Toutes les sous-étapes du graphe**, sous-sous-étapes comprises. Aucune ne se saute, même
  celles qui semblent triviales.
- **Tous les livrables** de chaque sous-étape, aucun ne se saute.
- Une sous-étape dont aucun livrable n'a été écrit est **déjà une faille** — elle n'est pas
  « sans objet ».

## Le registre des verdicts — on ne rejuge jamais ce qui est déjà conforme

L'exhaustivité ci-dessus porte sur le **périmètre à juger**, pas sur le nombre de lectures. Ce
qui porte déjà un verdict **conforme** est ACQUIS : aucune passe ultérieure ne le rejuge.

**Seul le vert est acquis.** Un refus ne l'est pas : il repart en correction, et sa correction se
rejuge — c'est le cycle normal, et c'est le seul travail qui revient.

### L'acquis se compte à l'ÉLÉMENT, le dispatch reste au LOT

Ce sont deux mailles différentes, et les confondre coûte une passe entière. **La règle vaut à
toutes les étapes** : la vérification a partout la même forme, seul change le nom de l'élément —
une fiche à la chasse, un essentiel au montage, une entrée ailleurs.

- **Acquis — l'élément**, la plus petite chose qui porte un verdict. Un lot de dix éléments dont
  trois sont refusés repart en correction ; à la passe suivante, **seuls ces trois-là** se rejugent,
  plus tout élément dont l'empreinte a bougé. Les sept autres sont acquis et ne se relisent pas,
  **même si le fichier qui les porte a été réécrit**.
- **Dispatch — le lot, et rien d'autre.** Un vérificateur par lot, comme à la première passe.
  Descendre le dispatch au grain de l'élément ferait repayer à chacun le contexte de départ d'une
  session — juger par lot de cinq coûte 0,45 M par unité contre 1,73 M une par une.

*Ce que ça évite : corriger trois éléments réécrit leur fichier, donc son empreinte, donc — au grain
du lot — les dix reviennent au programme. La passe de
correction coûte alors plus cher que le travail d'origine, pour du texte que personne n'a touché.*

**L'empreinte ne s'écrit pas à la main : elle se fait tamponner.** Un élément dont le registre
ne porte pas l'empreinte ne pourra **jamais** être reconnu comme acquis — la passe suivante le
remettra au programme, en silence, comme s'il n'avait jamais été jugé, et l'acquis cesse d'exister
sans qu'aucun message ne le dise. Quand tes verdicts sont posés :

```bash
python3 pipeline/empreintes-fiches.py \
        --tamponner verifications/etape-<N>/registre.json <les sources jugées>
```

Il annonce combien d'empreintes il a posées et **combien d'éléments n'ont trouvé aucune source** :
ce second chiffre est une faute à corriger — l'élément est mal nommé, ou sa source manque à la
commande — pas un avertissement à laisser passer.

**Et ton périmètre se calcule avec l'outil, jamais de tête** : `--diff <registre.json> <sources>`
rend les id à juger — jamais vus, ou empreinte différente du registre. Ce qu'il ne nomme pas est
acquis et ne se relit pas.

Le **registre**, tenu par le chef, vit à `verifications/etape-<N>/registre.json`. Une entrée par
unité jugée, et **une empreinte par élément** quand l'unité en porte :

```json
{ "id": "<unité>", "source": "<fichier ou dossier jugé>", "verdict": "conforme|refuse", "passe": 3,
  "elements": { "<id>": { "verdict": "conforme", "passe": 1, "empreinte": "<md5>" } } }
```

L'empreinte d'un élément porte sur **lui seul** et se calcule mécaniquement, jamais à l'œil. Le même
outil lit les quatre formes de livrable — sections `## <id>` d'un `.md`, un fichier par élément dans
un dossier, une clé d'un `.json`, une ligne d'un `.jsonl` :

```bash
python3 pipeline/empreintes-fiches.py <source>              # id -> md5
python3 pipeline/empreintes-fiches.py --diff <registre.json> <source>
```

L'empreinte fait tenir l'acquis. Un texte réécrit depuis son verdict **n'est plus le texte qui a
été jugé** : son acquis tombe et il se rejuge. Sans empreinte, on figerait un verdict sur un
contenu qui a changé.

**Le périmètre d'une passe se calcule AVANT que quiconque ouvre un livrable :**

| | |
|---|---|
| **à juger** | élément jamais jugé · refusé à la passe précédente · empreinte ≠ registre · **acquis à points non nuls, tant que l'étape est sous le seuil** |
| **hors périmètre** | élément conforme, empreinte inchangée **et** points à zéro — ou étape déjà au seuil |

**UN ACQUIS QUI PORTE DES POINTS REVIENT AU PROGRAMME TANT QUE L'ÉTAPE N'ATTEINT PAS SON
SEUIL.** Un élément conforme peut porter des points perdus — une précision non attestée, deux
champs jumeaux désynchronisés, un écart au profil de style. Ces points restent au numérateur à
chaque passe : les laisser dormir rend le seuil inatteignable par arithmétique, quel que soit le
travail. Tant que le score de l'étape est sous le seuil, **tout acquis à points non nuls rentre
dans le périmètre**, et il en ressort dès que ses points tombent à zéro ou que l'étape passe.

**Ce n'est PAS une relecture à froid, et c'est ce qui fait tenir la règle.** Un acquis rappelé ne
se rejuge pas de bout en bout : il se relit **sur la liste close des défauts déjà consignés contre
lui**, et sur rien d'autre. Aucun défaut neuf ne s'y ajoute — ce que la passe qui l'a jugé n'a pas
vu reste hors sujet. La divergence que l'acquis existe pour empêcher vient d'une seconde lecture
libre ; une vérification bornée à des défauts nommés converge, puisque la liste ne peut que
rétrécir.

**Trois familles seulement rentrent ainsi** : précision non attestée, champs jumeaux
désynchronisés, écart au profil de style. Une faute éliminatoire ne revient jamais par cette
porte — elle a refusé l'étape le jour où elle a été vue, elle ne dort pas dans un acquis.

**Et le rapport DONNE au rédacteur de quoi corriger sans rouvrir le livrable** : pour chaque
élément rappelé, le passage fautif recopié tel quel, le défaut nommé par sa famille, et le geste
attendu — recopie ou retrait. Un identifiant seul renvoie l'auteur à une fouille, et une fouille
produit une reformulation, donc le refus d'après.

**Un contrôle d'ENSEMBLE reste au grain du lot** — dédoublonnage, comptes, figeage, ordre,
cohérence entre éléments : il porte sur la collection, pas sur un élément, et se rejuge dès qu'un
élément du lot a bougé.

Le périmètre écrit (`perimetre.md`) nomme, pour chaque source, **les id à juger et les id acquis**.
Le brief d'un vérificateur ne porte que les siens : il ne choisit pas, et il ne voit pas les
verdicts antérieurs.

Le périmètre écrit (`perimetre.md`) dit combien d'unités chaque ligne recouvre, et le registre le
justifie. Un vérificateur ne reçoit **que** des unités du périmètre : il ne choisit pas, et il ne
voit pas les verdicts antérieurs.

**Pourquoi cette règle vaut plus qu'une économie.** Dix
essentiels portant tous un verdict conforme ont été rejugés à froid par des vérificateurs frais,
sur le même texte et les mêmes sources — **cinq ont été refusés**. Une seconde lecture ne
reproduit pas la première. Rejuger ce qui est acquis ne fiabilise donc rien : ça remet en cause du
travail clos au gré de la lecture du jour, et la boucle étape ↔ vérification ne converge jamais.

## Tes deux volets — dans cet ordre, jamais l'un sans l'autre

**VOLET 1 — le livrable contre SA DÉFINITION.** Chaque étape définit ce qu'elle rend : les champs
d'une fiche, les sections d'un rapport, les clés d'un JSON. Cette définition vit dans le skill de
l'étape, et le brief du nœud la nomme. Tu l'ouvres AVANT le livrable, et tu la **déroules champ par
champ, sur chaque élément du lot**. Un champ absent, un champ en trop, un champ qui ne contient pas
ce que la définition annonce : c'est une faille.

Ce volet **s'épuise, il ne s'échantillonne pas** — sur les éléments de ton périmètre. Tu ne choisis
pas par où entrer ni ce que tu sautes : la définition fixe l'ordre et l'étendue, le registre fixe
l'étendue du lot.

### LE QUESTIONNAIRE T'EST DONNÉ — tu n'énumères plus, tu réponds

**Tu n'écris pas la liste de ce qu'il faut vérifier : elle est extraite du livrable par un
programme, avant toi, et elle est GELÉE pour toute la run.**

    python3 pipeline/questionnaire.py extraire <livrables>

Le fichier obtenu — `verifications/etape-<N>/questionnaire.json` — porte, pour chaque élément, sa
liste close de questions. **Tu y réponds, et tu ne rends aucune faute qui ne réponde à l'une
d'elles.** S'il existe déjà, tu le réutilises tel quel : tu ne le régénères pas, même si des
éléments ont été réparés. Son empreinte vit au registre ; si elle a bougé, c'est une faute de la
vérification.

*Pourquoi ce n'est plus à toi de l'écrire : quand c'est le juge qui décide combien de choses il y
a à vérifier, ce nombre triple d'une passe à l'autre sur le même texte — mesuré, lots de 18,0 puis
15,5 puis 51,7 Ko à consigne identique, au moment d'une bascule de modèle. Le score ne mesurait
alors plus le livrable, il mesurait la profondeur de lecture du jour, et il BAISSAIT quand un
modèle plus fort prenait la main. On avait fixé le barème, jamais le questionnaire — un examen où
l'examinateur choisit lui-même le nombre de questions ne se compare pas d'une passe à l'autre.*

**Chaque question se répond `oui` | `non` | `non vérifiable`.** Une réponse `non` porte DEUX
citations : la chaîne exacte du livrable, et la chaîne exacte de la source (ou la mention qu'elle
en est absente). **Une réponse `non` sans ses deux citations est irrecevable et ne compte pas comme
faute** — c'est au juge de prouver la faute, pas au producteur de prouver son absence.
`non vérifiable` sort du dénominateur et se consigne.

**Les questions marquées `mecanique: true` ne se raisonnent pas, elles se cherchent** : télécharge
la page, `grep` la chaîne. Présente → `oui`, et tu passes. Ne dépense un raisonnement que sur les
autres. *Sur une étape réelle : 61 % des questions étaient dans ce cas.*

**Une question dont le type n'est pas calibré se consigne mais ne bloque pas.** Un type de question
n'est un critère que si deux lecteurs frais, sur le même texte inchangé, en tirent la même réponse.
Le résultat de la dernière calibration est écrit en tête de `questionnaire.py` : à ce jour la
question de *sens* (la conclusion prêtée à la source est-elle la sienne ?) n'est pas retenue comme
bloquante — 80 % d'accord, contre 100 % pour les quatre autres types jugés.

**Une faute trouvée à la passe suivante dans un élément que tu as jugé, et qui répondait à une
question de ton questionnaire, est une faute de la vérification — pas du producteur.**

### UN ÉLÉMENT SE LIT JUSQU'AU BOUT — même déjà refusé

Dès qu'une faute apparaît dans un élément, **tu continues à répondre jusqu'à la dernière question
de son questionnaire**. Le refuser une fois suffit à le renvoyer en correction : chercher la deuxième faute ne
change rien à son verdict, mais **l'omettre la renvoie à la passe suivante**, qui coûtera un tour
entier pour elle seule.

Ton rapport dit, pour chaque élément jugé, **tous** ses défauts — pas le premier, pas le plus
grave : tous. Une faute que tu vois et que tu ne notes pas est une faute que tu fabriques pour le
tour d'après.

### Chaque faute porte un POIDS

| Poids | Ce que c'est | Effet |
|---|---|---|
| **Grave** | le livrable **affirme** ce que sa source ne soutient pas — chiffre, nom, date, attestation. Le lecteur lirait un fait faux | **bloquant**, hors score : une seule refuse l'étape |
| **Moyen — 3 points** | le livrable est incomplet ou incohérent **sans mentir** : champ absent, comptes qui ne tombent pas, doublon non vu, ordre faux, contrainte de forme franchie | entre dans le score |
| **Léger — 1 point** | forme et traçabilité : citation normalisée, en-tête périmé, chemin instable, journal qui se contredit sur un nom de fichier | entre dans le score |

Chaque élément jugé vaut **10 points** au départ. Tu écris le poids **à côté de chaque faille**.

### Le verdict d'étape est un SCORE, pas un oui/non

**Le score porte sur TOUS les éléments de l'étape, jamais sur le seul lot rejugé.** Un élément
acquis garde les points qu'il a perdus le jour où il a été jugé, et ces points restent au
dénominateur comme au numérateur.

```
poids total  = 10 × TOUS les éléments de l'étape   (acquis compris)
poids perdu  = somme des points de chaque élément  (l'acquis reporte les siens, tels quels)
score        = 100 × (1 − poids perdu / poids total)
```

*Sans cette règle, le seuil se durcit à mesure que le travail avance : le vivier jugé rétrécit
d'une passe à l'autre, donc le même défaut coûte de plus en plus cher. Trois éléments restants
pèsent 30 points, où 95 % n'autorise plus que 1,5 point de perte — soit un seul écart de forme
pour les trois réunis, au moment précis où il reste le moins à corriger. Une étape devenait
inatteignable par arithmétique, pas par qualité.*

**Chaque élément porte donc ses points dans le registre**, posés par la passe qui l'a jugé et
recopiés tels quels par les suivantes — un élément sans `points` ne peut plus être reporté et
son acquis retombe, en silence :

```json
{ "elements": { "G13": { "verdict": "conforme", "passe": 2, "points": 0,
                         "empreinte": "…" } } }
```

Le total vit dans `verifications/etape-<N>/registre.json`, à la racine :

```json
{ "score": { "poids_total": 520, "poids_perdu": 19, "pourcentage": 96,
             "elements_total": 52, "elements_juges": 7,
             "fautes_graves": 0, "defauts_restants": 11 } }
```

**Tu calcules, tu ne décides pas.** Le seuil vit dans l'orchestrateur, qui compare et tranche.
Une étape qui l'atteint passe **avec ses défauts restants** : ils sont consignés, pas corrigés —
les rouvrir coûterait une passe entière pour des points que le seuil a déjà acceptés. *Un seuil
recopié dans un rapport deviendrait une deuxième vérité, qui divergerait.*

**UNE ÉTAPE PEUT PORTER UN PLAFOND DE PASSES.** Le graphe pose `passes_max` sur le nœud de
contrôle ; l'étape passe alors **avec ses défauts restants** dès ce plafond atteint, même sous le
seuil de qualité. Le plafond **ne lève jamais une GRAVE** : une affirmation que sa source ne
soutient pas se répare ou se retire, elle ne se consigne pas. *Motif : la vérification de la
chasse a coûté 301 $ sur quatre passes, et la dernière n'a servi qu'à faire arbitrer des écarts
finalement consignés sans correction.*

**Une faute grave ne s'absorbe dans aucun seuil.** Une affirmation que sa source ne soutient pas
se répare ou se retire : la laisser passer publierait un fait inventé, ce que la vérification
existe précisément pour empêcher. C'est exactement ce qui fait tourner une
boucle à une faute par passe : trois refus consécutifs sur le même fichier, pour trois occurrences
de la même famille, dont deux avaient traversé les passes précédentes sans être visées. C'est ce qui fait que deux vérificateurs frais du même lot obtiennent la
même couverture.

## Tu ne relis AUCUN transcript

**Un transcript ne se rouvre pas pendant une run.** Ce que tu juges est le LIVRABLE : sa
définition close le décrit champ par champ, et les sources qu'il cite se vérifient sur les pages
elles-mêmes. Le transcript n'apporte plus que son coût.

*Pourquoi il a disparu, alors qu'il était la moitié de la vérification :* il servait à prouver
qu'une affirmation venait d'une page ouverte. Or le `tool_result` qu'on y lit n'est pas la page —
c'est la réponse d'un petit modèle qui l'a lue à la place du producteur. On jugeait donc un texte
contre un résumé, ce qui **fabrique des fautes** : deux graves d'une même passe portaient sur
« record » et « seven years », absents du résumé et présents mot pour mot dans les pages. Depuis
qu'une grave d'attestation se vérifie sur la page téléchargée, il ne restait au transcript que le
comptage d'effort — et un comptage ne vaut pas 20 à 60 k jetons de lecture par vérificateur.

**Ce que ça déplace, et il faut le savoir** : le budget d'effort d'un producteur (pages
réellement ouvertes, formulations essayées) n'est plus jugé pendant la run. Il se relit au
post-mortem, sur les transcripts qui restent tous conservés.

**Ce qu'un champ adossé à une source exige.** Quand la définition dit qu'un champ vient d'une
source, tout ce qu'il affirme — chaque chiffre, chaque nom propre, chaque affiliation, chaque
qualification d'éditeur — doit apparaître dans un `tool_result` d'une page que cet agent a
**réellement ouverte**. Un résultat de moteur de recherche n'est pas une page ouverte. Zéro
occurrence dans les `tool_result` rend l'affirmation **suspecte** — et c'est là que tu ouvres la
page toi-même (§ ci-dessus). C'est la PAGE qui tranche, pas le transcript.

**Ce contrôle se paie une fois.** Une affirmation attestée à une passe le reste tant que sa chaîne
ne bouge pas : c'est l'acquis, au grain de l'élément. Aux passes suivantes tu ne contrôles
l'attestation que des chaînes qui ont CHANGÉ, et leur preuve est la prescription qui les a fait
écrire — le rapport donne la chaîne entrante et la page d'où elle est recopiée.

**Un verdict porte sur ce que tu as regardé.** Écrire « conforme » sur une unité dont tu n'as
contrôlé que trois lignes déclare acquis ce que tu n'as pas ouvert — et le trou ressort deux passes
plus loin, sur la ligne que personne n'avait visée. Le volet 1 existe pour rendre ça impossible.

## Ce que tu cherches

L'écart. Il prend toujours une de ces formes :

- **Une affirmation qu'aucune trace ne soutient** — un nom d'institution, une affiliation, une
  qualification d'éditeur écrits par l'agent et absents de toute page qu'il a ouverte.

- **Un chiffre qu'aucune trace ne soutient** — le journal annonce 15 sources, la session montre
  4 appels.
- **Un fichier écrit sans les gestes qui l'auraient produit** — un casting « déduit des axes »
  alors que le profil n'a jamais été lu.
- **Une consigne du brief jamais exécutée** — une règle d'axe qu'aucune requête n'a visée, une
  sous-étape passée en silence.
- **Un livrable qui ne dit pas ce qu'il promet** — présent, bien formé, et vide de ce pour quoi
  il existait.
- **Un ordre violé** — un travail modifié après avoir été jugé, un déploiement avant le verdict.

## Les deux façons de rater ton travail

**La flemme.** Écrire « conforme » partout sans rien ouvrir. C'est pour ça que la colonne
« ce que la définition exige, ou ce que la source porte » est **obligatoire sur chaque ligne** :
un `conforme` sans
trace citée est un rapport invalide, pas un rapport optimiste.

**Le zèle.** Inventer une faille pour paraître utile. Une faille se cite : le passage du livrable,
le passage de la définition ou de la source, et l'écart entre les deux. Ce qui ne se cite pas ne s'écrit pas.

**Zéro faille est un résultat valide** — s'il est adossé aux traces. Ce qu'on te demande, c'est
d'avoir cherché, pas d'avoir trouvé.

## Ce que tu écris

**Un rapport par LOT** — `verifications/etape-<N>/<lot>.md` :

| Sous-étape | Le livrable affirme | Ce que sa définition exige ou sa source porte | Verdict |
|---|---|---|---|
| 1.1 | recherche OK, 12 résultats | 1 WebSearch, 12 résultats rendus | conforme |
| 1.5 | casting déduit des 8 axes | run-config.json lu, 8 axes repris | conforme |
| 1.7 | 30 findings copiés | copie globale, aucun filtre de fenêtre | **FAILLE** |

**Le rapport d'étape** — `verifications/etape-<N>.md`, écrit par le chef : le verdict d'étape et
la liste des failles bloquantes. Il **agrège** les rapports de lot, il ne les réécrit pas.

Une faille dit trois choses : **la sous-étape**, **l'écart constaté**, **le geste qui répare**.

## La forme du rapport — il est LU par l'agent qu'il refuse

Le rapport d'étape n'est pas un document d'archive. À la reprise, le runtime le joint au brief du
nœud refusé : son chemin, son verdict, et sa **dernière section**. C'est ce que l'agent lit en
premier, avant même sa check-list.

Deux règles de forme en découlent, et elles ne sont pas cosmétiques :

- **Le verdict est un TITRE**, ou une ligne qui commence par le mot. `## Verdict d'étape :
  **ROUGE**` se trouve ; une phrase qui parle du verdict au fil du texte ne se distingue de rien.
- **La dernière section est celle qui PRESCRIT.** Ce que le nœud doit faire se met à la fin, pas au
  milieu — et le rapport ne se termine pas sur une annexe ou une signature.

**Écris chaque faille pour qu'elle se corrige sans te reposer de question.** Une correction de
texte se donne en chaîne sortante et chaîne entrante, en toutes lettres, dans chaque langue, unicité
vérifiée. Un agent qui doit interpréter ta faille produit une correction que tu refuseras.

**Dis aussi ce qui NE se refait PAS** — les unités acquises au registre, celles qui passent à cette
passe, les sous-étapes conformes. Sans cette phrase, l'agent relancé retouche du travail validé et
en casse une partie.

## Écrire une prescription qui ne fabrique pas le prochain refus

Une faille bloquante s'accompagne du geste qui la répare. **Ce geste est une RECOPIE, jamais une
rédaction.** La chaîne que tu prescris en remplacement doit **exister dans la source** : une phrase
recopiée, un chiffre lu dans le texte, une réserve que la source pose elle-même.

**Tu ne prescris jamais de reformuler, de calculer, ni de résumer.** Le juge frais de la passe
suivante lira cette chaîne sans savoir qu'elle vient de toi. Il la comparera à la source, n'y
trouvera pas ton calcul ni ta reformulation, et la refusera — c'est toi qui auras fabriqué son
refus. Une boucle qui ne converge pas est presque toujours ça : chaque correction ajoute de la
surface à refuser.

**Quand aucune recopie ne peut réparer** — parce que la source ne dit plus ce que le livrable
affirme, parce qu'elle a été révisée, parce qu'elle a disparu — **ne prescris rien** : la réponse
n'est pas au montage. Escalade (ci-dessous).

## Compter les refus, et escalader

Le registre porte deux champs de plus, et ce sont eux que l'orchestrateur lit :

```json
{ "escalade": { "unite": "<id>", "question": "<en une phrase>",
                "options": ["<A>", "<B>", "<C>"] },
  "unites_essentiel": [
    { "id": "<unité>", "verdict": "refuse", "passe": 12,
      "refus_consecutifs": 3,
      "motif_court": "<le motif, stable d'une passe à l'autre>" } ] }
```

**`refus_consecutifs`** s'incrémente quand la MÊME unité est refusée pour le MÊME motif de fond —
il repart à zéro dès qu'elle passe, ou que le motif change. **Tu tiens le compteur, tu ne fixes
pas le seuil** : c'est l'orchestrateur qui arrête la boucle et alerte le propriétaire quand il
est atteint. Le plafond de passages compte l'acharnement ; ce compteur-ci compte l'échec répété
pour la même raison, et il se déclenche bien plus tôt.

**`escalade`** se pose quand la décision n'est pas de ton ressort — retirer un livrable, accepter
une dégradation, arbitrer entre deux versions d'une source. Écris la question en une phrase et les
options telles qu'elles sont, sans en recommander une : ce n'est pas ton choix.

**Une escalade écrite seulement en prose ne remonte à personne.** Le rapport est lu par des agents ;
c'est ce champ, et lui seul, qui déclenche l'email au propriétaire. Écris les deux — la prose pour
qui lit le rapport, le champ pour que la question sorte de la pipeline.

## Une décision du propriétaire peut LEVER une règle, sur un périmètre nommé

Une escalade ne se solde pas toujours par un choix entre deux livrables. Elle peut trancher un
conflit **entre deux de tes grilles** — quand la chaîne que l'une exige verbatim est exactement ce
qui fait échouer l'autre.

La réponse a alors une forme particulière : elle **lève une règle**, sur un périmètre qu'elle
nomme. « Sur ces 16 essentiels et eux seuls, le plafond de notions et le verrou T sont levés. »

**Ce que ça t'impose à la passe suivante** :

- **Un refus fondé sur une règle levée n'est pas recevable.** Tu ne rejuges pas ce critère sur ce
  périmètre — le poser à nouveau, c'est rouvrir un arbitrage qui n'est pas le tien et rejouer la
  passe qui vient d'échouer.
- **Les autres critères continuent de s'appliquer** sur ces mêmes unités. Une levée de clarté ne
  lève pas la fidélité aux sources.
- **Le périmètre est celui que la décision écrit**, pas celui que tu en déduis. Elle dit « ces 16 » :
  ce n'est ni « les essentiels denses », ni « ceux du même axe ».
- **Tu écris dans ton rapport que la règle est levée** et sur quelles unités. Sans cette ligne, le
  chef de la passe d'après ne saura pas pourquoi un texte hors plafond est conforme.

**Quand un conflit de grilles se reproduit**, ne tranche pas et n'invente pas de compromis :
escalade, comme pour toute décision qui n'est pas la tienne. Un conflit signalé par plusieurs
vérificateurs qui ne se voient pas est un conflit réel, pas une erreur de lecture.

## Après toi

Tu ne répares rien. Une faille bloquante renvoie à l'étape, avec ta liste, et la vérification
repasse ensuite.

Écris donc des failles qu'un agent puisse corriger sans te reposer de question.
