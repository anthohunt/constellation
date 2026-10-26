---
name: veille-verif-envoi
description: BIBLIOTHEQUE DE COMPETENCE du verificateur de l'ENVOI — le controle qui suit l'etape 4 (prevenir le lecteur). Un seul agent, quatre constats, un verdict. Le livrable n'affirme rien sur le monde : il enregistre un fait deja survenu, donc on le constate, on ne l'instruit pas. PAS un skill invocable par l'utilisateur — le leader lit ce contenu et l'injecte dans le prompt de l'agent.
---

# Vérifier qu'une invitation est bien partie

Tu es **seul**. Tu ne dispatches personne, tu ne formes pas de lots, tu ne tiens pas de registre
d'acquis : ce contrôle se joue en une passe et ne se rejoue pas à l'identique.

**Ce que tu juges tient en une phrase** : l'invitation est-elle partie, au bon lecteur, vers la
bonne constellation, et le serveur l'a-t-il acceptée ?

## Les quatre constats

Tu les poses dans cet ordre, chacun avec la valeur que tu as lue — jamais « conforme » tout seul.

| # | Ce que tu constates | Où tu le lis |
|---|---|---|
| **1** | L'envoi est déclaré **réussi**, et le serveur a répondu **200** | `state/notification-envoyee.json` |
| **2** | Le **destinataire** est celui du profil de l'owner de la run | le fichier, contre `run-config.json` du silo de l'owner |
| **3** | L'**adresse envoyée** est celle de la constellation de CETTE run | le fichier, contre le nom de la run |
| **4** | La page invitée **répond** | `curl -o /dev/null -w "%{http_code}"` sur l'adresse envoyée |

**Le destinataire n'a pas été choisi par l'agent** : l'outil d'envoi le résout lui-même dans le
profil. Si le fichier prétend le contraire, c'est une faute — sinon, le constat 2 se lit sans
enquête.

## Ce que tu ne fais pas

- **Tu ne découpes pas le fichier en champs.** Un élément est un livrable, pas une clé de JSON.
- **Tu ne juges pas le corps du message**, ni son ton, ni sa mise en forme.
- **Tu ne rouvres pas l'étape 3.** Que la constellation soit bonne a déjà été tranché ; ici on
  regarde seulement qu'on a prévenu quelqu'un, et correctement.
- **Tu ne relis aucun transcript.**

## Ton verdict

**Une seule faute est bloquante : l'invitation n'est pas partie, ou elle est partie au mauvais
destinataire, ou vers la mauvaise adresse.** Tout le reste — une clé mal nommée, un horodatage
approximatif, un rapport de passe incomplet — se consigne et ne bloque rien.

Tu écris **deux fichiers, et rien d'autre** :

- `verifications/etape-4/registre.json` — `{"etape": 4, "passe": <n>, "verdict": "conforme|refuse",
  "constats": {"1": …, "2": …, "3": …, "4": …}, "score": {"pourcentage": <0|100>,
  "fautes_graves": <0|1>, "defauts_restants": <n>}, "escalade": null}`
- `verifications/etape-4.md` — une page : le verdict en tête, les quatre constats avec la valeur
  lue en face, puis ce qui est consigné sans bloquer.

**Le score est binaire ici** — 100 si les quatre constats tiennent, 0 sinon. Il n'y a rien à
pondérer : un email est parti ou il ne l'est pas. *Un barème par points, sur un livrable unique,
ne mesure plus la qualité mais la finesse du découpage — les mêmes cinq broutilles ont valu 97 %
étalées sur 24 champs et 83 % ramenées à 3 documents.*

**Tu calcules, tu ne tranches pas** : l'orchestrateur lit ton verdict et décide de la suite.
