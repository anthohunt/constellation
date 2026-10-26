---
name: veille-axes
description: Use to GENERATE the axes (mindmap branches) of a veille owner automatically from their profile description, get the operator's validation, then derive the casting (1 chasseur per axis + 2 transversaux + 1 eclaireur) and write the pipeline-ready artefacts. This is the MISSING FIRST STEP between a freshly-created profile (wizard or veille-profile without axes) and the run. Triggers on "/veille-axes <owner>", "génère les axes", "propose les axes de <owner>", "les axes de la veille <owner>". Does NOT source or run the pipeline — its output feeds /veille-launch-researcher.
---

# Veille axes — génération + validation des axes (étape 0 du pipeline)

## Pourquoi ce skill existe

Le wizard produit (et `veille-profile` peut produire) un profil owner **sans axes** : le sujet est décrit en prose, mais les **axes** — les grandes branches de la mindmap, un terrain de chasse par branche — ne sont pas définis. Jusqu'ici il fallait les **écrire à la main** (`veille-profile` Bloc A3). Ce skill les **génère automatiquement** depuis la description, les fait **valider par le lecteur**, puis écrit les artefacts que `veille-launch-researcher` consomme. C'est la marche manquante entre *profil créé* et *run lançable*.

> Les axes ne sont JAMAIS lancés tels quels sans validation humaine — la génération PROPOSE, le lecteur DISPOSE (édite/valide). Décision le lecteur 2026-07-17.

## Quand l'invoquer

- `/veille-axes <owner>` ou "génère les axes de <owner>", "propose les axes".
- Automatiquement suggéré après une création de profil (wizard ou `veille-profile`) quand l'owner n'a pas encore d'axes.
- Ne PAS invoquer pour un owner qui a déjà des axes validés et inchangés (utiliser `veille-modify` pour éditer un existant).

## Architecture (rappel)

