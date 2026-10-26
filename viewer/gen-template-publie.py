# -*- coding: utf-8 -*-
"""Genere le template de PUBLICATION a partir de celui d'evaluation.

Les deux surfaces n'ont pas le meme metier : on EVALUE sur l'une (on classe, on
commente, un parcours guide la premiere fois), on LIT sur l'autre. Melanger les
deux ramenait le tutoriel et la notation dans une page en lecture seule.

Le template de publication n'est pas maintenu a part : il est DERIVE, pour qu'un
correctif du template principal profite aux deux sans divergence possible.

Usage : gen-template-publie.py <source.html> <sortie.html>
"""
import sys, pathlib


# --------------------------------------------------------------------------
# Les filtres. La page publiee montre tout, livraison par livraison, et c'est
# ce qui la rend difficile a lire : pour retrouver ce qui a ete juge excellent,
# ou tout ce qui touche a l'energie, il faut ouvrir les semaines une par une et
# se souvenir. Les filtres retiennent un niveau d'interet, un axe, ou les deux,
# et effacent le reste — sans changer de vue : c'est la meme constellation, on
# y voit moins de choses.
# --------------------------------------------------------------------------
TUBE = r"""
// ---- Filtres : un niveau d'interet, un axe, ou les deux.
// Par defaut ils portent sur la livraison ouverte — c'est la question courante :
// « qu'est-ce que cette semaine a donne sur cet axe ». La vue globale, elle,
// repond a l'autre : « qu'est-ce que cet axe a donne depuis le debut ».
let tierFiltre=null, axeFiltre=null, modeGlobal=false;
function filtreActif(){ return !!(tierFiltre||axeFiltre); }
function retenu(d){
  if(!d) return false;
  if(!modeGlobal && d.run!==active) return false;
  if(tierFiltre && tierCourante(d)!==tierFiltre) return false;
  if(axeFiltre && d.axe!==axeFiltre) return false;
  return true;
}
// Bascule entre « cette livraison » et « tout depuis le debut ». Le reste de la
// page s'y accorde : les comptes des filtres, les chiffres, la fiche ouverte.
// Choisir une date, c'est choisir une semaine : la vue d'ensemble s'efface et on
// arrive directement sur celle-la — un seul mouvement, pas un retour suivi d'un vol.
function versLivraison(ri){
  if(modeGlobal){
    modeGlobal=false;
    document.documentElement.classList.remove('vue-globale');
    const b=document.getElementById('btn-global'); if(b) b.classList.remove('on');
    active=ri; peindreNav(); majProfondeur(); poserVueStandard();
    if(filtreActif()) ouvrirSelection();
    try{ window.dispatchEvent(new CustomEvent('constel-portee')); }catch(e){}
    return;
  }
  allerA(ri);
}
function vueGlobale(v){
  modeGlobal = (v==null) ? !modeGlobal : !!v;
  document.documentElement.classList.toggle('vue-globale', modeGlobal);
  const b=document.getElementById('btn-global');
  if(b) b.classList.toggle('on', modeGlobal);
  majProfondeur();
  if(modeGlobal) vueEnsemble(); else poserVueStandard();
  if(filtreActif()) ouvrirSelection();
  else if(modeGlobal) ouvrirBilan(); else fermerPanneau();
  try{ window.dispatchEvent(new CustomEvent('constel-portee')); }catch(e){}
  return modeGlobal;
}

// ---- La vue d'ensemble : quatre lectures d'un meme jugement.
// « Sur quoi ? » — un niveau propose par l'agent, ou un domaine. « Vu comment ? »
// — l'evolution dans le temps, ou le detail des glissements. Croiser les deux
// donne une grille : en colonnes le decoupage, en lignes la forme. Une seule
// serie par cellule : deux courbes superposees se lisent mal, sept ne se lisent
// plus — d'ou les onglets.
const BIL = {tier:'', axe:''};
const ENTETE_B = {tier:'Par niveau', axe:'Par axe'};
const FORMES_B = [['courbe','La similarité au fil des semaines'],
                  ['matrice','Proposé → décidé']];

// Trois crans d'ecart valent zero : la meme formule qu'a l'evaluation, appliquee
// ici a n'importe quel sous-ensemble de la matrice.
function simMat(m){
  let n=0, s=0;
  Object.keys(m||{}).forEach(k=>{ const p=k.split('>'), c=m[k];
    n+=c; s+=c*Math.abs((+p[1])-(+p[0])); });
  return {n:n, v:n?Math.round((1-(s/n)/3)*100):null};
}
// Isoler un niveau propose, c'est garder une ligne de la matrice.
function ligneDe(m, ai){
  const o={}; Object.keys(m||{}).forEach(k=>{ if(+k.split('>')[0]===ai) o[k]=m[k]; });
  return o;
}
function matRun(r, par, val){
  const P=(D.perf||{})[r]||{}, m=P.matrice||{};
  if(!val) return m;
  return (par==='axe') ? ((P.matAxe||{})[val]||{}) : ligneDe(m, TIERS.indexOf(val));
}
function matCumul(par, val){
  const t={};
  (D.runs||[]).forEach(r=>{ const m=matRun(r,par,val);
    Object.keys(m).forEach(k=>{ t[k]=(t[k]||0)+m[k]; }); });
  return t;
}
function couleurB(par, val){
  if(!val) return '#4ade80';
  return (par==='axe') ? ((typeof AXC!=='undefined' && AXC[val]) || '#7fb0ff')
                       : (TIERCOL[val] || '#7fb0ff');
}
// Un onglet doit tenir sur une ligne : on garde ce qui precede le premier
// separateur, le nom entier restant en infobulle.
function courtB(v){ return String(v).split(' & ')[0].split(' · ')[0].trim(); }

function courbeSimilarite(series, larg, haut, coul){
  const CL=coul||'#4ade80';
  const M={g:26,d:28,h:12,b:18}, W=larg-M.g-M.d, H=haut-M.h-M.b;
  const n=series.length; if(!n) return '';
  const x=i=> M.g + (n===1 ? W/2 : (W*i)/(n-1));
  const y=v=> M.h + H*(1-(v||0)/100);
  let g='<svg class="graphe" viewBox="0 0 '+larg+' '+haut+'" role="img" '
      + 'aria-label="Similarité au fil des livraisons">';
  [0,50,100].forEach(v=>{
    g+='<line x1="'+M.g+'" y1="'+y(v)+'" x2="'+(larg-M.d)+'" y2="'+y(v)+'" '
     + 'stroke="#1e2b45" stroke-width="1"/>'
     + '<text x="'+(M.g-4)+'" y="'+(y(v)+3)+'" text-anchor="end" '
     + 'font-size="8" fill="#5d739a">'+v+'</text>';
  });
  const pts=series.map((p,i)=>({x:x(i), y:y(p.v), p:p})).filter(o=>o.p.v!=null);
  if(pts.length>1){
    g+='<polyline fill="none" stroke="'+CL+'" stroke-width="2" stroke-linejoin="round" '
     + 'points="'+pts.map(o=>o.x.toFixed(1)+','+o.y.toFixed(1)).join(' ')+'"/>';
  }
  pts.forEach((o,i)=>{
    const dernier=(i===pts.length-1);
    g+='<circle cx="'+o.x.toFixed(1)+'" cy="'+o.y.toFixed(1)+'" r="'+(dernier?4.5:3.5)+'" '
     + 'fill="'+(dernier?CL:'#0e1a2f')+'" stroke="'+CL+'" stroke-width="2"/>';
    if(dernier) g+='<text x="'+(o.x-6)+'" y="'+(o.y-9)+'" text-anchor="end" '
     + 'font-size="10" font-weight="700" fill="'+CL+'">'+o.p.v+'%</text>';
  });
  series.forEach((p,i)=>{
    g+='<text x="'+x(i)+'" y="'+(haut-4)+'" text-anchor="middle" '
     + 'font-size="8" fill="#5d739a">'+p.d+'</text>';
  });
  return g+'</svg>';
}

// La matrice reste entiere meme quand un niveau est isole : c'est la grille
// complete qui donne l'echelle, la ligne retenue ressort par contraste.
function matriceB(par, val){
  const m=matCumul(par,val);
  const tot=Object.keys(m).reduce((a,k)=>a+m[k],0);
  if(!tot) return '<div class="videB">Aucun signal apparié ici.</div>';
  const ai0=(par==='tier' && val) ? TIERS.indexOf(val) : -1;
  const mx=Math.max.apply(null, Object.keys(m).map(k=>m[k]));
  let h='<table class="matB"><tr><td class="hd"></td>'
      + TIERS.map(t=>'<td class="hd" style="color:'+(TIERCOL[t]||'#8ea5c8')+'" title="'
        + t+'">'+t.slice(0,3)+'</td>').join('')+'</tr>';
  TIERS.forEach((ta,ai)=>{
    h+='<tr'+((ai0>=0 && ai!==ai0)?' class="pale"':'')+'><td class="hd" style="color:'
     + (TIERCOL[ta]||'#8ea5c8')+'" title="'+ta+'">'+ta.slice(0,3)+'</td>';
    TIERS.forEach((tu,ui)=>{
      const c=m[ai+'>'+ui]||0;
      const base = ai===ui ? '74,222,128' : (ui<ai ? '59,130,246' : '245,158,11');
      const op = c ? (0.16+0.55*Math.min(1,c/Math.max(4,mx))) : 0.04;
      h+='<td title="'+(c?c+' : '+ta+' → '+tu:'')+'" style="background:rgba('+base+','
       + op+');color:'+(c?'#eaf1ff':'#31435f')+'">'+(c||'·')+'</td>';
    });
    h+='</tr>';
  });
  return h+'</table>';
}

function ongletsB(par){
  const cour=BIL[par];
  const vals = (par==='axe') ? (D.axes||[]).slice() : TIERS.slice();
  let h='<div class="ongl"><button data-p="'+par+'" data-v=""'
      + (cour?'':' class="on"')+' style="--c:#4ade80">Global</button>';
  vals.forEach(v=>{
    h+='<button data-p="'+par+'" data-v="'+String(v).replace(/"/g,'&quot;')+'"'
     + (cour===v?' class="on"':'')+' style="--c:'+couleurB(par,v)+'" title="'+v+'">'
     + courtB(v)+'</button>';
  });
  return h+'</div>';
}
function corpsB(par, forme){
  const val=BIL[par], s=simMat(matCumul(par,val));
  const pied='<div class="noteB">'+s.n+' signaux appariés'
           + (s.v!=null?' · '+s.v+' % de similarité':'')+'</div>';
  if(forme==='courbe'){
    const serie=(D.runs||[]).map(r=>{ const u=simMat(matRun(r,par,val));
      return {d:fmtd(r), v:u.v}; });
    return courbeSimilarite(serie, 300, 134, couleurB(par,val)) + pied;
  }
  return matriceB(par,val) + pied;
}
function colonneB(par){
  return '<div class="colB" data-col="'+par+'"><h3 class="hB">'+ENTETE_B[par]+'</h3>'
   + ongletsB(par)
   + FORMES_B.map(f=>'<div class="celG"><h4>'+f[1]+'</h4>'
       + '<div class="corpsB" data-f="'+f[0]+'">'+corpsB(par,f[0])+'</div></div>').join('')
   + '</div>';
}
function majColonneB(par){
  const el=pbody.querySelector('[data-col="'+par+'"]'); if(!el) return;
  el.querySelectorAll('.ongl button').forEach(b=>
    b.classList.toggle('on', (b.dataset.v||'')===BIL[par]));
  el.querySelectorAll('.corpsB').forEach(c=>{ c.innerHTML=corpsB(par, c.dataset.f); });
}
function ouvrirBilan(){
  if(!D||!D.runs) return;
  viderPied();
  pushNav('axe'); curView={type:'bilan'};
  hiliAxe=null; hiliId=null; hiliTier=null;
  autoLargeur(0.46);
  const P=D.perf||{};
  let ex=0; Object.keys(P).forEach(k=>{ if(P[k].examines) ex+=P[k].examines; });
  pbody.innerHTML='<h2 style="border-left:4px solid #4ade80;padding-left:11px">'
   + 'Vue d’ensemble</h2>'
   + '<div class="meta">'+D.runs.length+' livraisons · '+D.nodes.length
   + ' signaux retenus'+(ex?' sur '+ex+' examinés':'')+'</div>'
   + '<div class="grilleB">'+colonneB('tier')+colonneB('axe')+'</div>';
  if(!pbody._bilanCable){
    pbody._bilanCable=true;
    pbody.addEventListener('click', e=>{
      const b=e.target.closest && e.target.closest('.ongl button');
      if(!b || !b.dataset.p) return;
      BIL[b.dataset.p]=b.dataset.v||'';
      majColonneB(b.dataset.p);
    });
  }
  panel.classList.add('on');
  panel.classList.toggle('gauche', false);
  recadrer();
}
// Voir toutes les livraisons demande de reculer ET de tourner : de la vue de
// lecture, les plus anciennes se cachent derriere la courante. On ouvre l'angle
// sans aller jusqu'au profil — de cote, les disques se reduiraient a des traits.
function vueEnsemble(){
  if(!D||!plans.length) return;
  const AZ=44*Math.PI/180, EL=17*Math.PI/180;
  const dir=new THREE.Vector3(Math.sin(AZ)*Math.cos(EL),Math.sin(EL),Math.cos(AZ)*Math.cos(EL));
  const z0=zPlane(0), z1=zPlane(D.runs.length-1);
  cadX=0; cadY=0;
  ctl.target.set(0,0,(z0+z1)/2);
  cam.position.copy(ctl.target.clone().add(dir.multiplyScalar(distanceFit()*1.5)));
  ctl.update(); recadrer(); ajusterCadrage();
}
function majBoutonsFiltre(){
  document.querySelectorAll('#tubes button').forEach(b=>{
    const on = (b.dataset.k==='tier' && b.dataset.t===tierFiltre)
            || (b.dataset.k==='axe'  && b.dataset.t===axeFiltre);
    b.classList.toggle('on', on);
  });
  const bar=document.getElementById('tubes');
  if(bar) bar.classList.toggle('actif', filtreActif());
}
function filtrer(genre, valeur){
  if(genre==='tier') tierFiltre=(tierFiltre===valeur)?null:valeur;
  else               axeFiltre =(axeFiltre ===valeur)?null:valeur;
  majBoutonsFiltre();
  majProfondeur();
  if(filtreActif()) ouvrirSelection(); else fermerPanneau();
  return {tier:tierFiltre, axe:axeFiltre};
}
function viderFiltres(){
  if(!filtreActif()) return false;
  tierFiltre=null; axeFiltre=null; majBoutonsFiltre(); majProfondeur();
  fermerPanneau(); return true;
}
// La fiche d'une selection : la meme lecture que celle d'une livraison, mais qui
// traverse toutes les semaines. C'est la seule facon de voir d'un bloc ce qu'un
// axe a donne depuis le debut, ou tout ce qui a ete juge excellent.
function ouvrirSelection(){
  if(!filtreActif()) return;
  viderPied();
  pushNav('axe'); curView={type:'selection'};
  hiliAxe=null; hiliId=null; hiliTier=null;
  autoLargeur(0.46);
  const lot=(D.nodes||[]).filter(n=>retenu(n));
  const titre=[tierFiltre,axeFiltre].filter(Boolean).join(' · ');
  const col=(axeFiltre&&AXC[axeFiltre]) || (tierFiltre&&TIERCOL[tierFiltre]) || '#7fb0ff';
  // par livraison, de la plus recente a la plus ancienne
  const parRun={};
  lot.forEach(n=>{ (parRun[n.run]=parRun[n.run]||[]).push(n); });
  const runs=Object.keys(parRun).map(Number).sort((a,b)=>b-a);
  let h='<h2 style="border-left:4px solid '+col+';padding-left:11px">'+esc(titre)+'</h2>'+
    '<div class="meta">'+lot.length+' signal'+(lot.length>1?'s':'')+' · '+
    (modeGlobal ? (runs.length+' livraison'+(runs.length>1?'s':''))
                : ('livraison du '+fmtd(D.runs[active])))+'</div>';
  runs.forEach(ri=>{
    const g=parRun[ri];
    if(modeGlobal) h+='<div class="sect">'+fmtd(D.runs[ri])+' — '+g.length+'</div>';
    g.forEach(n=>{
      const c=AXC[n.axe]||'#64748b', t=tierCourante(n);
      h+='<div class="ent selrow" data-nid="'+esc(n.id)+'" style="border-left-color:'+c+'">'+
         '<div class="c">'+esc(n.headline||n.titre||n.id)+'</div>'+
         '<div class="d" style="margin-top:4px"><span style="color:'+(TIERCOL[t]||'#8ea5c8')+
         ';font-weight:700">'+esc(t)+'</span> · '+esc(n.axe||'')+'</div></div>';
    });
  });
  pbody.innerHTML=h;
  pbody.querySelectorAll('.selrow').forEach(el=>{
    el.onmouseenter=()=>{ hiliId=el.dataset.nid; };
    el.onmouseleave=()=>{ hiliId=null; };
    el.onclick=()=>{ const n=D.nodes.filter(x=>x.id===el.dataset.nid)[0]; if(n)ouvrir(n); };
  });
  panel.classList.add('on');
  panel.classList.toggle('gauche', false);
  recadrer();
}
"""

