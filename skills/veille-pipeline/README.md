# Watch pipeline: design README

> This document is in French.

> **Ce qu'est ce document.** Le **pourquoi** de la pipeline veille : ce que chaque décision de
> design cherche à obtenir, et la référence qui l'appuie. Il ne dit pas *comment* on exécute —
> ça, c'est le graphe (`pipeline/workflows/veille.json`) et les skills d'étape.
>
> **Maintenance.** Une décision de design qui change se reporte ici avec sa justification. Un
> changement de procédure ne passe pas par ici : il passe par le graphe et le skill de l'étape,
> via `adjust-pipeline`.

---

## 1. Vue d'ensemble

**La phrase qui dit tout :** la pipeline veille transforme le paysage d'un domaine en
**intelligence vérifiée, sourcée, et rendue pour le lecteur qui en a besoin** — pas un résumé
d'IA de plus.

**Les huit étapes :**

`Préparer → Chasser → Monter → Prévenir → Noter (humain) → Feedback → Publier → Bilan`

**Chaque étape est suivie de sa vérification**, jouée par des agents frais qui n'ont pas
participé au travail qu'ils jugent. La notation n'en a pas : c'est une barrière humaine.

**Principe directeur :** ce n'est pas *la* seule source de vérité, c'est une **première étape
d'intel riche et vérifiée**, à confronter ensuite au travail d'autres chercheurs. Le point de
contrôle humain est **interchangeable** : l'expert *ou* le client peut piloter et corriger.

---

## 2. Les skills qui composent la pipeline

| Rôle | Skill(s) |
|---|---|
| Socle, injecté avec chaque protocole d'étape | `veille-pipeline` |
| Préparation du run | `veille-start` |
| Chasse | `veille-launch-researcher` · `veille-chasse-tableau` |
| Montage de la constellation | `veille-assemble-niveau1` · `veille-agent-synthetiseur` · `veille-style` |
| Vérification (toutes étapes) | `veille-verif-etape` · `veille-verif-interet` · `veille-verif-carte` · `veille-verif-style` |
| Feedback | `veille-feedback` |
| Prévenir et publier | `veille-publish` |
| Bilan | `veille-analyse-etape` |
| Support, hors graphe | `veille-axes` · `veille-profile` · `veille-modify` |

---

## 3. Les décisions de design, étape par étape

### Étape 1 — Préparer

- **Le casting se déduit des axes, il ne s'arbitre pas.** Un chasseur par axe, deux transversaux
  fixes, un éclaireur. Rien à décider : ce qui se discute, ce sont les axes, en amont.
  *Pourquoi :* une décision de casting prise au lancement de chaque run est une variable de plus
  entre deux runs, donc un bruit de plus quand on compare leurs résultats.

- **L'éclaireur est obligatoire.** Son mandat est *hors* de tous les axes.
  *Pourquoi :* une veille dont tous les chercheurs travaillent dans le cadre existant ne peut que
  confirmer ce qu'on sait déjà. La **diversité bat la capacité brute** — un groupe diversifié
  couvre plus de terrain qu'un groupe des « meilleurs » qui finissent par se ressembler.
  *Réf :* Hong & Page, PNAS 2004.

- **Le pré-vol est bloquant.** Moteur de recherche, mémoire libre, absence de run concurrente.
  *Pourquoi :* sans moteur, la chasse part à l'aveugle et produit un lot qu'il faudra jeter.

### Étape 2 — Chasser

