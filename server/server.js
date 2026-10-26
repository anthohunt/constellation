"use strict";
// AI-Watch — serveur de relecture collaborative MULTI-RUN. Node natif, zéro dépendance.
// Chaque run = /data/runs/<id>/{findings.json,meta.json,config.json}. URL = /r/<id>/.
// Annotations partagées dans /data/annotations.json, structurées run -> fid -> user -> {score,comment,ts}.
// Portail de connexion intégré (page brandée + cookie de session signé HMAC, mot de passe scrypt).
const http = require("http"), fs = require("fs"), path = require("path"), crypto = require("crypto");
const zlib = require("zlib");
const { execFile } = require("child_process");
const ROOT = process.env.DATAROOT || "/data";
const RUNS = path.join(ROOT, "runs");
const OWNERS = path.join(ROOT, "owners");         // profils clients : owners/<owner>/{profile.json,run-config.json,profile.md,subject.md}
const ANN  = path.join(ROOT, "annotations.json");
// Silo de la pipeline : le wizard POSE le profil, la pipeline le LIT au meme endroit.
// Sans ce montage, le profil ne sort pas du wizard et la run part sur un profil perime.
const SILO = process.env.SILO || "";
const SILO_UID = Number(process.env.SILO_UID || 1001), SILO_GID = Number(process.env.SILO_GID || 1001);
const PUB  = process.env.PUB || path.join(__dirname, "public");
const PORT = process.env.PORT || 8080;
const SITE_NAME = process.env.SITE_NAME || "Constellation";

// --- Auth / session ---
const AUTH_USER   = process.env.AUTH_USER || "admin";
const AUTH_HASH   = process.env.AUTH_HASH || "";        // "saltHex:hashHex" (scrypt, keylen = hash bytes)
const SESSION_SECRET = process.env.SESSION_SECRET || "";
const COOKIE = "veille_sess";
const MAXAGE = 30 * 24 * 3600;                            // 30 jours
const AUTH_ON = !!(AUTH_HASH.includes(":") && SESSION_SECRET);

function verifyPassword(pw) {
  if (!AUTH_HASH.includes(":")) return false;
  const [saltHex, hashHex] = AUTH_HASH.split(":");
  let salt, expected, got;
  try { salt = Buffer.from(saltHex, "hex"); expected = Buffer.from(hashHex, "hex"); } catch (e) { return false; }
  try { got = crypto.scryptSync(String(pw), salt, expected.length); } catch (e) { return false; }
  return got.length === expected.length && crypto.timingSafeEqual(got, expected);
}
const sign = v => crypto.createHmac("sha256", SESSION_SECRET).update(v).digest("hex");
function makeToken() {
  const payload = `${AUTH_USER}|${Date.now() + MAXAGE * 1000}`;
  return Buffer.from(payload).toString("base64url") + "." + sign(payload);
}
function validToken(req) {
  const raw = (req.headers.cookie || "").split(/;\s*/).find(c => c.startsWith(COOKIE + "="));
  if (!raw) return false;
  const token = raw.slice(COOKIE.length + 1);
  const dot = token.lastIndexOf(".");
  if (dot < 0) return false;
  let payload;
  try { payload = Buffer.from(token.slice(0, dot), "base64url").toString("utf8"); } catch (e) { return false; }
  const sig = token.slice(dot + 1), expected = sign(payload);
  if (sig.length !== expected.length) return false;
  try { if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return false; } catch (e) { return false; }
  const exp = Number(payload.split("|")[1]);
  return !!exp && Date.now() < exp;
}
const cookieSet   = () => `${COOKIE}=${makeToken()}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${MAXAGE}`;
const cookieClear = () => `${COOKIE}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`;
function redirect(res, loc, cookie) {
  const h = { location: loc, "cache-control": "no-store" };
  if (cookie) h["set-cookie"] = cookie;
  res.writeHead(302, h); res.end();
}
// n'accepte qu'un chemin interne (protection open-redirect)
const safeNext = n => (typeof n === "string" && /^\/(?!\/)/.test(n)) ? n : "/";

function loginPage(res, code, next, error) {
  const nx = esc(next || "/");
  send(res, code, "text/html; charset=utf-8",
`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Watch — Sign in</title>
<style>
:root{--bg:#0b1020;--card:#121a30;--fg:#e8ecf6;--muted:#8b97b4;--accent:#5b8cff;--accent2:#8b5bff;--line:#26314f;--err:#ff6b7d}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--fg);
 background:radial-gradient(1200px 600px at 15% -10%,#1a2440 0,transparent 55%),radial-gradient(1000px 700px at 110% 20%,#1c1440 0,transparent 50%),var(--bg);
 display:flex;align-items:center;justify-content:center;padding:24px}
.wrap{width:100%;max-width:400px}
.brand{display:flex;align-items:center;gap:12px;margin:0 0 22px 2px}
.logo{width:40px;height:40px;border-radius:11px;background:linear-gradient(135deg,var(--accent),var(--accent2));
 display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#fff;box-shadow:0 8px 24px rgba(91,140,255,.35)}
.brand h1{font-size:19px;margin:0;letter-spacing:.2px}
.brand p{margin:2px 0 0;font-size:12.5px;color:var(--muted)}
.card{background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,0)),var(--card);
 border:1px solid var(--line);border-radius:16px;padding:26px 24px;box-shadow:0 24px 60px rgba(0,0,0,.45)}
.card h2{margin:0 0 4px;font-size:17px}
.sub{margin:0 0 20px;font-size:13px;color:var(--muted)}
label{display:block;font-size:12.5px;color:var(--muted);margin:0 0 6px}
.field{margin-bottom:15px}
input{width:100%;padding:11px 13px;background:#0c122a;border:1px solid var(--line);border-radius:10px;
 color:var(--fg);font-size:14.5px;outline:none;transition:border-color .15s,box-shadow .15s}
input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(91,140,255,.18)}
button{width:100%;margin-top:6px;padding:12px;border:0;border-radius:10px;cursor:pointer;font-size:15px;font-weight:650;color:#fff;
 background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 10px 24px rgba(91,140,255,.32);transition:transform .06s,filter .15s}
button:hover{filter:brightness(1.06)}button:active{transform:translateY(1px)}
.err{background:rgba(255,107,125,.1);border:1px solid rgba(255,107,125,.35);color:var(--err);
 font-size:13px;padding:9px 12px;border-radius:9px;margin:0 0 16px}
.foot{margin:18px 2px 0;font-size:11.5px;color:var(--muted);text-align:center}
</style></head><body><div class="wrap">
<div class="brand"><div class="logo">AI</div><div><h1>AI Watch</h1><p>Watch review portal</p></div></div>
<form class="card" method="POST" action="/login">
<h2>Sign in</h2><p class="sub">Restricted access — sign in to continue.</p>
${error ? `<div class="err">Incorrect username or password.</div>` : ""}
<input type="hidden" name="next" value="${nx}">
<div class="field"><label for="u">Username</label>
<input id="u" name="user" autocomplete="username" autofocus spellcheck="false" required></div>
<div class="field"><label for="p">Password</label>
<input id="p" name="password" type="password" autocomplete="current-password" required></div>
<button type="submit">Sign in</button>
</form>
<div class="foot">${esc(SITE_NAME)} · secure session</div>
</div></body></html>`);
}

function parseForm(req, cb) {
  let b = ""; req.on("data", c => { b += c; if (b.length > 1e5) req.destroy(); });
  req.on("end", () => {
    const out = {};
    for (const kv of b.split("&")) {
      const i = kv.indexOf("="); if (i < 0) continue;
      try { out[decodeURIComponent(kv.slice(0, i).replace(/\+/g, " "))] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, " ")); } catch (e) {}
    }
    cb(out);
  });
}

const loadJSON = (f, d) => { try { return JSON.parse(fs.readFileSync(f, "utf8")); } catch (e) { return d; } };
const saveJSON = (f, o) => { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, JSON.stringify(o, null, 2)); };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// --- Owners / profils -------------------------------------------------------
const SLUG = s => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);
function listOwners() {
  try { return fs.readdirSync(OWNERS).filter(d => fs.existsSync(path.join(OWNERS, d, "profile.json"))); }
  catch (e) { return []; }
}
function ownerProfile(owner) { return loadJSON(path.join(OWNERS, owner, "profile.json"), null); }
// Recopie les artefacts que la pipeline lit dans le silo owner, avec les droits de l'agent
// (le conteneur ecrit en root ; sans chown, la run ne peut plus rien ecrire a cote).
function mirrorSilo(owner, files) {
  if (!SILO) return { ok: false, raison: "SILO non monte" };
  try {
    const dir = path.join(SILO, owner);
    for (const [rel, body] of Object.entries(files)) {
      const f = path.join(dir, rel);
      fs.mkdirSync(path.dirname(f), { recursive: true });
      fs.writeFileSync(f, body);
      try { fs.chownSync(f, SILO_UID, SILO_GID); } catch (e) {}
    }
    for (const d of [dir, path.join(dir, "preferences")]) { try { fs.chownSync(d, SILO_UID, SILO_GID); } catch (e) {} }
    return { ok: true, dir };
  } catch (e) { return { ok: false, raison: e.message || String(e) }; }
}

// --- Comptes utilisateurs (auth email + mot de passe) ----------------------
// Un compte = une veille. Identité = email ; owner = SLUG(email) (unique).
const ACCOUNTS = path.join(ROOT, "accounts");
const acctFile = key => path.join(ACCOUNTS, SLUG(key) + ".json");
const accountByEmail = email => loadJSON(acctFile(email), null);          // fichier = SLUG(email).json
const accountByOwner = owner => loadJSON(path.join(ACCOUNTS, owner + ".json"), null); // owner === SLUG(email)
function saveAccount(a) { saveJSON(acctFile(a.email), a); }

// Secret de session comptes : env prioritaire, sinon persistant dans /data
// (indépendant de l'auth admin, qui elle peut rester OFF).
let ACCT_SECRET = process.env.SESSION_SECRET || "";
if (!ACCT_SECRET) {
  const sf = path.join(ROOT, ".session-secret");
  try { ACCT_SECRET = fs.readFileSync(sf, "utf8").trim(); } catch (e) {}
  if (!ACCT_SECRET) {
    ACCT_SECRET = crypto.randomBytes(32).toString("hex");
    try { fs.mkdirSync(ROOT, { recursive: true }); fs.writeFileSync(sf, ACCT_SECRET); } catch (e) {}
  }
}
const ACCT_COOKIE = "veille_acct", ACCT_MAXAGE = 60 * 24 * 3600;
const acctSign = v => crypto.createHmac("sha256", ACCT_SECRET).update(v).digest("hex");
function acctCookie(owner) {
  const payload = `${owner}|${Date.now() + ACCT_MAXAGE * 1000}`;
  const tok = Buffer.from(payload).toString("base64url") + "." + acctSign(payload);
  return `${ACCT_COOKIE}=${tok}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${ACCT_MAXAGE}`;
}
const acctClear = `${ACCT_COOKIE}=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0`;
function currentOwner(req) {
  const raw = (req.headers.cookie || "").split(/;\s*/).find(c => c.startsWith(ACCT_COOKIE + "="));
  if (!raw) return null;
  const token = raw.slice(ACCT_COOKIE.length + 1), dot = token.lastIndexOf(".");
  if (dot < 0) return null;
  let payload; try { payload = Buffer.from(token.slice(0, dot), "base64url").toString("utf8"); } catch (e) { return null; }
  const sig = token.slice(dot + 1), expc = acctSign(payload);
  if (sig.length !== expc.length) return null;
  try { if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expc))) return null; } catch (e) { return null; }
  const parts = payload.split("|");
  if (!(Number(parts[1]) > Date.now())) return null;
  return parts[0] || null;
}
function hashPw(pw) { const salt = crypto.randomBytes(16); return salt.toString("hex") + ":" + crypto.scryptSync(String(pw), salt, 32).toString("hex"); }
function verifyPw(pw, stored) {
  if (!stored || !String(stored).includes(":")) return false;
  const [sh, hh] = String(stored).split(":"); let salt, exp, got;
  try { salt = Buffer.from(sh, "hex"); exp = Buffer.from(hh, "hex"); } catch (e) { return false; }
  try { got = crypto.scryptSync(String(pw), salt, exp.length); } catch (e) { return false; }
  return got.length === exp.length && crypto.timingSafeEqual(got, exp);
}
// emails vérifiés récemment (autorise le signup) — en mémoire, courte durée
const verifiedEmails = {};

