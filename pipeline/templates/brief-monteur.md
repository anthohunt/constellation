# CONTRAT DE SORTIE — Le monteur (étape 3, `veille-assemble-niveau1`)

**Ce bloc est machine-lisible. Tu DOIS respecter les gates d'entrée et écrire les
fichiers ci-dessous dans ce format EXACT. Un validateur automatique vérifie ta
sortie avant que l'étape 4 (notation humaine) puisse démarrer. Un écart bloque
la pipeline.**

## Gate d'entrée (à vérifier AVANT d'assembler quoi que ce soit)

1. Pour chaque chasseur de la chasse, `<base>/state/verifier_pass_stamp-<chasseur>-T<n>` DOIT exister → sinon, **REJET du lot entier**, exit avec message : « lot `<chasseur>` non vérifié, phase 2b manquante ».
2. Pour chaque chasseur, `<base>/notes-<chasseur>-T<n>.json` DOIT exister → sinon, **REJET** avec message : « notes du chasseur `<chasseur>` absentes ».
3. Chaque piste PASSANTE dans `notes-*.json` DOIT avoir ses 5 notes non-nulles-non-défaut (jamais `{0,0,0,0,0}` sans justification).

## Fichiers à écrire

### 1. `findings.json` (à la racine du workspace)
Bundle niveau 1. Un objet par finding retenu (après dédup).

**Schéma** :
```json
{
  "run": "<run-id>",
  "watch": "<watch>",
  "generated_at": "<ISO>",
  "findings": [
    {
      "id": "<fid>",
      "titre": "<titre>",
      "axe": "<nom-axe défini du profil owner> | Transverse | Découverte",
      "url": "<url source primaire>",
      "date_fait": "<YYYY-MM-DD>",
      "essentiel": "<4 paragraphes>",
      "notes_chasse": {"poids": <int>, "disruptivite": <int>, "delta": <int>, "matiere": <int>, "contradiction": <int>},
      "notes_justifications": {"poids": "...", "disruptivite": "...", ...},
      "tier": "Excellent" | "Cool" | "Intéressant" | "Neutre" | "Bof" | "Inutile",
      "tier_source": "agent",
      "tier_justification": "<1 phrase, 15-30 mots, pourquoi ce tier>",
      "titre_a_revoir": true|false,
      "fil": "<slug-fil>" | null,
      "verifier_pass_stamp": "<hash SHA1 du verdict>",
      "essentiel_verifie": true,
      "essentiel_verif_stamp": "<hash SHA1 du verdict verif-carte>",
      "priorite_relecture": true|false,
      "priorite_motif": "<court, ex. 'Excellent pré-classé à valider', 'hésite entre Cool et Intéressant', 'seul Excellent de son axe'>"
    }
  ],
  "fils": [
    {
      "slug": "<slug>",
      "libelle": "<nom lisible du fil>",
      "premiere_run": "<run-id>",
      "findings_courant": ["<fid>", "..."],
      "findings_passes": [{"run": "<run-id>", "fid": "<fid>", "titre": "..."}],
      "synthese": "<paragraphe 800-1500 caractères — synthèse productive du fil : où en est le mouvement, quelles évolutions récentes, quelle lecture actionnable en tirer>"
    }
  ],
  "axes": [{"nom": "<axe>", "findings": <n>, "tier_distribution": {"Excellent": n, ...}}]
}
```

**Règles dures sur les tiers** :
- Base du pré-classement : `notes_chasse` (poids × disruptivité × delta) + le deck (si présent).
- **Au mérite absolu** : un axe peut avoir 3 Excellents et 0 Inutile si la matière l'exige.
- **Test anti-symétrie** : si les 6 tiers ont exactement les mêmes comptes sur tous les axes (ex. `1/1/2/1/1/1` partout), c'est un remplissage de cases — REVOIR MANUELLEMENT.
- **Ordre des tiers (proéminence décroissante)** : Excellent · Cool · Intéressant · Neutre · Bof · Inutile.

## Priorité de relecture — uncertainty sampling

Tu DOIS marquer **entre 15 % et 25 % des findings** avec `priorite_relecture: true` — ceux où l'avis de l'utilisateur a le plus de valeur. Critères de sélection :
- **Findings incertains** : ton pré-classement était limite entre 2 tiers voisins (Cool vs Intéressant, Bof vs Neutre).
- **Excellents pré-classés** : à valider en priorité (pattern historique : plus vite rétrogradés que confirmés → besoin de check humain).
- **Findings singuliers** : seul de son axe dans un tier extrême (seul Excellent d'un axe, seul Inutile d'un axe → décision plus lourde de conséquences).
- **Contradictions internes** : notes chasse contradictoires (poids haut + delta bas, ou disruptivité haute + matière basse).

