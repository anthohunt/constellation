# -*- coding: utf-8 -*-
"""Genere constellation-data.json pour CE run, au format du moteur Three.js existant.

PROFILE-AGNOSTIC (refonte 2026-07-23) : les axes et l'axe de chaque finding sont
LUS DANS LES DONNEES DU RUN, plus jamais codes en dur pour ai-watch.
Ordre de preference des entrees :
  1. findings.json  (bundle canonique : id, titre, axe, url, essentiel, objets, cid)  + summaries.json (resumes)
  2. fallback legacy : cartes/F*.json + findings-pool.md (## Fn) + heuristique mots-cles + resumes/ dir

Usage : python build_constellation.py <workspace-du-run>
Sortie : <workspace>/constellation/constellation-data.json
"""
import io, os, re, json, glob, sys, unicodedata

if len(sys.argv) < 2:
    sys.exit("usage : python build_constellation.py <workspace-du-run>")
BASE = sys.argv[1]
OUT_DIR = os.path.join(BASE, "constellation")

# --- axes legacy ai-watch : SEULEMENT si le run ne porte aucune donnee d'axe ----
AXES_LEGACY = ["Builder ecosystem", "Frameworks self-host & runtimes",
        "Hardware self-host & local", "MCP & protocoles agents",
        "Modeles OSS self-hostables", "Nouveaux horizons",
        "Papers arXiv", "Personal AI, wearables, SLM edge"]
REGLES = [
    (r"\bMCP\b|model context protocol|protocole|protocol|agent framework|tool[- ]?use", "MCP & protocoles agents"),
    (r"VRAM|GPU|4090|3090|carte graphique|quantization|quantif|Go de RAM|\bGo\b|hardware|edge device|nvidia|cuda", "Hardware self-host & local"),
    (r"wearable|\bSLM\b|on[- ]?device|smartphone|Quest|lunettes|montre|Personal AI|assistant perso", "Personal AI, wearables, SLM edge"),
    (r"Ollama|llama\.cpp|vLLM|runtime|self[- ]?host|inference server|serveur d'inf|framework", "Frameworks self-host & runtimes"),
    (r"mod[eè]le|model|Qwen|Llama|Mistral|Gemma|SWE[- ]?bench|weights|open[- ]?weights|benchmark|OSS", "Modeles OSS self-hostables"),
    (r"IDE|dev tool|builder|ecosystem|Cursor|Copilot|editor|SDK", "Builder ecosystem"),
]


def _fils_depuis_liens(racine, nodes):
    """Convertit `publish/liens.json` en fils affichables.

    Une SUITE (meme sujet qui avance) devient une chaine datee, tracee dans la
    constellation. Un RAPPROCHEMENT (deux fiches qui s'eclairent sans se suivre)
    devient une chaine de deux, avec son texte : c'est lui qui traverse les axes.
    """
    import json as _json, pathlib as _pl
    base = _pl.Path(racine)
    f = None
    for cand in (base / 'publish' / 'liens.json', base / 'liens.json'):
        if cand.exists():
            f = cand; break
    if not f:
        return []
    try:
        L = _json.loads(f.read_text(encoding='utf-8'))
    except Exception:
        return []
    if isinstance(L, dict):
        L = L.get('liens') or []
    par_id = {}
    for n in nodes:
        par_id[str(n.get('id'))] = n
    fils, i = [], 0
    for l in L:
        if not isinstance(l, dict):
            continue
        srcs = l.get('signaux') or [x for x in (l.get('de'), l.get('vers')) if x]
        srcs = [str(x) for x in srcs if str(x) in par_id]
        if len(srcs) < 2:
            continue
        chaine = [{'id': s, 'date': par_id[s].get('date')} for s in srcs]
        fils.append({'i': i,
                     'type': l.get('type') or 'rapprochement',
                     'axe': (l.get('axes') or [par_id[srcs[-1]].get('axe')])[0],
                     'axes': l.get('axes') or [],
                     'titre': l.get('objet_commun') or 'lien',
                     'texte': l.get('texte') or '',
                     'chaine': chaine})
        for s in srcs:
            par_id[s]['fil'] = i
        i += 1
    return fils


def lire(p):
    try:
        return io.open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def loadj(p, d=None):
    try:
        return json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return d


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", s)) - {"and", "de", "du", "des", "la", "le", "les", "et", "&"}


