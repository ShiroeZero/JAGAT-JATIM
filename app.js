const TODAY_URL = "data/today.json";
const CASE_URL = "data/case_clusters.json";
const NEWS_URL = "data/news.json";
const ARCHIVE_INDEX_URL = "data/archive/index.json";

const JATIM_COORDS = {
  Surabaya: [-7.2575, 112.7521], Gresik: [-7.1568, 112.6551], Sidoarjo: [-7.4478, 112.7183],
  Mojokerto: [-7.4706, 112.4401], Jombang: [-7.5459, 112.2331], Nganjuk: [-7.6052, 111.9046],
  Madiun: [-7.6298, 111.5239], Magetan: [-7.6559, 111.3327], Ngawi: [-7.4032, 111.4461],
  Bojonegoro: [-7.1502, 111.8817], Tuban: [-6.8976, 112.0645], Lamongan: [-7.1167, 112.3333],
  Kediri: [-7.8167, 112.0167], Tulungagung: [-8.0657, 111.9025], Trenggalek: [-8.05, 111.7167],
  Blitar: [-8.0983, 112.1681], Malang: [-7.9819, 112.6265], Batu: [-7.87, 112.523],
  Pasuruan: [-7.6453, 112.9075], Probolinggo: [-7.7543, 113.2159], Lumajang: [-8.1335, 113.2248],
  Jember: [-8.1724, 113.7009], Bondowoso: [-7.9135, 113.8215], Situbondo: [-7.7062, 114.0098],
  Banyuwangi: [-8.2191, 114.3691], Pacitan: [-8.1949, 111.1047], Ponorogo: [-7.865, 111.4696],
  Sumenep: [-7.0167, 113.8667], Pamekasan: [-7.1568, 113.4746], Sampang: [-7.1872, 113.2394],
  Bangkalan: [-7.0455, 112.7351]
};

let todayData = null;
let caseData = { cases: [] };
let newsData = [];
let archiveFiles = [];
let currentView = "dashboard";
let monitoringMode = "all";
let archiveMode = "all";
let activeArchive = null;
let map = null;
let mapMarkers = [];

const $ = (id) => document.getElementById(id);
const number = (v) => Number.isFinite(Number(v)) ? Number(v).toLocaleString("id-ID") : "0";