/** Le COMPTE proprietaire d'une veille — l'adresse inscrite sur la plateforme.
 *  Une veille appartient a un compte ; un compte en porte plusieurs. Le fichier
 *  de compte fait foi ; s'il n'existe pas (silo cree a la main hors plateforme),
 *  on rend null et l'appelant garde ce qui etait deja pose. */
function compteDuOwner(owner) {
  try {
    const a = JSON.parse(fs.readFileSync(path.join(ACCOUNTS, owner + ".json"), "utf8"));
    if (a && a.email) return { compte: a.email, compte_nom: a.name || a.email };
  } catch (e) { /* pas de compte pour cet owner : rien a poser */ }
  return null;
}

// Dérive les 3 artefacts pipeline (run-config.json, profile.md, subject.md) depuis l'état brut du wizard.
function deriveArtifacts(owner, p) {
  const today = new Date().toISOString().slice(0, 10);
  // Tout finding est ecrit en FR ET en EN : ce champ dit seulement dans quelle langue
  // la constellation s'ouvre par defaut, pas dans quelle langue on ecrit.
  const langCode = (p.language === "en") ? "en" : "fr";
  // Deux façons de chercher : une VEILLE suit un sujet et l'explique, une COLLECTE
  // ramène des éléments précis. Le mode commande le reste du brief.
  const mode = (p.mode === "collecte") ? "collecte" : "veille";
  // Le niveau du lecteur ne se demande plus : la façon dont il décrit son sujet le dit
  // déjà. L'aval doit lire l'absence, pas une valeur inventée.
  const fam = null;
  // Les types de sources ne se demandent plus : la chasse va ou il faut. Ne reste que
  // ce a quoi le lecteur tient, ecrit en clair.
  const S = (p.sources && typeof p.sources === "object") ? p.sources : { free:"" };
  const sourcesPref = String(S.free || "").trim();
  const F = (p.freshness && typeof p.freshness === "object") ? p.freshness : { choice:"", free:"" };
  const FR = {"48h":"dernières 48h","semaine":"cette semaine","mois":"ce mois","annee":"cette année","tout":"sans limite"};
  // Axes définis par l'utilisateur, avec fraîcheur PAR AXE (fallback : fraîcheur globale, sinon non précisé).
  // Un chasseur = son axe + sa fraicheur, rien d'autre : aucun quota de sortie ne se pose ici,
  // la chasse est tenue par un budget d'EFFORT (cf. skill veille-launch-researcher).
  const A = Array.isArray(p.axes) ? p.axes.filter(a => a && String(a.name || "").trim()) : [];
  const axFreshLabel = a => (a.fresh ? (FR[a.fresh] || a.fresh) : (F.choice ? (FR[F.choice] || F.choice) : "non précisé"));
  const axesConfig = A.map(a => ({ name: String(a.name).trim(), desc: String(a.desc || "").trim(), freshness: a.fresh || F.choice || "", sources: String(a.sources || "").trim() }));
  const axesList = A.map(a => `- **${String(a.name).trim()}**${a.desc ? ` — ${String(a.desc).trim()}` : ""} · fraîcheur : ${axFreshLabel(a)}${String(a.sources || "").trim() ? "\n  · sources tenues sur cet axe : " + String(a.sources).trim().split(/\n+/).map(x => x.trim()).filter(Boolean).join(" · ") : ""}`);
  const eventAnchor = F.free ? `Repère événementiel commun : « ${F.free} »` : "";

  // Un seul livrable : la constellation web. C'est elle qu'on lit et qu'on note ;
  // rien d'autre ne se demande, donc rien d'autre ne se declare.
  const deliverables = [{ format: "mindmap", mediums: ["web"], structure: "par axes", length: "n/a" }];
  const livrablesLabel = { mindmap: "constellation web" };

  // Le nom de la veille (watch) sert de cle aux fichiers d'accumulation (deck, memoire) :
  // il ne se renomme jamais tout seul, sinon la run suivante repart sans son historique.
  const ancien = (SILO ? loadJSON(path.join(SILO, owner, "run-config.json"), null) : null)
    || loadJSON(path.join(OWNERS, owner, "run-config.json"), null);
  const watch = (ancien && ancien.subject_default) ? ancien.subject_default : (SLUG(p.title || owner) || owner);

  const runConfig = {
    owner,
    email: p.email || "",
    deliverables,                                            // formats declares par le lecteur — la publication les assemble
    language: langCode,                                      // langue de LECTURE par defaut ; chaque finding est ecrit FR + EN
    mode,                                                    // "veille" (comprendre un sujet) | "collecte" (ramener des éléments)
    familiarity: fam,
    sources: { types: {}, free: sourcesPref },
    axes: axesConfig,                                        // un axe = son intention + sa fraicheur
    freshness: { choice: F.choice || "", free: F.free || "", byAxis: true },
    accumulation: "cumulative",                              // les livraisons s'empilent
    subject_default: watch,
    updated: today
  };

  // Regles par axe : au premier tour, la description que le lecteur a ecrite de son axe EST
  // la regle. La chasse exige qu'une requete ait vise chaque regle ; sans ce depart, aucune
  // premiere run ne peut passer sa verification. Le feedback les affine ensuite.
  const STOP = new Set(("alors aussi avec avoir cela cette celui chaque comme dans depuis deux dont elle entre etre faire fait leur leurs mais meme moins notre plus pour pres quand quelle quels sans selon sous sur tout tous toute toutes tres vers etc les des une aux qui que quoi ceux").split(" "));
  const motsCles = s => Array.from(new Set(String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
      .split(/[^a-z0-9]+/).filter(w => w.length >= 4 && !STOP.has(w)))).slice(0, 6);
  // Ce que le feedback a induit d'une notation reelle prime : on ne SEME que les axes qui
  // n'ont encore aucune regle. Ecraser une regle induite ferait repartir la chasse a l'aveugle.
  const ancienRegles = (SILO ? loadJSON(path.join(SILO, owner, "preferences", "regles-axes.json"), null) : null)
    || loadJSON(path.join(OWNERS, owner, "preferences", "regles-axes.json"), null) || {};
  const axesRegles = Object.assign({}, (ancienRegles.axes && typeof ancienRegles.axes === "object") ? ancienRegles.axes : {});
  let semees = 0;
  for (const a of axesConfig) {
    if (Array.isArray(axesRegles[a.name]) && axesRegles[a.name].length) continue;
    semees++;
    axesRegles[a.name] = [{
      regle: a.desc || `Sur l'axe « ${a.name} », une piste monte si elle releve de ce que cet axe designe.`,
      sens: "cadre",
      mots_cles: motsCles(a.name + " " + a.desc),
      statut: "validee",
      preuve: { detail: "mots du lecteur, poses dans son profil — jamais induite d'un classement" },
      valide_le: today,
      valide_par: "profil (mots du lecteur)"
    }];
  }
  const reglesAxes = {
    watch,
    maj: semees ? today : (ancienRegles.maj || today),
    protocole: "une regle vient soit du profil (les mots du lecteur, au depart), soit du feedback (induite d'une notation reelle et gardee si elle retrouve les classements). Le profil ne remplace jamais une regle induite.",
    axes: axesRegles
  };

  const profileMd = `<!-- généré par le wizard veille le ${today} — owner: ${owner} -->
# Profil de veille — ${p.title || owner}

**Contact** : ${p.email || "(non fourni)"}
**Ce qu'on cherche** : ${mode === "collecte" ? "une COLLECTE — ramener des éléments précis, complets et vérifiables" : "une VEILLE — suivre un sujet dans la durée et en tirer ce qu'il faut retenir"}
**Profondeur technique** : elle se déduit de la description ci-dessous — c'est la façon dont le lecteur parle de son sujet qui dit à quel niveau lui écrire. Le ton reste clair dans tous les cas.

## De quoi parle cette veille
${p.description ? p.description : "(pas de description libre)"}

## Sources
${sourcesPref ? `Le lecteur tient à ces sources — les mettre devant, sans s'y limiter : ${sourcesPref}` : "Aucune source imposée : la chasse va où il faut."}

## Axes & fraîcheur (par axe)
${axesList.length ? axesList.join("\n") : "- (aucun axe défini — à générer à la création)"}${eventAnchor ? `\n\n${eventAnchor}` : ""}

## Livrables
${deliverables.map(d => `- ${livrablesLabel[d.format] || d.format} · ${d.structure} · ${d.mediums.join(", ")}`).join("\n")}
- Mode cumulatif : chaque livraison s'ajoute aux précédentes.
- Lecture par défaut en ${langCode.toUpperCase()} — chaque finding est écrit en français ET en anglais, la constellation bascule d'une langue à l'autre.
- Aucun volume cible : la chasse est tenue par un budget d'effort, pas par un nombre de findings ; tout ce qui est trouvé entre dans la constellation, le tri est humain.
`;
  const subjectMd = `<!-- brief de sourcing généré par le wizard le ${today} — owner: ${owner} -->
# Sujet de veille : ${p.title || owner}

## Mission / périmètre
${p.description ? p.description : "(à préciser)"}

${mode === "collecte" ? `## Ce qu'est une trouvaille
Un élément précis, pas un commentaire sur le domaine. Chaque trouvaille porte : ce que c'est (intitulé exact), qui la propose (nom de l'acteur, jamais un intermédiaire anonyme), où et quand, et le lien direct pour y accéder. Un champ manquant se dit — il ne s'invente pas. Une analyse du marché, une tendance, un chiffre global : hors sujet, quelle que soit sa qualité.

` : `## Ce qu'est une trouvaille
Un signal qui apprend quelque chose sur le sujet, expliqué pour être compris seul, avec sa source.

`}## Axes de chasse (définis par l'utilisateur) + fraîcheur par axe
${axesList.length ? axesList.join("\n") : "(aucun axe fourni — À GÉNÉRER automatiquement à partir du périmètre ci-dessus.)"}${eventAnchor ? `\n\n${eventAnchor}` : ""}

## Sources
${sourcesPref ? `À mettre devant, sans s'y limiter : ${sourcesPref}` : "Aucune source imposée — ratisser large, la qualité de la source se juge sur pièce."}

## Calibrage
- Profondeur technique : à déduire du périmètre ci-dessus (vocabulaire, angle, exclusions), jamais d'un curseur. Ton toujours clair.
- Écriture bilingue : chaque finding en français ET en anglais ; lecture par défaut en ${langCode.toUpperCase()}.
`;
  return { runConfig, profileMd, subjectMd, reglesAxes };
}

// --- Vérification email (code OTP via Brevo) --------------------------------
/* Les codes vivaient en memoire : un redemarrage du service les tuait tous a la
   fois, et le visiteur se voyait refuser un code recu deux minutes plus tot. Ils
   sont poses sur disque, relus au demarrage, et les perimes ne reviennent pas. */
const CODES_FILE = path.join(ROOT, "email-codes.json");
const emailCodes = (() => {                       // email -> { code, exp }
  try {
    const brut = JSON.parse(fs.readFileSync(CODES_FILE, "utf-8"));
    const vivants = {}, now = Date.now();
    for (const [mail, rec] of Object.entries(brut)) if (rec && rec.exp > now) vivants[mail] = rec;
    return vivants;
  } catch (e) { return {}; }
})();
function saveCodes() {
  try { fs.writeFileSync(CODES_FILE, JSON.stringify(emailCodes)); } catch (e) {}
}
const sendGuard = { byEmail: {}, byIp: {} };  // anti-abus : cooldown email + plafond IP
function allowSend(email, ip) {
  const now = Date.now();
  const last = sendGuard.byEmail[email] || 0;
  if (now - last < 60 * 1000) return { ok: false, wait: Math.ceil((60000 - (now - last)) / 1000) };
  const hits = (sendGuard.byIp[ip] || []).filter(t => now - t < 3600 * 1000);
  if (hits.length >= 15) return { ok: false, wait: 0, ip: true };
  sendGuard.byEmail[email] = now; hits.push(now); sendGuard.byIp[ip] = hits;
  return { ok: true };
}
// --- Remise DIRECTE au serveur du destinataire ------------------------------
// Certaines passerelles (par exemple celles de grandes organisations) refusent les connexions des IP
// mutualisees des routeurs d'emails : le message est accepte par le routeur puis
// reste bloque en file ("deferred - connection timeout"), sans rebond, donc sans
// alerte. On remet donc nous-memes le message au MX du destinataire, signe DKIM,
// et le routeur ne sert plus que de secours.
const dns = require("dns").promises, net = require("net"), tls = require("tls");
let DKIM_KEY = process.env.DKIM_KEY || "";              // cle privee PEM
if (!DKIM_KEY && process.env.DKIM_KEY_FILE) {
  try { DKIM_KEY = fs.readFileSync(process.env.DKIM_KEY_FILE, "utf8"); }
  catch (e) { console.error("[dkim] cle illisible : " + (e.message || e)); }
}
const DKIM_SELECTOR = process.env.DKIM_SELECTOR || "default";
const MAIL_DOMAIN = (process.env.MAIL_FROM || "noreply@example.org").split("@")[1];
const HELO = process.env.SMTP_HELO || MAIL_DOMAIN;

const canonHeader = (n, v) => n.toLowerCase() + ":" + String(v).replace(/\r?\n/g, "").replace(/[ \t]+/g, " ").trim() + "\r\n";
function canonBody(b) {
  let s = b.replace(/\r?\n/g, "\r\n").split("\r\n").map(l => l.replace(/[ \t]+$/, "")).join("\r\n");
  s = s.replace(/(\r\n)+$/, "");
  return s + "\r\n";
}
function dkimSign(headers, body) {
  if (!DKIM_KEY) return null;
  const bh = crypto.createHash("sha256").update(canonBody(body)).digest("base64");
  const noms = ["from", "to", "subject", "date", "mime-version", "content-type"].filter(n => headers[n] != null);
  let sig = `v=1; a=rsa-sha256; c=relaxed/relaxed; d=${MAIL_DOMAIN}; s=${DKIM_SELECTOR}; `
          + `t=${Math.floor(Date.now() / 1000)}; h=${noms.join(":")}; bh=${bh}; b=`;
  const aSigner = noms.map(n => canonHeader(n, headers[n])).join("") + canonHeader("dkim-signature", sig);
  const b = crypto.createSign("RSA-SHA256").update(aSigner).sign(DKIM_KEY, "base64");
  return "DKIM-Signature: " + sig + b;
}
function dialogue(sock, attendu) {          // lit une reponse SMTP complete
  return new Promise((ok, ko) => {
    let buf = "";
    const fin = () => { sock.removeListener("data", onData); sock.removeListener("error", onErr); };
    const onData = d => {
      buf += d.toString();
      const lignes = buf.split(/\r?\n/).filter(Boolean);
      const last = lignes[lignes.length - 1] || "";
      if (!/^\d{3} /.test(last)) return;                       // reponse multi-lignes en cours
      fin();
      const code = parseInt(last.slice(0, 3), 10);
      if (attendu && !attendu.includes(code)) return ko(new Error("SMTP " + code + " : " + last));
      ok({ code, texte: buf });
    };
    const onErr = e => { fin(); ko(e); };
    sock.on("data", onData); sock.once("error", onErr);
  });
}
async function sendDirect(to, subject, html) {
  const domaine = String(to).split("@")[1];
  const mx = (await dns.resolveMx(domaine)).sort((a, b) => a.priority - b.priority);
  if (!mx.length) throw new Error("aucun MX pour " + domaine);
  const from = process.env.MAIL_FROM || "noreply@example.org";
  const nomAffiche = process.env.MAIL_FROM_NAME || SITE_NAME;
  // Un en-tete ne transporte que de l'ASCII : ce qui ne l'est pas s'encode (RFC 2047),
  // sinon l'accent arrive casse chez le destinataire.
  const enTete = t => /^[\x00-\x7F]*$/.test(t) ? t : "=?UTF-8?B?" + Buffer.from(t, "utf8").toString("base64") + "?=";
  const headers = {
    "from": `${enTete(nomAffiche)} <${from}>`, "to": to, "subject": enTete(subject),
    "date": new Date().toUTCString(), "mime-version": "1.0",
    "content-type": 'text/html; charset="utf-8"'
  };
  const body = html;
  const sig = dkimSign(headers, body);
  const brut = (sig ? sig + "\r\n" : "")
    + Object.entries(headers).map(([n, v]) => n.replace(/(^|-)([a-z])/g, (m, a, b) => a + b.toUpperCase()) + ": " + v).join("\r\n")
    + "\r\n\r\n" + body.replace(/\r?\n/g, "\r\n").replace(/\r\n\./g, "\r\n..");
  let derniere = null;
  for (const cible of mx.slice(0, 3)) {
    let sock;
    try {
      sock = net.createConnection({ host: cible.exchange, port: 25, timeout: 20000 });
      await new Promise((ok, ko) => { sock.once("connect", ok); sock.once("error", ko); sock.once("timeout", () => ko(new Error("timeout"))); });
      await dialogue(sock, [220]);
      sock.write(`EHLO ${HELO}\r\n`); const ehlo = await dialogue(sock, [250]);
      if (/STARTTLS/i.test(ehlo.texte)) {
        sock.write("STARTTLS\r\n"); await dialogue(sock, [220]);
        sock = tls.connect({ socket: sock, servername: cible.exchange, rejectUnauthorized: false });
        await new Promise((ok, ko) => { sock.once("secureConnect", ok); sock.once("error", ko); });
        sock.write(`EHLO ${HELO}\r\n`); await dialogue(sock, [250]);
      }
      sock.write(`MAIL FROM:<${from}>\r\n`); await dialogue(sock, [250]);
      sock.write(`RCPT TO:<${to}>\r\n`); await dialogue(sock, [250, 251]);
      sock.write("DATA\r\n"); await dialogue(sock, [354]);
      sock.write(brut + "\r\n.\r\n"); const fin = await dialogue(sock, [250]);
      sock.write("QUIT\r\n"); sock.end();
      return { ok: true, mx: cible.exchange, reponse: fin.texte.trim().slice(0, 120) };
    } catch (e) {
      derniere = e; try { sock && sock.destroy(); } catch (x) {}
    }
  }
  throw new Error("remise directe impossible : " + (derniere && derniere.message));
}

// Le produit est bilingue : le lecteur trouve sa langue dans le meme mail, l'anglais
// sous le francais, et le code une seule fois entre les deux — c'est lui qu'on vient chercher.
function lienActivation(email, code) {
  // Le jeton EST le code, porte par l'URL : rien de nouveau a stocker, et il
  // expire avec lui. Cliquer et repondre menent au meme endroit.
  return BASE_PUBLIQUE + "/api/activer?e=" + encodeURIComponent(email)
       + "&t=" + encodeURIComponent(code);
}

function htmlCode(code, email) {
  const lien = lienActivation(email || "", code);
  return `<div style="font-family:sans-serif;color:#181712;line-height:1.5">`
    + `<p style="margin:0 0 18px">Un seul geste pour confirmer que cette adresse est bien la tienne :</p>`
    + `<p style="margin:0 0 18px"><a href="${lien}" style="display:inline-block;background:#0b6b5f;color:#fff;text-decoration:none;padding:13px 22px;border-radius:8px;font-weight:600">Activer mon compte</a></p>`
    + `<p style="color:#8a857a;font-size:13px;margin:0 0 18px">Le lien expire dans 10 minutes. Si tu n'es pas à l'origine de cette demande, ignore cet email.</p>`
    + `<hr style="border:none;border-top:1px solid #e6e3dc;margin:22px 0">`
    + `<p style="margin:0 0 12px">One click to confirm this address is yours:</p>`
    + `<p style="margin:0 0 12px"><a href="${lien}" style="display:inline-block;background:#0b6b5f;color:#fff;text-decoration:none;padding:13px 22px;border-radius:8px;font-weight:600">Activate my account</a></p>`
    + `<p style="color:#8a857a;font-size:13px;margin:0">The link expires in 10 minutes.</p>`
    + `</div>`;
}
// Remise directe d'abord, routeur d'emails en secours : c'est la seule facon d'atteindre
// une boite dont la passerelle bloque les IP mutualisees des routeurs.
// Un refus TEMPORAIRE (4xx) n'est pas un echec : c'est presque toujours du greylisting —
// le serveur d'en face ecarte le premier contact d'une IP inconnue et attend qu'on repasse.
// On repasse donc, en tache de fond, et le message finit par entrer. Une fois le trio
// (notre IP, l'expediteur, le destinataire) memorise en face, les envois suivants passent tout de suite.
const RETENTATIVES_MS = [45000, 105000, 240000, 420000];
const SUJET_CODE = "Ton code de vérification · Your verification code";
async function sendCode(email, code) {
  const sujet = SUJET_CODE, html = htmlCode(code, email);
  try {
    const r = await sendDirect(email, sujet, html);
    console.log("[code] direct -> " + email + " via " + r.mx);
    return "direct";
  } catch (e) {
    const msg = String(e.message || e);
    const temporaire = /SMTP 4\d\d|timeout|ECONNRESET|ETIMEDOUT/i.test(msg);
    console.error("[code] direct " + (temporaire ? "differe" : "KO") + " pour " + email + " : " + msg);
    if (temporaire) {
      (async () => {
        for (const attente of RETENTATIVES_MS) {
          await new Promise(r => setTimeout(r, attente));
          try { const r = await sendDirect(email, sujet, html); console.log("[code] direct (retentative) -> " + email + " via " + r.mx); return; }
          catch (e2) { console.error("[code] retentative KO : " + (e2.message || e2)); }
        }
        try { await sendBrevoCode(email, code); console.log("[code] secours routeur apres retentatives -> " + email); } catch (e3) {}
      })();
      return "direct-differe";
    }
    await sendBrevoCode(email, code);
    console.log("[code] secours routeur -> " + email);
    return "routeur";
  }
}
// Repondre a ce message vaut confirmation : une reponse est le signal le plus
// fort qu'une boite mail sache lire, et elle prouve la meme chose que le code —
// que la personne controle l'adresse. Le code reste la voie principale : si la
// reponse ne parvient pas, personne n'est bloque.
const BASE_PUBLIQUE = process.env.BASE_PUBLIQUE || ("http://localhost:" + PORT);
const REPLY_ADDR = process.env.REPLY_ADDR || "verif@reply.example.org";

async function sendBrevoCode(email, code) {
  const key = process.env.BREVO_API_KEY;
  if (!key) throw new Error("BREVO_API_KEY manquante");
  const from = process.env.MAIL_FROM || "noreply@example.org";
  const r = await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: { "content-type": "application/json", "api-key": key, "accept": "application/json" },
    body: JSON.stringify({
      sender: { name: process.env.MAIL_FROM_NAME || SITE_NAME, email: from },
      to: [{ email }],
      replyTo: { email: REPLY_ADDR, name: process.env.MAIL_FROM_NAME || SITE_NAME },
      subject: SUJET_CODE,
      htmlContent: htmlCode(code, email)
    })
  });
  if (!r.ok) throw new Error("brevo " + r.status + " " + (await r.text()).slice(0, 200));
}

// Notification « ta veille est prête » (appelée par le pipeline via /api/notify-ready).
async function sendReadyEmail(email, name, url) {
  const key = process.env.BREVO_API_KEY;
  if (!key) throw new Error("BREVO_API_KEY manquante");
  const from = process.env.MAIL_FROM || "noreply@example.org";
  const r = await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: { "content-type": "application/json", "api-key": key, "accept": "application/json" },
    body: JSON.stringify({
      sender: { name: process.env.MAIL_FROM_NAME || SITE_NAME, email: from },
      to: [{ email }],
      subject: "Ta veille est prête",
      // Une version texte : un message HTML seul est un signal de courrier de masse,
      // et c'est ce qui a envoyé l'invitation du 26/08 en indésirables chez Yahoo.
      textContent: (name ? "Bonjour " + name + "," : "Bonjour,")
        + "\n\nTa veille est prête. Tu peux la consulter ici :\n" + url
        + "\n\nSur chaque fiche, tu peux mettre une note et un commentaire : c'est ce qui affine les prochaines éditions."
        + "\n\nVersion bêta. Tes retours sur la forme (lisibilité, mise en page, navigation) sont bienvenus : réponds simplement à cet email.\n",
      htmlContent: `<div style="font-family:sans-serif;color:#181712;line-height:1.55">`
        + `<p>${name ? "Bonjour " + name + "," : "Bonjour,"}</p>`
        + `<p>Ta veille est prête. Tu peux la consulter ici :</p>`
        + `<p><a href="${url}" style="display:inline-block;background:#0b6b5f;color:#ffffff;text-decoration:none;padding:11px 20px;border-radius:9px;font-weight:600">Ouvrir ma veille</a></p>`
        + `<p style="color:#57534a;font-size:14px">Sur chaque fiche, tu peux mettre une note et un commentaire — c'est ce qui affine les prochaines éditions.</p>`
        + `<p style="color:#8a857a;font-size:13px;border-top:1px solid #e7e3d8;padding-top:12px;margin-top:18px">`
        + `Version bêta — tes retours sur la <b>forme</b> (lisibilité, mise en page, navigation) sont bienvenus : réponds simplement à cet email.</p>`
        + `</div>`
    })
  });
  if (!r.ok) throw new Error("brevo " + r.status + " " + (await r.text()).slice(0, 200));
}