def match_axe(libre, axes, axtokens=None):
    """Rattache une etiquette d'axe libre (courte ou pleine) a un axe du profil.
    Recouvrement de tokens contre NOM + DESCRIPTION de l'axe (le desc rattrape les
    synonymes : 'Regulation' -> 'Politique & economie' via le desc de l'axe)."""
    if not axes:
        return libre
    if libre in axes:
        return libre
    if libre and "transvers" in libre.lower():
        return next((a for a in axes if "transvers" in a.lower()), "Transverse")
    toks = norm(libre)
    best, score = axes[0], -1
    for a in axes:
        cible = (axtokens or {}).get(a) or norm(a)
        s = len(toks & cible)
        if s > score:
            best, score = a, s
    return best if score > 0 else axes[0]


def premiere_phrase(txt):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", txt or "").strip()
    m = re.search(r"^(.+?[\.\!\?])(\s|$)", t, re.S)
    return (m.group(1) if m else t)[:320].strip()


def norm_date(d):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", d or "")
    return m.group(0) if m else ""


# ---- fallback legacy : fiches depuis findings-pool.md (format ## Fn) ----------
def fiches_du_pool():
    txt = lire(os.path.join(BASE, "findings-pool.md"))
    out = {}
    for bloc in re.split(r"\n---\n", txt):
        m = re.search(r"^##\s*(F\d+)\s*-\s*(\S+)", bloc, re.M)
        if not m:
            continue
        def champ(nom):
            mm = re.search(r"\*\*%s\*\*\s*:\s*(.+)" % nom, bloc)
            return mm.group(1).strip() if mm else ""
        out[m.group(1)] = {"titre": champ("Titre"), "url": champ("Adresse primaire"),
                           "date": champ("Date reelle du fait"), "axe_libre": champ("Axe"),
                           "domaine": champ("Domaine"), "rare": "CASE RARE" in bloc}
    return out


def axe_legacy(meta, essentiel):
    blob = " ".join([meta.get("axe_libre", ""), meta.get("titre", ""), essentiel[:400]])
    for motif, axe in REGLES:
        if re.search(motif, blob, re.I):
            return axe
    if "arxiv.org" in (meta.get("domaine", "") + meta.get("url", "")).lower():
        return "Papers arXiv"
    return "Nouveaux horizons"


def date_de_cid(cid, cand):
    m = re.search(r"###\s*%s(?:\+\w+)?\s*\[.*?\n- URL:.*?date du fait:\s*(\d{4}-\d{2}-\d{2})" % re.escape(cid), cand, re.S)
    return m.group(1) if m else ""


