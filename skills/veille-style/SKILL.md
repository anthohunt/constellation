---
name: veille-style
description: MODÈLE D'ÉCRITURE de la veille — comment un signal se raconte pour qu'on ait envie de le lire jusqu'au bout. Les huit gestes, l'exemple de référence complet (avant / après), et la règle qui commande tout : on déplie, on ne compresse pas. Règle générale de la pipeline, commune à tous les owners, injectée à tout agent qui écrit du texte lu — y compris les sous-agents que dispatche un rédacteur. PAS un skill invocable par l'utilisateur.
---

# Style de vulgarisation — le modèle d'écriture de la veille


## Quand ce modèle ne s'applique pas

Il vaut pour une run en mode `veille` — celle qui explique un sujet. Une run en mode
`collecte` (cf. `mode` dans `run-config.json`) ramène des éléments à ficher, pas à raconter :
ni gestes, ni contraste, ni plafond de notions, et le juge de style ne passe pas sur ses
livrables. Une fiche d'offre bien remplie n'a pas à être une bonne explication.

## Ce qui commande tout le reste

**On déplie, on ne compresse pas.** Un essentiel n'est pas un résumé : c'est une explication.
Le lecteur doit pouvoir le lire d'une traite, sans relire une phrase deux fois, et savoir à la fin
ce qui a changé et ce que ça lui fait.

Il n'y a **pas de plafond de mots**, ni par phrase ni par texte — les traits mesurés de la référence et leurs tolérances vivent dans `profil-mesure.md`, et c'est contre eux que l'écriture se juge. Un signal simple tient en deux cents mots, un signal qui
demande de poser une notion en prend quatre cents. Ce qui se juge, c'est si ça se lit — pas si
c'est court. Une phrase qui porte trois idées est un défaut, même si elle fait gagner dix mots.

**Une idée par phrase. Une notion par paragraphe.** C'est la seule mesure qui compte.

Ce qu'on ne fait plus : empiler la date, les auteurs, le titre du papier et deux chiffres dans la
phrase d'ouverture. L'état civil du travail cité se donne quand le lecteur sait déjà de quoi on
parle, et par petits bouts.

---

## Portée : les moments de rédaction

- **l'essentiel** d'un finding, dans la constellation ;
- **les livrables** — digest, newsletter, résumés par axe.

Aucun de ces moments n'a de style propre : même modèle, même niveau de langue. Celui qui ouvre la
newsletter n'a pas moins droit à la clarté que celui qui note la constellation.

**Tout agent qui écrit reçoit l'exemple de référence ci-dessous dans son prompt, avant d'écrire.**
Un rédacteur qui dispatche des sous-agents le leur transmet : ils écrivent le texte que le lecteur
lira, ils doivent avoir vu à quoi il ressemble.

---

## Les huit gestes

### 1. Ouvrir par la question du lecteur
Le texte commence par ce que le lecteur se demanderait s'il tombait sur le sujet — pas par le
papier. « Quand on laisse un agent IA travailler tout seul, la question qui vient tout de suite,
c'est : comment on sait qu'il ne fait pas n'importe quoi ? »

**Test** : la première phrase ne contient ni date, ni nom propre, ni chiffre, ni référence.

### 2. Poser la notion avant de s'en servir
Un terme qui porte le sujet se définit par ce qu'il fait, en une phrase entière, avant la phrase
qui l'utilise. Pas entre parenthèses, pas en apposition.

**Test** : on peut supprimer la définition et le paragraphe suivant devient incompréhensible —
c'est qu'elle était au bon endroit.

### 3. Dire d'abord ce qui marchait
Un résultat ne surprend que si l'état antérieur a été posé. On raconte donc la solution en place,
et pourquoi elle semblait tenir, avant de dire ce qui la casse.

### 4. Frapper avec le chiffre, seul
Le chiffre fort occupe sa phrase, ou sa ligne. Il n'est pas noyé dans une énumération.
« Sur banc, ce type de surveillant attrape 95 % des tentatives. »