- **Un chasseur par axe, deux transversaux, un éclaireur — tous identiques par ailleurs.** Même
  skill, mêmes outils, même budget ; seuls l'axe et la tête méthodologique changent.
  *Pourquoi :* les personas servent la **diversité et la couverture, PAS l'exactitude** — c'est
  ainsi qu'il faut les défendre, et c'est pourquoi le rôle ne change ni les outils ni la rigueur
  attendue.
  *Réf :* Zheng et al., EMNLP 2024 (personas = zéro gain d'exactitude) · Anthropic,
  *multi-agent research system*, 2025 (+90 % vs agent unique en breadth-first).

- **Trois têtes méthodologiques sur un moteur de butinage commun.** PIR pour un axe (collection
  planning), signaux faibles d'Ansoff pour le transversal signal-faible, ACH de Heuer pour le
  transversal contre-preuve.
  *Pourquoi :* chercher « largement » sans méthode revient à chercher ce qui se trouve. Chaque
  tête est un protocole de couverture différent, pas un ton différent.
  *Réf :* Ansoff (weak signals / horizon scanning) · Heuer, *Psychology of Intelligence
  Analysis* (ACH).

- **Le budget porte sur l'EFFORT, jamais sur la sortie.** Pages ouvertes, formulations essayées,
  profondeur au-delà de la première page, sources hors moteur généraliste. **Zéro finding sur un
  axe est un résultat valide.**
  *Pourquoi :* un quota de sortie se remplit toujours — par du rembourrage. Un budget d'effort se
  vérifie sur le transcript et ne récompense pas le remplissage.

- **Le journal d'effort est la preuve.** Sans lui, le budget n'est pas vérifiable et le chasseur
  repart.

- **Une requête délibérément oblique par passe.** Angle adjacent, source atypique, terme
  contre-intuitif.
  *Pourquoi :* la sérendipité ne survient pas toute seule dans une recherche dirigée ; on lui
  réserve une place, sinon elle est arbitrée hors du lot à chaque fois.
  *Réf :* Erdelez (information encountering) · Carbonell & Goldstein, SIGIR 1998 (MMR) ·
  Kulesza & Taskar 2012 (DPP), pour le principe anti-clones.

- **Reciprocal Rank Fusion (k = 60) fusionne les listes.** Score = Σ 1/(60 + rang).
  *Pourquoi :* combiner les classements de plusieurs systèmes fait mieux que n'importe quel
  système seul, et mieux que les méthodes concurrentes (Condorcet). La fusion travaille sur des
  **rangs**, donc les chasseurs n'ont pas besoin de partager une échelle de notes.
  *Réf :* Cormack, Clarke & Büttcher, SIGIR 2009.

- **La récence est un poids, pas un filtre.** On capture l'âge, on pondère au tri.
  *Réf :* freshness-RAG, arXiv:2509.19376.

- **La tier se pose ici, par celui qui a les sources ouvertes.** Le chasseur classe sa trouvaille
  contre les règles de son axe et le deck du lecteur, avec la phrase qui dit pourquoi celle-là et
  pas la voisine.
  *Pourquoi :* classer plus tard, c'est classer sans les sources sous les yeux — le montage n'a
  plus que le titre et l'essentiel.

- **Le chasseur ne vérifie pas son propre travail.** La vérification est un nœud séparé, joué
  après, par des agents frais.
  *Réf :* voir « La vérification » ci-dessous.

### Étape 3 — Monter la constellation

- **Le vivier monte entier, et c'est le GROUPAGE qui tient la lecture.** En fin de chasse les
  doublons sont fusionnés, rien n'est coupé (`veille-launch-researcher`, § La déduplication) ;
  au montage, les findings apparentés d'un même axe sont réunis en **histoires** de 2 à 5, et
  chaque histoire reçoit un essentiel unique.
  *Pourquoi :* une constellation de soixante-dix faits isolés ne se lit pas — mais couper pour la
  rendre lisible revient à écarter avant que le lecteur ait vu, alors que le jugement de sélection
  lui appartient (étape 5). Grouper résout les deux : moins d'objets à lire, aucune trouvaille
  jetée, et un lien nommé entre les faits vaut mieux que les faits pris un par un. L'aval, qui se
  paie par unité rédigée, suit le nombre d'histoires et non celui des findings.

- **Le lien s'écrit avant le texte, comme un pari, puis se teste.** Le rédacteur reçoit une
  hypothèse — une phrase disant ce que ses faits racontent ensemble —, la pose avant d'ouvrir les
  sources, range les faits (par date ou par thème), confronte chacun à l'hypothèse, puis nomme la
  **cause commune**. Sans cause écrite en une phrase, il n'y a pas d'histoire : les findings
  repartent séparés.
  *Pourquoi :* laissé libre, un agent résume ce qu'il vient de lire et rend un texte-liste — « d'abord
  ceci, ensuite cela » — qui a la forme d'une histoire sans en être une. Poser le lien d'abord donne
  à la lecture quelque chose à chercher, et rend le lien réfutable : un fait qui ne le soutient pas
  se voit, et sort. C'est la méthode d'enquête de référence (*story-based inquiry*, manuel UNESCO de
  Mark Lee Hunter) : hypothèse, fichier maître rangé, vérification fait par fait. Le test de la
  cause vient du reportage de tendance, où l'erreur classique est l'accumulation — « trois exemples
  font une tendance » est un compte arbitraire ; ce qui fait une tendance est une cause commune
  retracée. Et l'ouverture sur le lien plutôt que sur le premier fait est le rôle du paragraphe-noyau
  (*nut graf*), doublé du mouvement de l'**échelle d'abstraction** (Roy Peter Clark) : monter nommer,
  redescendre montrer.
  Sources : [Story-Based Inquiry, UNESCO](https://www.unesco.org/en/articles/story-based-inquiry-0) ·
  [le nut graf, Poynter](https://www.poynter.org/archive/2003/the-nut-graf-part-i/) ·
  [l'échelle d'abstraction](https://www.theopennotebook.com/2023/05/30/using-the-ladder-of-abstraction-to-elevate-science-stories/) ·
  [la critique de la règle de trois](https://www.npr.org/2002/03/22/1140359/three-times-a-trend) ·
  [la théorie des liens entre textes d'un même sujet (CST)](https://aclanthology.org/L04-1239/), dont
  vient la liste fermée des liens recevables.

- **L'essentiel s'écrit depuis les sources, en closed-world strict.** Le synthétiseur ouvre les
  sources, relève ce que chacune apporte, choisit le fait décisif — celui qui, retiré, changerait
  la conclusion — puis écrit. Rien qui ne soit dans les sources.
  *Pourquoi :* le résultat d'abord, en langue courante, pour que le lecteur sache en deux phrases
  s'il est concerné.
  *Réf :* BLUF / pyramide inversée · lisibilité Kandel-Moles.

- **Aucun gabarit de paragraphes, aucun calibre, aucun plafond de longueur.** Une idée par
  phrase, une notion par paragraphe ; on déplie plutôt que de compresser.
  *Pourquoi :* un calibre fabrique du remplissage quand le sujet est court et de la compression
  illisible quand il est dense. La longueur n'est pas un critère et personne ne la mesure.

- **La référence de rédaction part en entier dans chaque dispatch.** Un synthétiseur qui ne l'a
  pas vue écrit au niveau qu'il croit attendu, et ce niveau est toujours plus bas.

- **Un seul style d'écriture, pour tous les owners.** Un owner apporte ses règles de sélection et
  son ton, jamais son propre niveau de langue.

- **Le monteur reporte la tier, il ne reclasse pas.** Une tier qui bouge entre la chasse et le
  montage est une faille.

- **La dédup est le seul travail global.** Tout le reste se parallélise.

### La vérification — après chaque étape

- **Un agent frais par transcript, aucun n'a participé au travail qu'il juge.**
  *Pourquoi :* un modèle qui juge sa propre prose se sur-note (self-preference marqué) ; le
  feedback **externe** corrige, l'introspection non.
  *Réf :* Panickssery et al., NeurIPS 2024 · Gou et al., CRITIC, ICLR 2024 vs Huang et al., 2024.

- **On juge les livrables CONTRE les transcripts, pas dans l'absolu.** Le runtime constate que
  les fichiers existent ; le vérificateur établit qu'ils ont été **gagnés**. Un journal qui
  annonce quinze sources quand le transcript en montre quatre ne se détecte d'aucune autre façon.

- **Anti-vérification circulaire.** Le vérificateur d'un fait ouvre **ses propres** sources.
  *Pourquoi :* recocher le lien du chasseur ne fait que tamponner une source mal lue ; en
  pratique, une minorité seulement des phrases fluides sont réellement soutenues.
  *Réf :* AttrScore / Liu et al., Stanford 2023 · MiniCheck, EMNLP 2024.

- **Zéro faille est un résultat valide**, s'il est adossé aux traces. On impose l'effort, jamais
  le résultat — la même bascule que le budget des chasseurs. Deux biais symétriques à
  neutraliser : la flemme (« conforme » partout, aucun transcript ouvert) et le zèle (des failles
  inventées pour paraître utile). D'où la règle : un `conforme` sans trace citée est un rapport
  invalide, et une faille qui ne se cite pas ne s'écrit pas.

- **Un verdict conforme est acquis ; aucune passe ultérieure ne le rejuge.**
  *Pourquoi :* deux lectures ne rendent pas le même verdict. Des essentiels conformes rejugés à
  froid par des vérificateurs frais, même texte et mêmes sources, ressortent partiellement
  refusés — rejuger un acquis rouvre du travail clos au gré de la lecture du jour, et la boucle
  étape ↔ vérification ne converge jamais.

- **Aucun juge ne réécrit.** Un refus renvoie à l'étape avec son motif. Un juge qui corrige prive
  le rédacteur de ce qu'il devait apprendre — et sa correction, rédigée plutôt que recopiée
  depuis la source, sera refusée par le juge frais de la passe suivante.
  *Réf :* FlipFlop, 2024 (sous pression de révision, un reviseur retourne une part importante de
  ce qui était correct) · Cross-Context Review, 2026 (l'œil neuf marche → garder l'auditeur
  séparé).

- **Un juge UNIQUE par essentiel, portant les trois questions.** Compris (il reformule sans la
  source), vrai (il rouvre les sources), bien écrit (grille de style) — et **un seul verdict**, la
  fidélité l'emportant quand les questions se contredisent.
  *Pourquoi ce choix, alors que la littérature recommande un panel :* la question ici n'est pas
  de **noter** mais d'**arbitrer**. Trois juges séparés ne peuvent pas s'arbitrer entre eux —
  chacun applique sa règle sans voir ce que l'autre exige, et le conflit remonte au propriétaire
  au lieu de se régler à la lecture. Un texte dense reste vrai ; un texte allégé de ce que sa
  source établit devient faux, donc la fidélité tranche.
  *Réf, pour le principe du panel là où il s'agit de noter :* Zheng et al., NeurIPS 2023 · PoLL,
  Verga et al., 2024 (panel > modèle unique, nettement moins cher) · Ma et al., 2025 (le débat
  amplifie le biais au lieu de le réduire — d'où l'absence de débat entre juges).

### Étape 4 — Prévenir le lecteur

- **L'invitation ne part qu'une fois la vérification verte**, et une seule fois.
  *Pourquoi :* un lecteur prévenu trop tôt note un travail refusé. Déployer ne prévient pas : la
  page est en ligne dès le montage, l'invitation est un geste séparé.

### Étape 5 — Noter (barrière humaine)

- **Le tri est humain, et rien n'est jeté.** Le lecteur corrige les tiers pré-placées, commente,
  fait évoluer les axes. **Ne rien déplacer est un résultat valide** : le classement de l'agent
  devient le sien.
  *Pourquoi :* contrôle humain interchangeable — expert ou client aux commandes — et c'est le
  seul point où la pipeline apprend ce que le lecteur veut vraiment.

- **La constellation classée EST le livrable de cette étape.** Pas une liste de gardés.

### Étape 6 — Feedback

- **Une règle ne s'écrit que si elle retrouve les classements réels.** Seuil : un nombre minimal
  de classements testés, et une majorité de tiers retrouvées. Sous le seuil, la règle ne se grave
  pas.
  *Pourquoi :* une règle induite d'un pattern et jamais testée est une hypothèse déguisée en
  préférence du lecteur — et elle pilotera toutes les runs suivantes.

- **Les mots explicites du lecteur priment sur ce qu'on déduit de ses gestes.**

- **Un finding non ouvert est un rejet prononcé sur le seul TITRE.** C'est le seul signal qui juge
  la porte d'entrée.

- **Aucun dialogue pendant l'étape.** Le rapport dit ce qui a été écrit et avec quel score ; le
  lecteur conteste après coup.
  *Réf :* **à sourcer** — human-in-the-loop / preference learning. *Trou assumé : cette étape
  n'a pas encore d'ancrage littérature formel comme les autres.*

### Étape 7 — Publier

- **Cette étape n'écrit rien, elle assemble.** Les essentiels ont été écrits à l'étape 3 et
  vérifiés juste après ; ce que l'agent compose, ce sont les liants — regroupement, ordre,
  transitions.

- **Plusieurs projections du même fond.** Constellation interactive, digest, newsletter — le
  format vient du profil du lecteur.
  *Pourquoi :* progressive disclosure — le lecteur descend à la profondeur qu'il veut ; le
  statique ne perd aucun fait, juste le repli.
  *Réf :* Nielsen (progressive disclosure) · BLUF.

- **Le rendu s'adapte à l'audience, pas la recherche.** Le registre change (en consulting, Minto
  Pyramid + SCQA), le fond est commun.
  *Réf :* Minto Pyramid · SCQA.

- **La constellation publiée se construit sur le silo ENTIER**, pas sur la seule run.
  *Pourquoi :* publier la semaine seule perd le cumul, qui est justement la valeur.

- **La mémoire du domaine se réécrit à chaque run, elle ne s'incrémente pas.** Une run publiée
  sans mise à jour de la mémoire est une accumulation perdue.

### Étape 8 — Bilan

- **Les chiffres sont MESURÉS sur les transcripts, jamais estimés.** Un transcript incomplet se
  signale ; un total faux, non.

- **Une faille qui revient à plusieurs étapes est un défaut de SPEC, pas d'exécution.** C'est le
  critère qui décide si un enseignement remonte dans les skills ou reste dans le post-mortem.

---

## 4. Modèle owner / subject

Un même **subject** est rendu pour plusieurs **owners** = profils de lecteur. La recherche est
commune ; seuls la sélection finale, le ton et la profondeur de rendu changent par owner. Chaque
owner porte son silo : ses règles de sélection, son deck de préférences, ses archives, sa mémoire
de domaine.

## 5. Cadrage honnête

- La pipeline est une **première étape** d'intel vérifiée, **pas la seule source** — elle se
  compare ensuite au travail d'autres chercheurs.
- Le **contrôle humain est interchangeable** : expert OU client aux commandes.
- **Le format et la mécanique sont validés** ; la profondeur de contenu par finding dépend
  entièrement de ce que les sources offrent sur le sujet du jour.

## 6. Ce qui n'est pas câblé

Trois mécanismes documentés dans la littérature n'ont **pas** de place dans la pipeline
actuelle. Les nommer évite de les réintroduire par réflexe :

- **La sélection automatique du lot** (composition par MMR/DPP, quotas par source et par axe).
  Le lot n'est pas composé par la machine : tous les passants dédupliqués entrent dans la
  constellation, et le lecteur filtre. Le principe anti-clones survit **chez le chasseur**, comme
  consigne de diversification, pas comme filtre de composition.
- **Le panel de juges sur l'essentiel** — voir le juge unique ci-dessus : ici on arbitre, on ne
  note pas.
- **Les bandits sur les sources** (UCB / Thompson / LinUCB) pour piloter l'exploration.
  Rien ne les câble aujourd'hui ; ce serait la voie si l'on voulait que la pipeline apprenne
  quelles sources rendent, au lieu de le laisser au budget d'effort.
  *Réf :* Auer, 2002 · Li et al., WWW 2010 (LinUCB).

---

## 7. Index des sources scientifiques

- **RRF :** Cormack, Clarke & Büttcher, *Reciprocal rank fusion outperforms Condorcet…*, SIGIR 2009.
- **Diversité > capacité :** Hong & Page, PNAS 2004.
- **Personas = diversité, pas exactitude :** Zheng et al., EMNLP 2024.
- **Architecture multi-agent :** Anthropic, *How we built our multi-agent research system*, 2025 ; Cognition, *don't build multi-agents* / *multi-agents working*.
- **Méthodes de recherche :** Ansoff (weak signals / horizon scanning) ; Heuer, *Psychology of Intelligence Analysis* (ACH) ; PIR / collection planning.
- **Sérendipité :** Erdelez (information encountering).
- **Diversité de sélection :** Carbonell & Goldstein, SIGIR 1998 (MMR) ; Kulesza & Taskar 2012 (DPP).
- **Panel de juges :** Zheng et al., NeurIPS 2023 ; PoLL — Verga et al., 2024 (arXiv:2404.18796) ; Ma et al., 2025 (débat = amplification).
- **Vérification / anti-circularité :** Gou et al., CRITIC, ICLR 2024 ; Huang et al., 2024 ; Liu et al. (AttrScore), Stanford 2023 ; MiniCheck, EMNLP 2024.
- **Self-preference :** Panickssery et al., NeurIPS 2024.
- **Sur-correction :** FlipFlop, 2024 ; Cross-Context Review, 2026.
- **Présentation du signal :** Pirolli & Card 1999 (Information Foraging) ; Nielsen (progressive disclosure) ; Nenkova & Passonneau (Pyramid) ; TextRank ; BLUF / pyramide inversée ; Minto Pyramid + SCQA ; lisibilité Kandel-Moles.
- **Récence :** freshness-RAG, arXiv:2509.19376.
- **Non câblé, pour mémoire :** Auer 2002 ; Li et al., WWW 2010 (LinUCB) ; MAST, arXiv:2503.13657.
