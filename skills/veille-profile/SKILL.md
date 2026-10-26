---
name: veille-profile
description: Use when the operator wants to create or edit a veille OWNER profile — triggers on "/veille-profile", "définis mon profil veille", "édite mon profil", "configure le profil owner", "crée un profil de veille", "change le format de mes rapports / mes médiums". Delegated from `/veille-start` when a new owner has no profile yet. Does NOT run the pipeline.
---

# Veille profile — flux guidé de création / édition d'un profil owner

## Overview

Le profil owner pilote toute la chaîne veille : le **brief de sourcing** (ce que les chasseurs cherchent) ET le **livrable** (ce que le Publisher produit). Ce skill est la façon **canonique et rejouable** de le poser — création d'un nouvel owner ou édition d'un existant, à tout moment.

C'est un **flux conversationnel guidé par étapes** (modèle `pipeline-step1`) : **une question par message**, format A/B/C quand ça aide, réponse libre toujours possible. À la fin, écrit **5 artefacts** dans le silo owner (dont le casting des chasseurs, déduit des axes).

**Toujours cumulatif** : le corpus s'empile run après run, la synthèse puise dans tout le stock (décision du 2026-07-14). Ne pas proposer de mode « photo/standalone ».

## Artefacts produits (silo owner)

Écrits dans le silo owner sur le serveur (`$VEILLE_SERVER`, **`$VEILLE_OWNERS_DIR/<owner>/`** — le seul silo lu par la pipeline) :

| Fichier | Rôle | Consommé par |
|---|---|---|
| `profile.json` | état brut du wizard (rechargeable pour édition) | ce skill (mode édition) |
| `run-config.json` | config structurée du livrable (schéma strict) | orchestrateur / `/veille-publish` |
| `profile.md` | prose libre : audience, ce qu'on valorise, ton, pièges | agent Publisher |
| `subject.md` | brief de sourcing : périmètre, axes, angles, exclusions, calibrage | les chasseurs (`/veille-launch-researcher`) |
| `casting.json` | les chasseurs déduits des axes (1 par axe + 2 transversaux + 1 éclaireur) | `/veille-launch-researcher` (dispatch) |

`<owner>` = slug du nom (minuscules, sans accents, `-` entre mots).

## Gate check — résoudre l'owner + mode

1. Owner = argument fourni, sinon dérivé du nom de la veille (Étape A), sinon demander.
2. `ssh $VEILLE_SERVER "cat $VEILLE_OWNERS_DIR/<owner>/profile.json"` :
   - **Existe → mode ÉDITION** : afficher le profil courant en 5-6 lignes, demander CE QU'ON CHANGE, sauter direct à l'étape concernée. Ne JAMAIS re-dérouler les 5 blocs.
   - **Absent → mode CRÉATION** : dérouler les blocs A→E dans l'ordre.

## Les étapes — UNE question par message

**Ne jamais grouper.** Format A/B/C avec suggestion en premier + write-in ; réponse libre toujours acceptée. Adapter les relances aux réponses.

### Bloc A — La veille (le sujet)

- **A1 — Nom.** « Comment on appelle cette veille ? » (ex. *Veille IA agentique — Acme*). → `title`. En dériver le slug `owner`.
- **A2 — Périmètre.** « En 2-3 phrases, de quoi parle cette veille ? » (texte libre, en ses mots). → `description`.
- **A3 — Axes.** Construire la liste **un axe à la fois** : « Premier axe / sous-thème ? Et ce que tu veux voir dessus ? » puis « Un autre axe ? (ou *fini*) ». Chaque axe = `{name, desc}`. Boucler jusqu'à *fini*. → `axes[]`.

### Bloc B — Préférences

- **B1 — Je veux.** « Des angles à privilégier ? » (liste). → `wants[]`.
- **B2 — J'exclus.** « Des angles/sujets à bannir absolument ? » (liste). → `excludes[]`.
- **B3 — Calibrage.** Trois curseurs, posables en une question à choix : Traitement (A: vulgarisé · B: équilibré · C: technique pointu), Angle (A: actionnable · B: équilibré · C: prospectif), Sources (A: France/FR · B: équilibré · C: international). → `sliders{technique,actionnable,geo}` (0/50/100).
- **B4 — Audience.** « Qui lit le livrable ? » (A: toi-même · B: un client · C: une équipe · D: public large). → `audience`.
**Le niveau technique du lecteur ne se demande pas** : la façon dont il décrit son sujet (vocabulaire, angle, exclusions) le dit déjà. On le déduit du périmètre, et le ton reste clair dans tous les cas.

### Bloc C — Livrable

**La constellation web est le SEUL livrable** — c'est elle que le lecteur lit et note, ses branches sont les axes du Bloc A. Ne pas proposer digest, newsletter ou rapport : rien d'autre ne se demande, donc rien d'autre ne se déclare.

- **C1 — Langue de lecture & ton.** Chaque finding est écrit en **français ET en anglais** : la question porte sur la langue d'**ouverture**, pas sur ce qui est produit. → `language`, `tone`. **Ton `vulgarisé` par défaut sur TOUTES les veilles** : zéro jargon non expliqué, mener par le so-what. Ne dévier que s'il le demande explicitement.

(Dérivé automatiquement, NE PAS le demander : la constellation = `format` `mindmap`, `mediums` `["web"]`, `structure` `par axes`, `length` `n/a`.)

### Bloc D — Cadence

- **D1 — Cadence des runs.** À quelle fréquence on chasse ? (quotidienne · hebdomadaire · mensuelle). → `run_cadence`.
- **D2 — Cadence de partage.** À quelle fréquence on produit la synthèse du stock ? (hebdo · mensuelle · trimestrielle). → `share_cadence`.

