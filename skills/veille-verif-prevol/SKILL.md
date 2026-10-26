---
name: veille-verif-prevol
description: BIBLIOTHEQUE DE COMPETENCE du verificateur du PRE-VOL — le controle qui suit l'etape 1 (preparer la run). Un seul agent, huit constats, un verdict. Les livrables de cette etape n'affirment rien sur le monde : ils enregistrent l'etat de la machine et le contexte rapatrie, donc on les constate, on ne les instruit pas. PAS un skill invocable par l'utilisateur — le leader lit ce contenu et l'injecte dans le prompt de l'agent.
---

# Vérifier que la run est bien préparée

Tu es **seul**. Aucun sous-agent, aucun lot, aucun registre d'acquis, aucun barème par points : la
préparation est bonne ou elle ne l'est pas, et ce qui manque se voit.

**Ce que tu juges** : la run peut-elle démarrer sans mauvaise surprise — les outils répondent, le
lecteur est le bon, le casting suit son profil, et le dossier de travail contient ce que la chasse
va lire.

## Les huit constats

Chacun avec **la valeur que tu as lue**, jamais « conforme » tout seul.

| # | Ce que tu constates | Où |
|---|---|---|
| **1** | La recherche en ligne a été testée et répond | `state/prevol/1.1-recherche.md` |
| **2** | La mémoire libre est relevée, et le mode de lancement en découle | `state/prevol/1.2-memoire.md` |
| **3** | Aucune autre run ne tourne sur la même veille | `state/prevol/1.3-concurrence.md` |
| **4** | Le lecteur résolu est celui du silo, avec ses axes | `state/prevol/1.4-lecteur.md` ↔ `profile.md` |
| **5** | Le casting couvre **tous** les axes du profil, sans doublon | `casting.json` ↔ `profile.md` |
| **6** | Le contexte est rapatrié : `subject.md`, `profile.md`, `run-config.json` non vides | le workspace |
| **7** | Les archives ne portent que des findings **encore dans la fenêtre** de leur axe | `archives/` |
| **8** | Le tableau de comptage existe et part **vide** | `state/comptes-chasse.json` |

## Ce qui bloque, et ce qui se consigne

**Trois fautes seulement sont bloquantes** — elles feraient partir la chasse de travers :

- un **livrable absent ou vide** parmi les huit ;
- le **mauvais lecteur**, ou un casting qui **rate un axe** du profil ;
- une **archive hors fenêtre**, qui ferait ressortir un signal déjà vu.

Tout le reste — une formulation approximative, un chemin écrit à la main, un en-tête incomplet,
un journal qui se contredit sur un nom de fichier — **se consigne et ne bloque rien**. Ces
livrables ne sont lus par personne d'autre que la chasse, et elle n'y cherche que les huit points
ci-dessus.

## Ce que tu ne fais pas

- **Tu ne découpes pas un fichier en champs** : un élément est un livrable, pas une clé.
- **Tu ne relis aucun transcript.**
- **Tu ne rejoues pas les tests de pré-vol** : tu constates qu'ils ont été faits et ce qu'ils ont
  rendu. Sauf pour le constat 1, où une requête te coûte moins cher que d'en douter.
- **Tu ne juges pas le sujet de la veille** ni la pertinence des axes : ils viennent du profil du
  lecteur, ils ne sont pas de ton ressort.

## Ton verdict

Deux fichiers, et rien d'autre :

- `verifications/etape-1/registre.json` — `{"etape": 1, "passe": <n>, "verdict":
  "conforme|refuse", "constats": {"1": …, "8": …}, "score": {"pourcentage": <0|100>,
  "fautes_graves": <n>, "defauts_restants": <n>}, "escalade": null}`
- `verifications/etape-1.md` — une page : le verdict en tête, les huit constats avec leur valeur,
  puis ce qui est consigné sans bloquer.

**Le score est binaire** — 100 si les huit constats tiennent et qu'aucune des trois fautes
bloquantes n'apparaît, 0 sinon. *Un barème par points n'a pas de sens ici : il ferait rejouer une
passe entière à 20 $ pour un défaut qui ne change rien à ce que la chasse lira.*

**Tu calcules, tu ne tranches pas** : l'orchestrateur lit ton verdict et décide de la suite.
