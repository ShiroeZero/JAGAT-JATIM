/* JAGAT V6.7.2 — situational East Java map. */
(() => {
  const GEOJSON_URL = "https://raw.githubusercontent.com/AlfianAliM/Indonesia-GeoJSON/master/kab_kota.geojson";
  let map=null, layer=null, geojson=null;
  const esc=v=>typeof escapeHtml==="function"?escapeHtml(v):String(v??"");
  const norm=v=>String(v||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim();
  const fmt=v=>Number(v||0).toLocaleString("id-ID");
  const areas=["Surabaya","Sidoarjo","Gresik","Lamongan","Tuban","Bojonegoro","Ngawi","Magetan","Madiun","Ponorogo","Pacitan","Nganjuk","Kediri","Tulungagung","Trenggalek","Blitar","Malang","Batu","Pasuruan","Probolinggo","Lumajang","Jember","Bondowoso","Situbondo","Banyuwangi","Mojokerto","Jombang","Pamekasan","Bangkalan","Sampang","Sumenep"];
  function items(){try{return typeof todayJatimItems==="function"?todayJatimItems():[]}catch(e){return[]}}
  function cases(){try{return typeof activeCases==="function"?activeCases():[]}catch(e){return[]}}
  function locality(x){try{return typeof getLocality==="function"?getLocality(x):(x.locality||x.area_label||"")}catch(e){return x.locality||""}}
  function score(x,c){try{return typeof getEffectiveAttentionScore==="function"?getEffectiveAttentionScore(x,c):Number(x.attention_score||0)}catch(e){return Number(x.attention_score||0)}}
  function areaName(f){const p=f?.properties||{};return p.name||p.NAME_2||p.NAME||p.namobj||p.WADMKK||p.kab_kota||p.KABKOT||p.NAMOBJ||""}
  function canonical(n){let x=norm(n).replace(/^kabupaten /,"").replace(/^kota /,"");const m={surabaya:"Surabaya",malang:"Malang",batu:"Batu",sidoarjo:"Sidoarjo",gresik:"Gresik",pasuruan:"Pasuruan",probolinggo:"Probolinggo",lumajang:"Lumajang",jember:"Jember",banyuwangi:"Banyuwangi",bondowoso:"Bondowoso",situbondo:"Situbondo",kediri:"Kediri",tulungagung:"Tulungagung",trenggalek:"Trenggalek",blitar:"Blitar",nganjuk:"Nganjuk",madiun:"Madiun",magetan:"Magetan",ngawi:"Ngawi",ponorogo:"Ponorogo",pacitan:"Pacitan",bojonegoro:"Bojonegoro",tuban:"Tuban",lamongan:"Lamongan",mojokerto:"Mojokerto",jombang:"Jombang",pamekasan:"Pamekasan",bangkalan:"Bangkalan",sampang:"Sampang",sumenep:"Sumenep"};return m[x]||String(n||"").replace(/^Kabupaten\s+/i,"").replace(/^Kota\s+/i,"")}
  function stats(area){const a=norm(area),c=cases(),r=items().filter(x=>norm(locality(x))===a);let max=0,neg=0,med=0,ids=new Set();r.forEach(x=>{const s=score(x,c);max=Math.max(max,s);if(s>=70)neg++;else if(s>=40)med++;if(String(x.scope||"").toLowerCase()==="negative")neg++;if(x.case_id)ids.add(x.case_id)});return{r,max,neg,med,cases:ids.size}}
  function fill(s){if(!s.r.length)return"#0a1b2b";if(s.neg||s.max>=70)return"#b52f43";if(s.max>=40||s.med)return"#a87828";return"#12658b"}
  function init(){const el=document.getElementById("jatimMap");if(!el||!window.L||map)return;map=L.map(el,{zoomControl:false,attributionControl:true,scrollWheelZoom:true}).setView([-7.78,112.55],8);L.control.zoom({position:"bottomright"}).addTo(map);fetchGeo()}
  async function fetchGeo(){try{const r=await fetch(GEOJSON_URL,{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);const all=await r.json();const features=(all.features||[]).filter(f=>areas.includes(canonical(areaName(f))));if(!features.length)throw Error("Tidak menemukan batas Jawa Timur");geojson={type:"FeatureCollection",features};render()}catch(e){console.error("JAGAT map:",e);const el=document.getElementById("jatimMap");if(el)el.innerHTML='<div class="jagat-map-error"><strong>Peta Jawa Timur gagal dimuat</strong><span>'+esc(e.message||"Sumber peta tidak tersedia")+'</span></div>'}}
  function render(){if(!map||!geojson)return;if(layer)layer.remove();layer=L.geoJSON(geojson,{style:f=>{const s=stats(canonical(areaName(f)));return{color:"#2b6687",weight:1,fillColor:fill(s),fillOpacity:s.r.length?.82:.32}},onEachFeature:(f,p)=>{const a=canonical(areaName(f)),s=stats(a);p.bindTooltip(esc(a),{sticky:true,className:"jagat-map-label"});p.bindPopup('<div class="jagat-map-popup"><div class="jagat-map-popup-eyebrow">JAWA TIMUR</div><strong>'+esc(a)+'</strong><div class="jagat-map-popup-grid"><b>'+fmt(s.r.length)+'<small>BERITA</small></b><b>'+fmt(s.cases)+'<small>KASUS</small></b><b>'+fmt(s.max)+'<small>ATENSI</small></b></div><button type="button" class="jagat-map-open">BUKA WILAYAH →</button></div>');p.on({mouseover:()=>p.setStyle({weight:2,color:"#57d7f0",fillOpacity:.92}),mouseout:()=>layer.resetStyle(p),popupopen:()=>p.getPopup().getElement()?.querySelector(".jagat-map-open")?.addEventListener("click",()=>{const r=items().filter(x=>norm(locality(x))===norm(a));if(typeof openRegionDrawer==="function")openRegionDrawer(a,r)})})}}).addTo(map);const b=layer.getBounds();if(b.isValid())map.fitBounds(b,{padding:[15,15],maxZoom:9});setTimeout(()=>map.invalidateSize(),200);const c=document.getElementById("mapCount");if(c)c.textContent=geojson.features.length+" kab/kota"}
  function boot(){const el=document.getElementById("jatimMap");if(!el)return;init();const badge=document.createElement("div");badge.className="jagat-polda-map-badge";badge.innerHTML='<span class="jagat-polda-pulse"></span><div><strong>POLDA JAWA TIMUR</strong><small>Unit pusat / fungsi Polda</small></div>';el.appendChild(badge)}
  document.addEventListener("DOMContentLoaded",()=>setTimeout(boot,500));window.addEventListener("resize",()=>map?.invalidateSize())
})();

/* JAGAT CONTEXTUAL UI PATCH v1.0 */
(() => {
  const fmt = v => Number(v || 0).toLocaleString("id-ID");
  const scope = x => String(x?.scope || "neutral").toLowerCase();
  const extraSearchText = x => [
    x?.title, x?.summary, x?.description, x?.source, x?.publisher,
    x?.region, x?.locality, x?.area_label, x?.polres, x?.polsek,
    x?.category, x?.scope, x?.scope_label, x?.issue_type, x?.issue_subtype,
    x?.polri_relation, x?.assertion_status,
    ...(Array.isArray(x?.discovery_tags) ? x.discovery_tags : []),
    ...(Array.isArray(x?.discovery_hits) ? x.discovery_hits : [])
  ].filter(Boolean).join(" ").toLowerCase();

  window.regionStatus = function(items, casesById) {
    const negative = items.filter(x => scope(x) === "negative").length;
    const positive = items.filter(x => scope(x) === "positive").length;
    const neutral = items.filter(x => scope(x) === "neutral").length;
    const cases = items.filter(x => scope(x) === "case").length;
    const attention = items.map(x => {
      try { return typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(x, casesById) : Number(x.attention_score || 0); }
      catch { return Number(x.attention_score || 0); }
    });
    const high = attention.filter(n => n >= 70).length;
    const medium = attention.filter(n => n >= 40 && n < 70).length;
    if (high) return { cls: "danger", label: `Atensi tinggi · ${fmt(high)} berita`, rank: 5 };
    if (negative) return { cls: "danger", label: `Ada ${fmt(negative)} berita negatif`, rank: 4 };
    if (medium) return { cls: "warning", label: `Atensi sedang · ${fmt(medium)} berita`, rank: 3 };
    if (positive && !neutral && !cases) return { cls: "success", label: `Positif · ${fmt(positive)} berita`, rank: 2 };
    return { cls: "neutral", label: `Terpantau · ${fmt(neutral)} netral`, rank: 1 };
  };

  window.applyMonitoringFilters = function(items) {
    const { from, to } = typeof currentDateBounds === "function" ? currentDateBounds() : { from: null, to: null };
    let out = typeof filterByDate === "function" ? filterByDate(items, from, to) : items.slice();
    const cases = typeof activeCases === "function" ? activeCases() : [];
    const search = (document.getElementById("search")?.value || "").trim().toLowerCase();
    const location = document.getElementById("region")?.value || "all";
    const polres = document.getElementById("polres")?.value || "all";
    const attention = document.getElementById("priority")?.value || "all";
    const selectedScope = document.getElementById("scope")?.value || "all";
    const category = document.getElementById("category")?.value || "all";

    if (search) out = out.filter(x => extraSearchText(x).includes(search));
    if (location !== "all") {
      if (location === "__JATIM__") out = out.filter(x => x?.is_jatim === true || String(x?.region || "").toLowerCase() === "jawa timur");
      else if (location === "__OUTSIDE__") out = out.filter(x => x?.region === "LUAR JATIM");
      else if (location === "__UNKNOWN__") out = out.filter(x => x?.region === "BELUM TERPETAKAN" || x?.is_jatim == null);
      else out = out.filter(x => String(typeof getFilterArea === "function" ? getFilterArea(x) : (x.locality || x.area_label || "")) === location);
    }
    if (polres !== "all") out = out.filter(x => String(x?.polres || "") === polres);
    if (attention !== "all" && typeof matchesAttentionBand === "function") out = out.filter(x => matchesAttentionBand(x, attention, cases));
    if (selectedScope !== "all") out = out.filter(x => scope(x) === selectedScope);
    if (category !== "all") out = out.filter(x => String(x?.category || "") === category);
    return out.sort((a,b) => {
      const sa = typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(a, cases) : Number(a.attention_score || 0);
      const sb = typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(b, cases) : Number(b.attention_score || 0);
      return sb - sa || new Date(b?.published_at || b?.collected_at || 0) - new Date(a?.published_at || a?.collected_at || 0);
    });
  };

  window.openArticleDrawer = function(article, dataset = typeof activeNews === "function" ? activeNews() : [], caseDataset = typeof activeCases === "function" ? activeCases() : []) {
    const c = typeof getCaseById === "function" ? getCaseById(article.case_id, caseDataset) : null;
    const url = typeof normalizeUrl === "function" ? normalizeUrl(article.url) : article.url;
    const attention = typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(article, caseDataset) : Number(article.attention_score || 0);
    const attentionLabel = typeof getEffectiveAttentionLabel === "function" ? getEffectiveAttentionLabel(article, caseDataset) : (article.attention_label || "Rendah");
    const esc = typeof escapeHtml === "function" ? escapeHtml : v => String(v ?? "");
    const reason = Array.isArray(article.attention_reasons) ? article.attention_reasons : [];
    const assertion = article.assertion_status || "-";
    const relation = article.polri_relation || "-";
    const evidence = Array.isArray(article.location_evidence) ? article.location_evidence.slice(0, 4) : [];
    const eyebrow = document.getElementById("drawerEyebrow");
    const content = document.getElementById("drawerContent");
    if (!content) return;
    if (eyebrow) eyebrow.textContent = "DETAIL BERITA";
    content.innerHTML = `
      <div class="drawer-title">${esc(typeof getTitle === "function" ? getTitle(article) : article.title)}</div>
      <div class="drawer-meta">${esc(typeof getSource === "function" ? getSource(article) : (article.source || ""))} · ${esc(typeof formatDateTime === "function" ? formatDateTime(article.published_at || article.collected_at) : "")}</div>
      <div class="drawer-pills">
        <span class="pill ${typeof attentionClass === "function" ? attentionClass(attention) : ""}">ATENSI ${fmt(attention)}/100 · ${esc(attentionLabel)}</span>
        <span class="pill">${esc(String(article.scope || "neutral").toUpperCase())}</span>
        ${c ? `<span class="pill">KASUS TERKAIT</span>` : ""}
      </div>
      <div class="detail-grid">
        <div><span>Wilayah</span><strong>${esc(article.locality || article.area_label || article.region || "Belum Terpetakan")}</strong></div>
        <div><span>Polres</span><strong>${esc(article.polres || "-")}</strong></div>
        <div><span>Polsek</span><strong>${esc(article.polsek || "-")}</strong></div>
        <div><span>Relasi Polri</span><strong>${esc(relation)}</strong></div>
        <div><span>Status Klaim</span><strong>${esc(assertion)}</strong></div>
        <div><span>Kategori</span><strong>${esc(article.category || "-")}</strong></div>
      </div>
      ${(reason.length || evidence.length) ? `<div class="context-evidence"><h4>Mengapa diklasifikasikan?</h4>${reason.length ? `<ul>${reason.slice(0, 5).map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}${evidence.length ? `<div class="muted">Bukti lokasi: ${esc(evidence.join(", "))}</div>` : ""}</div>` : ""}
      <div class="drawer-actions">
        ${url ? `<a class="primary-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Buka Berita Asli</a>` : ""}
      </div>`;
    if (typeof openDrawer === "function") openDrawer();
    if (typeof bindCopyButtons === "function") bindCopyButtons(content);
  };

  const css = document.createElement("style");
  css.textContent = `
    .context-evidence{margin:14px 0;padding:14px;border:1px solid rgba(100,140,180,.18);border-radius:14px;background:rgba(10,19,31,.55)}
    .context-evidence h4{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#8ea5bb}
    .context-evidence ul{margin:0 0 8px 18px;padding:0;color:#dbe8f4}
    .context-evidence li{margin:4px 0}
  `;
  document.head.appendChild(css);
})();
