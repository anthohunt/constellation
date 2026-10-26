---
name: veille-modify
description: Use when the operator invokes `/veille-modify <watch>` OR says he wants to change/tune a watch's config — axes, mission, scope, cadence, hors-scope explicite, profil de l'utilisateur. Brainstorming meeting-style pour identifier ce qui doit changer dans le subject file (et accessoirement preferences/current-stack), proposer le diff, appliquer. Trigger phrases : "je veux modifier la veille X", "il faut changer X dans la veille Y", "brainstorm sur la veille Z", "rework les axes de X", "la veille X part trop dans Y, à corriger".
---

# Veille modify — meta-tuning d'une watch

## Why

Au fil des runs, le lecteur se rend compte qu'une veille dérive : axes mal calibrés, scope trop large, sujets répétitifs, profil de l'utilisateur obsolète, etc. Plutôt que de patcher au coup par coup via `/veille-feedback` (qui est par-finding), `/veille-modify` ouvre une discussion meta sur **la veille elle-même** — sa mission, ses axes, son scope.

C'est aussi le bon endroit pour réagir aux insights cross-run : "tiens, ai-infra n'arrête pas de me proposer du solaire mais je n'en ai pas → il faut que la veille comprenne ma stack actuelle" (cas réel 2026-05-22 qui a déclenché la création du système current-stack.md).

## When to invoke

- `/veille-modify <watch>` slash command
- "je veux modifier la veille X", "rework la veille Y", "il faut changer X dans Y"
- Le lecteur pointe un pattern récurrent qui n'est pas un finding isolé mais une dérive globale ("ça part toujours dans la même direction qui ne m'intéresse pas", "je vois jamais de findings sur Z alors que c'est mon priorité")

## What this skill can modify

Files éditables via cette skill :

| Fichier | Contenu | Quand modifier |
|---|---|---|
| `$VEILLE_SUBJECTS_DIR/<watch>.md` | Mission, axes, cadence, profil du lecteur, hors-scope, `findings` par axe (plus de « volume cible » global — purge 2026-07-30) | Refonte structurelle (changer un axe, élargir/réduire scope, mettre à jour profil) |
| `$VEILLE_STATE_DIR/<watch>-current-stack.md` | Stack actuelle du lecteur + achats prévus / deep-dive | Ajustement deep-dive sans toucher au scope global |
| `$VEILLE_STATE_DIR/preferences-<watch>-rules.md` | Règles spécifiques (drops, format, ton, cross-watch) | Patterns récurrents à coder en règle |
| `$VEILLE_STATE_DIR/<watch>-strategy.md` | Notes de stratégie long terme (optionnel) | Vision globale à expliciter |
| Crontab via `crontab -l` | Cadence (daily/weekly/monthly) | Demander confirmation avant — c'est une opération autre que les fichiers |

## The protocol

### Step 1 — Présenter l'état actuel (concise)

Charger et résumer en **bullets clairs** (pas d'ASCII tables) :

```
**Veille `<watch>` — état actuel** :

- **Mission** : <pitch 1 phrase tiré du subject file>
- **Cadence** : <daily/weekly/monthly + jour>
- **Axes actuels** ({N}) :
  - <nom axe 1>
  - <nom axe 2>
  - ...
- **Stack actuelle du lecteur** (résumé current-stack.md) : <1-2 phrases sur ce qu'il a TODAY + deep-dives activés>
- **Drops actifs** (rules.md + archive-overrides) : <liste 1-line par drop>
- **3 derniers runs** : <date + headline tirés de suggestions/archive/>
- **Patterns ratings** : <quelques stats : score moyen, axes les plus aimés/rejetés>
```

Puis question ouverte : *"Qu'est-ce qui te chagrine dans cette veille ? Ou tu veux changer quoi en premier ?"*

### Step 2 — Mode brainstorm one-topic-at-a-time

Le lecteur nomme un problème (ex: "l'axe 4 produit toujours des trucs hors scope"). Pour chaque sujet :

1. **Diagnostic** : creuser ensemble pour comprendre la racine (1-2 questions courtes max)
2. **Propose 2-3 options de fix** :
   - **A** Modif minime (1-2 lignes dans le subject file)
   - **B** Modif structurelle (refonte axe / ajout règle / mise à jour stack)
   - **C** Drop du sujet (si vraiment hors scope)
3. **Le lecteur choisit** (ou propose autre chose)
4. **Show diff before apply** : montrer EXACTEMENT ce qui va changer (extrait avant + extrait après) — le lecteur confirme
5. **Apply** : Edit le fichier concerné
6. **Confirme** + propose le prochain sujet : *"Modif appliquée. Tu vois autre chose à changer ?"*

### Step 3 — Backup avant gros changement

Si une modification touche >30% du subject file, créer un backup d'abord :

```bash
cp $VEILLE_SUBJECTS_DIR/<watch>.md $VEILLE_SUBJECTS_DIR/.bak-<watch>-$(date +%Y%m%d-%H%M).md
```

(2026-04-22 — règle déjà appliquée par d'autres skills.)

### Step 4 — Pas de test run automatique

À la fin de la session, **ne PAS déclencher** un `/veille-start` test automatique. Le lecteur doit explicitement demander (coût $3-5 par run en opus-4-7). Dire :

> *"Modifs appliquées sur `<watch>`. Le prochain run cron utilisera la nouvelle config. Si tu veux tester tout de suite, dis-moi et je lance un /veille-start."*

### Step 5 — Log + memory

- Si la modification révèle un pattern universel (applicable à plusieurs veilles), proposer de l'extraire en règle globale dans `state/preferences-global.md` (l'agent voit ce file en plus du fichier per-watch)

## Hard rules

- **NEVER** modify le crontab sans confirmation explicite ("oui change la cadence en mensuel" — clair).
- **NEVER** lancer un /veille-start automatique en fin de session.
- **NEVER** dump 2+ propositions de modif en même temps. One topic at a time, même règle que `/veille-feedback`.
- **TOUJOURS** montrer le diff avant d'appliquer (extrait avant/après en 5-10 lignes max).
- **TOUJOURS** backup si modification structurelle (>30% file).
- Pas de tableaux ASCII — puces markdown.

## Phrases déclencheurs additionnelles à reconnaître

- "il faudrait que la veille X regarde aussi Y"
- "la veille X ne devrait plus parler de Y"
- "change le focus de la veille X vers Y"
- "élargis / réduis le scope de la veille X"
- "ajoute / retire un axe à la veille X"
- "la veille X est devenue trop / pas assez technique"

## Différence avec /veille-feedback

| `/veille-feedback` | `/veille-modify` |
|---|---|
| Discute des findings d'UN run précis | Discute de la **veille en tant que système** |
| Drops/keeps individuels via ratings | Refonte axes, scope, mission, profil |
| Per-finding meeting | Brainstorm structurel |
| Persiste dans archive-overrides.json | Persiste dans subject file / current-stack.md / rules.md |

Les 2 sont complémentaires : `/veille-feedback` traite les symptômes (un finding noté bas), `/veille-modify` traite la cause racine (l'axe qui produit ces findings n'est plus aligné).
