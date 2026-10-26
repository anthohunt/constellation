#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prevenir le lecteur que son evaluation l'attend.

Une constellation deployee que personne ne sait deployee ne sert a rien : la
barriere humaine ne se franchit que si quelqu'un vient. Le nœud qui deploie
previent donc l'owner, a l'adresse de son profil, avec le lien et de quoi savoir
ce qui l'attend.

La trace de l'envoi est un livrable : sans elle, on ne saurait pas si le mail est
parti, et le nœud pourrait se declarer fini sans avoir prevenu personne.

Usage : notifier-eval.py <workspace> <url> [--dry-run]
"""
import json, pathlib, subprocess, sys, datetime
from email.header import Header


def compte(ws):
    """De quoi le lecteur va-t-il juger : combien de signaux, sur quels axes."""
    try:
        d = json.loads((ws / 'constellation-bundle' / 'constellation-data.json')
                       .read_text(encoding='utf-8'))
    except Exception:
        return 0, []
    n = d.get('nodes') or []
    axes = {}
    for x in n:
        if x.get('type') == 'leaf' or 'axe' in x:
            a = x.get('axe')
            if a:
                axes[a] = axes.get(a, 0) + 1
    return len([x for x in n if x.get('axe')]), sorted(axes.items(), key=lambda kv: -kv[1])


def main():
    ws = pathlib.Path(sys.argv[1])
    url = sys.argv[2]
    essai = '--dry-run' in sys.argv

    cfg = json.loads((ws / 'run-config.json').read_text(encoding='utf-8'))
    dest = cfg.get('email')
    if not dest:
        sys.exit("run-config.json ne porte pas d'adresse : personne a prevenir")

    total, axes = compte(ws)
    detail = ' · '.join('%s %d' % (a, c) for a, c in axes[:6])
    corps = (
        "Ta veille est prête à être évaluée.\n\n"
        "%s\n\n"
        "%d signaux t'attendent%s.\n\n"
        "Tu les parcours, tu corriges le classement de ceux qui sont mal placés, "
        "et tu commentes ce qui mérite un mot. C'est ce que tu corriges qui apprend "
        "à l'agent — pas ce que tu laisses.\n"
        % (url, total, (' — ' + detail) if detail else '')
    )
    sujet = "Ta veille est prête — %d signaux à évaluer" % total
    # un en-tete de courrier ne porte que de l'ASCII : la norme RFC 2047
    # encode le reste, sinon les accents ressortent en charabia
    sujet_entete = Header(sujet, 'utf-8').encode()

    cmd = ['gws', 'gmail', '+send', '--to', dest, '--subject', sujet_entete, '--body', corps]
    if essai:
        cmd.append('--dry-run')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    trace = {'a': dest, 'sujet': sujet, 'url': url, 'signaux': total,
             'envoye': r.returncode == 0, 'essai': essai,
             'quand': datetime.datetime.now(datetime.timezone.utc)
                      .isoformat(timespec='seconds').replace('+00:00', 'Z')}
    if r.returncode != 0:
        trace['erreur'] = (r.stderr or r.stdout)[:400]
    (ws / 'state').mkdir(exist_ok=True)
    (ws / 'state' / 'notification-eval.json').write_text(
        json.dumps(trace, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(trace, ensure_ascii=False))
    return 0 if r.returncode == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
