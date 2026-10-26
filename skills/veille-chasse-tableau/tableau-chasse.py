# -*- coding: utf-8 -*-
"""Tableau de controle de la chasse — schema v6.1 (1 chasseur par axe + 2 transversaux).

Version locale a la run. Motif : le script global `veille-chasse-tableau/tableau-chasse.py`
est reste au schema v5 (regex de slug sans tiret + plancher 15 en dur) et ne collecterait
aucun transcript de cette run. Ecart consigne dans `state/ecarts-etape2.md` (E7).
Le script global n'a PAS ete modifie.

Usage :
    python tableau-chasse-v6.py <base-de-run> [--sortie <fichier.md>]

Sources  : mesurees sur <base>/transcripts/chasseur-<slug>-round<N>.jsonl (I9 : sur le
           transcript, jamais sur ce que l'agent declare)
Findings : <base>/state/comptes-chasse.json — INCREMENT par passe, jamais un cumul
Planchers: <base>/state/comptes-chasse.json -> `_planchers` (propre a chaque chasseur)
"""
import io, os, re, sys, json, glob, time, collections


def mesurer(path):
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    fetches = re.findall(r'"name":"WebFetch","input":\{"url":"([^"]*)"', raw)
    searches = re.findall(r'"name":"WebSearch","input":\{"query":"((?:[^"\\]|\\.)*)"', raw)
    cmds = re.findall(r'"name":"Bash","input":\{"command":"((?:[^"\\]|\\.)*)"', raw)
    shell = []
    for c in cmds:
        c = c.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ")
        shell += re.findall(r"https?://[^\s'\"\\)>|;]+", c)
    urls = list(dict.fromkeys(u.rstrip(".,);") for u in fetches + shell))
    hosts = collections.Counter()
    for u in urls:
        m = re.match(r"https?://([^/]+)", u)
        if m:
            hosts[m.group(1).replace("www.", "")] += 1
    dyn = len(re.findall(r'https?://[^\s"\']*(?:\$\(|\$\{|\$[A-Za-z_]|<query>)', raw))
    return {"urls": len(urls), "hosts": len(hosts), "searches": len(searches),
            "top": hosts.most_common(1)[0] if hosts else ("-", 0), "dyn": dyn}


def date_passe(path):
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for _ in range(400):
                l = fh.readline()
                if not l:
                    break
                m = re.search(r'"timestamp"\s*:\s*"(\d{4})-(\d{2})-(\d{2})', l)
                if m:
                    return "%s/%s" % (m.group(3), m.group(2))
    except Exception:
        pass
    return time.strftime("%d/%m", time.localtime(os.path.getmtime(path)))