`priorite_motif` : phrase courte qui explique pourquoi ce finding est prioritaire — le viewer l'affiche en tooltip.

L'utilisateur peut voir ces findings d'abord (mode « prioritaires en tête »). Les autres restent visibles mais leur pré-classement est **le default validé** si l'utilisateur ne les ouvre pas.

## Règles dures sur les axes

Trois familles d'axes, distinctes :
- **Axes définis** — ceux du profil owner (`owners/<owner>/preferences/<watch>-preferences.md` ou équivalent). Chaque finding qui relève clairement d'un axe défini y est rangé.
- **Transverse** — findings qui **traversent** ≥ 2 axes définis (ex. un finding modèles + hardware). Un axe technique, pas une catégorie fourre-tout.
- **Découverte** — findings qui ne relèvent d'aucun axe défini ET ne traversent rien de connu — sujet nouveau, souvent remonté par la sérendipité / le quota d'exploration. Cet axe rend visible ce que la veille apporte au-delà de ce qu'on lui a demandé.

**Interdit** : ranger en Transverse un finding qui ne traverse pas — c'est un Découverte, pas un Transverse.
- **Signal de préférence gradué émis vers le run suivant** : Excellent +3 · Cool +2 · Intéressant +1 · Neutre 0 · Bof −2 · Inutile −3.
- `tier_justification` OBLIGATOIRE pour chaque finding (pas d'exception).

### 1.a.bis Vérification de chaque essentiel — via `veille-verif-carte`

Après qu'un synthétiseur t'a rendu son essentiel 4-temps, tu DOIS dispatcher un `veille-verif-carte` sur cet essentiel avant de l'accepter dans le bundle. Le vérificateur applique le **test profane** (jargon glosé, TON STANDARDISÉ, pas de sur-traduction, P2 ouvre par une analogie) et rend un verdict `PASSANT | À_RÉÉCRIRE`.

- Verdict PASSANT → finding porte `essentiel_verifie: true` + `essentiel_verif_stamp: <hash>`.
- Verdict À_RÉÉCRIRE → tu renvoies au synthétiseur avec le retour du vérificateur (max 3 allers-retours). Après 3 tours, tu passes en PASSANT-forcé et loggues.

Écris chaque verdict dans `<base>/verifications-carte/<fid>.json` : `{fid, verdict, motifs: [...], reecritures: [...], stamp: <hash>}`.

### 1.b. Synthèse par fil actif — via synthétiseur mode FIL

Pour **chaque fil actif dans le run** (≥ 2 findings courants OU ≥ 1 finding courant + ≥ 2 findings passés), tu DOIS dispatcher un synthétiseur en mode FIL qui produit `synthese` — un paragraphe de 800-1500 caractères qui :
- constate les mouvements du fil (que dit-il, à travers ses findings courants + passés)
- pointe les évolutions récentes (accélérations, contradictions, virages)
- tire une lecture actionnable (« → arrêter de tracker X, chercher plutôt Y »)

Le synthétiseur reçoit en entrée : les findings du fil (courants) + les findings des mêmes fils dans les runs passés (lus depuis `owners/<owner>/db/memory/<watch>.json`). Il écrit `synthese` dans l'objet `fils[]` du bundle.

### 2. `constellation-data.json` (dans le bundle de déploiement)
Généré via `build_constellation.py` à partir de `findings.json`. Doit porter chaque
node avec ses champs (voir `contracts/constellation.schema.json`).

## Ce que tu ne dois PAS faire

- Assembler un findings.json avec `notes: {0,0,0,0,0}` sur tous les findings — signal que les scores n'ont pas voyagé (contrat cassé côté vérificateur).
- Créer une répartition 1/2/2/1 uniforme sur tous les axes (symétrie mécanique interdite).
- Sauter le champ `tier_justification`, `titre_a_revoir`, `fil`.
- Inventer un slug de fil hors de la liste-close des fils suivis.
- Déployer la constellation avant d'avoir écrit findings.json valide.

## Comment le validateur teste

Après ta phase, le validateur `etape3_constellation.py` vérifie :
- `findings.json` existe, JSON valide, schéma respecté.
- Chaque finding a ses 5 `notes_chasse` non-défaut, `tier` valide, `tier_justification` présent (15-30 mots), `titre_a_revoir` renseigné.
- Ratio de findings avec `notes_chasse.poids == 0 && matiere == 0 && delta == 0` < 5 % (sinon = les scores n'ont pas voyagé).
- Anti-symétrie : pas de distribution identique sur ≥ 6 axes.
- `constellation-data.json` déployé + `/c/<run>-eval/` répond HTTP 200.

Un seul manquement → exit 2, message précis.