### 5. Montrer le mécanisme en gestes concrets
Ce que fait l'attaque, la méthode, le système — en verbes que le lecteur peut se représenter.
« Ils ne touchent pas aux commandes. Pas une ligne. Ils réécrivent seulement l'explication. »

### 6. Nommer ce qui est cassé
Après le fait, une phrase qui dit ce que ce fait détruit — une hypothèse, une pratique, une
croyance de métier. C'est ce paragraphe qui distingue une nouvelle d'un signal.

### 7. Nuancer juste après avoir frappé
La réserve suit immédiatement le point fort : d'où viennent les chiffres, ce qui reste debout.
Jamais en fin de texte comme une clause de style.

### 8. Finir sur le geste du lecteur
La dernière phrase dit ce qui change pour lui, dans son travail, avec un exemple qu'il fait
vraiment — pas une recommandation générale.

---

## Ce qui tue la lecture

- **Deux idées dans une phrase.** Le premier défaut, et de loin.
- **Les chevilles répétées.** « Il faut bien voir », « À noter », « Concrètement » : une seule
  par texte, jamais deux paragraphes qui s'ouvrent de la même façon.
- **L'état civil en ouverture.** Date, auteurs, titre, référence : tout ça d'un coup, en tête.
- **Le télégramme.** Des phrases sans verbe, des listes déguisées en prose.
- **Le jargon en apposition** : « le harness (l'environnement d'exécution) » — c'est le geste 2
  qui manque.

---

## Le texte de référence

**`reference-redaction.md`, à côté de ce fichier — et `reference-redaction.en.md` pour l'anglais.**
C'est le matériau d'où sortent les huit gestes : 1 250 mots de vulgarisation, explication pure, sur
un sujet technique (DeepSeek Harness). Il a été désigné comme le niveau à atteindre. Quand un
doute subsiste sur le grain d'un texte, on le relit — c'est lui qui tranche, avant les consignes et
avant l'exemple avant/après.

**Tout agent qui écrit du texte lu le reçoit dans son prompt**, en entier, avant d'écrire, **dans
la langue qu'il écrit** — la version anglaise pour un texte anglais. Sans étalon dans sa langue,
l'agent écrit au niveau qu'il croit attendu, et ce niveau est toujours plus bas. Un rédacteur qui
dispatche des sous-agents la leur transmet.

La version anglaise est une **traduction éditoriale** de la française, pas un mot-à-mot : mêmes
faits, mêmes chiffres, mêmes réserves, même ordre — et une phrase qui se lit aussi bien.

Ce qu'il faut en retenir en le lisant : le texte prend le temps d'une notion à la fois, ne
convoque jamais deux idées dans une phrase, définit avant d'utiliser, dit ce qui marchait avant de
dire ce qui casse, et finit sur ce que le lecteur en fait. Il ne compresse rien.

## L'exemple de référence

Quand un doute subsiste, c'est ce couple avant/après qui tranche, pas les consignes.

**Avant** — 200 mots, quatre paragraphes, tout est là et rien ne se lit :

> Le 1er août 2026, Shikhar Shiromani et Leo Richter (*A False Average*, arXiv 2608.00583)
> montrent qu'un __moniteur qui lit la pensée d'un agent IA passe de 95 % à moins de 11 % de
> détection__ quand l'attaquant se contente de réécrire cette pensée, les commandes exécutées
> restant identiques.
>
> Un agent laisse deux pistes : ce qu'il se dit à voix haute (*chain-of-thought*) et ce qu'il tape
> vraiment. Le moniteur lit surtout la première. L'attaque garde les commandes malveillantes
> intactes et réhabille seulement l'explication en revue de code de bonne foi.
>
> D'ordinaire on suppose que si l'agent complote, il en laissera trace en pensant tout haut. Ici
> l'attaquant met en scène une pensée innocente par-dessus une action nuisible.
>
> En clair : résultat sur banc adversarial ; un moniteur mixte trace + action récupère un peu de
> robustesse. Il faut une sonde hors trace sur chaque geste irréversible.

**Après** — 437 mots, sept paragraphes, les huit gestes :

