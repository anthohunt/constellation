# -*- coding: utf-8 -*-
"""Le mode d'une run : VEILLE ou COLLECTE.

Une veille suit un sujet et l'explique — son livrable se juge sur la clarte de ce
qu'il fait comprendre. Une collecte ramene des elements precis (des offres, des
appels, des dates) — son livrable se juge sur la completude et la verifiabilite
de chaque element, pas sur la qualite d'une explication qu'il n'a pas a produire.

Les contrats de redaction (C6 forme de l'essentiel, C16 mesures dures, C17
relecture profane, C22 style de vulgarisation, C23 juge de style) sont ecrits
pour une veille. En
collecte ils condamneraient un travail correct : une fiche d'offre n'a ni quatre
paragraphes, ni phrase de contraste, et ses sigles (CDI, ESN, R&D) sont le
vocabulaire de son domaine, pas du jargon a gloser.

Une run sans mode declare est une VEILLE : c'est le mode historique, et tous les
profils anterieurs a la question du wizard en relevent.
"""

import json
import pathlib

# Ce qui juge une explication redigee, et n'a donc pas de sens sur une collecte.
CONTRATS_REDACTION = {"C6", "C16", "C17", "C22", "C23"}


def mode_run(workspace):
    """"veille" (defaut) ou "collecte", lu dans le run-config.json du workspace."""
    try:
        rc = pathlib.Path(workspace) / "run-config.json"
        if rc.exists():
            cfg = json.loads(rc.read_text(encoding="utf-8"))
            if str(cfg.get("mode", "")).strip().lower() == "collecte":
                return "collecte"
    except Exception:
        pass
    return "veille"


def est_collecte(workspace):
    return mode_run(workspace) == "collecte"


def filtrer_redaction(errs, workspace, code_de):
    """Retire les defauts de redaction quand la run est une collecte."""
    if not est_collecte(workspace):
        return errs
    return [e for e in errs if code_de(e) not in CONTRATS_REDACTION]