// --- Suggestion d'axes -------------------------------------------------------
// Déduit des axes du sujet SANS LLM : découpe la description en sous-thèmes.
function fallbackAxes(desc) {
  const raw = String(desc || "").replace(/^[^:]{0,40}:\s*/, "");            // enlève un "les news de :" éventuel
  const strip = s => s.replace(/^\s*(l'|le |la |les |des |du |de la |de l'|d'|the )/i, "").trim();
  const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  let parts = raw.split(/,| et | ou |;|·|\/|\n/).map(s => strip(s.trim()))
    .filter(s => s && s.length > 1 && !/^(etc\.?|…|\.\.\.)$/i.test(s));
  let axes = parts.slice(0, 6).map(s => ({ name: cap(s), desc: "" }));
  if (axes.length <= 1) {                                                     // sujet unique -> sous-angles génériques
    const topic = (axes[0] ? axes[0].name : cap(strip(raw)) || "ce sujet").toLowerCase();
    axes = [
      { name: "Nouveautés & annonces", desc: `Ce qui vient de sortir autour de ${topic}.` },
      { name: "Acteurs & références", desc: "Qui compte, qui fait autorité." },
      { name: "Tendances de fond", desc: "Les dynamiques qui se dessinent." },
      { name: "Analyses & débats", desc: "Points de vue, controverses, décryptages." }
    ];
  }
  return axes;
}
function axesPrompt(desc, existing, count) {
  let p = `Tu prépares une veille sur : "${desc}".\n`
    + `CHERCHE EN LIGNE l'actualité et le paysage récent de ce sujet (acteurs, tendances, sous-thèmes qui bougent), puis appuie-toi sur ce que tu trouves réellement.\n`;
  if (existing && existing.length)
    p += `Axes DÉJÀ retenus (n'en propose AUCUN de similaire) : ${existing.join(" · ")}.\n`
       + `Propose ${count === 1 ? "UN nouvel axe distinct et complémentaire" : count + " nouveaux axes distincts et complémentaires"}.\n`;
  else
    p += `Propose ${count} axes de suivi distincts, concrets et non redondants (un axe = un sous-thème précis, ancré dans ce que tu as trouvé).\n`;
  p += `Chaque axe : un "name" court (2-5 mots), un "desc" d'une phrase (EN FRANÇAIS) qui dit ce qui compte sur cet axe, et une "freshness" parmi "48h" | "semaine" | "mois" | "annee" | "tout" = jusqu'où remonter sur CET axe selon son rythme réel (axe très actif → 48h ou semaine ; axe lent / de niche → mois, annee). Différencie : ne mets pas la même valeur partout. Aucun nombre de trouvailles à viser : la chasse est tenue par un budget d'effort, pas par un quota.\n`
     + `Termine IMPÉRATIVEMENT ta réponse par une ligne "===AXES===" suivie UNIQUEMENT de ce JSON : {"axes":[{"name":"...","desc":"...","freshness":"semaine"}]}`;
  return p;
}
// Extraction robuste du JSON (la recherche web interdit response_format, la sortie contient du texte + citations).
function extractJSON(s) {
  s = String(s || "");
  const mk = s.lastIndexOf("===AXES===");
  if (mk >= 0) s = s.slice(mk + 10);
  const m = s.match(/\{[\s\S]*\}/);
  if (m) { try { return JSON.parse(m[0]); } catch (e) {} }
  const starts = []; for (let i = 0; i < s.length; i++) if (s[i] === "{") starts.push(i);
  for (const st of starts) for (let en = s.length; en > st; en--) if (s[en - 1] === "}") {
    try { return JSON.parse(s.slice(st, en)); } catch (e) {}
  }
  throw new Error("no json");
}
function parseAxes(txt) {
  const parsed = extractJSON(txt);
  const FRESH = ["48h", "semaine", "mois", "annee", "tout"];
  const axes = (parsed.axes || []).filter(a => a && a.name)
    .map(a => ({ name: String(a.name).slice(0, 80), desc: String(a.desc || "").slice(0, 220),
                 freshness: FRESH.includes(a.freshness) ? a.freshness : "" }));
  if (!axes.length) throw new Error("empty");
  return axes.slice(0, 6);
}
// Claude Code backend (abo Max, WebSearch intégré, zéro clé API). Piloté en headless `claude -p`.
function claudePrompt(desc, existing, count) {
  let p = `Utilise IMPERATIVEMENT l'outil WebSearch pour te renseigner sur l'actualite et le paysage recent du sujet d'une veille : "${desc}". Fais au moins une recherche web reelle.\n`;
  if (existing && existing.length)
    p += `Axes deja retenus (n'en propose AUCUN de similaire) : ${existing.join(" · ")}. Propose ${count === 1 ? "UN nouvel axe distinct et complementaire" : count + " nouveaux axes distincts et complementaires"}.\n`;
  else
    p += `Propose ${count} axes de veille distincts, concrets et non redondants, ancres dans ce que tu as trouve.\n`;
  p += `Chaque axe : un "name" court (2-5 mots), un "desc" d'une phrase (FRANCAIS) qui dit ce qui compte sur cet axe, et une "freshness" parmi "48h" | "semaine" | "mois" | "annee" | "tout" = jusqu'ou remonter sur CET axe selon son rythme reel (axe tres actif -> 48h/semaine ; axe lent ou de niche -> mois, annee ; differencie, pas la meme valeur partout). Aucun nombre de trouvailles a viser : la chasse est tenue par un budget d'effort, pas par un quota.\n`
     + `Reponds A LA FIN uniquement avec ce JSON (rien apres) : {"axes":[{"name":"...","desc":"...","freshness":"semaine"}]}`;
  return p;
}
function claudeAxes(desc, opts) {
  opts = opts || {};
  const existing = opts.existing || [], count = opts.count || 5;
  const env = Object.assign({}, process.env,
    { CLAUDE_CONFIG_DIR: process.env.CLAUDE_CONFIG_DIR || path.join(require("os").homedir(), ".claude") });
  const model = process.env.CLAUDE_MODEL || "claude-haiku-4-5";
  return new Promise((resolve, reject) => {
    execFile("claude",
      ["-p", claudePrompt(desc, existing, count), "--model", model, "--allowedTools", "WebSearch", "--output-format", "json"],
      { env, timeout: 150000, maxBuffer: 20 * 1024 * 1024, cwd: "/tmp" },
      (err, stdout) => {
        if (err && !stdout) return reject(new Error("claude " + (err.message || "")));
        try {
          const outer = JSON.parse(stdout);
          if (outer.is_error) return reject(new Error("claude result error"));
          resolve(parseAxes(outer.result || "").slice(0, count));
        } catch (e) { reject(e); }
      });
  });
}
// Groq (OpenAI-compatible). search=true -> recherche web intégrée (browser_search, gpt-oss, powered by Exa).
async function groqAxes(desc, key, opts) {
  opts = opts || {};
  const existing = opts.existing || [], count = opts.count || 5, search = opts.search !== false;
  const model = process.env.GROQ_MODEL || "openai/gpt-oss-120b";
  const body = { model, messages: [{ role: "user", content: axesPrompt(desc, existing, count) }], top_p: 1 };
  if (search) { body.tools = [{ type: "browser_search" }]; body.tool_choice = "required"; body.temperature = 1; body.max_completion_tokens = 4096; }
  else { body.response_format = { type: "json_object" }; body.temperature = 0.5; body.max_tokens = 800; }
  const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST", headers: { "content-type": "application/json", "authorization": "Bearer " + key },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error("groq " + r.status);
  const j = await r.json();
  return parseAxes(j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content).slice(0, count);
}
// Anthropic (secours, sans recherche web).
async function anthropicAxes(desc, key, opts) {
  opts = opts || {};
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST", headers: { "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({ model: "claude-sonnet-5", max_tokens: 700, messages: [{ role: "user", content: axesPrompt(desc, opts.existing || [], opts.count || 5) }] })
  });
  if (!r.ok) throw new Error("anthropic " + r.status);
  const j = await r.json();
  return parseAxes((j.content && j.content[0] && j.content[0].text) || "").slice(0, opts.count || 5);
}

