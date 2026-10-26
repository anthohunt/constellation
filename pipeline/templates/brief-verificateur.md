# CONTRAT DE SORTIE — vérificateur de chasse (phase A)

**Ce bloc est machine-lisible. Tu DOIS écrire les fichiers ci-dessous dans ce format
EXACT, avec ces noms EXACTS. Un validateur automatique vérifie ta sortie avant
que le monteur puisse démarrer. Un écart bloque la pipeline.**

## Fichiers à écrire (dans le workspace `<base>/`)

### 1. `notes-<chasseur>-T<n>.json`
Un fichier par (chasseur × tour), à la racine du workspace. Nommé exactement
`notes-<slug-chasseur>-T<n>.json` (ex. `notes-cognition-creation-T1.json`).

**Schéma** :
```json
{
  "chasseur": "<slug>",
  "tour": <n>,
  "pistes": [
    {
      "id": "<fid>",
      "titre": "<titre du finding>",
      "verdict": "PASSANT" | "SOUS-BARRE" | "ÉLIMINÉ",
      "eliminatoires": {"E1": true|false, "E2": true|false, "E3": true|false, "E4": true|false, "E5": true|false},
      "notes": {"poids": 0-3, "disruptivite": 0-3, "delta": 0-3, "matiere": 0-3, "contradiction": 0-3},
      "justifications": {"poids": "<phrase + objet cité>", "disruptivite": "...", "delta": "...", "matiere": "...", "contradiction": "..."},
      "titre_a_revoir": true|false,
      "raison_titre": "<si titre à énigme, note ici — sinon champ absent>"
    }
  ]
}
```

**Règles dures** :
- Un objet par piste, TOUJOURS les 5 notes (jamais partiel).
- Score = entier de 0 à 3. **Pas de valeur par défaut 0 non justifiée** — si tu mets 0, dis pourquoi dans `justifications`.
- `titre_a_revoir` OBLIGATOIRE (true si accroche à énigme / sujet caché / « Ceux qui… », false sinon). **Ne jamais éliminer un finding pour son titre** — signale-le pour réécriture.

### 2. `circulation-<chasseur>-T<n>.json`
Dossier de circulation (contexte injecté aux juges du poids et de la matière).

**Schéma** :
```json
{
  "chasseur": "<slug>",
  "tour": <n>,
  "pistes_soumises_au_poids": [{"id": "<fid>", "resume": "..."}],
  "pistes_soumises_a_la_matiere": [{"id": "<fid>", "objets_a_verifier": [...]}]
}
```

### 3. `retour-<chasseur>-T<n>.md`
Message au chasseur pour son prochain tour. Prose libre, mais DOIT contenir :
- Ce qui passe / ce qui ne passe pas et pourquoi (par éliminatoire E1-E5)
- Ce que le chasseur doit rejouer / creuser au tour suivant
- Les titres à réécrire (avec proposition)

### 4. `verifier_pass_stamp` (fichier vide, un par lot)
`<base>/state/verifier_pass_stamp-<chasseur>-T<n>` — signe que ce lot a été vérifié.
Le monteur refuse tout lot sans ce stamp.

## Ce que tu ne dois PAS faire

- Écrire un `verif-<chasseur>-T<n>.md` fourre-tout (prose + JSON embarqué). Le monteur ne le lit pas.
- Laisser les 5 notes à 0 sans justification (défaut de placeholder = même effet que ne pas avoir noté).
- Sauter le champ `titre_a_revoir`.
- Éliminer un finding pour son titre.

## Comment le validateur teste

Après ta phase, le validateur `etape2_chasse.py` vérifie :
- Un `notes-*.json` par slug de chasseur (obligatoire).
- Chaque piste a les 5 notes ENTIÈRES (pas d'entier à 0 sans justif).
- Chaque piste a `titre_a_revoir` renseigné.
- Un `verifier_pass_stamp` par (chasseur, tour).

Un seul manquement → exit 2, message précis (chasseur/piste/champ).
