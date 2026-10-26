---
name: veille-chasse-tableau
description: Produit les tableaux de bord d'une phase de chasse de veille — sources explorées et rendement (pistes → passants), par chasseur et par tour, tours en axe horizontal, totaux en ligne et en colonne. Mesure les sources automatiquement sur les transcripts bruts (jamais sur ce que le chasseur déclare) et confronte chaque passe au budget d'effort du chasseur. Déclencheurs — "/veille-chasse-tableau", "tableau de chasse", "tableau des sources", "bilan par chasseur et par tour", "montre les compteurs de la run". Utilisable en cours de run comme après.
---

# Veille — tableaux de chasse

## Ce que fait ce skill

Deux tableaux, dans ce format, **demandés souvent** par le lecteur :

1. **Sources explorées** — URL distinctes, hôtes distincts entre parenthèses.
2. **Pistes écrites → passants** — le rendement.

Plus une confrontation au **budget d'effort** (≥15 pages ouvertes · ≥8 formulations · ≥5 hors liste de résultats · ≥3 hors moteur généraliste — barème dans `veille-launch-researcher`) et un signalement de la **concentration** sur un hôte unique. Les chiffres se relèvent dans les lots de pistes et dans le transcript de chaque chasseur — aucun journal d'effort n'existe. **Une source ouverte est une URL réellement ouverte** (`WebFetch`, `curl`, `gh api`) : les pages de résultats de recherche n'en sont pas, et ne se comptent nulle part dans ces tableaux.

## Les trois règles de forme, non négociables

Elles viennent de corrections explicites du lecteur. Ne pas y déroger sans qu'il le demande.

• **Les tours sont en axe HORIZONTAL**, les chasseurs en lignes. Jamais l'inverse.
• **Les totaux figurent toujours** — en bout de ligne (par chasseur) *et* en bas de colonne (par tour). Le total de `passants` en particulier : son absence a été signalée comme un manque.
• **L'ordre est celui du casting**, pas l'ordre alphabétique. C'est l'ordre dans lequel le lecteur lit ses chasseurs.

## Usage

```bash
python ~/.claude/skills/veille-chasse-tableau/tableau-chasse.py <base-de-run>
# options : --seuil 50   --sortie <fichier.md>
```

`<base-de-run>` = le dossier de la run, ex. `$FLUX_RUNS_HOME/veille-runs/<owner>-<horodatage>`.
Si le lecteur ne précise pas la run, prendre le workspace de l'**owner actif** dans `$FLUX_RUNS_HOME/veille-runs/` — pas simplement le plus récent, les workspaces sont owner-tagués.

## D'où viennent les deux moitiés du tableau

**Les sources sont mesurées, jamais déclarées.** Extraction sur `<base>/transcripts/chasseur-<persona>-round<n>.jsonl` : WebFetch, URL dans les commandes Bash, requêtes WebSearch. Le chasseur ne se compte pas lui-même — c'est le principe de tout le dispositif.

Les transcripts doivent donc être **figés dans le workspace** sous ce nom exact. S'ils manquent, les copier depuis `~/.claude/projects/<slug>/<sessionId>/subagents/agent-<agentId>.jsonl`.

**Les findings sont lus dans `<base>/state/comptes-chasse.json`**, tenu par le leader à chaque retour de vérificateur :

```json
{
  "academique": { "1": {"pistes": 18, "passants": 10},
                  "2": {"pistes": 5,  "passants": 1} },
  "contrarian": { "3": {"pistes": 13, "passants": null} }
}
```

• `"passants": null` → affiché `nv` (non vérifié), **exclu des totaux acquis**. Ne jamais estimer un lot non vérifié pour gonfler un total.
• Un tour absent → affiché `-`.
• Les clés commençant par `_` sont des métadonnées, ignorées.
• Sans ce fichier, seul le tableau des sources est produit.

## Deux pièges de lecture, à reporter avec le tableau

**1. L'extraction sous-compte les chasseurs qui scriptent.** Un chasseur qui construit ses URL à l'exécution (`$(python -c ...)`, `$IDS`) est invisible à l'extraction. Cas mesuré : **2 requêtes comptées pour 25 réelles**, et un vérificateur a d'abord lu ça comme une fabrication avant de conclure l'inverse. Le script marque ces passes `[scripté : à reconstituer]`. **Ne jamais déclarer un chasseur sous son budget sans avoir reconstitué son compte dans le brut.**

**2. Le nombre d'hôtes est un indicateur, pas un second seuil.** Un chasseur qui atteint son compte de pages sur 3 hôtes a satisfait la lettre du budget en paginant. Le script signale toute passe à ≥ 50 % sur un seul hôte. Cas réel : un chasseur à **100 % sur `api.github.com`** pendant un tour entier. Ça se signale au rapport de méthode, ça ne bloque pas le lot.

## Ce que le tableau sert à voir

Ce n'est pas de la décoration de rapport. Les lectures qu'il a déjà permises :

• **L'effondrement du tour 2** — chaque chasseur explore moins au tour 2 qu'au tour 1, sans exception. C'est cette mesure qui a fait écrire la note de réouverture dans `veille-launch-researcher`.
• **Le rendement décroît par tour** (38 % → 39 % → 21 %) : les chasseurs cueillent le plus accessible d'abord. D'où l'argument du budget d'effort — un premier tour étroit plafonne le compte final, quel que soit le nombre de tours ensuite.
• **Volume et rendement ne sont pas la même chose.** Le chasseur qui a le plus exploré au tour 1 n'a pas le meilleur rendement ; celui qui a le meilleur rendement a le plus mauvais compte final. Explorer large ne garantit pas de trouver, mais explorer étroit plafonne le total.

En commentant le tableau, **rester sur ce que la mesure porte**. Treize passes, c'est peu : signaler les contre-exemples au lieu de les lisser.

## Règles dures

• **Sources mesurées sur le transcript, jamais sur la déclaration du chasseur.**
• **Un lot non vérifié reste `nv`** et n'entre dans aucun total acquis.
• **Tours en horizontal, totaux en ligne et en colonne, ordre du casting.**
• **Signaler la concentration sur un hôte** en même temps que le compte d'URL — l'un sans l'autre se laisse tromper.
• **Reconstituer avant d'accuser** un chasseur qui script.