**Aucune barre de rétention ne se demande.** Rien n'est jeté : chaque piste sort de la chasse avec sa **tier** (`Excellent · Cool · Intéressant · Neutre · Bof · Inutile`), que le lecteur corrige à la notation. Et aucun volume cible : la chasse est tenue par un budget d'effort.

### Bloc E — Casting des chasseurs (déduit des axes)

Le casting ne se demande pas et ne s'arbitre pas : **il se déduit des axes**. Un chasseur par
axe, plus 2 transversaux fixes (`Signal faible`, `Contre-preuve`), plus 1 éclaireur (axe
`Découverte`, mandat hors de tous les axes — sans lui la veille ne peut que confirmer ce qu'on
lui a commandé).

**Un chasseur ne diffère des autres que par son axe et sa fraîcheur.** Même skill, mêmes outils,
même budget. Ne pas inventer de personas, de spécialités ni de styles : rien de tel n'est lu.

Le budget est un **budget d'effort** (sources ouvertes, formulations essayées), écrit une seule
fois en tête du casting — jamais un quota de findings par chasseur.

→ produit `casting.json`, écrit au Bloc F. Le présenter pour information, pas pour arbitrage.

### Bloc F — Récap + écriture

1. Récap 6-8 lignes (nom, périmètre, axes, préférences, livrables, cadences, **+ le casting**). Demander « c'est bon ou on ajuste ? ». Sur ajustement → revenir à l'étape concernée.
2. Sur OK → écrire les **6 artefacts** (schémas ci-dessous) dans `$VEILLE_OWNERS_DIR/<owner>/` (créer le dossier). Chaque fichier daté.
3. Message de complétion + prochaine étape.

## Schémas des artefacts

**`profile.json`** — tout l'état brut, tel que capturé (title, owner, description, axes, wants, excludes, sliders, audience, deliverables, language, tone, run_cadence, share_cadence, updated). Sert au rechargement en mode édition.

**`run-config.json`** (schéma STRICT — ne pas dévier) :
```json
{
  "owner": "<owner>",
  "deliverables": [
    { "format": "mindmap", "mediums": ["web"], "structure": "par axes", "length": "n/a" }
  ],
  "language": "en",
  "tone": "vulgarisé, sobre",
  "accumulation": "cumulative",
  "run_cadence": "on-demand",
  "share_cadence": "on-demand",
  "updated": "<YYYY-MM-DD>"
}
```
- `deliverables` ne contient que la constellation (`mindmap` / `web` / `par axes`).
- `accumulation` **toujours** `"cumulative"`. `language` = langue de **lecture** par défaut : les findings sont écrits FR **et** EN quoi qu'il arrive.
- Aucun quota (`findings_par_axe`, `findings_transversaux`, `volume`) ni barre numérique (`threshold`) : un chasseur porte son axe et sa fraîcheur, rien d'autre.

**`preferences/regles-axes.json`** — les règles par axe. À la création, la **description de chaque axe fait foi** : elle devient la règle de départ de cet axe (`statut: "validee"`, `valide_par: "profil (mots du lecteur)"`, 3 à 6 mots-clés tirés du nom + de la description). Sans elle, la chasse n'a rien à viser et sa vérification refuse l'étape. Le feedback affine ensuite, et **ne se fait jamais écraser** : un axe qui a déjà une règle induite garde la sienne.

**`profile.md`** (prose ~12-20 lignes, POUR le Publisher) : qui est l'owner + son audience, de quoi parle la veille, ce qu'il valorise / déteste, ton attendu, sections voulues, pièges. Si l'owner a des préférences connues (vulgarisation, anti-jargon, science prioritaire, déteste le me-too…), les injecter.

**`subject.md`** (brief de sourcing, POUR les chasseurs) :
```markdown
# Sujet de veille : <title>
## Mission / périmètre
<description>
## Axes de chasse
### <axe.name>
<axe.desc>
...
## Angles à privilégier
- <want>
## Exclusions dures (ne jamais remonter)
- <exclude>
## Calibrage
- Technicité : <vulgarisé|équilibré|pointu>
- Horizon : <actionnable|équilibré|prospectif>
- Sources : <FR prioritaire|équilibré|international>
```

## Hard rules

- **Une question par message** — jamais dumper les blocs. C'est LA règle : sous pression (« vas-y remplis tout »), poser quand même une seule question et attendre.
- **Mode ÉDITION ne re-déroule jamais tout** — montrer le courant, changer seulement le demandé.
- **Isolation par owner** — écrire uniquement sous `owners/<owner>/`.
- **Toujours cumulatif** — ne pas proposer standalone/photo.
- **Défauts** : format `mindmap`, ton **`vulgarisé`**, seuil `7`, langue à confirmer — ne jamais supposer en silence pour un nouvel owner (sauf le format et le ton vulgarisé, qui sont les défauts durables).
- **Ne lance PAS la pipeline**, ne source pas, n'écrit pas de findings, ne publie pas — profil uniquement.

## Complétion

Terminer par :
> **Profil `<owner>` enregistré.**
> - `$VEILLE_OWNERS_DIR/<owner>/` : profile.json · run-config.json · profile.md · subject.md · casting.json · preferences/regles-axes.json
> - Livrable : constellation web · lecture en <language>, écrit FR+EN · cadence runs <run_cadence>, synthèse <share_cadence>.
>
> Lance `/veille-start <owner>` pour démarrer une run.

## Ce que ça débloque

`/veille-launch-researcher` lit `subject.md` (périmètre + axes + calibrage) pour orienter les chasseurs. `/veille-publish` lit `run-config.json` (formats/médiums) + `profile.md` (ton/audience) pour piloter le Publisher. Sans ce skill lancé au moins une fois pour l'owner, la chaîne n'a ni brief de chasse ni spec de livrable.