function escapeHtml(v) {
  return String(v ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}
function normalizeUrl(v) { const s = String(v || "").trim(); return /^https?:\/\//i.test(s) ? s : ""; }
function formatDate(v) { const d = new Date(v); if (!v || Number.isNaN(d.getTime())) return v || "-"; return d.toLocaleDateString("id-ID", {day:"2-digit", month:"long", year:"numeric"}); }
function formatDateTime(v) { const d = new Date(v); if (!v || Number.isNaN(d.getTime())) return v || "-"; return d.toLocaleString("id-ID", {day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit", hour12:false}) + " WIB"; }
function dateKey(v) { const d = new Date(v); if (!v || Number.isNaN(d.getTime())) return ""; return d.toLocaleDateString("en-CA", {timeZone:"Asia/Jakarta"}); }
function dateToInput(v) { return dateKey(v); }
function getTitle(x) { return x?.title || "Tanpa judul"; }
function getSource(x) { return x?.source || x?.publisher || "Sumber tidak diketahui"; }
function getItemDate(x) { return x?.collected_at || x?.published_at || x?.detected_at || ""; }
function getPriority(x) { return String(x?.priority || "low").toLowerCase(); }
function getScope(x) { return String(x?.scope || "neutral").toLowerCase(); }
function getCategory(x) { return x?.category || "NETRAL / LAINNYA"; }
function isJatim(x) { return x?.is_jatim === true; }
function priorityRank(v) { return ({high:3, medium:2, low:1})[String(v || "low").toLowerCase()] || 1; }
function unique(a) { return [...new Set(a.filter(Boolean))]; }
function setStatus(text, ok) { if ($("statusText")) $("statusText").textContent = text; if ($("statusDot")) $("statusDot").style.background = ok ? "var(--ok)" : "var(--danger)"; }

async function fetchJson(url) { const r = await fetch(url + "?t=" + Date.now()); if (!r.ok) throw new Error(`${url} HTTP ${r.status}`); return r.json(); }

async function loadAllData() {
  setStatus("Memuat data...", false);
  try {
    const [today, cases, news, archiveIndex] = await Promise.all([fetchJson(TODAY_URL), fetchJson(CASE_URL), fetchJson(NEWS_URL), fetchJson(ARCHIVE_INDEX_URL)]);
    todayData = today || {};
    caseData = cases || {cases:[]};
    newsData = Array.isArray(news) ? news : (news?.items || []);
    archiveFiles = Array.isArray(archiveIndex) ? archiveIndex : (archiveIndex?.files || []);
    initializeDefaultMonitoringDates();
    renderAll();
    setStatus("Data aktif", true);
  } catch (e) { console.error(e); setStatus("Gagal memuat data", false); if ($("lastUpdated")) $("lastUpdated").textContent = "Data gagal dimuat"; }
}

function showView(view) {
  currentView = view;
  document.querySelectorAll(".view").forEach(v => v.classList.toggle("hidden", !v.id.startsWith(view)));
  document.querySelectorAll("[data-view]").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  const titles = {dashboard:"Dashboard", monitoring:"Monitoring", reports:"Laporan", archive:"Arsip"};
  if ($("pageTitle")) $("pageTitle").textContent = titles[view] || "PNM";
  if (view === "dashboard") { renderDashboard(); setTimeout(() => map?.invalidateSize(), 80); }
  if (view === "monitoring") { renderMonitoring(); }
  if (view === "archive") { renderArchiveList(); }
}

document.querySelectorAll("[data-view]").forEach(b => b.addEventListener("click", () => showView(b.dataset.view)));

document.querySelectorAll("[data-open-monitoring]").forEach(b => b.addEventListener("click", () => { monitoringMode = b.dataset.openMonitoring === "jatim" ? "jatim" : b.dataset.openMonitoring === "high" ? "high" : "all"; showView("monitoring"); syncModeButtons(); renderMonitoring(); }));

function renderAll() {
  if (!todayData) return;
  $("todayDate").textContent = formatDate(todayData.date);
  $("lastUpdated").textContent = "Update terakhir: " + formatDateTime(todayData.last_successful_update || todayData.updated_at);
  $("sTotal").textContent = number(todayData.summary?.news_today);
  $("sCases").textContent = number(todayData.summary?.cases_today);
  $("sYoutube").textContent = number(todayData.summary?.youtube_today);
  $("sHigh").textContent = number(todayData.summary?.case_high ?? todayData.cases?.priority_high ?? 0);
  $("sNegative").textContent = number(todayData.summary?.negative_today);
  $("sJatim").textContent = number(todayData.summary?.jatim_news);
  $("sCaseHigh").textContent = number(todayData.summary?.case_high ?? todayData.cases?.priority_high ?? 0);
  $("sTotalCases").textContent = number(caseData?.total_cases);
  renderDashboard();
  renderArchiveList();
}

function todayItems() { return Array.isArray(todayData?.news?.items) ? todayData.news.items : []; }
function globalCases() { return Array.isArray(caseData?.cases) ? caseData.cases : []; }
function activeNews() { return activeArchive ? (activeArchive.news?.items || []) : newsData; }
function activeCases() { return activeArchive ? (activeArchive.cases?.items || []) : globalCases(); }
function caseMap(cases = activeCases()) { return new Map(cases.map(c => [c.case_id, c])); }

function localityFromPolres(polres) {
  const t = String(polres || "").toLowerCase();
  for (const name of Object.keys(JATIM_COORDS)) if (t.includes(name.toLowerCase())) return name;
  return "";
}
function getLocality(x) {
  const p = localityFromPolres(x?.polres);
  if (p) return p;
  const t = `${x?.title || ""} ${x?.location || ""} ${x?.region || ""}`.toLowerCase();
  for (const name of Object.keys(JATIM_COORDS)) if (t.includes(name.toLowerCase())) return name;
  return "";
}
function getCaseById(id, cases = activeCases()) { return id ? cases.find(c => c.case_id === id) || null : null; }
function getArticleById(id, items = activeNews()) { return id ? items.find(n => n.id === id) || null : null; }

function getCasePriorityIds(cases = activeCases()) { return new Set(cases.filter(c => getPriority(c) === "high").map(c => c.case_id)); }
function isCaseHighArticle(article, cases = activeCases()) { return !!article.case_id && getCasePriorityIds(cases).has(article.case_id); }
function getCaseArticleIds(caseItem) { return new Set(caseItem?.article_ids || (caseItem?.articles || []).map(a => a.id).filter(Boolean)); }

function articlePassesMode(article, mode, cases) {
  if (mode === "jatim") return isJatim(article);
  if (mode === "high") return isCaseHighArticle(article, cases);
  return true;
}

function setDefaultTodayRange() {
  if (!$('dateFrom') || !$('dateTo') || !todayData?.date) return;
  $('dateFrom').value = todayData.date;
  $('dateTo').value = todayData.date;
}
function initializeDefaultMonitoringDates() {
  if (!$('dateFrom') || !$('dateTo')) return;
  if (!$('dateFrom').value && !$('dateTo').value) setDefaultTodayRange();
}

function currentDateBounds() { return {from: $("dateFrom")?.value || "", to: $("dateTo")?.value || ""}; }

function renderDashboard() {
  const items = todayItems();
  renderRegionsToday(items);
  renderCategories(items);
  renderLatest(items);
  renderLatestCases();
  initMap();
  renderMap(items);
}

function renderRegionsToday(items) {
  const target = $("regionToday"); if (!target) return;
  const groups = new Map();
  items.filter(isJatim).forEach(item => { const r = getLocality(item) || "Jawa Timur"; if (!groups.has(r)) groups.set(r, {count:0}); groups.get(r).count++; });
  const cases = activeCases();
  const byRegion = new Map();
  cases.forEach(c => { const r = getLocality(c); if (!r) return; if (!byRegion.has(r)) byRegion.set(r,{high:0,cases:0}); byRegion.get(r).cases++; if (getPriority(c)==="high") byRegion.get(r).high++; });
  const rows = [...groups.entries()].sort((a,b)=>b[1].count-a[1].count);
  target.innerHTML = rows.length ? rows.map(([name,v]) => { const meta=byRegion.get(name)||{high:0,cases:0}; return `<button class="region-row" data-region="${escapeHtml(name)}"><span><strong>${escapeHtml(name)}</strong><small>${number(v.count)} berita · ${number(meta.cases)} case</small></span><span class="region-right">${meta.high ? `<span class="pill high">HIGH ${number(meta.high)}</span>` : `<span class="pill low">TERPANTAU</span>`}<b>→</b></span></button>`; }).join("") : `<div class="empty">Tidak ada wilayah Jawa Timur terdeteksi hari ini.</div>`;
  target.querySelectorAll("[data-region]").forEach(btn => btn.addEventListener("click",()=>{showView("monitoring"); monitoringMode="jatim"; syncModeButtons(); $("region").value=btn.dataset.region; renderMonitoring();}));
}

function renderCategories(items) {
  const target=$("categories"); if(!target)return;
  const c={Negatif:0,"Ungkap Kasus":0,Positif:0,Netral:0};
  items.forEach(i=>{const s=getScope(i); if(s==="negative")c.Negatif++; else if(s==="case")c["Ungkap Kasus"]++; else if(s==="positive")c.Positif++; else c.Netral++;});
  const rows=Object.entries(c), max=Math.max(...rows.map(x=>x[1]),1);
  target.innerHTML=rows.map(([label,count])=>`<div class="bar"><div class="bar-top"><span>${escapeHtml(label)}</span><strong>${number(count)}</strong></div><div class="bar-bg"><div class="bar-fill" style="width:${(count/max)*100}%"></div></div></div>`).join("");
}

function articleCard(item, compact=false) {
  const url=normalizeUrl(item.url), caseItem=getCaseById(item.case_id), caseHigh=caseItem && getPriority(caseItem)==="high";
  return `<article class="news-card clickable" data-article-id="${escapeHtml(item.id)}"><div class="news-card-top"><div><div class="news-card-meta">${escapeHtml(getSource(item))} · ${escapeHtml(getLocality(item)||item.region||"Indonesia")} · ${escapeHtml(formatDateTime(getItemDate(item)))}</div><h3>${escapeHtml(getTitle(item))}</h3><div class="news-card-meta">${escapeHtml(getCategory(item))}${caseItem ? ` · ${escapeHtml(caseHigh ? "Case HIGH" : "Terkait Case")}` : " · Belum terkait Case"}</div></div><div class="badges"><span class="pill ${escapeHtml(getPriority(item))}">${escapeHtml(getPriority(item).toUpperCase())}</span>${caseItem?`<span class="pill ${caseHigh?'high':''}">CASE</span>`:`<span class="pill">${escapeHtml(getScope(item).toUpperCase())}</span>`}</div></div><div class="card-action">${url?"Klik untuk detail · sumber tersedia ↗":"Klik untuk detail"}</div></article>`;
}
function caseCard(c,index) {
  const p=getPriority(c), locality=getLocality(c), score=c.priority_score!=null?` · ${number(c.priority_score)}/100`:"";
  return `<article class="case-card clickable" data-case-id="${escapeHtml(c.case_id)}"><div class="case-card-top"><span class="case-id">CASE ${String(index).padStart(2,'0')}</span><span class="pill ${escapeHtml(p)}">${escapeHtml(p.toUpperCase())}${score}</span></div><strong>${escapeHtml(c.title || "Case")}</strong><div class="news-card-meta">${escapeHtml(locality||c.region||"Indonesia")} · ${number(c.article_count || c.article_ids?.length || 0)} sumber · update ${escapeHtml(formatDateTime(c.last_detected_at || c.last_seen))}</div><div class="card-action">Klik untuk melihat seluruh sumber →</div></article>`;
}
function renderLatest(items){const t=$("latest"); if(!t)return; const x=[...items].sort((a,b)=>new Date(getItemDate(b)||0)-new Date(getItemDate(a)||0)).slice(0,8); t.innerHTML=x.length?x.map(i=>articleCard(i,true)).join(""):`<div class="empty">Belum ada berita hari ini.</div>`;bindArticleClicks(t);}
function renderLatestCases(){const t=$("latestCases");if(!t)return;const x=[...activeCases()].sort((a,b)=>priorityRank(b.priority)-priorityRank(a.priority)||new Date(b.last_detected_at||b.last_seen||0)-new Date(a.last_detected_at||a.last_seen||0)).slice(0,6);t.innerHTML=x.length?x.map((c,i)=>caseCard(c,i+1)).join(""):`<div class="empty">Belum ada case hari ini.</div>`;bindCaseClicks(t);}
function bindArticleClicks(root){root.querySelectorAll("[data-article-id]").forEach(el=>el.addEventListener("click",()=>openArticleDrawer(getArticleById(el.dataset.articleId))));}
function bindCaseClicks(root){root.querySelectorAll("[data-case-id]").forEach(el=>el.addEventListener("click",()=>openCaseDrawer(getCaseById(el.dataset.caseId))));}

function populateSelect(el, first, values, selected){if(!el)return;el.innerHTML=`<option value="all">${escapeHtml(first)}</option>`+values.map(v=>`<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join(""); if(values.includes(selected))el.value=selected;}
function populateMonitoringFilters(){
  const {from,to}=currentDateBounds();
  const dateItems=newsData.filter(x=>(!from||dateKey(getItemDate(x))>=from)&&(!to||dateKey(getItemDate(x))<=to));
  const currentRegion=$("region").value, currentPolres=$("polres").value, currentCategory=$("category").value;
  const regions=unique(dateItems.filter(isJatim).map(getLocality).sort((a,b)=>a.localeCompare(b)));
  populateSelect($("region"),"Semua Wilayah",regions,currentRegion);
  const filteredRegion=currentRegion!=="all"?dateItems.filter(x=>getLocality(x)===currentRegion):dateItems;
  const polres=unique(filteredRegion.map(x=>x.polres).filter(Boolean).sort((a,b)=>a.localeCompare(b)));
  populateSelect($("polres"),"Semua Polres Terdeteksi",polres,currentPolres);
  const categories=unique(dateItems.map(getCategory).sort((a,b)=>a.localeCompare(b)));
  populateSelect($("category"),"Semua Kategori",categories,currentCategory);
}

function applyCommonFilters(items, mode, prefix="") {
  const p=prefix;
  let out=[...items];
  const get=(id)=>$(p+id)?.value||"all";
  const from=$(p+"dateFrom")?.value||"";
  const to=$(p+"dateTo")?.value||"";
  if(from)out=out.filter(x=>dateKey(getItemDate(x))>=from);
  if(to)out=out.filter(x=>dateKey(getItemDate(x))<=to);
  if(mode==="jatim")out=out.filter(isJatim);
  if(mode==="high")out=out.filter(x=>isCaseHighArticle(x, prefix?activeCases():globalCases()));
  const search=get("search").toLowerCase();
  if(search)out=out.filter(x=>[getTitle(x),getSource(x),x.region,x.polres,getLocality(x),getCategory(x),getScope(x)].filter(Boolean).join(" ").toLowerCase().includes(search));
  if(get("region")!=="all")out=out.filter(x=>getLocality(x)===get("region"));
  if(get("polres")!=="all")out=out.filter(x=>String(x.polres||"")===get("polres"));
  if(get("priority")!=="all")out=out.filter(x=>getPriority(x)===get("priority"));
  if(get("scope")!=="all")out=out.filter(x=>getScope(x)===get("scope"));
  if(get("category")!=="all")out=out.filter(x=>getCategory(x)===get("category"));
  return out;
}

function getRelevantCases(items,cases,mode,from,to,region,polres){
  const ids=new Set(items.map(x=>x.case_id).filter(Boolean));
  let result=cases.filter(c=>ids.has(c.case_id));
  result=result.filter(c=>{const d=dateKey(c.last_detected_at||c.last_seen||c.updated_at||c.created_at); return (!from||d>=from)&&(!to||d<=to);});
  if(mode==="high")result=result.filter(c=>getPriority(c)==="high");
  if(mode==="jatim")result=result.filter(c=>c.is_jatim!==false && !!getLocality(c));
  if(region && region!=="all")result=result.filter(c=>getLocality(c)===region);
  if(polres && polres!=="all")result=result.filter(c=>String(c.polres||"")===polres);
  return result.sort((a,b)=>priorityRank(b.priority)-priorityRank(a.priority)||new Date(b.last_detected_at||b.last_seen||0)-new Date(a.last_detected_at||a.last_seen||0));
}

function renderMonitoring(){
  syncModeButtons();
  populateMonitoringFilters();
  const items=applyCommonFilters(newsData,monitoringMode);
  const {from,to}=currentDateBounds();
  const cases=getRelevantCases(items,globalCases(),monitoringMode,from,to,$("region")?.value||"all",$("polres")?.value||"all");
  $("resultCount").textContent=`${number(items.length)} berita · ${number(cases.length)} case`;
  $("resultContext").textContent=`${from||"awal"}${to?` s/d ${to}`:" s/d sekarang"}`;
  $("monitoringContextText").textContent=from||to?`Rentang ${formatDate(from||to)}${to?` — ${formatDate(to)}`:""}.`:`Data hari ini.`;
  const caseTarget=$("monitoringCases");
  caseTarget.innerHTML=cases.length?`<div class="subsection-head"><div><h3>Case / Incident</h3><div class="muted">Prioritas Case berlaku untuk incident, bukan setiap artikel.</div></div></div><div class="case-grid">${cases.map((c,i)=>caseCard(c,i+1)).join("")}</div>`:`<div class="case-empty">Tidak ada Case yang memenuhi filter.</div>`;
  bindCaseClicks(caseTarget);
  const list=$("list");
  list.innerHTML=items.length?items.slice().sort((a,b)=>new Date(getItemDate(b)||0)-new Date(getItemDate(a)||0)).map(articleCard).join(""):`<div class="empty">Tidak ada berita yang cocok dengan filter.</div>`;
  bindArticleClicks(list);
}

function syncModeButtons(){document.querySelectorAll(".mode-tab[data-mode]").forEach(b=>b.classList.toggle("active",b.dataset.mode===monitoringMode));}
function setQuickDate(days){if(days==="all"){$("dateFrom").value="";$("dateTo").value="";}else if(days==="today"){setDefaultTodayRange();}else{const end=new Date(todayData?.date||new Date());const start=new Date(end);start.setDate(start.getDate()-(Number(days)-1));$("dateFrom").value=dateKey(start);$("dateTo").value=todayData?.date||dateKey(end);}populateMonitoringFilters();renderMonitoring();}

document.querySelectorAll("[data-mode]").forEach(b=>b.addEventListener("click",()=>{monitoringMode=b.dataset.mode;syncModeButtons();renderMonitoring();}));
document.querySelectorAll("[data-quick-date]").forEach(b=>b.addEventListener("click",()=>setQuickDate(b.dataset.quickDate)));
["search","region","polres","priority","scope","category","dateFrom","dateTo"].forEach(id=>{$(id)?.addEventListener("input",()=>{populateMonitoringFilters();renderMonitoring();});$(id)?.addEventListener("change",()=>{populateMonitoringFilters();renderMonitoring();});});
$("clearFilters")?.addEventListener("click",()=>{["search"].forEach(id=>$(id).value="");$("region").value="all";$("polres").value="all";$("priority").value="all";$("scope").value="all";$("category").value="all";setDefaultTodayRange();monitoringMode="all";syncModeButtons();populateMonitoringFilters();renderMonitoring();});

function openDrawer(){ $("detailDrawer").classList.add("open");$("detailDrawer").setAttribute("aria-hidden","false");$("drawerOverlay").classList.remove("hidden"); }
function closeDrawer(){ $("detailDrawer").classList.remove("open");$("detailDrawer").setAttribute("aria-hidden","true");$("drawerOverlay").classList.add("hidden"); }
$("drawerClose")?.addEventListener("click",closeDrawer);$("drawerOverlay")?.addEventListener("click",closeDrawer);document.addEventListener("keydown",e=>{if(e.key==="Escape")closeDrawer();});

function openArticleDrawer(article){
  if(!article)return;
  const c=getCaseById(article.case_id), cHigh=c&&getPriority(c)==="high", url=normalizeUrl(article.url);
  $("drawerEyebrow").textContent="DETAIL BERITA";
  $("drawerContent").innerHTML=`<div class="drawer-title">${escapeHtml(getTitle(article))}</div><div class="drawer-meta">${escapeHtml(getSource(article))} · ${escapeHtml(formatDateTime(getItemDate(article)))}</div><div class="drawer-pills"><span class="pill ${escapeHtml(getPriority(article))}">ARTIKEL ${escapeHtml(getPriority(article).toUpperCase())}</span>${c?`<span class="pill ${cHigh?'high':''}">CASE ${escapeHtml(cHigh?'HIGH':'TERKAIT')}</span>`:`<span class="pill">BELUM TERKAIT CASE</span>`}</div><div class="detail-grid"><div><span>Wilayah</span><strong>${escapeHtml(getLocality(article)||article.region||"Indonesia")}</strong></div><div><span>Polres</span><strong>${escapeHtml(article.polres||"-")}</strong></div><div><span>Scope</span><strong>${escapeHtml(getScope(article))}</strong></div><div><span>Kategori</span><strong>${escapeHtml(getCategory(article))}</strong></div><div><span>Publikasi</span><strong>${escapeHtml(formatDateTime(article.published_at||article.collected_at))}</strong></div><div><span>Ditemukan</span><strong>${escapeHtml(formatDateTime(article.collected_at))}</strong></div></div><div class="drawer-actions">${url?`<a class="primary-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Buka Berita Asli ↗</a>`:""}${c?`<button class="secondary" id="drawerCaseButton">Lihat Case & Semua Sumber</button>`:""}</div>`;
  openDrawer();
  $("drawerCaseButton")?.addEventListener("click",()=>openCaseDrawer(c));
}

function caseArticles(c, items){const ids=getCaseArticleIds(c); return items.filter(x=>ids.has(x.id));}
function openCaseDrawer(c){
  if(!c)return;
  const items=caseArticles(c, activeNews()), p=getPriority(c), score=c.priority_score!=null?`${number(c.priority_score)}/100`:"-";
  const reasons=Array.isArray(c.priority_reasons)?c.priority_reasons:[];
  $("drawerEyebrow").textContent="CASE / INCIDENT";
  $("drawerContent").innerHTML=`<div class="drawer-title">${escapeHtml(c.title||"Case")}</div><div class="drawer-meta">${escapeHtml(getLocality(c)||c.region||"Indonesia")} · ${number(c.article_count||items.length)} sumber</div><div class="case-detail-head"><span class="pill ${escapeHtml(p)}">${escapeHtml(p.toUpperCase())}</span><strong>${escapeHtml(score)}</strong></div>${reasons.length?`<div class="priority-reasons"><h4>Alasan prioritas</h4><ul>${reasons.map(r=>`<li>${escapeHtml(r)}</li>`).join("")}</ul></div>`:""}<div class="source-list"><h4>Seluruh sumber terkait</h4>${items.length?items.map((a,i)=>{const u=normalizeUrl(a.url);return `<div class="source-row"><div><b>${number(i+1)}. ${escapeHtml(getSource(a))}</b><div>${escapeHtml(getTitle(a))}</div><small>${escapeHtml(formatDateTime(getItemDate(a)))}</small></div>${u?`<a href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer">Buka ↗</a>`:""}</div>`}).join(""):`<div class="empty">Sumber detail tidak tersedia pada dataset aktif.</div>`}</div>`;
  openDrawer();
}

function initMap(){if(map||!window.L||!$("jatimMap"))return;map=L.map("jatimMap",{zoomControl:true,tap:true}).setView([-7.75,112.45],8);L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:18,attribution:"&copy; OpenStreetMap contributors"}).addTo(map);}
function renderMap(items){if(!map)return;mapMarkers.forEach(m=>m.remove());mapMarkers=[];const groups=new Map();items.filter(isJatim).forEach(item=>{const r=getLocality(item);if(!r||!JATIM_COORDS[r])return;if(!groups.has(r))groups.set(r,{name:r,items:[],cases:new Set(),high:0,medium:0});const g=groups.get(r);g.items.push(item);if(item.case_id)g.cases.add(item.case_id);});const cMap=new Map(globalCases().map(c=>[c.case_id,c]));groups.forEach(g=>g.cases.forEach(id=>{const c=cMap.get(id);if(c?.priority==='high')g.high++;else if(c?.priority==='medium')g.medium++;}));$("mapCount").textContent=`${number(groups.size)} lokasi`;const bounds=[];groups.forEach(g=>{const coords=JATIM_COORDS[g.name];bounds.push(coords);const level=g.high?'high':g.medium?'medium':'low';const size=Math.min(42,22+Math.floor(g.items.length/2)*2);const icon=L.divIcon({className:"",html:`<div class="pnm-marker ${level}" style="width:${size}px;height:${size}px">${number(g.items.length)}</div>`,iconSize:[size,size],iconAnchor:[size/2,size/2]});const m=L.marker(coords,{icon}).addTo(map);const cases=[...g.cases].map(id=>cMap.get(id)).filter(Boolean).sort((a,b)=>priorityRank(b.priority)-priorityRank(a.priority));const top=g.items.slice().sort((a,b)=>new Date(getItemDate(b)||0)-new Date(getItemDate(a)||0)).slice(0,4);m.bindPopup(`<div class="map-popup"><strong>${escapeHtml(g.name)}</strong><div>${number(g.items.length)} berita · ${number(g.cases.size)} case</div>${g.high?`<div class="map-popup-high">High case: ${number(g.high)}</div>`:""}<div class="map-popup-list">${cases.slice(0,3).map(c=>`<div>• ${escapeHtml(c.title)}</div>`).join("")||top.map(a=>`<div>• ${escapeHtml(getTitle(a))}</div>`).join("")}</div><button class="map-open-region" data-region="${escapeHtml(g.name)}">Buka monitoring wilayah →</button></div>`);m.on("popupopen",()=>{document.querySelectorAll(".map-open-region").forEach(b=>b.onclick=()=>{showView("monitoring");monitoringMode="jatim";syncModeButtons();$("region").value=g.name;renderMonitoring();});});mapMarkers.push(m);});if(bounds.length)map.fitBounds(bounds,{padding:[25,25],maxZoom:9});setTimeout(()=>map.invalidateSize(),80);}

async function loadArchive(date){try{activeArchive=await fetchJson(`data/archive/${encodeURIComponent(date)}.json`);openArchiveDetail();}catch(e){console.error(e);alert("Snapshot arsip tidak dapat dibuka.");}}
function renderArchiveList(){const t=$("archiveList");if(!t)return;if(!archiveFiles.length){t.innerHTML=`<div class="empty">Belum ada arsip.</div>`;return;}t.innerHTML=archiveFiles.map(d=>`<button class="archive-item" data-archive-date="${escapeHtml(d)}"><span><strong>${escapeHtml(formatDate(d))}</strong><small>Snapshot monitoring</small></span><b>→</b></button>`).join("");t.querySelectorAll("[data-archive-date]").forEach(b=>b.addEventListener("click",()=>loadArchive(b.dataset.archiveDate)));}

function populateArchiveFilters(){const items=activeArchive?.news?.items||[];const current={r:$("archiveRegion").value,p:$("archivePolres").value,c:$("archiveCategory").value};populateSelect($("archiveRegion"),"Semua Wilayah",unique(items.filter(isJatim).map(getLocality).sort()),current.r);populateSelect($("archivePolres"),"Semua Polres Terdeteksi",unique(items.map(x=>x.polres).filter(Boolean).sort()),current.p);populateSelect($("archiveCategory"),"Semua Kategori",unique(items.map(getCategory).sort()),current.c);}
function getArchiveHighIds(){return getCasePriorityIds(activeArchive?.cases?.items||[]);}
function renderArchiveNews(){if(!activeArchive)return;const items=activeArchive.news?.items||[], cases=activeArchive.cases?.items||[];let results=items.filter(i=>{if(archiveMode==="jatim")return isJatim(i);if(archiveMode==="high")return !!i.case_id&&getArchiveHighIds().has(i.case_id);return true;});const s=$("archiveSearch").value.trim().toLowerCase(),r=$("archiveRegion").value,p=$("archivePolres").value,pr=$("archivePriority").value,sc=$("archiveScope").value,cat=$("archiveCategory").value;if(s)results=results.filter(x=>[getTitle(x),getSource(x),x.region,x.polres,getLocality(x),getCategory(x),getScope(x)].filter(Boolean).join(" ").toLowerCase().includes(s));if(r!=="all")results=results.filter(x=>getLocality(x)===r);if(p!=="all")results=results.filter(x=>String(x.polres||"")===p);if(pr!=="all")results=results.filter(x=>getPriority(x)===pr);if(sc!=="all")results=results.filter(x=>getScope(x)===sc);if(cat!=="all")results=results.filter(x=>getCategory(x)===cat);const date=activeArchive.date;$("archiveResultCount").textContent=`${number(results.length)} hasil`;$("archiveResultContext").textContent=`Snapshot ${formatDate(date)}`;const highCases=cases.filter(c=>getPriority(c)==="high");$("archiveCases").textContent=number(cases.length);$("archiveNews").textContent=number(items.length);$("archiveJatim").textContent=number(items.filter(isJatim).length);$("archiveHigh").textContent=number(highCases.length);const target=$("archiveNewsList");target.innerHTML=results.length?results.map(articleCard).join(""):`<div class="empty">Tidak ada berita yang cocok.</div>`;bindArticleClicks(target);const ct=$("archiveCases");const rel=cases.filter(c=>results.some(i=>i.case_id===c.case_id)).sort((a,b)=>priorityRank(b.priority)-priorityRank(a.priority)||new Date(b.last_seen||0)-new Date(a.last_seen||0));ct.innerHTML=rel.length?`<div class="subsection-head"><div><h3>Case / Incident</h3><div class="muted">Case pada snapshot ini.</div></div></div><div class="case-grid">${rel.map((c,i)=>caseCard(c,i+1)).join("")}</div>`:"";bindCaseClicks(ct);}
function openArchiveDetail(){if(!activeArchive)return;$("archiveListPanel").classList.add("hidden");$("archiveDetail").classList.remove("hidden");$("archiveTitle").textContent=formatDate(activeArchive.date);$("archiveUpdated").textContent="Update: "+formatDateTime(activeArchive.last_successful_update||activeArchive.updated_at);archiveMode="all";document.querySelectorAll("[data-archive-mode]").forEach(b=>b.classList.toggle("active",b.dataset.archiveMode==="all"));populateArchiveFilters();renderArchiveNews();}
function closeArchiveDetail(){activeArchive=null;$("archiveDetail")?.classList.add("hidden");$("archiveListPanel")?.classList.remove("hidden");}
$("archiveBack")?.addEventListener("click",()=>{closeArchiveDetail();showView("archive");});
document.querySelectorAll("[data-archive-mode]").forEach(b=>b.addEventListener("click",()=>{archiveMode=b.dataset.archiveMode;document.querySelectorAll("[data-archive-mode]").forEach(x=>x.classList.toggle("active",x.dataset.archiveMode===archiveMode));renderArchiveNews();}));
["archiveSearch","archiveRegion","archivePolres","archivePriority","archiveScope","archiveCategory"].forEach(id=>{$(id)?.addEventListener("input",renderArchiveNews);$(id)?.addEventListener("change",renderArchiveNews);});
$("archiveClear")?.addEventListener("click",()=>{$("archiveSearch").value="";$("archiveRegion").value="all";$("archivePolres").value="all";$("archivePriority").value="all";$("archiveScope").value="all";$("archiveCategory").value="all";renderArchiveNews();});
$("refresh")?.addEventListener("click",()=>loadAllData());
window.addEventListener("resize",()=>setTimeout(()=>map?.invalidateSize(),80));

showView("dashboard");
loadAllData();