function listRuns() { try { return fs.readdirSync(RUNS).filter(d => fs.existsSync(path.join(RUNS, d, "findings.json"))); } catch (e) { return []; } }
function runMeta(id) {
  const m = loadJSON(path.join(RUNS, id, "meta.json"), {});
  const cfg = loadJSON(path.join(RUNS, id, "config.json"), { revealPeers: false });
  return { id, owner: m.owner || "", watch: m.watch || "", run: m.run || id, created: m.created || "", revealPeers: !!cfg.revealPeers };
}
const CT = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png" };

function send(res, code, ct, body) { res.writeHead(code, { "content-type": ct, "cache-control": "no-store" }); res.end(body); }

// --- Console admin : HTTP Basic Auth (indépendant du portail AUTH global) ---
function adminOK(req) {
  const pass = process.env.ADMIN_PASS || "";
  if (!pass) return false;                          // pas de mot de passe -> console fermée
  const user = process.env.ADMIN_USER || "admin";
  const m = /^Basic\s+(.+)$/i.exec(req.headers["authorization"] || "");
  if (!m) return false;
  let dec = ""; try { dec = Buffer.from(m[1], "base64").toString("utf8"); } catch (e) { return false; }
  const i = dec.indexOf(":");
  return dec.slice(0, i) === user && dec.slice(i + 1) === pass;
}
function adminChallenge(res) {
  res.writeHead(401, { "www-authenticate": 'Basic realm="Constellation Console", charset="UTF-8"', "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" });
  res.end("Authentification requise");
}
// ── POSTHOG : analytics + session replay, derriere un bandeau de consentement ─
// Injecte dans TOUTE page HTML servie (home, wizard, constellations publiees et
// d evaluation) — sendFile est leur passage commun, donc une page nouvelle est
// instrumentee sans qu on y pense.
//
// RIEN NE PART SANS ACCORD : opt_out_capturing_by_default coupe la capture au
// chargement ; seul le clic sur « Accepter » appelle opt_in_capturing(). Le
// replay filme l ecran d un tiers — donnee personnelle, d ou le Cloud EU et le
// masquage des saisies.
//
// Sans POSTHOG_KEY, rien n est injecte : poser la cle suffit a tout activer.
const POSTHOG_KEY = process.env.POSTHOG_KEY || "";
const POSTHOG_HOST = process.env.POSTHOG_HOST || "https://eu.i.posthog.com";