def main():
    cfg = loadj(os.path.join(BASE, "run-config.json"), {}) or {}
    subj = lire(os.path.join(BASE, "subject.md"))
    findings_bundle = loadj(os.path.join(BASE, "findings.json"), None)
    summaries = loadj(os.path.join(BASE, "summaries.json"), None)
    cand = lire(os.path.join(BASE, "candidates.md"))
    degr = set(re.findall(r"\bF\d+\b", lire(os.path.join(BASE, "DEGRADATIONS.md"))))  # vide si absent

    # --- 1. determiner la LISTE D'AXES (depuis les donnees du run) ---
    axes, axtokens = [], {}
    for a in (cfg.get("axes") or []):
        if isinstance(a, dict):
            nom, desc = (a.get("name") or "").strip(), a.get("desc") or ""
        else:
            nom, desc = str(a).strip(), ""
        if nom:
            axes.append(nom)
            axtokens[nom] = norm(nom + " " + desc)
    if not axes and findings_bundle:
        seen = []
        for f in findings_bundle.get("findings", []):
            ax = (f.get("axe") or "").strip()
            if ax and ax not in seen:
                seen.append(ax)
        axes = seen
    legacy = not axes
    if legacy:
        axes = AXES_LEGACY

    nodes = []

    # --- 2. construire les nodes ---
    def sources_de(f):
        """Les sources d'une histoire, normalisees. Un objet a un seul finding en a une :
        le tableau est toujours rempli, c'est lui que la carte affiche."""
        out = []
        for sc in (f.get("sources") or []):
            if not isinstance(sc, dict):
                continue
            url = (sc.get("url") or "").strip()
            if not url:
                continue
            out.append({"titre": (sc.get("titre") or "").strip(),
                        "url": url,
                        "date": norm_date(sc.get("date") or ""),
                        "trouve_par": (sc.get("trouve_par") or "").strip(),
                        "fid": (sc.get("fid") or "").strip()})
        if not out and (f.get("url") or "").strip():
            # bundle sans tableau de sources : la source primaire fait une entree
            out.append({"titre": (f.get("titre") or "").strip(),
                        "url": f["url"].strip(),
                        "date": norm_date(f.get("date_fait") or f.get("date") or ""),
                        "trouve_par": "", "fid": f.get("id", "")})
        return out

    if findings_bundle and not legacy:
        # chemin canonique : findings.json porte l'axe reel par finding
        for i, f in enumerate(findings_bundle.get("findings", [])):
            fid = f.get("id")
            essentiel = f.get("essentiel", "") or ""
            axe = match_axe((f.get("axe") or "").strip(), axes, axtokens)
            head = f.get("titre") or fid
            rapport = lire(os.path.join(BASE, "rapports", "%s.md" % fid))
            date = date_de_cid(f.get("cid", ""), cand) or norm_date(f.get("date_fait") or f.get("date") or "")
            node_id = fid.lower() + "-" + re.sub(r"[^a-z0-9]+", "-", head.lower())[:60].strip("-")
            # --- champs bilingues : langue native = FR ; _en = traduction si presente ---
            head_fr = f.get("titre_fr") or head
            head_en = f.get("titre_en") or f.get("headline_en") or ""
            ess_fr = f.get("essentiel_fr") or essentiel
            ess_en = f.get("essentiel_en") or ""
            lead_fr = f.get("lead_fr") or premiere_phrase(ess_fr)
            lead_en = f.get("lead_en") or (premiere_phrase(ess_en) if ess_en else "")
            node = {"id": node_id, "run": 0, "date": date, "lane": i, "axe": axe,
                "headline": head, "lead": premiere_phrase(essentiel), "kind": "iso",
                "fil": None, "rel": [], "fid": fid, "rare": bool(f.get("rare")),
                "degrade": fid in degr,
                "tier": f.get("tier"), "tier_source": f.get("tier_source"),
                "notes": f.get("notes"),   # vecteur 5 critères de chasse (pré-classement + affichage carte)
                "headline_fr": head_fr, "lead_fr": lead_fr,
                "fiche": {"essentiel": essentiel, "objets": f.get("objets", []) or [],
                          "lead": premiere_phrase(essentiel), "rapport": rapport or None,
                          "essentiel_fr": ess_fr,
                          "sources": sources_de(f),
                          "url": f.get("url", "")}}
            if head_en:
                node["headline_en"] = head_en
            if lead_en:
                node["lead_en"] = lead_en
            if ess_en:
                node["fiche"]["essentiel_en"] = ess_en
            nodes.append(node)
    else:
        # fallback legacy : cartes/ + findings-pool.md + heuristique
        pool = fiches_du_pool()
        for p in sorted(glob.glob(os.path.join(BASE, "cartes", "F*.json")),
                        key=lambda x: int(re.sub(r"\D", "", os.path.basename(x)))):
            c = loadj(p, {})
            fid = c.get("id", os.path.basename(p).replace(".json", ""))
            meta = pool.get(fid, {})
            essentiel = c.get("essentiel", "") or ""
            axe = match_axe(meta.get("axe_libre", ""), axes, axtokens) if not legacy else axe_legacy(meta, essentiel)
            head = meta.get("titre", "") or fid
            rapport = lire(os.path.join(BASE, "rapports", "%s.md" % fid))
            node_id = fid.lower() + "-" + re.sub(r"[^a-z0-9]+", "-", head.lower())[:60].strip("-")
            nodes.append({"id": node_id, "run": 0, "date": norm_date(meta.get("date", "")),
                "lane": len(nodes), "axe": axe, "headline": head,
                "lead": premiere_phrase(essentiel), "kind": "iso", "fil": None, "rel": [],
                "fid": fid, "rare": bool(meta.get("rare")), "degrade": fid in degr,
                "fiche": {"essentiel": essentiel, "objets": c.get("objets", []) or [],
                          "lead": premiere_phrase(essentiel), "rapport": rapport or None,
                          "url": meta.get("url", "")}})

    # --- 3. resumes de niveau ---
    resume_livraison, resume_axe = "", {}
    if summaries:
        resume_livraison = (summaries.get("delivery") or "").strip()
        resume_axe = {k: v for k, v in (summaries.get("axes") or {}).items() if v}
    else:
        rdir = os.path.join(OUT_DIR, "resumes")
        resume_livraison = lire(os.path.join(rdir, "livraison.md")).strip()
        for p in glob.glob(os.path.join(rdir, "axe-*.md")):
            txt = lire(p).strip()
            if txt:
                # 1re ligne = titre d'axe, sinon nom de fichier
                m = re.search(r"^#+\s*(.+)$", txt, re.M)
                resume_axe[match_axe(m.group(1) if m else os.path.basename(p), axes, axtokens)] = txt

    suggestions = (loadj(os.path.join(OUT_DIR, "suggestions-axes.json"), {}) or {}).get("suggestions", [])

    # --- 4. profil de base (pre-remplit l'interface Profil) ---
    def section_md(txt, titre):
        m = re.search(r"^#+\s*" + re.escape(titre) + r".*?\n(.*?)(?=\n#+\s|\Z)", txt, re.S | re.M | re.I)
        return re.sub(r"\n{3,}", "\n\n", m.group(1)).strip() if m else ""
    srules = lire(os.path.join(BASE, "state", "selection-rules.md"))
    profil_base = {
        "mission": (section_md(subj, "Mission") or section_md(subj, "Sujet") or section_md(subj, "Perimetre"))[:800],
        "ton": cfg.get("tone", ""), "audience": cfg.get("audience", ""),
        "reader_level": ("" if (cfg.get("reader_level", cfg.get("familiarity")) is None)
                         else str(cfg.get("reader_level", cfg.get("familiarity")))),
        "langue": cfg.get("language", "fr"), "seuil": cfg.get("threshold", 7),
        "volume": cfg.get("volume", 20),
        "sources": section_md(srules, "Sources scientifiques prioritaires")[:600],
    }

    owner = cfg.get("owner") or (findings_bundle or {}).get("owner") or "demo"
    watch = (findings_bundle or {}).get("subject") or cfg.get("subject_default") or "veille"
    theme = cfg.get("theme") or (re.search(r"#\s*Sujet de veille\s*:\s*(.+)", subj) or [None, watch])[1]
    dates = sorted({n["date"] for n in nodes if n["date"]}) or ["2026-07-23"]

    # fraicheur par axe (parametre du profil) — affichee dans le panneau d'axe du viewer
    _gfr = (cfg.get("freshness") or {})
    _gfr = _gfr.get("choice") if isinstance(_gfr, dict) else _gfr
    axes_freshness = {}
    for a in (cfg.get("axes") or []):
        if isinstance(a, dict) and (a.get("name") or "").strip():
            axes_freshness[a["name"].strip()] = a.get("freshness") or _gfr or ""

    # --- axes bilingues : langue native = FR ; axes_en depuis findings.json (map fr->en) ---
    axes_i18n = (findings_bundle or {}).get("axes_i18n") or {}
    # Run a langue native ANGLAISE : findings.json peut porter `axes_i18n_fr`
    # (map nom-d-axe-source -> nom francais). Sans cette cle, comportement inchange.
    axes_i18n_fr = (findings_bundle or {}).get("axes_i18n_fr") or {}
    axes_fr = [axes_i18n_fr.get(a) or a for a in axes]
    axes_en = [axes_i18n.get(a) or a for a in axes]
    data = {"watch": watch, "owner": owner, "theme": str(theme).strip(),
            "runs": [dates[-1]], "nlanes": max(1, len(nodes)),
            "axes": axes, "axes_fr": axes_fr, "axes_en": axes_en,
            "axes_freshness": axes_freshness, "fils": _fils_depuis_liens(BASE, nodes), "nodes": nodes,
            "resume_livraison": resume_livraison, "resume_axe": resume_axe,
            "suggestions_axes": suggestions, "profil_base": profil_base}
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    io.open(os.path.join(OUT_DIR, "constellation-data.json"), "w",
            encoding="utf-8").write(json.dumps(data, ensure_ascii=False))

    from collections import Counter
    rep = Counter(n["axe"] for n in nodes)
    mode = "legacy ai-watch" if legacy else "profile-agnostic"
    print("constellation-data.json : %d signaux, %d/%d axes (%s)" % (len(nodes), len(rep), len(axes), mode))
    for a in axes:
        print("   %2d  %s" % (rep.get(a, 0), a))


if __name__ == "__main__":
    main()