> Quand on laisse un agent IA travailler tout seul sur une machine, la question qui vient tout de
> suite, c'est : comment on sait qu'il ne fait pas n'importe quoi ? La réponse qui s'est imposée,
> c'est de lire ce qu'il se dit à lui-même. Un agent moderne ne passe pas directement à l'action :
> il déroule d'abord son raisonnement à voix haute — c'est ce qu'on appelle la *chain-of-thought*,
> et c'est ce que tu vois défiler quand Claude Code t'annonce ce qu'il va faire avant de le faire.
> L'idée derrière la surveillance est simple : si l'agent prépare un mauvais coup, il devrait le
> dire quelque part dans ce monologue. On met donc un second modèle en lecture, et on le laisse
> lever la main.
>
> Ça marche très bien. Sur banc, ce type de surveillant attrape 95 % des tentatives.
>
> Le 1er août 2026, Shikhar Shiromani et Leo Richter publient *A False Average*
> (arXiv 2608.00583) et montrent que ce chiffre s'effondre à **moins de 11 %** — sans que l'attaque
> devienne plus sophistiquée pour autant. Ce qu'ils font est presque décevant de simplicité : ils
> ne touchent pas aux commandes. Pas une ligne. Ils réécrivent seulement l'explication qui les
> accompagne, pour qu'elle ressemble à une relecture de code de bonne foi. L'agent fait exactement
> la même chose qu'avant ; il la raconte autrement. Le surveillant, lui, lit surtout l'histoire —
> et l'histoire est propre.
>
> Ce qui tombe ici n'est pas un surveillant qui rate un cas tordu : c'est une hypothèse de départ.
> On supposait qu'un agent qui complote en laisserait forcément une trace en pensant tout haut. Or
> rien n'oblige la pensée affichée à correspondre à l'action. Ce sont deux pistes séparées, et
> seule la seconde engage quelque chose. Un deuxième papier (Severi et al., arXiv 2608.02820)
> arrive au même résultat par un autre chemin, en ré-entraînant le modèle plutôt qu'en réécrivant
> ses sorties.
>
> À nuancer quand même : ces chiffres viennent d'un banc conçu pour attaquer, pas d'un usage
> ordinaire. Et les auteurs notent qu'un surveillant qui lit **à la fois** la trace et les actions
> récupère une partie du terrain.
>
> Pour toi : « je lis l'*Extended Thinking* et j'attrape les dérapages » ne tient plus comme
> garde-fou. Ce qui tient, c'est de contrôler les gestes eux-mêmes — un `git push`, un envoi de
> mail, un appel d'API payant — avec quelque chose qui regarde l'action et pas le récit qui
> l'accompagne.

**Ce qui a changé** : mêmes faits, mêmes chiffres, mêmes réserves, même source. Le texte a doublé
de longueur et il se lit deux fois plus vite. L'ouverture pose la question avant le papier ; la
notion est définie avant d'être utilisée ; le 95 % est seul dans sa phrase ; le mécanisme est en
gestes ; l'hypothèse cassée est nommée ; la réserve suit le chiffre ; la fin donne un geste.

---

## Ce que le modèle n'est pas

- **Pas de promotion** : aucune accroche, aucune chute percutante, aucun superlatif décoratif.
- **Pas de tutoriel** : on ne raconte pas une installation pas-à-pas dans un essentiel.
- **Pas de familiarité forcée** : le tutoiement du lecteur est naturel, les interjections non
  (« bah », « du coup », « allez »).

---

## Ce qui ne change pas

- Le **niveau de langue ne varie pas** avec la difficulté du sujet : hardware, robotique et cyber
  s'écrivent au même niveau qu'un sujet d'interface.
- **Jargon IA courant laissé en anglais** : benchmark, transformer, embedding, RAG, agent, token,
  prompt. Banlist : « banc-test », « plongement », « invite ».
- **Toute entité glosée à sa première apparition dans la veille**, pas seulement dans la run.
- Accents complets, apostrophe droite, pas de caractères décoratifs.