function posthogSnippet() {
  if (!POSTHOG_KEY) return "";
  return `
<script>
!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
posthog.init('${POSTHOG_KEY}', {
  api_host: '${POSTHOG_HOST}',
  person_profiles: 'identified_only',
  // Le coeur du dispositif : aucune capture, aucun replay, tant que le bandeau
  // n a pas recu un clic. Le choix est memorise par PostHog lui-meme.
  opt_out_capturing_by_default: true,
  session_recording: { maskAllInputs: true, maskTextSelector: '[data-ph-mask]' }
});
(function(){
  // Le bandeau. Il ne s affiche que si le choix n a jamais ete fait : PostHog
  // garde la reponse, donc un refus ne se redemande pas a chaque page.
  // Le choix se lit dans NOTRE marqueur, jamais dans has_opted_out_capturing() :
  // opt_out_capturing_by_default met ce dernier a true des le depart, sans que
  // personne ait rien choisi. S'y fier fait sauter le bandeau — et le bug est
  // intermittent, puisqu'il depend de la vitesse de chargement d'array.js.
  var CLE = 'ph-consent-constellation';
  function pret(){
    // Les demonstrations de la page d accueil sont ces memes pages, incrustees en
    // iframe. Un bandeau de consentement y apparaitrait PAR-DESSUS la demonstration,
    // en double avec celui de la page hote — qui est le seul a compter.
    try {
      var q0 = new URLSearchParams(location.search);
      if (q0.get('embed') === '1' || q0.get('face') === '1' || window.top !== window.self) return;
    } catch(e) { return; }
    var choix = null;
    try { choix = localStorage.getItem(CLE); } catch(e) {}
    if (choix === 'oui') { try { posthog.opt_in_capturing(); } catch(e) {} return; }
    if (choix === 'non') return;
    var d = document.createElement('div');
    d.id = 'ph-consent';
    d.setAttribute('role','dialog');
    d.setAttribute('aria-label','Mesure d audience');
    d.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:2147483000;'
      + 'display:flex;flex-wrap:wrap;align-items:center;gap:14px;'
      + 'padding:14px 18px calc(14px + env(safe-area-inset-bottom));'
      + 'background:#0e1626;color:#dfe7f5;border-top:1px solid #2b3b59;'
      + 'box-shadow:0 -10px 30px rgba(0,0,0,.45);'
      + 'font:400 13px/1.5 system-ui,-apple-system,Segoe UI,sans-serif';
    // Le produit est bilingue, ET la langue change en cours de visite : un bandeau
    // fige au chargement reste en francais sous une interface passee en anglais.
    // On le reecrit donc a chaque bascule de <html lang>.
    function remplir(){
    var en = (document.documentElement.lang || '').slice(0,2).toLowerCase() === 'en';
    d.innerHTML = '<span style="flex:1 1 260px;min-width:0">'
      + (en ? 'This page can record how you browse it (clicks, moves, scrolling) to improve '
            + 'the interface. The data stays in Europe and input fields are masked. '
            + '<a href="https://posthog.com/privacy" target="_blank" rel="noopener" '
            + 'style="color:#7fb0ff">Learn more</a>'
            : 'Cette page peut enregistrer votre navigation (clics, d&eacute;placements, '
            + 'd&eacute;filement) pour am&eacute;liorer l&rsquo;interface. Les donn&eacute;es '
            + 'restent en Europe et les champs de saisie sont masqu&eacute;s. '
            + '<a href="https://posthog.com/privacy" target="_blank" rel="noopener" '
            + 'style="color:#7fb0ff">En savoir plus</a>')
      + '</span>'
      + '<span style="display:flex;gap:9px;flex:0 0 auto">'
      + '<button id="ph-non" style="cursor:pointer;padding:10px 15px;border-radius:9px;min-height:44px;'
      + 'border:1px solid #3a4a66;background:transparent;color:#b9c8e4;font:600 12.5px system-ui">'
      + (en ? 'Decline' : 'Refuser') + '</button>'
      + '<button id="ph-oui" style="cursor:pointer;padding:10px 17px;border-radius:9px;min-height:44px;'
      + 'border:1px solid #2f6bd8;background:#2f6bd8;color:#fff;font:600 12.5px system-ui">'
      + (en ? 'Accept' : 'Accepter') + '</button>'
      + '</span>';
    brancher();
    }
    document.body.appendChild(d);
    // Le bandeau est en bas, en z-index maximal : sans precaution il recouvre la barre
    // d action de la page (le Suivant du questionnaire, les fleches de livraison de la
    // constellation) et rend le produit inutilisable — surtout sur telephone, ou il
    // mesure 154 px. Il annonce donc sa hauteur, et les barres fixes s en ecartent
    // avec calc(... + var(--ph-bandeau)).
    function mesurer(){ document.documentElement.style.setProperty('--ph-bandeau', d.offsetHeight + 'px'); }
    mesurer();
    if (window.ResizeObserver) { try { new ResizeObserver(mesurer).observe(d); } catch(e) {} }
    window.addEventListener('resize', mesurer);
    function garder(v){ try { localStorage.setItem(CLE, v); } catch(e) {} }
    function partir(){
      window.removeEventListener('resize', mesurer);
      if (obs) { try { obs.disconnect(); } catch(e) {} }
      document.documentElement.style.setProperty('--ph-bandeau', '0px');
      d.remove();
    }
    function brancher(){
      d.querySelector('#ph-oui').onclick = function(){ garder('oui'); try{posthog.opt_in_capturing();}catch(e){} partir(); };
      d.querySelector('#ph-non').onclick = function(){ garder('non'); try{posthog.opt_out_capturing();}catch(e){} partir(); };
    }
    var obs = null;
    remplir();
    mesurer();          // la premiere mesure portait sur un bandeau encore vide
    try {
      obs = new MutationObserver(function(){ remplir(); mesurer(); });
      obs.observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
    } catch(e) {}
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', pret);
  else pret();
})();
</script>
`;
}

function injecterPosthog(html) {
  const sn = posthogSnippet();
  if (!sn) return html;
  const i = html.indexOf('</head>');
  if (i < 0) return html;                     // pas de <head> : on ne touche a rien
  return html.slice(0, i) + sn + html.slice(i);
}

function sendFile(res, fp, fallbackCT, req) {
  fs.readFile(fp, (e, d) => { if (e) { send(res, 404, "text/plain; charset=utf-8", "404"); return; }
    const ct = CT[path.extname(fp)] || fallbackCT || "application/octet-stream";
    // PostHog s injecte AVANT la compression, sinon le gzip porterait sur un
    // document qui ne contient pas le snippet.
    if (/text\/html/.test(ct) && POSTHOG_KEY) {
      const h = injecterPosthog(d.toString("utf8"));
      d = Buffer.from(h, "utf8");
    }
    const head = { "content-type": ct, "cache-control": "no-store, must-revalidate" };
    // compression a la volee : un bundle de constellation passe de ~950 Ko a ~270 Ko,
    // et les modules Three.js de 2,1 Mo a environ 500 Ko.
    const ae = String((req && req.headers && req.headers["accept-encoding"]) || "");
    const compressible = /json|text|javascript|svg/.test(ct);
    if (compressible && d.length > 4096 && ae.indexOf("gzip") !== -1) {
      zlib.gzip(d, (err, gz) => {
        if (err) { res.writeHead(200, head); res.end(d); return; }
        head["content-encoding"] = "gzip";
        head["vary"] = "accept-encoding";
        res.writeHead(200, head); res.end(gz);
      });
      return;
    }
    res.writeHead(200, head); res.end(d); })
}


