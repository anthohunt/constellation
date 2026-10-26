# Le profil du texte de référence — traits mesurés, gelés

**Ce que c'est** — la traduction chiffrée de `reference-redaction.md`. Le style ne se juge pas
contre une liste de règles écrites à côté de l'exemple : il se juge contre l'exemple lui-même,
mesuré une fois et figé ici. Une règle et son exemple finissent toujours par se contredire ;
un profil extrait de l'exemple ne le peut pas.

**Comment il a été obtenu** — `outils/profil-style.py reference-redaction.md --corps-apres-tirets`,
sur le corps du texte seul (l'en-tête documentaire est exclu). Le même script tourne sur
l'essentiel à juger : l'écart est une mesure, pas une impression.

**Il ne se recalcule pas à chaque passe.** Deux juges qui ré-analysent l'exemple en tirent deux
lectures, et la variance qu'on cherche à supprimer revient par là. Ces valeurs ne bougent que si
le texte de référence change.

## Les valeurs

| Trait | Référence | Tolérance |
|---|---|---|
| Mots par phrase — médiane | **15** | 11 à 19 |
| Mots par phrase — étendue | **4 à 51** | aucun plafond : l'étendue EST le trait |
| Phrases courtes (≤8 mots) | **26 %** | ≥15 % |
| Phrases longues (>25 mots) | **15 %** | ≤25 % |
| Phrases par paragraphe — médiane | **3** | 2 à 4, jamais plus de 6 |
| Deux-points explicatif | **24 %** des phrases | 10 à 40 % |
| Ouverture sur un connecteur | **31 %** des phrases | 15 à 45 % |
| Gras par paragraphe | **0,4** | ≤1 |
| Questions au lecteur | **0** | 0 |
| Antithèse à négation (« X, pas Y ») | **1** sur 62 phrases | au plus 1 par texte |
| Première personne (« je ») | **0** | 0 |

## Ce que ces mesures démentent

Deux règles qui circulaient ne survivent pas à la mesure, et un juge qui les invoque pose un
défaut irrecevable :

- **Il n'y a pas de plafond de longueur de phrase.** La référence monte à 51 mots. Ce qui fait
  le rythme est l'alternance — un quart de phrases très courtes contre un sixième de très
  longues —, pas un maximum.
- **L'antithèse à négation n'est pas interdite.** La référence l'emploie, une fois. La règle
  vraie est un plafond de fréquence, pas une interdiction.

## Ce qu'un profil ne mesure pas

Il dit si un texte a la **mécanique** de la référence, jamais s'il a sa valeur. Un texte peut
tomber dans toutes les tolérances et n'expliquer rien. C'est pourquoi l'écart de profil ne
bloque jamais une histoire : il coûte des points, et la fidélité aux fiches reste seule
éliminatoire.
