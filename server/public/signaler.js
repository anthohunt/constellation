/* Signaler — module de retour utilisateur, posé sur toutes les surfaces du produit.
   Le formulaire n'est pas ce qui compte : ce qui compte est ce qu'il joint tout seul
   (page exacte, langue, navigateur, taille d'écran, compte connecté). Un testeur écrit
   « ça marche pas » et le rapport reste exploitable.
   Tout vit dans un shadow DOM : la page hôte est une constellation Three.js ou un
   questionnaire, aucune de leurs règles CSS ne doit pouvoir déformer ce panneau,
   et aucune des nôtres ne doit fuir chez elles. */
(function () {
  "use strict";
  if (window.__signalerPose) return;               // idempotent : un seul module par page
  window.__signalerPose = true;
  /* Les constellations de demonstration de la page d'accueil sont les MEMES pages,
     incrustees dans un cadre. Un bouton de signalement y serait minuscule, en double
     avec celui de la page hote, et pointerait sur une demo. On ne se pose pas la. */
  try {
    var p0 = new URLSearchParams(location.search);
    if (p0.get("embed") === "1" || p0.get("face") === "1" || window.top !== window.self) return;
  } catch (e) { return; }

  var T = {
    fr: {
      ouvrir: "Signaler un problème",
      titre: "Signaler un problème",
      sous: "Un bug, une erreur, une remarque — tout est utile.",
      nom: "Votre nom",
      nomPh: "Prénom ou nom",
      msg: "Que s'est-il passé&nbsp;?",
      msgPh: "Décrivez ce que vous faisiez, ce que vous attendiez, et ce qui s'est passé à la place.",
      joint: "La page, la langue et votre navigateur sont joints automatiquement.",
      envoyer: "Envoyer",
      envoi: "Envoi…",
      merci: "Merci, c'est envoyé.",
      merciSous: "Le message est arrivé sur le serveur. Vous pouvez fermer cette fenêtre.",
      fermer: "Fermer",
      encore: "Signaler autre chose",
      manque: "Il manque votre nom ou votre message.",
      rate: "Trop de messages d'affilée — patientez un instant.",
      erreur: "L'envoi a échoué. Réessayez dans un instant."
    },
    en: {
      ouvrir: "Report an issue",
      titre: "Report an issue",
      sous: "A bug, a mistake, a remark — all of it helps.",
      nom: "Your name",
      nomPh: "First or last name",
      msg: "What happened?",
      msgPh: "Describe what you were doing, what you expected, and what happened instead.",
      joint: "The page, the language and your browser are attached automatically.",
      envoyer: "Send",
      envoi: "Sending…",
      merci: "Thanks, it's sent.",
      merciSous: "The message reached the server. You can close this window.",
      fermer: "Close",
      encore: "Report something else",
      manque: "Your name or your message is missing.",
      rate: "Too many messages in a row — hold on a moment.",
      erreur: "Sending failed. Try again in a moment."
    }
  };
  /* La langue se lit au moment de l'ouverture, jamais au chargement : sur ces pages
     elle change en cours de visite (bascule FR/EN) et le panneau doit suivre. */
  function lang() {
    try {
      var q = new URLSearchParams(location.search).get("lang");
      if (q === "fr" || q === "en") return q;
      var s = localStorage.getItem("constel-lang");
      if (s === "fr" || s === "en") return s;
    } catch (e) {}
    var h = (document.documentElement.lang || "").slice(0, 2).toLowerCase();
    if (h === "fr" || h === "en") return h;
    return (navigator.language || "fr").slice(0, 2).toLowerCase() === "en" ? "en" : "fr";
  }
  var t = T.fr;

  var CSS = ''
    + ':host{all:initial}'
    + '*{box-sizing:border-box;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}'
    /* La pastille ne doit se poser sur AUCUNE barre d action : les pages declarent
       la hauteur a laisser libre (--signaler-bas), et le bandeau de consentement
       annonce la sienne (--ph-bandeau). Les deux s additionnent. */
    + '.b{position:fixed;right:18px;z-index:2147483000;display:inline-flex;align-items:center;gap:8px;'
    + 'bottom:calc(var(--signaler-bas, 18px) + var(--ph-bandeau, 0px));'
    + 'background:#0d9488;color:#fff;border:0;border-radius:999px;padding:10px 16px 10px 13px;font-size:13.5px;'
    + 'font-weight:600;letter-spacing:.01em;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.28);'
    + 'transition:background .15s,transform .15s,box-shadow .15s}'
    + '.b:hover{background:#0f766e;transform:translateY(-1px);box-shadow:0 7px 22px rgba(0,0,0,.34)}'
    + '.b:focus-visible{outline:2px solid #fff;outline-offset:2px}'
    + '.b svg{width:15px;height:15px;flex:0 0 auto}'
    + '.b .lb{white-space:nowrap}'
    + '@media (max-width:560px){.b .lb{display:none}.b{padding:12px;right:14px}}'
    + '.voile{position:fixed;inset:0;z-index:2147483001;background:rgba(12,14,16,.45);'
    + 'display:flex;align-items:flex-end;justify-content:flex-end;padding:18px;backdrop-filter:blur(2px)}'
    + '.p{width:380px;max-width:100%;max-height:88vh;overflow:auto;background:#fff;color:#181712;'
    + 'border-radius:14px;box-shadow:0 18px 60px rgba(0,0,0,.4);padding:20px 20px 18px;'
    + 'animation:mo .16s ease-out}'
    + '@keyframes mo{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}'
    + '.hd{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}'
    + 'h2{margin:0;font-size:16px;font-weight:700;letter-spacing:-.01em}'
    + '.x{border:0;background:none;color:#8a857a;font-size:20px;line-height:1;cursor:pointer;padding:0 2px}'
    + '.x:hover{color:#181712}'
    + '.sous{margin:5px 0 15px;font-size:13px;color:#6f6a60;line-height:1.45}'
    + 'label{display:block;font-size:12px;font-weight:600;color:#4a453d;margin:0 0 5px;'
    + 'text-transform:uppercase;letter-spacing:.05em}'
    + 'input,textarea{width:100%;border:1px solid #ddd8cf;border-radius:9px;padding:9px 11px;'
    + 'font-size:14px;color:#181712;background:#fdfcfa;resize:vertical}'
    + 'input:focus,textarea:focus{outline:0;border-color:#0d9488;box-shadow:0 0 0 3px rgba(13,148,136,.14)}'
    + 'textarea{min-height:104px;line-height:1.5}'
    + '.ch{margin-bottom:13px}'
    + '.note{font-size:11.5px;color:#8a857a;line-height:1.45;margin:0 0 13px}'
    + '.env{width:100%;background:#0d9488;color:#fff;border:0;border-radius:9px;padding:11px;'
    + 'font-size:14px;font-weight:600;cursor:pointer}'
    + '.env:hover{background:#0f766e}.env[disabled]{opacity:.55;cursor:default}'
    + '.err{margin:10px 0 0;font-size:12.5px;color:#b3261e;line-height:1.4}'
    + '.ok{text-align:center;padding:12px 4px 4px}'
    + '.ok .rond{width:44px;height:44px;border-radius:50%;background:#e6f5f2;color:#0d9488;'
    + 'display:flex;align-items:center;justify-content:center;margin:0 auto 12px}'
    + '.ok .rond svg{width:22px;height:22px}'
    + '.ok p{margin:0 0 4px;font-size:15px;font-weight:600}'
    + '.ok .m{font-size:13px;color:#6f6a60;font-weight:400;line-height:1.45}'
    + '.rangee{display:flex;gap:8px;margin-top:16px}'
    + '.rangee button{flex:1;border-radius:9px;padding:9px;font-size:13px;font-weight:600;cursor:pointer}'
    + '.sec{background:#fff;color:#4a453d;border:1px solid #ddd8cf}.sec:hover{background:#f6f4f0}'
    + '.pri{background:#0d9488;color:#fff;border:0}.pri:hover{background:#0f766e}';

  var hote = document.createElement("div");
  hote.id = "constellation-signaler";
  var sh = hote.attachShadow({ mode: "open" });
  var style = document.createElement("style"); style.textContent = CSS; sh.appendChild(style);

  var ICONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    + 'stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4"/><path d="M12 17h.01"/>'
    + '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>';
  var CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" '
    + 'stroke-linecap="round" stroke-linejoin="round"><path d="m20 6-11 11-5-5"/></svg>';

  var bouton = document.createElement("button");
  bouton.className = "b"; bouton.type = "button";
  sh.appendChild(bouton);

  var voile = null;

  function majBouton() {
    bouton.innerHTML = ICONE + '<span class="lb"></span>';
    bouton.querySelector(".lb").textContent = t.ouvrir;
    bouton.setAttribute("aria-label", t.ouvrir);
    bouton.title = t.ouvrir;
  }

  /* Ce que le message emporte avec lui. Le compte connecté, s'il y en a un, sort du
     wizard (window.__ivCompte) — on ne le demande pas, on ne le devine pas. */
  function contexte() {
    var c = {
      page: location.href,
      titre: (document.title || "").slice(0, 200),
      lang: lang(),
      ua: (navigator.userAgent || "").slice(0, 300),
      ecran: window.innerWidth + "x" + window.innerHeight
    };
    try {
      var cpt = window.__ivCompte;
      if (cpt && cpt.email) { c.compte = String(cpt.email).slice(0, 160); }
    } catch (e) {}
    return c;
  }

  function fermer() { if (voile) { voile.remove(); voile = null; bouton.style.display = ""; bouton.focus(); } }

  function ouvrir() {
    if (voile) return;
    t = T[lang()];
    bouton.style.display = "none";
    voile = document.createElement("div"); voile.className = "voile";
    voile.addEventListener("click", function (e) { if (e.target === voile) fermer(); });
    var p = document.createElement("div"); p.className = "p";
    p.setAttribute("role", "dialog"); p.setAttribute("aria-modal", "true");
    voile.appendChild(p); sh.appendChild(voile);
    formulaire(p);
    var n = p.querySelector("#nom"); if (n) n.focus();
  }

  function formulaire(p) {
    p.innerHTML = ''
      + '<div class="hd"><h2></h2><button class="x" type="button" aria-label="fermer">&times;</button></div>'
      + '<p class="sous"></p>'
      + '<div class="ch"><label for="nom"></label><input id="nom" type="text" maxlength="80" autocomplete="name"></div>'
      + '<div class="ch"><label for="msg"></label><textarea id="msg" maxlength="4000"></textarea></div>'
      + '<p class="note"></p>'
      + '<button class="env" type="button"></button>'
      + '<p class="err" hidden></p>';
    p.querySelector("h2").textContent = t.titre;
    p.querySelector(".sous").textContent = t.sous;
    p.querySelector('label[for="nom"]').textContent = t.nom;
    p.querySelector('label[for="msg"]').innerHTML = t.msg;
    p.querySelector(".note").textContent = t.joint;
    p.querySelector(".env").textContent = t.envoyer;
    var nom = p.querySelector("#nom"), msg = p.querySelector("#msg");
    nom.placeholder = t.nomPh; msg.placeholder = t.msgPh;
    /* On se souvient du nom, pas du message : le deuxième signalement ne doit pas
       recommencer par une case à remplir, mais il ne doit pas non plus rejouer le premier. */
    try { nom.value = localStorage.getItem("signaler-nom") || ""; } catch (e) {}
    try {
      var cpt = window.__ivCompte;
      if (!nom.value && cpt && cpt.name) nom.value = cpt.name;
    } catch (e) {}
    if (nom.value) msg.focus();
    p.querySelector(".x").addEventListener("click", fermer);
    p.querySelector(".env").addEventListener("click", function () { envoyer(p); });
    msg.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") envoyer(p);
    });
  }

  function envoyer(p) {
    var nom = p.querySelector("#nom"), msg = p.querySelector("#msg");
    var b = p.querySelector(".env"), err = p.querySelector(".err");
    var n = nom.value.trim(), m = msg.value.trim();
    err.hidden = true;
    if (!n || !m) { err.textContent = t.manque; err.hidden = false; (n ? msg : nom).focus(); return; }
    try { localStorage.setItem("signaler-nom", n); } catch (e) {}
    b.disabled = true; b.textContent = t.envoi;
    var charge = contexte(); charge.nom = n; charge.message = m;
    fetch("/api/signalement", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify(charge)
    }).then(function (r) {
      if (r.status === 429) throw new Error("rate");
      if (!r.ok) throw new Error("http " + r.status);
      return r.json();
    }).then(function () { remercier(p); })
      .catch(function (e) {
        b.disabled = false; b.textContent = t.envoyer;
        err.textContent = String(e && e.message) === "rate" ? t.rate : t.erreur;
        err.hidden = false;
      });
  }

  function remercier(p) {
    p.innerHTML = '<div class="ok"><div class="rond">' + CHECK + '</div>'
      + '<p></p><p class="m"></p></div>'
      + '<div class="rangee"><button class="sec" type="button"></button>'
      + '<button class="pri" type="button"></button></div>';
    p.querySelector(".ok p").textContent = t.merci;
    p.querySelector(".ok .m").textContent = t.merciSous;
    var sec = p.querySelector(".sec"), pri = p.querySelector(".pri");
    sec.textContent = t.encore; pri.textContent = t.fermer;
    sec.addEventListener("click", function () { formulaire(p); p.querySelector("#msg").focus(); });
    pri.addEventListener("click", fermer);
    pri.focus();
  }

  /* La langue change en cours de visite sur ces pages (bascule FR/EN). Plutot que de
     demander a chaque page de nous prevenir, on regarde <html lang> : c'est le seul
     endroit que les deux surfaces mettent deja a jour. */
  try {
    new MutationObserver(function () { t = T[lang()]; majBouton(); })
      .observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  } catch (e) {}

  bouton.addEventListener("click", ouvrir);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && voile) fermer(); });
  majBouton();

  function poser() {
    if (document.body) { document.body.appendChild(hote); majBouton(); }
    else document.addEventListener("DOMContentLoaded", poser);
  }
  poser();

  /* La page hôte peut rafraîchir le libellé quand elle bascule de langue. */
  window.__signaler = { ouvrir: ouvrir, fermer: fermer, majLangue: function () { t = T[lang()]; majBouton(); } };
})();