def tab(base):
    src = collections.defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(base, "transcripts", "chasseur-*.jsonl"))):
        m = re.search(r"chasseur-(.+)-round(\d+)\.jsonl$", os.path.basename(f))  # slugs A TIRETS
        if not m:
            continue
        d = mesurer(f)
        d["date"] = date_passe(f)
        src[m.group(1)][int(m.group(2))] = d

    cc = json.load(io.open(os.path.join(base, "state", "comptes-chasse.json"), encoding="utf-8"))
    planchers = cc.get("_planchers", {})
    plancher_phase = cc.get("_plancher_phase")
    comptes = cc.get("chasseurs", {})

    ordre = []
    cast = os.path.join(base, "casting.json")
    if os.path.exists(cast):
        for a in json.load(io.open(cast, encoding="utf-8")).get("agents", []):
            if a.get("slug"):
                ordre.append(a["slug"])
    trouves = set(src) | set(comptes) | set(planchers)
    chasseurs = [s for s in ordre if s in trouves] + sorted(trouves - set(ordre))
    passes = sorted({t for d in src.values() for t in d} |
                    {int(k.lstrip("p")) for d in comptes.values() for k in d})
    if not passes:
        passes = [1]

    acquis, nv = {}, {}
    for s in chasseurs:
        acquis[s] = sum(v.get("passants") or 0 for v in comptes.get(s, {}).values())
        nv[s] = sum(1 for v in comptes.get(s, {}).values() if v.get("passants") is None)

    out = ["# Tableau de chasse — %s" % os.path.basename(base), "",
           "Mesures prises sur les transcripts figes, jamais sur ce que l'agent declare (I9).", "",
           "## Sources explorees — URL distinctes (hotes distincts) · date de la passe", ""]
    out.append("| Chasseur | " + " | ".join("Passe %d" % t for t in passes) + " | Total URL |")
    out.append("|---|" + "---:|" * (len(passes) + 1))
    col = collections.Counter()
    for s in chasseurs:
        cells, tot = [], 0
        for t in passes:
            d = src.get(s, {}).get(t)
            if not d:
                faites = sorted(src.get(s, {}))
                dernier = max(faites) if faites else 0
                if t > dernier and acquis.get(s, 0) >= planchers.get(s, 10**9):
                    cells.append("*arrete, plancher atteint*")
                elif t > dernier:
                    cells.append("*pas encore*")
                else:
                    cells.append("-")
                continue
            marque = "**%d**" % d["hosts"] if d["hosts"] <= 3 else str(d["hosts"])
            cells.append("%d (%s) · %s" % (d["urls"], marque, d["date"]))
            tot += d["urls"]
            col[t] += d["urls"]
        out.append("| %s | %s | **%d** |" % (s, " | ".join(cells), tot))
    out.append("| **Total** | " + " | ".join("**%d**" % col[t] for t in passes) +
               " | **%d** |" % sum(col.values()))
    out += ["", "*Un nombre d'hotes <= 3 est mis en gras : le brief de cette run ne fixe pas de "
                "quota d'URL, mais signale explicitement le fait de rester sur 3 hotes.*", ""]

    out += ["## Pistes ecrites -> passants (increments par passe)", ""]
    out.append("| Chasseur | " + " | ".join("Passe %d" % t for t in passes) +
               " | Pistes | Passants | Plancher | Statut |")
    out.append("|---|" + "---|" * len(passes) + "---:|---:|---:|---|")
    cp, cq, tp_g, tq_g = collections.Counter(), collections.Counter(), 0, 0
    for s in chasseurs:
        cells, tp, tq = [], 0, 0
        for t in passes:
            c = comptes.get(s, {}).get("p%d" % t)
            if not c:
                cells.append("-" if t <= max(list(comptes.get(s, {}) and
                             [int(k.lstrip('p')) for k in comptes.get(s, {})]) or [0]) else "*pas encore*")
                continue
            pi, pa = c.get("pistes") or 0, c.get("passants")
            tp += pi
            cp[t] += pi
            if pa is None:
                cells.append("%d -> *nv*" % pi)
            else:
                cells.append("%d -> **%d**" % (pi, pa))
                tq += pa
                cq[t] += pa
        pl = planchers.get(s, 0)
        if tq >= pl and pl:
            statut = "**atteint — ne pas relancer**"
        elif nv.get(s):
            statut = "un lot en verification"
        elif len([t for t in passes if comptes.get(s, {}).get("p%d" % t)]) >= 5:
            statut = "**5 passes epuisees — signaler et avancer**"
        else:
            statut = "sous le plancher (-%d) — repart" % (pl - tq)
        out.append("| %s | %s | %d | **%d** | %d | %s |" % (s, " | ".join(cells), tp, tq, pl, statut))
        tp_g += tp
        tq_g += tq
    out.append("| **Total** | " + " | ".join("**%d -> %d**" % (cp[t], cq[t]) for t in passes) +
               " | **%d** | **%d** | **%s** | |" % (tp_g, tq_g, plancher_phase))
    out += ["", "*nv = non verifie, exclu des totaux acquis.*", ""]

    reste = (plancher_phase or 0) - tq_g
    out += ["## Gate de phase", "",
            "- plancher global (somme des planchers de chasseur) : **%s**" % plancher_phase,
            "- passants acquis : **%d**" % tq_g,
            "- reste : **%d**" % reste,
            "", "**%s**" % ("GATE OUVERT — la distillation peut commencer." if reste <= 0 else
                            "GATE FERME — pas de distillation avant le plancher (tranche le 2026-07-21)."), ""]

    conc = []
    for s in chasseurs:
        for t in sorted(src.get(s, {})):
            d = src[s][t]
            if d["urls"] and 100.0 * d["top"][1] / d["urls"] >= 50:
                conc.append("%s p%d : %.0f %% sur `%s`" % (s, t, 100.0 * d["top"][1] / d["urls"], d["top"][0]))
    out += ["## Methode — concentration >= 50 %% sur un seul hote", "",
            ("; ".join(conc) if conc else "aucune"), "",
            "*L'extraction SOUS-COMPTE un chasseur qui script ses appels (cas mesure : 2 comptees "
            "pour 25 reelles). Reconstituer le compte reel dans le brut avant de conclure.*"]
    return "\n".join(out)


def main():
    base = sys.argv[1]
    txt = tab(base)
    if "--sortie" in sys.argv:
        p = sys.argv[sys.argv.index("--sortie") + 1]
        io.open(p, "w", encoding="utf-8").write(txt + "\n")
        print("Ecrit : %s" % p)
    print(txt)


if __name__ == "__main__":
    main()
