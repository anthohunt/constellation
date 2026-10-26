---
name: constellation
description: Constellation — le système de veille autonome (graphe `veille` exécuté par le moteur flux + template racine partagé du visualiseur). À utiliser pour lancer ou reprendre une run de veille de bout en bout, comprendre l'architecture, ou propager un correctif du visualiseur à toutes les veilles. Déclencheurs — "/constellation", "lance une veille", "constellation", "propage le template", "reprends la run". Distinct du visualiseur (la page /c/<run>-eval/) : ici c'est le MOTEUR qui produit ces pages.
---

# Constellation — moteur de veille

**Constellation** produit les veilles : le moteur flux déroule le graphe `pipeline/workflows/veille.json` (8 étapes), chaque étape est suivie de sa vérification et d'un validateur bloquant (`pipeline/validate.py`), et toutes les pages sont servies depuis un seul template racine.

## Lancer / reprendre une run

1. Préparer la run (workspace, profil, casting) : skill `veille-start`.
2. Lancer les nœuds depuis la console de flux, ou en ligne de commande :
   `python3 $FLUX_HOME/runtime/run-node.py veille <noeud> --workspace <ws>`.

- **Reprise gratuite** : un nœud déjà vert n'est pas rejoué.
- **Barrière humaine** : la run s'arrête à la notation (le lecteur note sur `/c/<run>-eval/`), puis reprend au feedback et à la publication.
- **Blocage propre** : un validateur rouge stoppe net avec le contrat cassé — jamais de « je crois l'avoir fait ».

## Le template racine partagé (règle d'or)

Le site (`server/`) sert, pour chaque run, `constellation.html`, `constellation-data.json` et `vendor/` depuis `$CONSTELLATION_DATA/runs/<run>/`. La page est une copie du template canonique ; seule la **data** change d'une run à l'autre.

**Toute correction du visualiseur se fait dans le template canonique** `viewer/constellation.template.html`, puis se recopie dans les runs déjà déployées (`viewer/deployer-eval.sh` le pose au premier déploiement). Ne jamais éditer une copie par run : elle divergerait.

## Données bilingues

Chaque finding porte ses deux langues (`headline_fr/_en`, `lead_fr/_en`, `fiche.essentiel_fr/_en`) et les axes bilingues à la racine (`axes_fr`, `axes_en`). Le visualiseur bascule FR↔EN ; sans les champs traduits, le bouton EN ne s'affiche pas. Le synthétiseur (étape 3) DOIT produire les deux langues — voir `veille-agent-synthetiseur` et `veille-assemble-niveau1`.

## Vérifier une UI du visualiseur

Le navigateur se pilote sans écran : Chromium sans tête (puppeteer ou Playwright), WebGL via `--enable-unsafe-swiftshader`. `grep -a` obligatoire sur le template (lignes très longues → grep le voit comme binaire sinon).