# Le style des pieces de la vue d'ensemble, injecte dans la feuille du template.
STYLE_ENSEMBLE = """  .ent.selrow{cursor:pointer;border-radius:0 8px 8px 0;transition:background .12s}
  .ent.selrow:hover{background:rgba(127,176,255,.10)}
  /* la vue d'ensemble : une grille de quatre cellules a onglets */
  .grilleB{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-top:11px;
    align-items:start}
  /* MOBILE-2026 : deux colonnes dans 390px = deux graphes illisibles cote a cote. */
  @media (max-width:700px), (orientation:landscape) and (max-height:500px){
    .grilleB{grid-template-columns:1fr}
    #btn-global{min-height:44px;padding:11px 16px}
  }
  .colB{display:flex;flex-direction:column;gap:8px;min-width:0}
  .hB{margin:0;font:600 12.5px/1.3 var(--sans);color:#cfe0ff;letter-spacing:.01em}
  .celG{border:1px solid #22314e;border-radius:11px;background:#0c1526;
    padding:9px 10px 8px;min-width:0}
  .celG h4{margin:0 0 7px;font:600 10.5px/1.3 var(--sans);letter-spacing:.05em;
    text-transform:uppercase;color:#8ea5c8}
  .ongl{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:8px}
  .ongl button{padding:2px 7px;border-radius:6px;border:1px solid #2b3a55;
    background:transparent;color:#8ea5c8;font:600 10px var(--sans);cursor:pointer;
    white-space:nowrap}
  .ongl button:hover{border-color:var(--c);color:#cfe0ff}
  .ongl button.on{background:var(--c);border-color:var(--c);color:#0b1220}
  .graphe{width:100%;height:auto;display:block}
  .matB{border-collapse:separate;border-spacing:3px;width:100%;table-layout:fixed}
  .matB td{text-align:center;border-radius:6px;height:25px;
    font:700 11px var(--sans);font-variant-numeric:tabular-nums}
  .matB td.hd{background:none;font:600 9px var(--sans);padding:0 1px;
    letter-spacing:.02em}
  /* isoler un niveau n'enleve pas la grille : elle donne l'echelle */
  .matB tr.pale td{opacity:.22}
  .noteB{margin-top:6px;font:11px/1.4 var(--sans);color:#6f86ad}
  .videB{padding:16px 0;text-align:center;font:11.5px var(--sans);color:#6f86ad}"""

