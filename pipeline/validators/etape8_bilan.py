"""
Validateur étape 7 — BILAN / POST-MORTEM.

Gate de sortie : la run a-t-elle produit son bilan (rendement de chasse, mesures,
ce qui doit survivre) ? C'est ce qui rend le système apprenant d'une run à l'autre.

Contrats :
1. Au moins un artefact de bilan présent : post-mortem.md, OU metrics/tokens-run.md,
   OU un metrics/substeps-etape-*.md.
"""
import glob, pathlib

def validate(workspace):
    errs = []
    ws = pathlib.Path(workspace)

    has = (
        (ws / 'post-mortem.md').exists()
        or (ws / 'metrics' / 'tokens-run.md').exists()
        or bool(glob.glob(str(ws / 'metrics' / 'substeps-etape-*.md')))
    )
    if not has:
        errs.append("C1: aucun artefact de bilan (ni `post-mortem.md`, ni `metrics/tokens-run.md`, "
                    "ni `metrics/substeps-etape-*.md`) — la run n'a pas produit son retour d'expérience")

    return errs