- **TOI (conversation principale) = leader.** Les sous-agents ne peuvent pas spawner d'autres agents.
- **Max 5 agents en parallèle.** Ici on n'en lance qu'**1** (le générateur d'axes).
- Chemin du profil : `$VEILLE_OWNERS_DIR/<owner>/` (serveur `$VEILLE_SERVER`) — le wizard web y écrit directement, c'est le seul silo.

## Procédure

### Étape 1 — Résoudre l'owner + charger le profil

```bash
ssh $VEILLE_SERVER "cat $VEILLE_OWNERS_DIR/<owner>/profile.json 2>/dev/null"
```

- Absent → STOP : « Pas de profil pour `<owner>`. Crée-le d'abord (wizard `$CONSTELLATION_BASE_URL/profil` ou `/veille-profile`). »
- Extraire : `description` (le sujet), `familiarity` (0-10, ou `null` = sans objet), `sources` (types + libre), `language`, `title`.

### Étape 2 — Générer les axes proposés (1 agent avec recherche web)

Spawn **UN** agent (`Agent`, `mode:"bypassPermissions"`, `run_in_background:false` — on attend le résultat) avec ce prompt (adapter `<...>`), **à propager** : chercher en ligne d'abord, une seule question à la fois, TL;DR, bypass permissions.

> Tu es un architecte de veille. À partir de la description ci-dessous, propose les **axes** d'une veille — les grandes branches de la mindmap, chacune un terrain de chasse distinct pour un agent sourceur.
>
> **Sujet** : `<description>`
> **Familiarité du lecteur avec le sujet** : `<familiarity>`/10 (règle la profondeur : bas = axes larges et pédagogiques ; haut = axes pointus). `familiarity` à `null` = la veille remonte des annonces et non des explications : omettre cette ligne du brief et calibrer les axes sur le périmètre seul.
> **Langue** : `<language>`.
>
> **Méthode** : fais d'abord **2-4 recherches web** pour cadrer le domaine réel (acteurs, sous-thèmes, débats actuels) — ne devine pas. Puis dégage **4 à 6 axes** :
> - **MECE** : mutuellement distincts (pas de recouvrement) et couvrant ensemble le sujet.
> - chacun = `{ "name": "<2-4 mots>", "desc": "<1 phrase : ce que cet axe couvre / ce qu'on y chasse>" }`.
> - orientés *terrain de chasse* (un agent doit pouvoir chasser dessus), pas catégories abstraites.
> - adaptés à la familiarité et au périmètre ; si le sujet est étroit, 4 axes suffisent ; large → 5-6.
>
> **Sortie** : UNIQUEMENT un JSON `{"axes":[{"name":"","desc":""}, …], "note":"<1 ligne : comment tu as découpé>"}`. Rien d'autre.

Parser le JSON (robuste : extraire le premier `{...}` équilibré). Si l'agent échoue/retourne vide → relancer une fois avec une consigne renforcée, jamais inventer les axes soi-même sans recherche.

### Étape 3 — Présenter + faire valider (human-in-the-loop)

Afficher les axes proposés numérotés, sobrement (pas de punchline) :

```
Axes proposés pour <title> :
1. <name> — <desc>
2. …
(<note>)

On garde ? Tu peux : renommer, reformuler, retirer, ajouter, réordonner. Dis « ok » quand c'est bon.
```

Appliquer les retours du lecteur (édition libre), ré-afficher si changement, boucler jusqu'à « ok / valide / parfait ». **Ne pas continuer sans validation explicite.**

### Étape 4 — Dériver le casting des axes validés

Le casting **se déduit des axes**, il ne se choisit pas : 1 chasseur par axe validé, + 2
transversaux fixes (`Signal faible`, `Contre-preuve`), + 1 éclaireur (axe `Découverte`, mandat
hors de tous les axes — sans lui la veille ne peut que confirmer ce qu'on lui a commandé).

**Un chasseur ne diffère des autres que par son axe et sa fraîcheur.** Même skill, mêmes outils,
même budget. Ne pas inventer de personas, de spécialités ni de styles : rien de tel n'est lu.

Il n'y a donc rien à arbitrer ici — présenter le casting obtenu (une ligne par chasseur) pour
information, et passer à l'écriture.

### Étape 5 — Écrire les artefacts (format pipeline) + projeter

Écrire dans `$VEILLE_OWNERS_DIR/<owner>/` (silo live) :

- **`subject.md`** — régénéré/complété avec la section axes (schéma ci-dessous).
- **`casting.json`** — les chasseurs dérivés des axes.
- **`profile.json`** — mettre à jour avec les `axes[]` validés.
- Ne PAS écraser un `run-config.json` existant sans raison ; le créer s'il manque (format mindmap, `structure:"par axes"`).

Si le profil source venait du wizard, laisser le wizard-silo tel quel (source d'origine) — le silo live est désormais la vérité pour le pipeline.

### Étape 6 — Confirmer

```
Axes validés + casting écrits pour <owner> → prêt pour /veille-launch-researcher.
```

Ne PAS enchaîner le run automatiquement (Le lecteur décide quand lancer).

## Schémas des artefacts

**`subject.md`** (brief de sourcing lu par les chasseurs) :

```markdown
<!-- brief de sourcing — owner: <owner> — axes générés + validés le <date> -->
# Sujet de veille : <title>

## Mission / périmètre
<description>

## Axes de chasse
### <axe.name>
<axe.desc>

### <axe.name>
<axe.desc>
…

## Calibrage
- Profondeur technique : <familiarity>/10 (ton toujours clair) — ligne omise si `familiarity` vaut `null`.
- Sources privilégiées : <types + libre>.
- Langue du livrable : <FR|EN>.
```

**`casting.json`** — le budget est écrit UNE fois, en tête :

```json
{
  "owner": "<owner>",
  "subject": "<veille>",
  "budget_effort": { "sources_min": 15, "requetes_min": 8,
                     "hors_liste_resultats_min": 5, "hors_moteur_generaliste_min": 3 },
  "chasseurs": [
    {"axe": "<axe validé>", "freshness": "48h|semaine|mois|trimestre"},
    {"axe": "Signal faible"},
    {"axe": "Contre-preuve"},
    {"axe": "Découverte", "role": "eclaireur"}
  ]
}
```

`freshness` vient de l'axe. `consigne` s'ajoute seulement si le feedback en a produit une.

**Chaque chasseur porte une `freshness`, transversaux et éclaireur compris.** Sans elle on ne
peut pas dire si un finding archivé peut encore ressortir, et l'anti-doublon copie tout ce qui
existe au lieu de ce qui compte. Défaut pour les trois non-axés (`Signal faible`,
`Contre-preuve`, `Découverte`) : `mois`.

**Le budget est un budget d'EFFORT, jamais un quota de sortie** : zéro finding sur un axe est un
résultat valide.

`<owner>` = slug (minuscules, sans accents, `-`).

## Gotchas

- **Ne jamais inventer les axes sans recherche web** — l'agent DOIT sourcer le domaine réel d'abord.
- **Validation obligatoire** avant écriture — pas de génération silencieuse projetée.
- Un axe = un terrain chassable, pas une catégorie abstraite (« Cadre & risques », pas « Divers »).