function landing(res) {
  const rows = listRuns().map(runMeta).sort((a, b) => (b.created || "").localeCompare(a.created || "")).map(r =>
    `<li><a href="/r/${encodeURIComponent(r.id)}/">${esc(r.owner || r.id)}</a>` +
    `<span class="meta">${esc(r.watch)} · ${esc(r.run)} · ${r.revealPeers ? "peer reviews visible" : "blind"}</span></li>`).join("");
  const profs = listOwners().map(o => { const pr = ownerProfile(o) || {}; return { o, title: pr.title || o, updated: pr.updated || "" }; })
    .sort((a, b) => (b.updated || "").localeCompare(a.updated || "")).map(x =>
    `<li><a href="/wizard?owner=${encodeURIComponent(x.o)}">${esc(x.title)}</a>` +
    `<span class="meta">${esc(x.o)}${x.updated ? " · maj " + esc(x.updated) : ""}</span></li>`).join("");
  send(res, 200, "text/html; charset=utf-8",
    `<!doctype html><meta charset="utf-8"><title>Veille — Console</title>` +
    `<style>body{font:16px/1.5 system-ui,sans-serif;max-width:680px;margin:48px auto;padding:0 20px;color:#222}` +
    `h1{font-size:22px}h2{font-size:15px;color:#475569;margin:30px 0 6px;text-transform:uppercase;letter-spacing:.04em}` +
    `li{margin:10px 0}a{color:#0f766e;text-decoration:none;font-weight:600}.meta{color:#888;font-size:13px;margin-left:8px}` +
    `.top{display:flex;justify-content:space-between;align-items:baseline}.out{font-size:13px;color:#888;text-decoration:none}` +
    `.cta{display:inline-block;margin:8px 0 2px;background:#0d9488;color:#fff;padding:9px 16px;border-radius:8px;font-weight:600}` +
    `.cta:hover{background:#0f766e}</style>` +
    `<div class="top"><h1>Veille — Console</h1><span class="out">admin</span></div>` +
    `<h2>Profils de veille</h2><ul>${profs || "<li>Aucun profil.</li>"}</ul>` +
    `<a class="cta" href="/wizard">+ Nouveau profil</a>` +
    `<h2>Signalements</h2><ul><li><a href="/admin/signalements">Les retours des testeurs</a></li></ul>` +
    `<h2>Runs publiés</h2><ul>${rows || "<li>No run published yet.</li>"}</ul>`);
}

// --- Signalements : le canal de retour des testeurs ---
// Le module cote page ne demande qu'un nom et un message ; tout le contexte (page exacte,
// langue, navigateur, taille d'ecran, compte connecte) arrive avec, sans etre demande.
// Un signalement qui se perd est pire que pas de canal du tout : on ecrit d'abord sur
// disque, la notification par mail n'est qu'un bonus qui a le droit d'echouer.
const SIGNALEMENTS = path.join(ROOT, "signalements.jsonl");
const REPORT_TO = (process.env.REPORT_TO || "").trim();
// Garde-fou par IP, pas un anti-spam : le canal reste ouvert sans compte, il ne doit
// simplement pas pouvoir servir de robinet.
const signalHist = {};
function signalementAutorise(ip) {
  const now = Date.now(), h = signalHist[ip] || (signalHist[ip] = []);
  while (h.length && now - h[0] > 3600e3) h.shift();
  if (h.length >= 20) return false;                          // 20 par heure
  if (h.length && now - h[h.length - 1] < 8000) return false; // 8 s entre deux
  h.push(now); return true;
}
function htmlSignalement(s) {
  const l = (k, v) => v ? `<tr><td style="color:#8a857a;padding:2px 12px 2px 0;white-space:nowrap">${esc(k)}</td><td>${esc(v)}</td></tr>` : "";
  return `<div style="font-family:sans-serif;color:#181712;line-height:1.5">`
    + `<p style="margin:0 0 10px"><strong>${esc(s.nom)}</strong> signale quelque chose.</p>`
    + `<blockquote style="margin:0 0 16px;padding:10px 14px;border-left:3px solid #0d9488;background:#f6f4f0;white-space:pre-wrap">${esc(s.message)}</blockquote>`
    + `<table style="font-size:13px;border-collapse:collapse">`
    + l("page", s.page) + l("titre", s.titre) + l("langue", s.lang) + l("ecran", s.ecran)
    + l("compte", s.compte) + l("navigateur", s.ua) + l("quand", s.ts)
    + `</table></div>`;
}
function lireSignalements() {
  let brut = ""; try { brut = fs.readFileSync(SIGNALEMENTS, "utf8"); } catch (e) { return []; }
  return brut.split("\n").filter(Boolean).map(l => { try { return JSON.parse(l); } catch (e) { return null; } })
    .filter(Boolean).reverse();                               // le plus recent en haut
}
function pageSignalements(res) {
  const rows = lireSignalements().map(s => {
    const meta = [s.lang, s.ecran, s.compte].filter(Boolean).join(" · ");
    return `<article><header><strong>${esc(s.nom)}</strong>`
      + `<span class="q">${esc((s.ts || "").replace("T", " ").slice(0, 16))}</span></header>`
      + `<p class="msg">${esc(s.message)}</p>`
      + `<p class="ctx"><a href="${esc(s.page)}">${esc(s.page)}</a>${meta ? " — " + esc(meta) : ""}</p>`
      + `<p class="ua">${esc(s.ua || "")}</p></article>`;
  }).join("");
  send(res, 200, "text/html; charset=utf-8",
    `<!doctype html><meta charset="utf-8"><title>Signalements</title>`
    + `<style>body{font:15px/1.55 system-ui,sans-serif;max-width:780px;margin:44px auto;padding:0 20px;color:#222}`
    + `h1{font-size:22px;margin:0 0 4px}.sub{color:#888;font-size:13px;margin:0 0 26px}`
    + `article{border:1px solid #e6e3dc;border-radius:10px;padding:14px 16px;margin:0 0 14px;background:#fdfcfa}`
    + `header{display:flex;justify-content:space-between;align-items:baseline;gap:12px}`
    + `.q{color:#8a857a;font-size:12.5px;white-space:nowrap}`
    + `.msg{white-space:pre-wrap;margin:8px 0 10px}`
    + `.ctx{font-size:12.5px;color:#6f6a60;margin:0}.ctx a{color:#0f766e}`
    + `.ua{font-size:11px;color:#b3aea3;margin:4px 0 0;word-break:break-all}`
    + `a.back{color:#0f766e;font-weight:600;text-decoration:none;font-size:13px}</style>`
    + `<a class="back" href="/admin">&larr; Console</a>`
    + `<h1>Signalements</h1><p class="sub">${lireSignalements().length} message(s) — du plus recent au plus ancien.</p>`
    + (rows || `<p style="color:#888">Aucun signalement pour l'instant.</p>`));
}

