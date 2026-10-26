# CONTRAT DE SORTIE — chasseur (phase A)

**Ce bloc est machine-lisible. Tu DOIS écrire les fichiers ci-dessous dans ce format
EXACT. Un validateur automatique le teste. Un écart bloque la pipeline.**

## Rappel — tu es le chasseur, PAS le scoreur

Tu remontes des pistes, tu **ne notes pas** les critères poids/disruptivité/delta/matière/contradiction. C'est le vérificateur qui note. Tu livres la matière brute pour qu'il puisse noter.

## Fichiers à écrire

### 1. `pistes-<chasseur>-T<n>.md` (à la racine du workspace)
Un fichier par (chasseur × tour), nommé EXACTEMENT `pistes-<slug>-T<n>.md` — pas `notes/pistes-…`, pas `candidates-…`. Le monteur ne trouve rien sinon.

Liste ORDONNÉE, meilleur en premier, un finding par bloc. Format libre en markdown, mais chaque bloc DOIT contenir :
- `## <fid> — <titre compréhensible seul>`  
  (titre en FR, sans jargon non glosé, sujet nommé, fait concret en tête — **JAMAIS** « Ceux qui… », « Un truc qui… », accroche à énigme)
- `**URL** : <url réelle>`
- `**Date du fait** : <YYYY-MM-DD>` + `**Âge** : <N> jours`
- `**Domaine source** : <domaine>`
- `**Sources indépendantes** : ` (liste séparée si plusieurs)
- `**Pertinence owner** : <1 ligne : en quoi ce finding importe au lecteur>`
- `**Tag continuité** : NEW | MÀJ:<slug-fil> | SUITE:<entité> | PROMEUT:<signal>`
- (Si disruptif) `**Ce qui est bousculé** : <nommé, avec fait daté>`

### 2. `passants-raw.jsonl` (à la racine)
Un JSON par ligne, la version machine-lisible de tes pistes, pour que le vérificateur puisse les manger sans reparser du markdown.

**Schéma** :
```json
{"id": "<fid>", "titre": "...", "url": "...", "date_fait": "YYYY-MM-DD", "age_jours": N, "domaine": "...", "sources": [{"url": "...", "date": "...", "titre": "..."}], "so_what": "...", "continuation_fil": "<slug>" | null, "bousculement": "..." | null, "matiere_factuelle": "<dossier factuel libre>"}
```

## Ce que tu ne dois PAS faire

- Écrire tes pistes dans `notes/pistes-…` — utilise la racine.
- Renommer le fichier (`candidates-*`, `lot-*`, etc.). Nom figé.
- Renseigner des scores (`poids`, `disruptivite`, `delta`, `matiere`, `contradiction`) — c'est le vérificateur.
- Titre à énigme (« Ceux qui… », « Un truc qui… ») — sujet nommé, fait concret en tête, TOUJOURS.
- Rendre un finding sans URL réelle ni date_fait.

## Comment le validateur teste

Le validateur `etape2_chasse.py` vérifie sur `passants-raw.jsonl` :
- Chaque ligne : `titre`, `url`, `date_fait`, `age_jours`, `so_what`, `continuation_fil` présents.
- `titre` ne commence pas par « Ceux qui », « Un truc qui », « Une chose qui », « Comment », « Pourquoi » (heuristique titre-à-énigme).
- `age_jours` ≤ fenêtre de fraîcheur de l'axe.
- Fichier `pistes-<chasseur>-T<n>.md` correspond à la racine du workspace.

Un manquement → exit 2, message précis.
