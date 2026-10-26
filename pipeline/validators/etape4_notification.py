"""
Validateur etape 3.8 — PREVENIR LE LECTEUR.

Un seul contrat : l'invitation est PARTIE, et on peut le constater.
Le noeud existe pour une raison — le lecteur ne doit pas etre invite sur une
constellation que la verification n'a pas laissee passer — donc la trace de
l'envoi doit dire QUI, VERS QUOI, et AVEC QUEL RETOUR.

C1. `state/notification-envoyee.json` existe et est du JSON lisible.
C2. Il porte un destinataire, l'URL envoyee, et le code de retour de l'API.
C3. Le retour est un succes : une invitation refusee par l'API n'est pas une
    invitation envoyee.

Retour : liste de strings, une par contrat casse.
"""
import json, pathlib


def validate(workspace):
    errs = []
    f = pathlib.Path(workspace) / 'state' / 'notification-envoyee.json'
    if not f.exists():
        return ["C1: `state/notification-envoyee.json` absent — sans trace, on ne sait pas si "
                "le lecteur a ete invite ni sur quelle URL"]
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return [f"C1: `state/notification-envoyee.json` JSON invalide: {e}"]

    dest = d.get('email') or d.get('destinataire') or d.get('to')
    url = d.get('url') or d.get('lien')
    code = d.get('code') or d.get('status') or d.get('http') or d.get('retour')

    if not dest:
        errs.append("C2: aucun destinataire dans la trace — `email` attendu")
    if not url:
        errs.append("C2: aucune URL dans la trace — `url` attendu, celle deployee en 3.4")
    elif '-eval' not in str(url):
        errs.append(f"C2: l'URL envoyee ({url}) n'est pas une constellation d'evaluation "
                    f"— le lecteur note sur `/c/<run>-eval/`, pas ailleurs")
    if code is None:
        errs.append("C2: aucun code de retour — un envoi sans retour n'est pas constate")
    else:
        ok = (str(code).strip() in ('200', '201', 'True', 'true', 'ok', 'OK')
              or d.get('ok') is True)
        if not ok:
            errs.append(f"C3: l'API a repondu `{code}` — l'invitation n'est pas partie. "
                        f"Donner l'URL a la main plutot que de la croire envoyee.")
    return errs