const server = http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  const p = u.pathname;
  if (p.startsWith("/api/")) console.log(new Date().toISOString(), req.method, p);   // trace requêtes API

  // --- Portail de connexion ---
  if (AUTH_ON) {
    if (p === "/login") {
      if (req.method === "GET") { loginPage(res, 200, safeNext(u.searchParams.get("next")), false); return; }
      if (req.method === "POST") {
        parseForm(req, f => {
          const next = safeNext(f.next);
          if (String(f.user || "") === AUTH_USER && verifyPassword(f.password || "")) redirect(res, next, cookieSet());
          else loginPage(res, 401, next, true);
        });
        return;
      }
      send(res, 405, "text/plain", "method not allowed"); return;
    }
    if (p === "/logout") { redirect(res, "/login", cookieClear()); return; }
    if (!validToken(req)) {
      if (p.startsWith("/api/")) { send(res, 401, "application/json", '{"error":"auth required"}'); return; }
      redirect(res, "/login?next=" + encodeURIComponent(p + (u.search || ""))); return;
    }
  }

  // --- Wizard de profil (page) ---
  // /profil et /profil/<etape> pointent tous vers wizard.html (routage SPA côté client) :
  // sans ça, rafraîchir ou ouvrir un lien direct d'étape renvoyait un 404.
  if (p === "/wizard" || p === "/wizard/" || p === "/setup-profile" || p === "/setup-profile/"
      || p === "/profil" || p === "/profil/" || p.startsWith("/profil/")) {
    sendFile(res, path.join(PUB, "wizard.html"), "text/html; charset=utf-8"); return;
  }

  // --- API owners / profils (admin only) ---
  if (p === "/api/owners" && req.method === "GET") {
    if (!adminOK(req)) { send(res, 401, "application/json", '{"error":"admin only"}'); return; }
    send(res, 200, "application/json", JSON.stringify(listOwners().map(o => {
      const pr = ownerProfile(o) || {};
      return { owner: o, title: pr.title || o, updated: pr.updated || "" };
    })));
    return;
  }
  // --- Vérification email : envoi du code ---
  if (p === "/api/send-code" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e4) req.destroy(); });
    req.on("end", async () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const email = String(body.email || "").trim().toLowerCase();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { send(res, 400, "application/json", '{"error":"email invalide"}'); return; }
      const ip = String(req.headers["x-forwarded-for"] || req.socket.remoteAddress || "").split(",")[0].trim();
      const gate = allowSend(email, ip);
      if (!gate.ok) { send(res, 429, "application/json", JSON.stringify({ error: gate.ip ? "trop de demandes, réessaie plus tard" : "attends un instant avant de redemander un code", wait: gate.wait })); return; }
      const code = String(crypto.randomInt(100000, 1000000));
      emailCodes[email] = { code, exp: Date.now() + 10 * 60 * 1000 };
      saveCodes();
      try {
        const voie = await sendCode(email, code);
        send(res, 200, "application/json", JSON.stringify({ ok: true, voie }));
      } catch (e) {
        send(res, 500, "application/json", JSON.stringify({ error: "envoi impossible", detail: String(e.message || e).slice(0, 140) }));
      }
    });
    return;
  }
  // --- Notification « veille prête » (pipeline, admin only) ---
  if (p === "/api/notify-ready" && req.method === "POST") {
    if (!adminOK(req)) { send(res, 401, "application/json", '{"error":"admin only"}'); return; }
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e4) req.destroy(); });
    req.on("end", async () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const email = String(body.email || "").trim();
      const url = String(body.url || "").trim();
      if (!email || !url) { send(res, 400, "application/json", '{"error":"email et url requis"}'); return; }
      try {
        await sendReadyEmail(email, String(body.name || "").trim(), url);
        console.log("[notify-ready] envoyé à " + email + " -> " + url);
        send(res, 200, "application/json", '{"ok":true}');
      } catch (e) {
        send(res, 500, "application/json", JSON.stringify({ error: "envoi impossible", detail: String(e.message || e).slice(0, 140) }));
      }
    });
    return;
  }

  // --- Vérification email : vérif du code ---
  // --- Une REPONSE vaut confirmation (webhook entrant de Brevo) ---
  // --- Entrer sans mot de passe : l'email confirme SUFFIT ---
  // Le lien d'activation (ou une reponse) a deja prouve que la personne
  // controle l'adresse. Exiger un mot de passe en plus n'ajoute aucune preuve,
  // et donne un secret de plus a perdre.
  if (p === "/api/entrer" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e4) req.destroy(); });
    req.on("end", () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const email = String(body.email || "").trim().toLowerCase();
      const nom = String(body.name || "").trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { send(res, 400, "application/json", '{"error":"email invalide"}'); return; }
      const v = verifiedEmails[email];
      if (!(v && v > Date.now())) { send(res, 403, "application/json", '{"error":"email non vérifié"}'); return; }
      const compte = accountByEmail(email);
      try {
        if (compte) {
          delete verifiedEmails[email];
          console.log("[entrer] connexion " + email + " owner=" + compte.owner);
          res.writeHead(200, { "content-type": "application/json", "set-cookie": acctCookie(compte.owner), "cache-control": "no-store" });
          res.end(JSON.stringify({ ok: true, owner: compte.owner, name: compte.name || "", nouveau: false }));
          return;
        }
        if (!nom) { send(res, 400, "application/json", '{"error":"nom requis"}'); return; }
        const owner = SLUG(email);
        const today = new Date().toISOString().slice(0, 10);
        saveAccount({ email, owner, name: nom, passHash: null, verified: true, created: today });
        delete verifiedEmails[email];
        console.log("[entrer] creation owner=" + owner + " email=" + email);
        res.writeHead(200, { "content-type": "application/json", "set-cookie": acctCookie(owner), "cache-control": "no-store" });
        res.end(JSON.stringify({ ok: true, owner, name: nom, nouveau: true }));
      } catch (e) {
        send(res, 500, "application/json", JSON.stringify({ error: String(e.message || e).slice(0, 140) }));
      }
    });
    return;
  }

  // --- Le LIEN d'activation du mail ---
  if (p === "/api/activer" && req.method === "GET") {
    const email = String(u.searchParams.get("e") || "").trim().toLowerCase();
    const t = String(u.searchParams.get("t") || "").trim();
    const rec = emailCodes[email];
    const ok = !!(rec && rec.code === t && Date.now() < rec.exp);
    if (ok) { delete emailCodes[email]; saveCodes(); verifiedEmails[email] = Date.now() + 30 * 60 * 1000;
              console.log("[activer] " + email); }
    // On ne renvoie pas vers « un autre onglet » : le parcours REPREND ici.
    const dest = "/?active=" + (ok ? "1" : "0") + "&e=" + encodeURIComponent(email);
    res.writeHead(302, { "location": dest, "cache-control": "no-store" });
    res.end();
    return;
  }

  if (p === "/api/inbound-reply" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 5e6) req.destroy(); });
    req.on("end", () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const items = Array.isArray(body.items) ? body.items : [body];
      const vus = [];
      for (const it of items) {
        const f = (it && it.from) || {};
        const addr = String(f.address || f.email || "").trim().toLowerCase();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(addr)) continue;
        // On ne confirme que ce qui a ete demande : sans code en attente pour
        // cette adresse, une reponse ne prouve rien qu'on ait sollicite.
        if (!emailCodes[addr]) continue;
        delete emailCodes[addr]; saveCodes();
        verifiedEmails[addr] = Date.now() + 30 * 60 * 1000;
        vus.push(addr);
      }
      if (vus.length) console.log("[inbound-reply] confirme par reponse : " + vus.join(", "));
      send(res, 200, "application/json", JSON.stringify({ ok: true, confirmes: vus.length }));
    });
    return;
  }

  // --- Le front demande si l'email a ete confirme entre-temps (par reponse) ---
  if (p === "/api/email-confirme" && req.method === "GET") {
    const email = String((u.searchParams.get("email") || "")).trim().toLowerCase();
    const v = verifiedEmails[email];
    send(res, 200, "application/json", JSON.stringify({ ok: !!(v && v > Date.now()) }));
    return;
  }

  if (p === "/api/verify-code" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e4) req.destroy(); });
    req.on("end", () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const email = String(body.email || "").trim().toLowerCase();
      const code = String(body.code || "").trim();
      const rec = emailCodes[email];
      const ok = !!(rec && rec.code === code && Date.now() < rec.exp);
      if (ok) { delete emailCodes[email]; saveCodes(); verifiedEmails[email] = Date.now() + 30 * 60 * 1000; }  // fenêtre de signup
      send(res, 200, "application/json", JSON.stringify({ ok }));
    });
    return;
  }

  // --- Comptes : création (signup) ---
  if (p === "/api/signup" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e4) req.destroy(); });
    req.on("end", () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const email = String(body.email || "").trim().toLowerCase();
      const password = String(body.password || "");
      const name = String(body.name || "").trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { send(res, 400, "application/json", '{"error":"email invalide"}'); return; }
      if (password.length < 8) { send(res, 400, "application/json", '{"error":"mot de passe trop court"}'); return; }
      if (!name) { send(res, 400, "application/json", '{"error":"nom requis"}'); return; }
      if (accountByEmail(email)) { send(res, 409, "application/json", '{"error":"exists"}'); return; }
      const v = verifiedEmails[email];
      if (!(v && v > Date.now())) { send(res, 403, "application/json", '{"error":"email non vérifié"}'); return; }
      const owner = SLUG(email);
      const today = new Date().toISOString().slice(0, 10);
      try {
        saveAccount({ email, owner, name, passHash: hashPw(password), verified: true, created: today });
        delete verifiedEmails[email];
        console.log("[signup] owner=" + owner + " email=" + email);
        res.writeHead(200, { "content-type": "application/json", "set-cookie": acctCookie(owner), "cache-control": "no-store" });
        res.end(JSON.stringify({ ok: true, owner, name }));
      } catch (e) { console.error("[signup] FAIL " + email + " " + (e.message || e)); send(res, 500, "application/json", '{"error":"création impossible"}'); }
    });
    return;
  }

  // --- Comptes : connexion (login) ---
  if (p === "/api/login" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e4) req.destroy(); });
    req.on("end", () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const email = String(body.email || "").trim().toLowerCase();
      const password = String(body.password || "");
      const a = accountByEmail(email);
      if (!a || !verifyPw(password, a.passHash)) { send(res, 401, "application/json", '{"error":"identifiants invalides"}'); return; }
      res.writeHead(200, { "content-type": "application/json", "set-cookie": acctCookie(a.owner), "cache-control": "no-store" });
      res.end(JSON.stringify({ ok: true, owner: a.owner, name: a.name || "" }));
    });
    return;
  }

  // --- Comptes : mot de passe oublié (réinitialisation par code email) ---
  // Flux : le front demande d'abord un code via /api/send-code, puis poste ici
  // {email, code, password}. On vérifie le code (même réserve que verify-code),
  // l'existence du compte, on remplace le hash, et on ouvre une session.
  if (p === "/api/reset-password" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e4) req.destroy(); });
    req.on("end", () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const email = String(body.email || "").trim().toLowerCase();
      const code = String(body.code || "").trim();
      const password = String(body.password || "");
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { send(res, 400, "application/json", '{"error":"email invalide"}'); return; }
      if (password.length < 8) { send(res, 400, "application/json", '{"error":"mot de passe trop court"}'); return; }
      const rec = emailCodes[email];
      if (!(rec && rec.code === code && Date.now() < rec.exp)) { send(res, 401, "application/json", '{"error":"code invalide ou expiré"}'); return; }
      const a = accountByEmail(email);
      if (!a) { send(res, 404, "application/json", '{"error":"aucun compte pour cet email"}'); return; }
      try {
        a.passHash = hashPw(password);
        saveAccount(a);
        delete emailCodes[email];
        saveCodes();
        console.log("[reset-password] owner=" + a.owner);
        res.writeHead(200, { "content-type": "application/json", "set-cookie": acctCookie(a.owner), "cache-control": "no-store" });
        res.end(JSON.stringify({ ok: true, owner: a.owner, name: a.name || "" }));
      } catch (e) { console.error("[reset-password] FAIL " + email + " " + (e.message || e)); send(res, 500, "application/json", '{"error":"réinitialisation impossible"}'); }
    });
    return;
  }

  // --- Comptes : déconnexion ---
  if (p === "/api/logout" && req.method === "POST") {
    res.writeHead(200, { "content-type": "application/json", "set-cookie": acctClear, "cache-control": "no-store" });
    res.end('{"ok":true}'); return;
  }

  // --- Comptes : qui suis-je (session courante) ---
  if (p === "/api/me" && req.method === "GET") {
    const owner = currentOwner(req);
    if (!owner) { send(res, 200, "application/json", '{"ok":false}'); return; }
    const a = accountByOwner(owner);
    if (!a) { send(res, 200, "application/json", '{"ok":false}'); return; }
    send(res, 200, "application/json", JSON.stringify({ ok: true, owner, email: a.email, name: a.name || "" }));
    return;
  }

  // --- Comptes : email déjà pris ? (bascule signup/login côté front) ---
  if (p === "/api/account-exists" && req.method === "GET") {
    const email = String(u.searchParams.get("email") || "").trim().toLowerCase();
    send(res, 200, "application/json", JSON.stringify({ exists: !!(email && accountByEmail(email)) }));
    return;
  }

  if (p === "/api/profile") {
    // Lecture : la session prime (son propre profil) ; sinon ?owner= réservé à l'admin.
    if (req.method === "GET") {
      const sess = currentOwner(req);
      const owner = sess || (adminOK(req) ? SLUG(u.searchParams.get("owner") || "") : "");
      if (!owner) { send(res, 401, "application/json", '{"error":"connexion requise"}'); return; }
      const pr = ownerProfile(owner);
      if (pr && pr.passHash) delete pr.passHash;   // jamais de hash renvoyé au client
      send(res, 200, "application/json", JSON.stringify(pr)); return;   // null si absent
    }
    if (req.method === "POST") {
      let b = ""; req.on("data", c => { b += c; if (b.length > 2e5) req.destroy(); });
      req.on("end", () => {
        let body; try { body = JSON.parse(b || "{}"); } catch (e) { send(res, 400, "application/json", '{"error":"invalid json"}'); return; }
        const prof = body.profile || {};
        // owner = compte connecté (sécurité : on n'écrase jamais le profil d'un autre).
        // L'admin peut viser un owner explicite pour éditer les profils de démo.
        const sess = currentOwner(req);
        const owner = sess || (adminOK(req) ? SLUG(body.owner || prof.title || "") : "");
        if (!owner) { send(res, 401, "application/json", '{"error":"connexion requise"}'); return; }
        if (!prof.title || !String(prof.title).trim()) { send(res, 400, "application/json", '{"error":"title required"}'); return; }
        const today = new Date().toISOString().slice(0, 10);
        prof.owner = owner; prof.updated = today;
        // Le mot de passe vit dans le COMPTE (pas dans le profil) : on ne le stocke jamais ici.
        delete prof.password;
        // Le hash éventuellement présent sur un ancien profil est laissé tel quel (compat), sinon absent.
        try {
          const { runConfig, profileMd, subjectMd, reglesAxes } = deriveArtifacts(owner, prof);
          // Le nom et le compte vivent dans les DEUX fichiers : le flux lit l'un ou
          // l'autre selon ce qu'il trouve, et une veille sans nom s'affiche en slug.
          const cptOwner = compteDuOwner(owner);
          if (!prof.nom) prof.nom = (prof.title && String(prof.title).trim()) || owner;
          if (cptOwner && !prof.compte) { prof.compte = cptOwner.compte; prof.compte_nom = cptOwner.compte_nom; }
          if (!runConfig.nom) runConfig.nom = prof.nom;
          if (cptOwner && !runConfig.compte) { runConfig.compte = cptOwner.compte; runConfig.compte_nom = cptOwner.compte_nom; }
          saveJSON(path.join(OWNERS, owner, "profile.json"), prof);
          saveJSON(path.join(OWNERS, owner, "run-config.json"), runConfig);
          fs.writeFileSync(path.join(OWNERS, owner, "profile.md"), profileMd);
          fs.writeFileSync(path.join(OWNERS, owner, "subject.md"), subjectMd);
          saveJSON(path.join(OWNERS, owner, "preferences", "regles-axes.json"), reglesAxes);
          // Le silo est le seul endroit ou la pipeline va chercher : y ecrire fait partie de l'enregistrement.
          const silo = mirrorSilo(owner, {
            "profile.json": JSON.stringify(prof, null, 2),
            "run-config.json": JSON.stringify(runConfig, null, 2),
            "profile.md": profileMd,
            "subject.md": subjectMd,
            "preferences/regles-axes.json": JSON.stringify(reglesAxes, null, 2)
          });
          if (!silo.ok) console.error("[profile] SILO NON ECRIT owner=" + owner + " — " + silo.raison);
          console.log("[profile] SAVED owner=" + owner + " title=" + (prof.title || "") + " email=" + (prof.email || "") + " verified=" + !!prof.emailVerified + " silo=" + (silo.ok ? silo.dir : "NON"));
          send(res, 200, "application/json", JSON.stringify({ ok: true, owner, updated: today, silo: !!silo.ok }));
        } catch (e) { console.error("[profile] WRITE FAILED owner=" + owner + " err=" + (e.message || e)); send(res, 500, "application/json", '{"error":"write failed"}'); }
      });
      return;
    }
    send(res, 405, "text/plain", "method not allowed"); return;
  }

  // --- API suggestion d'axes ---
  if (p === "/api/suggest-axes" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 1e5) req.destroy(); });
    req.on("end", async () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const desc = String(body.description || "").slice(0, 2000);
      const existing = Array.isArray(body.existing) ? body.existing.map(x => String(x).slice(0, 80)).filter(Boolean).slice(0, 12) : [];
      const count = Math.min(Math.max(parseInt(body.count, 10) || 5, 1), 6);
      let axes = null, source = "fallback";
      if (desc.trim()) {
        // Backend par défaut = Claude Code headless + WebSearch (abo Max, zéro clé).
        if (process.env.AXES_BACKEND !== "off") {
          try { axes = await claudeAxes(desc, { existing, count }); source = "claude+web"; } catch (e) { axes = null; }
        }
        // Secours si une clé est fournie (dév local hors serveur).
        if (!axes && process.env.GROQ_API_KEY) { try { axes = await groqAxes(desc, process.env.GROQ_API_KEY, { existing, count, search: true }); source = "groq+web"; } catch (e) { axes = null; } }
        if (!axes && process.env.ANTHROPIC_API_KEY) { try { axes = await anthropicAxes(desc, process.env.ANTHROPIC_API_KEY, { existing, count }); source = "anthropic"; } catch (e) { axes = null; } }
      }
      if (!axes) { axes = fallbackAxes(desc).slice(0, count); source = "fallback"; }
      send(res, 200, "application/json", JSON.stringify({ axes, source }));
    });
    return;
  }

  // --- API annotations ---
  if (p === "/api/annotations") {
    if (req.method === "GET") { const run = u.searchParams.get("run") || ""; send(res, 200, "application/json", JSON.stringify(loadJSON(ANN, {})[run] || {})); return; }
    if (req.method === "POST") {
      let b = ""; req.on("data", c => { b += c; if (b.length > 1e6) req.destroy(); });
      req.on("end", () => {
        try {
          const { run, fid, user, score, comment, form, source_score } = JSON.parse(b || "{}");
          if (!run || !fid || !user) { send(res, 400, "application/json", '{"error":"run/fid/user required"}'); return; }
          const db = loadJSON(ANN, {});
          db[run] = db[run] || {}; db[run][fid] = db[run][fid] || {};
          db[run][fid][String(user).slice(0, 80)] = {
            score: (typeof score === "number" && score >= 1 && score <= 10) ? score : null,
            comment: String(comment || "").slice(0, 4000),
            form: String(form || "").slice(0, 4000),
            source_score: (typeof source_score === "number" && source_score >= 1 && source_score <= 5) ? source_score : null,
            ts: new Date().toISOString()
          };
          saveJSON(ANN, db); send(res, 200, "application/json", '{"ok":true}');
        } catch (e) { send(res, 400, "application/json", '{"error":"invalid json"}'); }
      });
      return;
    }
    send(res, 405, "text/plain", "method not allowed"); return;
  }
  if (p === "/api/notation-terminee" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 5e6) req.destroy(); });
    req.on("end", () => {
      try {
        const o = JSON.parse(b || "{}");
        const id = String(o.run || "").replace(/[^a-zA-Z0-9._-]/g, "");
        const dir = path.join(RUNS, id);
        if (!id || !fs.existsSync(dir)) { send(res, 400, "application/json", '{"error":"run inconnu"}'); return; }
        const rec = { done: true, ts: new Date().toISOString(), barre_qualite: (typeof o.barre_qualite === "number" ? o.barre_qualite : null), notes: o.notes || {}, profil_prochaine_run: o.profil_prochaine_run || null };
        fs.writeFileSync(path.join(dir, "notation-terminee.json"), JSON.stringify(rec, null, 2));
        send(res, 200, "application/json", '{"ok":true}');
      } catch (e) { send(res, 400, "application/json", '{"error":"invalid json"}'); }
    });
    return;
  }

  if (p === "/api/export" && req.method === "GET") {
    const run = u.searchParams.get("run");
    const db = loadJSON(ANN, {});
    res.writeHead(200, { "content-type": "application/json", "content-disposition": "attachment; filename=annotations.json" });
    res.end(JSON.stringify(run ? (db[run] || {}) : db, null, 2)); return;
  }
  if (p === "/api/runs" && req.method === "GET") { send(res, 200, "application/json", JSON.stringify(listRuns().map(runMeta))); return; }

  // --- Signalement d'un bug / d'une remarque (ouvert a tous, sans compte) ---
  if (p === "/api/signalement" && req.method === "POST") {
    let b = ""; req.on("data", c => { b += c; if (b.length > 2e4) req.destroy(); });
    req.on("end", () => {
      let body; try { body = JSON.parse(b || "{}"); } catch (e) { body = {}; }
      const nom = String(body.nom || "").trim().slice(0, 80);
      const message = String(body.message || "").trim().slice(0, 4000);
      if (!nom || !message) { send(res, 400, "application/json", '{"error":"nom et message requis"}'); return; }
      const ip = String(req.headers["x-forwarded-for"] || req.socket.remoteAddress || "").split(",")[0].trim();
      if (!signalementAutorise(ip)) { send(res, 429, "application/json", '{"error":"trop de signalements"}'); return; }
      const ligne = {
        ts: new Date().toISOString(), nom, message,
        page:   String(body.page   || "").slice(0, 400),
        titre:  String(body.titre  || "").slice(0, 200),
        lang:   String(body.lang   || "").slice(0, 5),
        ecran:  String(body.ecran  || "").slice(0, 20),
        compte: String(body.compte || "").slice(0, 160),
        ua:     String(body.ua     || "").slice(0, 300),
        ip
      };
      try { fs.appendFileSync(SIGNALEMENTS, JSON.stringify(ligne) + "\n"); }
      catch (e) {
        console.error("[signalement] ecriture impossible : " + e.message);
        send(res, 500, "application/json", '{"error":"enregistrement impossible"}'); return;
      }
      console.log("[signalement] " + nom + " — " + ligne.page);
      send(res, 200, "application/json", '{"ok":true}');
      // Le mail part apres la reponse : le testeur n'attend pas notre serveur de sortie.
      if (REPORT_TO) {
        sendDirect(REPORT_TO, "Signalement de " + nom + " — Constellation", htmlSignalement(ligne))
          .then(r => console.log("[signalement] mail -> " + REPORT_TO + " via " + r.mx))
          .catch(e => console.error("[signalement] mail impossible : " + e.message));
      }
    });
    return;
  }

  // --- Les signalements recus (console admin) ---
  if (p === "/admin/signalements" || p === "/admin/signalements/") {
    if (!adminOK(req)) { adminChallenge(res); return; }
    pageSignalements(res); return;
  }

  // --- /m/<id>/ : ancienne mindmap autonome -> l'app intégrée (mindmap = écran d'accueil de /r/) ---
  const mm = p.match(/^\/m\/([^/]+)(\/.*)?$/);
  if (mm) {
    const id = mm[1]; // déjà encodé dans l'URL
    res.writeHead(302, { location: "/r/" + id + "/" + (u.search || ""), "cache-control": "no-store" });
    res.end(); return;
  }

  // --- graphe de findings : /g/<id>/ (design v3, Connected Papers) ---
  const mg = p.match(/^\/g\/([^/]+)(\/.*)?$/);
  if (mg) {
    const id = decodeURIComponent(mg[1]); const sub = mg[2] || "/";
    const dir = path.join(RUNS, id);
    if (sub === "/" || sub === "/index.html") { sendFile(res, path.join(PUB, "graph.html"), "text/html; charset=utf-8"); return; }
    if (sub === "/findings.json") { sendFile(res, path.join(dir, "findings.json"), req); return; }
    if (sub === "/links.json") { sendFile(res, path.join(dir, "links.json"), req); return; }
    send(res, 404, "text/plain", "404"); return;
  }

  // --- constellation par-run : /c/<id>/ (surface d evaluation Three.js, bundle self-contained) ---
  const mc = p.match(/^\/c\/([^/]+)(\/.*)?$/);
  if (mc) {
    const id = decodeURIComponent(mc[1]); const dir = path.join(RUNS, id);
    const rel = ((mc[2] || "/").replace(/^\//, "")) || "index.html";
    const target = rel === "index.html" ? "constellation.html" : rel;
    if (target === "constellation.html" || target === "constellation-data.json" || target.indexOf("vendor/") === 0) {
      const fp = path.join(dir, path.normalize(target));
      if (fp.indexOf(dir) === 0 && fs.existsSync(fp)) { sendFile(res, fp, req); return; }
    }
    send(res, 404, "text/plain", "404"); return;
  }

  // --- per-run static : /r/<id>/(index.html|findings.json|config.json) ---
  const mr = p.match(/^\/r\/([^/]+)(\/.*)?$/);
  if (mr) {
    const id = decodeURIComponent(mr[1]); const sub = mr[2] || "/";
    const dir = path.join(RUNS, id);
    if (sub === "/" || sub === "/index.html") { sendFile(res, path.join(PUB, "app.html"), "text/html; charset=utf-8"); return; }
    if (sub === "/findings.json") { sendFile(res, path.join(dir, "findings.json"), req); return; }
    if (sub === "/config.json") {
      const cfg = loadJSON(path.join(dir, "config.json"), { revealPeers: false });
      send(res, 200, "application/json", JSON.stringify({ revealPeers: !!cfg.revealPeers })); return;
    }
    if (sub === "/profile.json") {
      const pf = path.join(dir, "profile.json");
      if (!fs.existsSync(pf)) { send(res, 200, "application/json", "null"); return; }  // pas de profil -> bouton masqué
      sendFile(res, pf, req); return;
    }
    send(res, 404, "text/plain", "404"); return;
  }

  // --- Console admin (protégée) ---
  if (p === "/admin" || p === "/admin/") {
    if (!adminOK(req)) { adminChallenge(res); return; }
    landing(res); return;
  }

  // --- Racine = page produit (landing + wizard), PAS la console ---
  if (p === "/") { sendFile(res, path.join(PUB, "wizard.html"), "text/html; charset=utf-8"); return; }

  // --- static fallback ---
  let fp = path.join(PUB, path.normalize(p).replace(/^(\.\.[/\\])+/, ""));
  if (!fp.startsWith(PUB)) { send(res, 403, "text/plain", "forbidden"); return; }
  sendFile(res, fp, req);
});

server.listen(PORT, () => console.log("AI-Watch multi-run review server on :" + PORT + " (data=" + ROOT + ", auth=" + (AUTH_ON ? "on" : "OFF") + ")"));