BARRE = """
<style>
/* Les filtres : un niveau d'interet, un axe, ou les deux. */
/* Les deux encarts vivent dans un meme bandeau, cote a cote : empiles en
   `fixed` ils se chevauchaient des que la fenetre raccourcissait. */
#hud{position:fixed;left:18px;top:74px;bottom:20px;z-index:31;display:flex;
  flex-direction:column;align-items:flex-start;justify-content:space-between;
  gap:10px;pointer-events:none}
#hud>*{pointer-events:auto}
/* les encarts peuvent defiler, mais la barre du systeme casse le fond sombre */
#hud>*{scrollbar-width:thin;scrollbar-color:#2b3a55 transparent}
#hud>*::-webkit-scrollbar{width:7px}
#hud>*::-webkit-scrollbar-track{background:transparent}
#hud>*::-webkit-scrollbar-thumb{background:#2b3a55;border-radius:4px}
#tubes{display:flex;flex-direction:column;gap:2px;width:214px;flex:0 1 auto;min-height:0;
  margin-top:auto;   /* les filtres restent en bas, meme quand les chiffres se replient */

  padding:9px 10px;border-radius:12px;border:1px solid #23324e;background:rgba(10,17,32,.86);
  backdrop-filter:blur(7px);font:12px system-ui,sans-serif;overflow:auto}
#tubes h5{margin:5px 0 2px;font:700 10px/1.3 system-ui;letter-spacing:.09em;
  text-transform:uppercase;color:#8ea5c8}
#tubes h5:first-child{margin-top:0}
#tubes button{display:flex;align-items:center;gap:7px;padding:3px 8px;border-radius:8px;cursor:pointer;
  border:1px solid transparent;background:transparent;color:#cfe0ff;font:600 12px system-ui,sans-serif;
  text-align:left;width:100%}
#tubes button i{width:9px;height:9px;border-radius:50%;background:var(--c);flex:none}
#tubes button span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#tubes button small{color:#6f86ad;font-weight:500}
#tubes button:hover{background:rgba(127,176,255,.10)}
#tubes button.on{border-color:var(--c);background:rgba(127,176,255,.12);color:#fff}
#tubes .quitter{display:none;margin-top:6px;color:#8ea5c8;font:500 11px system-ui}
#tubes.actif .quitter{display:block}
/* MOBILE-2026 : sous 980px, le bandeau (#statsrun = bilan de la livraison, similarite
   agent/humain ; #tubes = les 11 filtres Niveau et Axe) etait purement SUPPRIME — sur
   telephone comme sur une fenetre d'ordinateur de 960px ou un ecran partage. On ne masque
   plus, on REPLIE : meme contenu, en tiroir, ouvert par la cle « Bilan & filtres ». */
@media (max-width:980px){
  #hud{left:0;right:0;top:auto;bottom:0;z-index:33;display:block;
    max-height:76dvh;overflow:auto;overscroll-behavior:contain;
    padding:14px 12px calc(16px + env(safe-area-inset-bottom));
    background:rgba(8,14,26,.98);border-top:1px solid #23324e;
    border-top-left-radius:16px;border-top-right-radius:16px;
    box-shadow:0 -18px 50px rgba(4,9,18,.65);
    transform:translateY(101%);transition:transform .22s;pointer-events:auto}
  #hud.ouvert{transform:none}
  #hud #statsrun,#hud #tubes{width:auto;max-width:none;margin-top:0;overflow:visible}
  #hud #statsrun{margin-bottom:10px}
  #hud #tubes button{min-height:40px;font-size:13px}
  #hud #tubes h5,#hud #statsrun h5{font-size:11px}
  /* dans le tiroir, les chiffres restent lisibles meme si une fiche est ouverte */
  html:has(aside#panel.on) #hud.ouvert #statsrun{display:block}
  #hud-cle{position:fixed;z-index:32;left:calc(12px + env(safe-area-inset-left));
    bottom:calc(18px + var(--ph-bandeau,0px) + 108px);
    min-height:44px;padding:9px 14px;border-radius:12px;border:1px solid #2b3b59;
    background:rgba(19,31,54,.94);color:#eaf0fb;
    font:600 12.5px system-ui,sans-serif;cursor:pointer;
    display:flex;align-items:center;gap:7px;white-space:nowrap}
  #hud-cle .fx{font-size:13px;color:#9ec5ff}
  #hud-fond{position:fixed;inset:0;z-index:32;background:rgba(3,7,15,.55);display:none}
  #hud-fond.on{display:block}
}
@media (min-width:981px){#hud-cle,#hud-fond{display:none!important}}
/* Le bouton de portee, au bout du rail des dates. */
#btn-global{position:absolute;left:50%;bottom:calc(100% + 9px);
  transform:translateX(-50%);padding:5px 12px;border-radius:9px;cursor:pointer;
  min-height:32px;
  border:1px solid #2b3b59;background:transparent;color:#9ec5ff;
  font:600 12px system-ui,sans-serif;white-space:nowrap}
#btn-global:hover{border-color:#9ec5ff}
#btn-global.on{background:#9ec5ff;border-color:#9ec5ff;color:#0b1220}
/* en vue globale, aucune date n'est « celle qu'on regarde » */
html.vue-globale #rail .stop.on{background:transparent;color:#8ea5c8;border-color:transparent}
/* Une fiche ouverte prend la moitie de l'ecran : les chiffres de la livraison
   se replient alors, sinon il ne reste plus rien pour la constellation. En vue
   d'ensemble ils disparaissent tout court — la fiche de droite les reprend, en
   plus large et avec leurs courbes. */
html:has(aside#panel.on) #statsrun{display:none}
html.vue-globale #statsrun{display:none}

/* Les chiffres de la livraison ouverte, sous les filtres : combien la semaine a
   rapporte, et comment elle se repartit — la chasse se juge sur ce qui a tenu,
   pas sur le volume ramene. */
#statsrun{width:296px;flex:0 1 auto;min-height:0;
  padding:11px 13px;border-radius:12px;border:1px solid #23324e;background:rgba(10,17,32,.86);
  backdrop-filter:blur(7px);font:12px system-ui,sans-serif;color:#cfe0ff;overflow:auto}
#statsrun h5{margin:0 0 2px;font:700 10px/1.3 system-ui;letter-spacing:.09em;
  text-transform:uppercase;color:#8ea5c8}
#statsrun .date{font:700 14px/1.2 system-ui;margin-bottom:1px}
#statsrun .tot{color:#8ea5c8;font-size:11px;margin-bottom:8px}
#statsrun .jauge{display:flex;height:7px;border-radius:4px;overflow:hidden;
  background:rgba(255,255,255,.05);margin-bottom:8px}
#statsrun .jauge i{display:block;height:100%}
#statsrun .l{display:flex;align-items:center;gap:7px;padding:2px 0;font-size:12px}
#statsrun .l i{width:8px;height:8px;border-radius:50%;background:var(--c);flex:none}
#statsrun .l span{flex:1;color:#b9cae6}
#statsrun .l b{font-weight:700}
#statsrun .l em{font-style:normal;color:#6f86ad;font-size:11px;min-width:34px;text-align:right}
#statsrun .cmp{margin-top:8px;padding-top:7px;border-top:1px solid #1d2a44;
  color:#8ea5c8;font-size:11px;line-height:1.45}
#statsrun .cmp b{color:#cfe0ff}
/* les trois tuiles de la vue d'ensemble, a l'echelle de l'encart */
#statsrun .tuiles{display:flex;gap:5px;margin:9px 0 4px}
#statsrun .t{flex:1;background:#0c1526;border:1px solid #22314e;border-radius:9px;
  padding:7px 4px;text-align:center}
#statsrun .t b{display:block;font:800 17px/1 system-ui;color:#eaf1ff}
#statsrun .t span{display:block;margin-top:4px;font:9.5px/1.2 system-ui;color:#8ea5c8;
  text-transform:uppercase;letter-spacing:.04em}
#statsrun h5.m{margin-top:9px}
#statsrun .mat{border-collapse:separate;border-spacing:2px;margin:2px auto 0}
#statsrun .mat td{width:26px;height:21px;text-align:center;border-radius:5px;
  font:700 10.5px system-ui}
#statsrun .mat td.hd{width:auto;background:none;font:700 9px system-ui;
  letter-spacing:.03em;padding:0 2px}

</style>
<div id="hud"><div id="statsrun" hidden></div><div id="tubes"></div></div>
<script>
(function(){
  // Meme echelle que la constellation — mesuree, pas choisie a l'oeil :
  // separation 16,1 en vision normale, 11,8 en protanopie, contraste > 3:1.
  const TCOUL={'Excellent':'#4ade80','Cool':'#06b6d4','Int\\u00e9ressant':'#3b82f6',
               'Neutre':'#f472b6','Bof':'#f59e0b','Inutile':'#64748b'};
  const bar=document.getElementById('tubes');
  (function monter(){
    const C=window.__constel;
    const D=C&&C.donnees&&C.donnees();
    if(!D||!D.nodes) return setTimeout(monter,400);
    const coulAxe = C.couleurAxe || (()=>'#7fb0ff');
    const ligne=(genre,nom,n,coul)=>{
      const b=document.createElement('button');
      b.dataset.k=genre; b.dataset.t=nom; b.style.setProperty('--c',coul);
      b.innerHTML='<i></i><span>'+nom+'</span><small>'+n+'</small>';
      b.onclick=()=>C.filtrer(genre,nom);
      return b;
    };
    const actif=()=>{ const b=document.querySelector('#rail .stop.on');
      return b ? +b.dataset.ri : null; };
    const global=()=>document.documentElement.classList.contains('vue-globale');
    // Les comptes suivent la portee : ce que la semaine ouverte a donne, ou ce
    // que toute la bibliotheque a donne.
    const peindreFiltres=()=>{
      const ri=actif();
      const lot = global()||ri==null ? D.nodes : D.nodes.filter(n=>n.run===ri);
      const parTier={}, parAxe={};
      lot.forEach(n=>{ const t=n.tier||'Bof'; parTier[t]=(parTier[t]||0)+1;
                       if(n.axe) parAxe[n.axe]=(parAxe[n.axe]||0)+1; });
      bar.innerHTML='';
      const ent=document.createElement('h5');
      ent.textContent = global() ? 'Toutes les livraisons' : 'Cette livraison';
      ent.style.color = global() ? '#9ec5ff' : '';
      bar.appendChild(ent);
      const tiers=Object.keys(TCOUL).filter(t=>parTier[t]);
      if(tiers.length){
        const h=document.createElement('h5'); h.textContent='Niveau'; bar.appendChild(h);
        tiers.forEach(t=>bar.appendChild(ligne('tier',t,parTier[t],TCOUL[t])));
      }
      const axes=Object.keys(parAxe).sort((a,b)=>parAxe[b]-parAxe[a]);
      if(axes.length){
        const h=document.createElement('h5'); h.textContent='Axe'; bar.appendChild(h);
        axes.forEach(a=>bar.appendChild(ligne('axe',a,parAxe[a],coulAxe(a))));
      }
      const q=document.createElement('div');
      q.className='quitter'; q.textContent='\\u00c9chap \\u2014 tout revoir';
      bar.appendChild(q);
      if(C.rappelerFiltres) C.rappelerFiltres();
    };
    peindreFiltres();

    // Le bouton de portee, au-dessus du rail : les dates montrent une
    // semaine, celui-ci les montre toutes. Au bout de la file il se serait
    // lu comme une date de plus.
    const nav=document.getElementById('nav');
    if(nav && !document.getElementById('btn-global')){
      const g=document.createElement('button');
      g.id='btn-global'; g.type='button';
      g.textContent='Vue globale';
      g.title='Voir toutes les livraisons ensemble';
      g.onclick=()=>{ C.vueGlobale(); peindreFiltres(); };
      nav.appendChild(g);
    }

    // MOBILE-2026 : sous 980px le bandeau de gauche est un TIROIR (cf. CSS). Sa cle vit en
    // bas a gauche, au-dessus du rail des dates. Sans elle, le bilan de la livraison et les
    // filtres seraient toujours invisibles — c'etait la moitie du produit qui disparaissait.
    (function tiroirBilan(){
      if(document.getElementById('hud-cle')) return;
      const hud=document.getElementById('hud'); if(!hud) return;
      const fond=document.createElement('div'); fond.id='hud-fond';
      const cle=document.createElement('button'); cle.type='button'; cle.id='hud-cle';
      cle.innerHTML='<span class="fx">\u25a4</span><span>Bilan &amp; filtres</span>';
      cle.setAttribute('aria-expanded','false');
      const basculer=(ouvrir)=>{
        const o = (ouvrir==null) ? !hud.classList.contains('ouvert') : !!ouvrir;
        hud.classList.toggle('ouvert',o); fond.classList.toggle('on',o);
        cle.setAttribute('aria-expanded', o?'true':'false');
      };
      cle.addEventListener('click',()=>basculer());
      fond.addEventListener('click',()=>basculer(false));
      document.addEventListener('keydown',e=>{ if(e.key==='Escape') basculer(false); });
      document.body.appendChild(fond); document.body.appendChild(cle);
    })();

    // ---- Les chiffres de la livraison ouverte.
    // Une livraison ne se juge pas au volume ramene mais a ce qui a tenu : on
    // montre donc la repartition par niveau, et la part retenue rapportee a la
    // moyenne des autres semaines — un nombre seul ne dit pas si c'est beaucoup.
    const st=document.getElementById('statsrun');
    const ORDRE=Object.keys(TCOUL);
    const parRun=(ri)=>{
      const n=D.nodes.filter(x=>x.run===ri), c={}, ax={};
      n.forEach(x=>{ const t=x.tier||'Bof'; c[t]=(c[t]||0)+1;
        const a=x.axe||'Transverse';
        ax[a]=ax[a]||{n:0,haut:0};
        ax[a].n++; if(t==='Excellent'||t==='Cool') ax[a].haut++; });
      // L'axe le plus apprecie est celui dont la plus grande part a ete jugee
      // excellente ou cool — pas le plus fourni : chercher beaucoup quelque part
      // n'est pas la meme chose qu'y trouver du bon. Deux fiches au moins, sinon
      // un unique finding bien note ferait gagner un axe a lui seul.
      let top=null;
      Object.keys(ax).forEach(a=>{ const o=ax[a]; if(o.n<2||!o.haut) return;
        const p=o.haut/o.n;
        if(!top || p>top.p || (p===top.p && o.n>top.n)) top={axe:a,p:p,n:o.n,haut:o.haut}; });
      return {n:n.length, c:c, garde:(c['Excellent']||0)+(c['Cool']||0), top:top,
              perf:(D.perf||{})[D.runs[ri]]||null};
    };
    const stats=D.runs.map((r,i)=>parRun(i));
    // Le cumul : les memes mesures, sur toute la bibliotheque. Les taux sont
    // ponderes par le nombre de fiches comparees, pas moyennes entre semaines —
    // sinon une livraison de six fiches pese autant qu'une de soixante-douze.
    const cumul=(()=>{
      const c={}, ax={};
      D.nodes.forEach(x=>{ const t=x.tier||'Bof'; c[t]=(c[t]||0)+1;
        const a=x.axe||'Transverse'; ax[a]=ax[a]||{n:0,haut:0};
        ax[a].n++; if(t==='Excellent'||t==='Cool') ax[a].haut++; });
      let top=null;
      Object.keys(ax).forEach(a=>{ const o=ax[a]; if(o.n<2||!o.haut) return;
        const p=o.haut/o.n;
        if(!top||p>top.p||(p===top.p&&o.n>top.n)) top={axe:a,p:p,n:o.n,haut:o.haut}; });
      let ex=0, ap=0, ret=0, som=0, mat={};
      Object.keys(D.perf||{}).forEach(k=>{ const P=D.perf[k];
        ret+=P.retenus||0;
        if(P.examines){ ex+=P.examines; ap+=P.apparies||0; som+=P.exact||0;
          Object.keys(P.matrice||{}).forEach(kk=>{ mat[kk]=(mat[kk]||0)+P.matrice[kk]; }); }
      });
      let sim=null;
      if(ap){ let ecarts=0;
        Object.keys(mat).forEach(kk=>{ const p=kk.split('>');
          ecarts+=Math.abs(+p[1]-+p[0])*mat[kk]; });
        sim=Math.round((1-(ecarts/ap)/3)*100); }
      return {n:D.nodes.length, c:c, garde:(c['Excellent']||0)+(c['Cool']||0), top:top,
              perf: ex ? {retenus:ret, examines:ex, apparies:ap, exact:som,
                          similarite:sim, matrice:mat} : null};
    })();
    const fmtDate=(s)=>{ const m=/^(\\d{4})-(\\d{2})-(\\d{2})/.exec(s||'');
      return m ? m[3]+'/'+m[2] : (s||''); };
    const peindre=(ri)=>{
      const tout=document.documentElement.classList.contains('vue-globale');
      if(!tout && (ri==null||!stats[ri])){ st.hidden=true; return; }
      const s = tout ? cumul : stats[ri];
      let h = tout
          ? ('<h5>Toutes les livraisons</h5>'
             + '<div class="date">'+D.runs.length+' livraisons</div>')
          : ('<h5>Cette livraison</h5>'
             + '<div class="date">'+fmtDate(D.runs[ri])+'</div>');
      // la tuile « retenus » porte deja ce compte : pas deux fois la meme chose
      h += (s.perf&&s.perf.examines ? ''
            : '<div class="tot">'+s.n+' '
              + (s.n>1?'signaux retenus':'signal retenu')+'</div>');
      h+='<div class="jauge">';
      ORDRE.forEach(t=>{ const v=s.c[t]||0; if(!v) return;
        h+='<i style="width:'+(100*v/s.n).toFixed(1)+'%;background:'+TCOUL[t]+'"></i>'; });
      h+='</div>';
      ORDRE.forEach(t=>{ const v=s.c[t]||0; if(!v) return;
        h+='<div class="l" style="--c:'+TCOUL[t]+'"><i></i><span>'+t+'</span>'
         + '<b>'+v+'</b><em>'+Math.round(100*v/s.n)+'%</em></div>'; });
      // Les memes reperes que la vue d'ensemble de l'evaluation, a l'echelle de
      // l'encart : trois tuiles, puis la matrice « ce que l'agent proposait ->
      // ce qui a ete decide ». Diagonale = d'accord ; au-dessus = tu as promu ;
      // en dessous = tu as retrograde.
      const P=s.perf;
      if(P && P.similarite!=null){
        h+='<div class="tuiles">'
         + '<div class="t"><b style="color:'+TCOUL['Excellent']+'">'+P.similarite+'%</b>'
         + '<span>similarit\\u00e9</span></div>'
         + '<div class="t"><b style="color:'+TCOUL['Intéressant']+'">'+P.retenus+'/'+P.examines+'</b>'
         + '<span>retenus</span></div>'
         + '<div class="t"><b>'+P.exact+'</b><span>class\\u00e9s juste</span></div></div>';
        if(P.matrice){
          h+='<h5 class="m">Agent \\u2192 toi</h5><table class="mat">';
          h+='<tr><td></td>'+ORDRE.map(t=>'<td class="hd" style="color:'+TCOUL[t]
            + '">'+t.slice(0,2)+'</td>').join('')+'</tr>';
          ORDRE.forEach((ta,ai)=>{
            h+='<tr><td class="hd" style="color:'+TCOUL[ta]+';text-align:right">'+ta.slice(0,2)+'</td>';
            ORDRE.forEach((tu,ui)=>{
              const c=P.matrice[ai+'>'+ui]||0;
              const base = ai===ui ? '74,222,128' : (ui<ai ? '59,130,246' : '245,158,11');
              const op = c ? (0.16+0.55*Math.min(1,c/6)) : 0.04;
              h+='<td title="'+(c?c+' : '+ta+' \\u2192 '+tu:'')+'" style="background:rgba('
               + base+','+op+');color:'+(c?'#eaf1ff':'#31435f')+'">'+(c||'\\u00b7')+'</td>';
            });
            h+='</tr>';
          });
          h+='</table>';
        }
      }
      h+='<div class="cmp">';
      if(s.top){
        h+='Axe le plus appr\\u00e9ci\\u00e9 : <b>'+s.top.axe+'</b> \\u2014 '
         + s.top.haut+' de ses '+s.top.n+' signaux en haut de tier.';
      } else {
        h+='<b>'+Math.round(100*s.garde/s.n)+' %</b> d\\u2019excellent ou cool.';
      }
      h+='</div>';
      st.innerHTML=h; st.hidden=false;
    };
    peindre(actif());
    const rail=document.getElementById('rail');
    if(rail) new MutationObserver(()=>{ peindre(actif()); peindreFiltres(); })
      .observe(rail,{subtree:true,attributes:true,attributeFilter:['class']});
    // la bascule de portee repeint tout
    window.addEventListener('constel-portee',()=>{ peindre(actif()); peindreFiltres(); });
  })();
})();
</script>
"""

