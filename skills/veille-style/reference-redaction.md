# Le texte de référence du style de veille — à fournir

**Ce fichier est vide dans ce dépôt, volontairement.** Le texte de référence d'origine est la
transcription d'une vidéo de vulgarisation tierce : il n'appartient pas à l'auteur de ce dépôt et
ne peut pas être redistribué.

**Ce qu'il faut y mettre** — 1 000 à 1 500 mots d'**explication pure** sur un sujet technique,
dans la langue de la veille, que vous avez le droit d'utiliser (votre propre texte, ou un texte
sous licence libre). C'est lui qui donne le grain d'écriture : les huit gestes de `SKILL.md` en
sont tirés, et le juge de style compare chaque essentiel à ce texte.

**Après l'avoir posé** — séparer l'en-tête documentaire du corps par une ligne `---`, puis
recalculer le profil gelé :

```bash
python3 outils/profil-style.py reference-redaction.md --corps-apres-tirets
```

et reporter les valeurs dans `profil-mesure.md` (celles qui y figurent sont celles du texte
d'origine, à titre d'exemple). Une version anglaise se pose de la même façon dans
`reference-redaction.en.md`.
