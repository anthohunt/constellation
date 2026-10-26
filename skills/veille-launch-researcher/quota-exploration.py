"""Controle de la CONCENTRATION d'exploration (pas de quota d'URL).

Decision post-mortem 2026-07-29 : le brief de chasse prime sur l'ancien plancher
d'effort de 50 URL (regle du 2026-07-21, abrogee ici). « Ouvrir 50 pages au hasard
est contre-productif ; mais rester sur 3 hotes sera signale. » Le SIGNAL de methode
est donc la concentration d'hotes, jamais le nombre d'URL. Le nombre d'URL reste
mesure, mais a titre indicatif seulement.

Usage :
    python quota-exploration.py <dossier-transcripts> [seuil]

Compte, par transcript de chasseur :
  - URL distinctes reellement appelees (WebFetch, curl en Bash, Playwright)
  - hotes distincts (indicateur d'accompagnement, PAS un second seuil)
  - requetes WebSearch litterales

AVERTISSEMENT INTEGRE AU RESULTAT : l'extraction mecanique SOUS-COMPTE un chasseur
qui script ses appels d'API (URL construites a l'execution). Cas mesure le 2026-07-20 :
2 requetes comptees pour 25 reelles. Avant de declarer un chasseur sous le quota,
reconstituer le compte reel dans le brut.
"""
import io, os, re, sys, glob, collections

SEUIL_DEFAUT = 50


def compter(path):
    raw = io.open(path, encoding="utf-8", errors="replace").read()

    fetches = re.findall(r'"name":"WebFetch","input":\{"url":"([^"]*)"', raw)
    searches = re.findall(r'"name":"WebSearch","input":\{"query":"((?:[^"\\]|\\.)*)"', raw)
    cmds = re.findall(r'"name":"Bash","input":\{"command":"((?:[^"\\]|\\.)*)"', raw)

    shell = []
    for c in cmds:
        c = c.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ")
        shell += re.findall(r"https?://[^\s'\"\\)>|;]+", c)

    urls = [u.rstrip(".,);") for u in fetches + shell]
    distinctes = list(dict.fromkeys(urls))

    hosts = collections.Counter()
    for u in distinctes:
        m = re.match(r"https?://([^/]+)", u)
        if m:
            hosts[m.group(1).replace("www.", "")] += 1

    # signal de scriptage : URL construites dynamiquement
    dyn = len(re.findall(r'https?://[^\s"\']*(?:\$\(|\$\{|\$[A-Za-z_]|<query>)', raw))

    return {
        "urls": len(distinctes),
        "hosts": len(hosts),
        "top_host": hosts.most_common(1)[0] if hosts else ("-", 0),
        "searches": len(searches),
        "dyn": dyn,
    }


def main():
    dossier = sys.argv[1] if len(sys.argv) > 1 else "."
    seuil = int(sys.argv[2]) if len(sys.argv) > 2 else SEUIL_DEFAUT

    fichiers = sorted(glob.glob(os.path.join(dossier, "chasseur-*.jsonl")))
    if not fichiers:
        print("Aucun transcript de chasseur dans %s" % dossier)
        return

    print("PAS de quota d'URL (decision post-mortem 2026-07-29 : le brief prime).")
    print("Signal de methode = CONCENTRATION d'hotes. Le nombre d'URL est indicatif (ref %d)." % seuil)
    print()
    print("%-34s %7s %7s %8s  %-28s %s" %
          ("passe", "URL", "hotes", "search", "hote dominant", "verdict"))
    print("-" * 104)

    suspects = []
    for f in fichiers:
        nom = os.path.basename(f).replace(".jsonl", "")
        d = compter(f)
        # Verdict = CONCENTRATION d'hotes (brief : « rester sur 3 hotes sera signale »), pas le compte d'URL.
        pct_top = 100.0 * d["top_host"][1] / max(d["urls"], 1) if d["hosts"] else 0
        if d["hosts"] <= 3 or pct_top > 60:
            verdict = "CONCENTRE (%d hotes, top %.0f%%) - a signaler" % (d["hosts"], pct_top)
        else:
            verdict = "OK (diversite d'hotes)"
        if d["dyn"] > 0:
            verdict += " [scripte : a reconstituer]"
            suspects.append(nom)
        part = ""
        if d["hosts"]:
            pct = 100.0 * d["top_host"][1] / max(d["urls"], 1)
            part = "%s (%.0f%%)" % (d["top_host"][0][:20], pct)
        print("%-34s %7d %7d %8d  %-28s %s" %
              (nom[:34], d["urls"], d["hosts"], d["searches"], part, verdict))

    print()
    print("Le nombre d'URL est un INDICATEUR, jamais un seuil de passage.")
    print("Signale : rester sur <=3 hotes ou >60%% sur un seul hote (chasse en tunnel).")
    print("Signaler au rapport de methode, ne JAMAIS bloquer un lot sur ce motif.")
    if suspects:
        print()
        print("A RECONSTITUER AVANT DE CONCLURE (URL construites a l'execution) :")
        for s in suspects:
            print("  - %s" % s)


if __name__ == "__main__":
    main()