AJUSTEMENT = r"""
// Ce qui se lit ne s'arrete pas au disque : les etiquettes sont du DOM pose
// au-dessus du canvas, leur taille ne suit pas la distance. On mesure la boite
// qu'elles occupent vraiment et on recule jusqu'a ce qu'elle tienne entre le
// bandeau et le rail des dates, puis on la recentre dans cette bande.
let cadX=0, cadY=0;          // decalage de cadrage, en pixels ecran
function zoneUtile(){
  const hd=document.querySelector('header');
  const nv=document.getElementById('nav');
  const hu=document.getElementById('hud');
  const hb=hd?hd.getBoundingClientRect().bottom:0;
  const nt=nv&&nv.offsetParent?nv.getBoundingClientRect().top:innerHeight;
  const M=16;
  // le bandeau de gauche occupe la place : la constellation commence apres lui
  // `offsetParent` est nul pour un element en position fixed : on juge sur ce
  // qu'il occupe vraiment a l'ecran.
  let x1=M;
  if(hu && getComputedStyle(hu).display!=='none'){
    const r=hu.getBoundingClientRect();
    if(r.width>10) x1=Math.max(x1, r.right+M);
  }
  return {x1:x1, x2:innerWidth-M, y1:hb+M, y2:nt-M};
}
function boiteLisible(){
  // Ce qui doit tenir : les reperes de lecture — etiquettes d axe et coeur de la
  // livraison. Les titres de findings restent masques la plupart du temps, et un
  // point passe derriere la camera se projette a des milliers de pixels : les
  // compter faisait fuir la mesure et reculer la vue sans fin.
  const els=[...document.querySelectorAll('#lab .lb.axe:not(.vide), #lab .lb.core:not(.vide)')]
    .filter(e=>e.offsetParent&&e.textContent.trim()&&e.style.opacity!=='0');
  let x1=1e9,y1=1e9,x2=-1e9,y2=-1e9;
  const borne=4*Math.max(innerWidth,innerHeight);
  els.forEach(e=>{ const r=e.getBoundingClientRect();
    if(r.width<1 || Math.abs(r.left)>borne || Math.abs(r.top)>borne) return;
    x1=Math.min(x1,r.left); y1=Math.min(y1,r.top);
    x2=Math.max(x2,r.right); y2=Math.max(y2,r.bottom); });
  return x1>x2 ? null : {x1:x1,y1:y1,x2:x2,y2:y2};
}
function ajusterCadrage(){
  const z=zoneUtile(), zw=z.x2-z.x1, zh=z.y2-z.y1;
  if(zw<80||zh<80) return;
  let bouge=false;
  for(let k=0;k<2;k++){
    const b=boiteLisible(); if(!b) return;
    const f=Math.max((b.x2-b.x1)/zw, (b.y2-b.y1)/zh);
    const dx=((z.x1+z.x2)/2)-((b.x1+b.x2)/2), dy=((z.y1+z.y2)/2)-((b.y1+b.y2)/2);
    if(f<=1.005 && Math.abs(dx)<7 && Math.abs(dy)<7) break;
    // Reculer retrecit le disque, pas les etiquettes : leur taille en pixels ne
    // depend pas de la distance. Sans borne, la boite ne diminue jamais assez et
    // la boucle s eloigne jusqu a rendre la constellation minuscule.
    if(f>1.005){
      const o=cam.position.clone().sub(ctl.target);
      const plafond=distanceFit()*1.30;
      const vise=Math.min(o.length()*Math.min(1.18,f), plafond);
      if(vise>o.length()+1){ o.setLength(vise); cam.position.copy(ctl.target.clone().add(o)); }
    }
    cadX-=dx; cadY-=dy; bouge=true;
    recadrer();
    // reprojeter avant de remesurer, sinon on mesure la vue precedente
    try{ rnd.render(scene,cam); lab.render(scene,cam); }catch(e){}
  }
  // les etiquettes ne se re-espacent qu'une fois, quand la vue a bouge
  if(bouge){ try{ espacerEtiquettesAxes(); }catch(e){} }
}
"""


