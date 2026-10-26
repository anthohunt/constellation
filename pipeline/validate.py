#!/usr/bin/env python3
"""
Runner de validation de la pipeline.

Usage :
    python validate.py <N> <workspace>

<N>          numéro d'étape (1..8), ou « <N>-verification » pour son contrôle
<workspace>  chemin absolu du workspace du run

Exit codes :
    0  = tous les contrats de l'étape N sont respectés
    2  = au moins un contrat cassé (message d'erreur détaillé sur stderr)
    3  = erreur interne (validateur introuvable, workspace invalide, etc.)
"""
import sys, os, re, importlib.util, pathlib

VALIDATORS = {
    # Pipeline « veille » — PLUS AUCUN NŒUD NE LES APPELLE : le graphe veille.json ne
    # declare plus de `gate.validateur`. Le travail y est juge par les nœuds de
    # verification (agents frais qui lisent les transcripts), et le seul controle
    # mecanique restant est la PRESENCE des livrables, tenue par run-node.py.
    # Ces entrees restent ici pour rendre un retour en arriere trivial.
    # Le numero de l'etape, le fichier qui la jugeait.
    # Une etape N est suivie de sa verification N.5, jugee par le generique.
    # L'etape 5 (notation) est une barriere HUMAINE : ni transcript ni agent a auditer,
    # donc pas de 5.5.
    1: 'etape1_prevol',
    2: 'etape2_chasse',
    3: 'etape3_constellation',
    4: 'etape4_notification',
    5: 'etape5_notation',
    6: 'etape6_feedback',
    7: 'etape7_publish',
    8: 'etape8_bilan',
    # La verification n'est pas une etape de plus : elle porte le numero de celle
    # qu'elle juge. Un seul contrat generique, parametre par ce numero.
    '1-verification': 'verif_etape',
    '2-verification': 'verif_etape',
    '3-verification': 'verif_etape',
    '4-verification': 'verif_etape',
    '6-verification': 'verif_etape',
    '7-verification': 'verif_etape',
    # Pipeline « web app » — identifiants textuels : un workflow flux par famille,
    # le numero seul ne suffit plus a designer une etape.
    # Les trois nœuds du graphe : concevoir (composite des moments), construire, revue.
    'webapp-concevoir': 'webapp_concevoir',
    'webapp-parcours': 'webapp_parcours',
    'webapp-construire': 'webapp_construire',
    'webapp-revue': 'webapp_revue',
    # Moments appelés par le composite, jouables seuls. Les entrées build, durcissement
    # et livraison ne sont plus appelées par aucun nœud : elles restent pour rendre un
    # retour en arrière trivial, comme celles de la veille.
    'webapp-cadrage': 'webapp_cadrage',
    'webapp-concept': 'webapp_concept',
    'webapp-canvas': 'webapp_canvas',
    'webapp-design-valide': 'webapp_design_valide',
    'webapp-kit': 'webapp_kit',
    'webapp-approbation': 'webapp_approbation',
    'webapp-build': 'webapp_build',
    'webapp-durcissement': 'webapp_durcissement',
    'webapp-livraison': 'webapp_livraison',
    # Pipeline « agent » — trois nœuds : concevoir, construire un palier, revue.
    'agent-concevoir': 'agent_concevoir',
    'agent-construire': 'agent_construire',
    'agent-revue': 'agent_revue',
}

def load_validator(name):
    here = pathlib.Path(__file__).parent / 'validators' / f'{name}.py'
    if not here.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, here)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 3
    raw = sys.argv[1].strip()
    try:
        N = float(raw)
        if N == int(N):
            N = int(N)
    except ValueError:
        # identifiant textuel (ex. « webapp3 ») : une etape d un autre workflow flux
        N = raw
    workspace = os.path.abspath(sys.argv[2])
    if not os.path.isdir(workspace):
        print(f"workspace introuvable: {workspace}", file=sys.stderr)
        return 3

    name = VALIDATORS.get(N)
    if not name:
        print(f"[validate] étape {N} — aucun validateur défini (pass-through)", file=sys.stderr)
        return 0

    mod = load_validator(name)
    if not mod:
        print(f"[validate] validateur '{name}' introuvable pour étape {N}", file=sys.stderr)
        return 3

    print(f"[validate] étape {N} — {name} — workspace {workspace}", file=sys.stderr)
    # Le validateur generique de verification a besoin de savoir QUELLE etape il juge.
    try:
        errors = mod.validate(workspace, etape=N) if name == 'verif_etape' else mod.validate(workspace)
    except TypeError:
        errors = mod.validate(workspace)
    # Les codes de contrat (C1, C2, C6…) sont LOCAUX a leur validateur : le C6 de la
    # chasse et celui du montage n'ont rien a voir. On prefixe donc chaque message par
    # l'etape qui definit le contrat — « 2·C6 » se cherche sans ambiguite, « C6 » non.
    # Un contrat porte le numero de l'ETAPE qui le definit : les contrats de contenu
    # appeles par une verification viennent du module de son etape, pas du sien.
    # Un identifiant textuel (webapp-construire) EST le contrat : « webapp·C2 » ne dirait pas
    # lequel des validateurs webapp a refusé.
    prefixe = N if isinstance(N, str) and not N[:1].isdigit() else str(N).split('-')[0]
    errors = [re.sub(r'^\s*(C\d+)', prefixe + '\u00b7' + r'\1', e) if isinstance(e, str) else e
              for e in errors]

    exit_code = 0 if not errors else 2
    if not errors:
        print(f"[validate] ✓ étape {N} — tous les contrats respectés", file=sys.stderr)
    else:
        print(f"\n[validate] ✗ étape {N} — {len(errors)} contrat(s) cassé(s) :\n", file=sys.stderr)
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}", file=sys.stderr)
        print("\n[validate] l'étape suivante ne démarrera pas. Corrige et relance.", file=sys.stderr)

    # HOOK — régénère le rapport de run à chaque validation (idempotent), que ça passe ou pas.
    # Ainsi l'opérateur a toujours une page à jour à ouvrir pour voir où en est/pourquoi ça a planté.
    report_script = pathlib.Path(__file__).parent / 'build_run_report.py'
    if report_script.exists():
        import subprocess
        try:
            r = subprocess.run(
                [sys.executable, str(report_script), workspace],
                capture_output=True, text=True, timeout=30
            )
            if r.returncode == 0:
                # Extrait l'URL du stdout pour la logger
                for line in r.stdout.splitlines():
                    if line.startswith('URL:'):
                        print(f"[report] {line}", file=sys.stderr)
                        break
            else:
                print(f"[report] build_run_report échec (rc={r.returncode}): {r.stderr[:200]}", file=sys.stderr)
        except Exception as e:
            print(f"[report] hook crashé: {type(e).__name__}: {e}", file=sys.stderr)

    return exit_code

if __name__ == '__main__':
    sys.exit(main())