def generer(src, dst):
    s = pathlib.Path(src).read_text(encoding='utf-8')

    # 1. drapeau pose en dur : c'est une page de lecture
    marqueur = '<script type="module">'
    i = s.find(marqueur)
    assert i > 0, 'point d insertion introuvable'
    s = (s[:i + len(marqueur)]
         + "\n/* Page de LECTURE (publication) : ni parcours guide, ni notation. */\n"
           "window.__PUBLICATION = true;\n"
         + s[i + len(marqueur):])

    # 2. ni parcours guide, ni proposition de constellation d'exemple
    s = s.replace("      if(su && window.__constel.watch() === 'tutoriel') buildOverlay();\n"
                  "      else ouvrirDemo();",
                  "      if(window.__PUBLICATION) return;   // page de lecture : aucun parcours\n"
                  "      if(su && window.__constel.watch() === 'tutoriel') buildOverlay();\n"
                  "      else ouvrirDemo();")
    s = s.replace("  function buildOverlay(){",
                  "  function buildOverlay(){\n"
                  "    if(window.__PUBLICATION) return;   // page de lecture", 1)

    # 3. rien de ce qui sert a evaluer
    s = s.replace("function tierPicker(d){",
                  "function tierPicker(d){\n"
                  "  if(window.__PUBLICATION) return document.createComment('lecture seule');", 1)
    s = s.replace("function piedNotation(d){",
                  "function piedNotation(d){\n"
                  "  if(window.__PUBLICATION) return document.createComment('lecture seule');", 1)
    # les avis nourrissent la run suivante : sans destinataire ici, on ne les propose pas
    s = s.replace("const AVIS=[", "const AVIS=window.__PUBLICATION?[]:[", 1)

    # 4. navigation libre : on tourne et on zoome autour de la constellation
    s = s.replace("  ctl.enableRotate=false; ctl.enablePan=false;",
                  "  ctl.enableRotate=true; ctl.enablePan=false;")
    s = s.replace("  ctl.enableZoom=false;", "  ctl.enableZoom=true;")
    s = s.replace("  ctl.mouseButtons={LEFT:null,MIDDLE:null,RIGHT:null};\n"
                  "  ctl.touches={ONE:null,TWO:null};",
                  "  ctl.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.DOLLY,RIGHT:null};\n"
                  "  ctl.touches={ONE:THREE.TOUCH.ROTATE,TWO:THREE.TOUCH.DOLLY_PAN};")
    # L'orbite reste AUTOUR de la vue de reference. Une constellation de plusieurs
    # livraisons est un empilement de plans : passe un certain angle on la regarde
    # par la tranche, tout s'etale hors cadre et plus rien n'est lisible. On tourne
    # donc dans un cone — assez pour sentir la profondeur, pas assez pour se perdre.
    s = s.replace("ctl.minDistance=140; ctl.maxDistance=16000;",
                  "ctl.minDistance=140; ctl.maxDistance=16000;\n"
                  "  ctl.minAzimuthAngle=(26-42)*Math.PI/180; "
                  "ctl.maxAzimuthAngle=(26+42)*Math.PI/180;\n"
                  "  ctl.minPolarAngle=62*Math.PI/180; ctl.maxPolarAngle=106*Math.PI/180;")

    # 4 bis. LA VUE DU LECTEUR PRIME SUR LE RECADRAGE AUTOMATIQUE.
    # En evaluation, personne ne pouvait bouger la camera : recadrer() en etait le
    # seul maitre et la reposait entierement (distance calculee + vue de trois
    # quarts) a chaque ouverture de panneau ou changement de taille. Ici le lecteur
    # tourne et zoome : ces memes evenements lui reprenaient sa vue sans prevenir,
    # d'ou un zoom qui « saute » selon ce qu'on venait de faire. Des qu'il a pris la
    # main, le recadrage ne fait plus que suivre le centre — il garde sa distance et
    # son angle. Echap rend la vue standard.
    # (a) la vue de reference devient une pose EXPLICITE, au lieu d'un effet de bord
    #     du recadrage. C'est la seule chose qui a le droit de bouger la camera sans
    #     que le lecteur l'ait demande.
    a = "  ctl.target.copy(centre);"
    assert a in s, 'cible du recadrage introuvable'
    s = s.replace(a,
                  "  // En lecture, le recadrage ne reprend JAMAIS la vue : il suit le centre\n"
                  "  // (livraison regardee, place laissee au panneau) en conservant l'ecart\n"
                  "  // camera-cible, donc la distance et l'angle choisis par le lecteur.\n"
                  "  const ecart=cam.position.clone().sub(ctl.target);\n"
                  "  ctl.target.copy(centre); cam.position.copy(centre.clone().add(ecart));\n"
                  "  ctl.update(); return;\n", 1)
    assert 'function recadrer(){' in s, 'recadrer introuvable'
    s = s.replace('function recadrer(){', AJUSTEMENT.strip() + '\nfunction recadrer(){', 1)
    s = s.replace('function recadrer(){',
                  "// La vue de reference : de trois quarts, a la distance qui fait tenir la\n"
                  "// livraison regardee. Posee a l'arrivee et sur Echap, jamais au milieu d'une\n"
                  "// lecture — sinon le zoom sauterait a chaque panneau ouvert.\n"
                  "function poserVueStandard(){\n"
                  "  if(!D||!plans.length)return;\n"
                  "  const AZ=26*Math.PI/180, EL=14*Math.PI/180;\n"
                  "  const dir=new THREE.Vector3(Math.sin(AZ)*Math.cos(EL),Math.sin(EL),\n"
                  "                              Math.cos(AZ)*Math.cos(EL));\n"
                  "  cadX=0; cadY=0;\n"
                  "  ctl.target.set(0,0,zPlane(active));\n"
                  "  cam.position.copy(ctl.target.clone().add(dir.multiplyScalar(distanceFit()*1.12)));\n"
                  "  ctl.update(); recadrer(); ajusterCadrage();\n"
                  "  // les etiquettes ne sont posees qu au premier rendu : on remesure\n"
                  "  setTimeout(ajusterCadrage, 280);\n"
                  "}\n"
                  "function recadrer(){", 1)
    # (b) l'arrivee posait la vue de face, ecrasant le trois-quarts
    ins = ("  if(instant){cam.position.set(0,0,zPlane(ri)+distanceFit(ri));"
           "ctl.target.copy(cible);ctl.update();return;}")
    assert ins in s, 'arrivee instantanee introuvable'
    s = s.replace(ins,
                  "  if(instant){ poserVueStandard(); return; }   // lecture : on arrive de biais", 1)
    # (c) Echap rend la vue de reference
    esc = ("  if(e.key==='Escape'){if(panel.classList.contains('on')){retour();}"
           "else allerA(active);}")
    assert esc in s, 'raccourci Echap introuvable'
    s = s.replace(esc,
                  "  if(e.key==='Escape'){if(panel.classList.contains('on')){retour();}\n"
                  "    else poserVueStandard();}", 1)
    s = s.replace("<span class=\"r\"><b>Échap</b> — recentrer</span>",
                  "<span class=\"r\">glisser — tourner &nbsp;·&nbsp; molette — zoomer</span>\n"
                  "  <span class=\"r\"><b>Échap</b> — revenir à la vue d'ensemble</span>", 1)

    # 5. le style, et le canvas qui doit recevoir la souris pour qu'on tourne
    style = ("\n/* page de lecture : rien de ce qui sert a evaluer n'y a sa place, et la "
             "constellation se manipule a la souris */\n"
             "html.lecture .tier-picker, html.lecture .note-sticky, html.lecture .avis-row,\n"
             "html.lecture #wt-scrim, html.lecture #wt-tooltip{display:none!important}\n"
             "html.lecture canvas{pointer-events:auto!important}\n"
             # sous filtre, ce qui n'est pas retenu ne doit plus distraire — et la
             # boucle de rendu, qui repose l'opacite a chaque image, ne doit pas
             # pouvoir le rallumer
             "html.lecture .lb.masque{opacity:0!important;pointer-events:none!important}\n"
             "</style>")
    s = s.replace('</style>', style, 1)
    s = s.replace('<body', '<body onload="document.documentElement.classList.add(\'lecture\')"', 1)

    # une fenetre redimensionnee change la zone utile : on remesure
    s = s.replace("  recadrer();   // la constellation se reajuste pour tenir dans la nouvelle taille",
                  "  recadrer(); ajusterCadrage();   // on remesure : la zone utile a change", 1)

    # une page de lecture n'a pas de notes a precharger : le fetch finissait en 404
    s = s.replace("const r=await fetch('notes-preset.json'",
                  "const r=window.__PUBLICATION?{ok:false}:await fetch('notes-preset.json'")

    # arriver sur une autre livraison change ce qu'il y a a cadrer : on remesure
    av = "    if(k<1)requestAnimationFrame(step);"
    assert av in s, 'boucle de vol introuvable'
    s = s.replace(av,
                  "    if(k<1)requestAnimationFrame(step);\n"
                  "    else { cadX=0; cadY=0; ajusterCadrage();\n"
                  "      // on a change de livraison : la selection ouverte suit\n"
                  "      if(!modeGlobal && filtreActif()) ouvrirSelection();\n"
                  "    }   // fin du vol : on recadre", 1)

    # 6. LES FILTRES — un niveau d'interet, un axe, ou les deux, a travers tout.
    #    La page montre tout, livraison par livraison, et c'est ce qui la rend
    #    difficile a lire : pour retrouver ce qui a ete juge excellent, ou tout
    #    ce qui touche a l'energie, il faut ouvrir les semaines une par une et se
    #    souvenir. Un filtre retient et efface le reste, sans changer de vue.
    assert 'function recadrer(){' in s, 'recadrer introuvable (filtres)'
    s = s.replace('function recadrer(){', TUBE.strip() + '\nfunction recadrer(){', 1)

    #    sous filtre, une etoile retenue se clique dans n'importe quelle livraison
    a_att = ("function atteignables(){\n"
             "  const multi = (D && (D.runs||[]).length>1 && D.mode==='publish');\n"
             "  if(!multi) return etoiles;")
    assert a_att in s, 'atteignables introuvable'
    s = s.replace(a_att, a_att + "\n"
                  "  if(filtreActif()) return etoiles.filter(m=>m.userData "
                  "&& m.userData.type==='leaf'\n"
                  "    && retenu(m.userData.d));", 1)

    #    la profondeur obeit au filtre : ce qui est retenu prime sur la livraison
    a_prof = ("      u.lb.style.display = vis ? '' : 'none';\n"
              "    }\n"
              "  });\n"
              "}")
    assert a_prof in s, 'fin de majProfondeur introuvable'
    s = s.replace(a_prof,
                  "      u.lb.style.display = vis ? '' : 'none';\n"
                  "      if(!filtreActif()) u.lb.classList.remove('masque');\n"
                  "    }\n"
                  "    // en vue d'ensemble, aucune livraison n'est « celle du fond »\n"
                  "    if(modeGlobal && u.type==='leaf'){\n"
                  "      if(m.material&&m.material.opacity!=null){ m.material.opacity=1; }\n"
                  "      if(u.halo&&u.halo.material) u.halo.material.opacity=0.5;\n"
                  "    }\n"
                  "  });\n"
                  "  if(!filtreActif()) plans.forEach(pl=>{ (pl.etiquettes||[]).forEach(el=>{\n"
                  "    el.classList.remove('masque'); }); });\n"
                  "  if(modeGlobal) plans.forEach(pl=>{\n"
                  "    if(pl.limite) pl.limite.material.opacity=0.34;\n"
                  "    if(pl.dateEl) pl.dateEl.style.display=''; });\n"
                  "  // Sous filtre, ce qui est retenu reste plein dans toutes les couches et le\n"
                  "  // reste s'efface au point de ne plus distraire. Le masquage passe par une\n"
                  "  // classe : le moteur d'etiquettes reecrit `display` a chaque rendu.\n"
                  "  if(filtreActif()){\n"
                  "    etoiles.forEach(m=>{\n"
                  "      const u=m.userData||{};\n"
                  "      if(u.type==='axe'){\n"
                  "        // l'axe retenu reste lisible ; les autres s'effacent\n"
                  "        const garde = !axeFiltre || u.axe===axeFiltre;\n"
                  "        if(m.material&&m.material.opacity!=null){ m.material.transparent=true;\n"
                  "          m.material.opacity = garde?Math.min(m.material.opacity,0.7):0.05; }\n"
                  "        if(u.halo&&u.halo.material) u.halo.material.opacity = garde?0.3:0.02;\n"
                  "        if(u.lb) u.lb.classList.toggle('masque', !garde);\n"
                  "        return;\n"
                  "      }\n"
                  "      if(u.type!=='leaf') return;\n"
                  "      const dedans = retenu(u.d);\n"
                  "      if(m.material&&m.material.opacity!=null){ m.material.transparent=true;\n"
                  "        m.material.opacity = dedans?1:0.045; }\n"
                  "      if(u.halo&&u.halo.material) u.halo.material.opacity = dedans?0.6:0.01;\n"
                  "      if(u.lb) u.lb.classList.toggle('masque', !dedans);\n"
                  "    });\n"
                  "  }\n"
                  "}", 1)

    #    choisir une date sort de la vue d'ensemble
    a_rail = "    b.textContent=fmtd(run); b.onclick=()=>allerA(ri);"
    assert a_rail in s, 'onclick du rail introuvable'
    s = s.replace(a_rail,
                  "    b.textContent=fmtd(run); b.onclick=()=>versLivraison(ri);", 1)
    n_fl = s.count("allerA(active+1)") + s.count("allerA(active-1)")
    s = s.replace("allerA(active+1)", "versLivraison(active+1)")
    s = s.replace("allerA(active-1)", "versLivraison(active-1)")
    assert n_fl >= 2, 'fleches du rail introuvables'

    #    Echap quitte d'abord les filtres
    #    deux gardes "clic hors panneau" fermaient la fiche que la barre ouvrait
    a_g1 = ("  if(t.closest&&t.closest('#lang-toggle,header,#nav,#exportbtn,.resizer,"
            "#fbmodal,#wt-scrim,#tuto-scrim,#help-btn-wt,#keys,.lb'))return;")
    assert a_g1 in s, 'garde pointerdown introuvable'
    s = s.replace(a_g1, a_g1.replace("#exportbtn,", "#exportbtn,#hud,"), 1)
    a_g2 = ("    if(e.target.closest && e.target.closest('#gl, canvas, .lb, #nav, #lang-toggle, "
            "#help-btn-wt, #wt-scrim, #wt-masque, #wt-tooltip, .resizer')) return;")
    assert a_g2 in s, 'garde click introuvable'
    s = s.replace(a_g2, a_g2.replace(".resizer')", ".resizer, #hud')"), 1)

    #    la selection se rouvre depuis la pile de navigation, et ses lignes se
    #    survolent comme celles d'un axe
    a_rv = "    else if(v.type==='axe')  ouvrirAxe(v.axe,v.ri);"
    assert a_rv in s, 'rouvrir introuvable'
    s = s.replace(a_rv, "    else if(v.type==='selection') ouvrirSelection();\n"
                        "    else if(v.type==='bilan') ouvrirBilan();\n" + a_rv, 1)
    a_css = "  .ent.lienf{cursor:pointer;border-radius:0 8px 8px 0;transition:background .12s}"
    assert a_css in s, 'style des lignes introuvable'
    s = s.replace(a_css, a_css + "\n" + STYLE_ENSEMBLE, 1)

    a_esc = ("  if(e.key==='Escape'){if(panel.classList.contains('on')){retour();}\n"
             "    else poserVueStandard();}")
    assert a_esc in s, 'raccourci Echap introuvable (filtres)'
    s = s.replace(a_esc,
                  "  if(e.key==='Escape'){if(panel.classList.contains('on')){retour();}\n"
                  "    else if(viderFiltres()){}\n"
                  "    else poserVueStandard();}", 1)

    # 7. la sonde de camera : pouvoir constater ce qu'on regarde
    assert "montrerFil(i){" in s, 'pont __constel introuvable'
    s = s.replace("  montrerFil(i){",
                  "  rappelerFiltres(){ try{ majBoutonsFiltre(); }catch(e){} },\n"
                  "  vueGlobale(v){ try{ return vueGlobale(v); }"
                  "catch(e){ return String(e); } },\n"
                  "  filtrer(genre,valeur){ try{ return filtrer(genre,valeur); }"
                  "catch(e){ return String(e); } },\n"
                  "  couleurAxe(a){ try{ return AXC[a]||'#7fb0ff'; }catch(e){ return '#7fb0ff'; } },\n"
                  "  cadrer(){ try{ ajusterCadrage(); return true; }catch(e){ return String(e); } },\n"
                  "  camera(){ const o=cam.position.clone().sub(ctl.target);\n"
                  "    return { dist:+o.length().toFixed(1),\n"
                  "      azimut:+(Math.atan2(o.x,o.z)*180/Math.PI).toFixed(1),\n"
                  "      polaire:+(Math.acos(Math.max(-1,Math.min(1,o.y/o.length())))*180/Math.PI).toFixed(1),\n"
                  "      cible:[+ctl.target.x.toFixed(0),+ctl.target.y.toFixed(0),+ctl.target.z.toFixed(0)] }; },\n"
                  "  montrerFil(i){", 1)

    #    le panneau decale la FENETRE, plus le centre : sinon on orbite autour d'un
    #    point qui n'est pas la constellation, et elle sort du cadre au premier glisser
    dec = ("  const decal=(largeurPanneau()/2/innerWidth)*Wworld;"
           "   // pousse le contenu vers la gauche")
    assert dec in s, 'decal du recadrage introuvable'
    s = s.replace(dec,
                  "  // Le panneau ne deplace plus le CENTRE : il decale la fenetre de\n"
                  "  // projection. L'orbite reste ancree sur la constellation, qui ne part\n"
                  "  // donc plus hors cadre des qu'on la fait tourner.\n"
                  "  const decal=0;\n"
                  "  (function(){ const w=largeurPanneau();\n"
                  "    const ox=(w>2?w/2:0)+cadX, oy=cadY;\n"
                  "    if(ox||oy) cam.setViewOffset(innerWidth,innerHeight,\n"
                  "      ox,oy,innerWidth,innerHeight);\n"
                  "    else cam.clearViewOffset(); })();", 1)

    # 8. la barre du filtre, hors module
    s = s.replace('</body>', BARRE + '</body>', 1)

    pathlib.Path(dst).write_text(s, encoding='utf-8')
    return len(s)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    n = generer(sys.argv[1], sys.argv[2])
    print('template de publication genere (%d Ko)' % (n // 1024))
