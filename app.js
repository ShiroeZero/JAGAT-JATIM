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
let archiveMode = "all";
let activeArchive = null;
let map = null;
let mapMarkers = [];
let initialized = false;

const $ = (id) => document.getElementById(id);
const number = (v) => Number.isFinite(Number(v)) ? Number(v).toLocaleString("id-ID") : "0";

function escapeHtml(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeUrl(v) {
  const s = String(v || "").trim();
  return /^https?:\/\//i.test(s) ? s : "";
}

function parseDate(v) {
  if (!v) return null;
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? null : d;
}

function dateKey(v) {
  const d = parseDate(v);
  return d ? d.toLocaleDateString("en-CA", { timeZone: "Asia/Jakarta" }) : "";
}

function formatDate(v) {
  const d = parseDate(v);
  if (!d) return String(v || "-");
  return d.toLocaleDateString("id-ID", { day: "2-digit", month: "long", year: "numeric" });
}

function formatDateTime(v) {
  const d = parseDate(v);
  if (!d) return String(v || "-");
  return `${d.toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" })} ${d.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", hour12: false })} WIB`;
}

function getTitle(x) { return x?.title || "Tanpa judul"; }
function getSource(x) { return x?.source || x?.publisher || "Sumber tidak diketahui"; }
function getItemDate(x) { return x?.collected_at || x?.detected_at || x?.published_at || x?.last_detected_at || ""; }
function getPriority(x) { return String(x?.priority || "low").toLowerCase(); }
function getAttentionScore(x) {
  const n = Number(x?.attention_score ?? x?.priority_score);
  if (Number.isFinite(n)) return Math.max(0, Math.min(100, n));
  return ({ high: 75, medium: 50, low: 20 })[getPriority(x)] || 20;
}
function attentionBand(score) {
  const n = getAttentionScore({ attention_score: score });
  if (n <= 24) return "Rendah";
  if (n <= 49) return "Perlu Perhatian";
  if (n <= 69) return "Atensi";
  if (n <= 84) return "Atensi Tinggi";
  return "Kritis";
}
function attentionClass(score) {
  const n = getAttentionScore({ attention_score: score });
  if (n <= 24) return "low";
  if (n <= 49) return "medium";
  if (n <= 69) return "attention";
  return "high";
}
function getEffectiveAttentionScore(article, cases = activeCases()) {
  const related = article?.case_id ? getCaseById(article.case_id, cases) : null;
  return getAttentionScore(related || article);
}
function getEffectiveAttentionLabel(article, cases = activeCases()) {
  const related = article?.case_id ? getCaseById(article.case_id, cases) : null;
  return related?.attention_label || attentionBand(getEffectiveAttentionScore(article, cases));
}
function attentionBandValue(value) {
  return String(value || "");
}
function matchesAttentionBand(article, value, cases = activeCases()) {
  if (!value || value === "all") return true;
  const n = getEffectiveAttentionScore(article, cases);
  const [lo, hi] = value.split("-").map(Number);
  return Number.isFinite(lo) && Number.isFinite(hi) && n >= lo && n <= hi;
}
function getScope(x) { return String(x?.scope || "neutral").toLowerCase(); }
function getCategory(x) { return x?.category || "NETRAL / LAINNYA"; }
function isJatim(x) { return x?.is_jatim === true || String(x?.region || "").toLowerCase() === "jawa timur"; }
function priorityRank(v) { return ({ high: 3, medium: 2, low: 1 })[String(v || "low").toLowerCase()] || 1; }
function unique(a) { return [...new Set((a || []).filter(Boolean))]; }

function setStatus(text, ok) {
  if ($("statusText")) $("statusText").textContent = text;
  if ($("statusDot")) $("statusDot").style.background = ok ? "var(--ok)" : "var(--danger)";
}

async function fetchJson(url) {
  const r = await fetch(`${url}?t=${Date.now()}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url} HTTP ${r.status}`);
  return r.json();
}

function todayItems() {
  return Array.isArray(todayData?.news?.items) ? todayData.news.items : [];
}

function globalCases() {
  return Array.isArray(caseData?.cases) ? caseData.cases : [];
}

function activeNews() {
  return activeArchive ? (activeArchive.news?.items || []) : newsData;
}

function activeCases() {
  return activeArchive ? (activeArchive.cases?.items || []) : globalCases();
}

function caseMap(cases = activeCases()) {
  return new Map(cases.map(c => [c.case_id, c]));
}

function getCaseById(id, cases = activeCases()) {
  return id ? (cases.find(c => c.case_id === id) || null) : null;
}

function getArticleById(id, items = activeNews()) {
  return id ? (items.find(n => n.id === id) || null) : null;
}

function localityFromPolres(polres) {
  const text = String(polres || "").toLowerCase();
  for (const name of Object.keys(JATIM_COORDS)) {
    if (text.includes(name.toLowerCase())) return name;
  }
  return "";
}

function getLocality(x) {
  if (x?.locality) return String(x.locality);
  const fromPolres = localityFromPolres(x?.polres);
  return fromPolres || "";
}

function getFilterArea(x) {
  if (x?.region === "BELUM TERPETAKAN" || x?.is_jatim == null) return "BELUM TERPETAKAN";
  if (!isJatim(x)) return "LUAR JATIM";
  return String(x?.locality || getLocality(x) || "Jawa Timur (Umum)");
}

function filterLocationValue(x) {
  if (x?.region === "BELUM TERPETAKAN" || x?.is_jatim == null) return "__UNKNOWN__";
  if (isJatim(x)) return "__JATIM__";
  return "__OUTSIDE__";
}

function getCasePriorityIds(cases = activeCases()) {
  return new Set(cases.filter(c => getPriority(c) === "high").map(c => c.case_id));
}

function getEffectivePriority(article, cases = activeCases()) {
  const related = article?.case_id ? getCaseById(article.case_id, cases) : null;
  return related ? getPriority(related) : getPriority(article);
}

function isCaseHighArticle(article, cases = activeCases()) {
  return getEffectivePriority(article, cases) === "high";
}

function caseArticleIds(c) {
  return new Set(c?.article_ids || (c?.articles || []).map(a => a.id).filter(Boolean));
}

function caseArticles(c, items = activeNews()) {
  const ids = caseArticleIds(c);
  if (ids.size) return items.filter(x => ids.has(x.id));
  if (Array.isArray(c?.articles)) return c.articles;
  return [];
}

async function loadAllData() {
  setStatus("Memuat data...", false);
  try {
    const [today, cases, news, archiveIndex] = await Promise.all([
      fetchJson(TODAY_URL),
      fetchJson(CASE_URL),
      fetchJson(NEWS_URL),
      fetchJson(ARCHIVE_INDEX_URL)
    ]);

    todayData = today || {};
    caseData = cases || { cases: [] };
    newsData = Array.isArray(news) ? news : (news?.items || []);
    archiveFiles = Array.isArray(archiveIndex) ? archiveIndex : (archiveIndex?.files || []);

    initializeMonitoringDates(true);
    renderAll();
    setStatus("Data aktif", true);
  } catch (e) {
    console.error(e);
    setStatus("Gagal memuat data", false);
    if ($("lastUpdated")) $("lastUpdated").textContent = "Data gagal dimuat";
  }
}

function initializeMonitoringDates(force = false) {
  if (!$('dateFrom') || !$('dateTo') || !todayData?.date) return;
  if (force || (!$('dateFrom').value && !$('dateTo').value)) {
    $('dateFrom').value = todayData.date;
    $('dateTo').value = todayData.date;
  }
}

function currentDateBounds() {
  return {
    from: $("dateFrom")?.value || "",
    to: $("dateTo")?.value || ""
  };
}

function selectBaseNewsDataset() {
  return activeArchive ? (activeArchive.news?.items || []) : newsData;
}

function filterByDate(items, from, to) {
  return items.filter(item => {
    const d = dateKey(getItemDate(item));
    if (!d) return false;
    if (from && d < from) return false;
    if (to && d > to) return false;
    return true;
  });
}

function showView(view) {
  currentView = view;

  if (view !== "archive") {
    activeArchive = null;
  }

  document.querySelectorAll(".view").forEach(section => {
    const active = section.id === `${view}View`;
    section.hidden = !active;
    section.classList.toggle("hidden", !active);
  });

  document.querySelectorAll("[data-view]").forEach(button => {
    button.classList.toggle("active", button.dataset.view === view);
  });

  const titles = {
    dashboard: "Dashboard",
    monitoring: activeArchive ? "Monitoring Arsip" : "Monitoring",
    reports: "Laporan",
    archive: "Arsip"
  };
  if ($("pageTitle")) $("pageTitle").textContent = titles[view] || "PNM";
  if ($("todayDate")) $("todayDate").textContent = activeArchive ? `Snapshot ${formatDate(activeArchive.date)}` : formatDate(todayData?.date);

  if (view !== "archive") {
    activeArchive = null;
    closeArchiveDetail();
  }

  if (view === "dashboard") {
    renderDashboard();
    setTimeout(() => map?.invalidateSize(), 100);
  }
  if (view === "monitoring") renderMonitoring();
  if (view === "archive") {
    if (activeArchive) openArchiveDetail();
    else closeArchiveDetail(false);
    renderArchiveList();
  }
}

function renderHeader() {
  if (!todayData) return;
  const items = todayJatimItems();
  const cases = todayJatimCaseSet();
  const negative = items.filter(x => getScope(x) === "negative").length;
  const caseScope = items.filter(x => getScope(x) === "case").length;
  const positive = items.filter(x => getScope(x) === "positive").length;
  const neutral = items.length - negative - caseScope - positive;
  const high = cases.filter(c => getPriority(c) === "high").length;

  if ($("todayDate")) $("todayDate").textContent = formatDate(todayData.date);
  if ($("lastUpdated")) $("lastUpdated").textContent = `Update terakhir: ${formatDateTime(todayData.last_successful_update || todayData.updated_at)}`;
  if ($("sTotal")) $("sTotal").textContent = number(items.length);
  if ($("sCaseToday")) $("sCaseToday").textContent = number(cases.length);
  if ($("sHigh")) $("sHigh").textContent = number(high);
  if ($("sNegative")) $("sNegative").textContent = number(negative);
  if ($("sCaseUngkap")) $("sCaseUngkap").textContent = number(caseScope);
  if ($("sPositive")) $("sPositive").textContent = number(positive);
  if ($("sNeutral")) $("sNeutral").textContent = number(neutral);
  const regionCount = unique(items.map(getFilterArea).filter(x => x && x !== "LUAR JATIM" && x !== "BELUM TERPETAKAN")).length;
  if ($("sRegions")) $("sRegions").textContent = number(regionCount);
}


function renderAll() {
  renderHeader();
  renderDashboard();
  populateMonitoringFilters();
  renderMonitoring();
  renderArchiveList();
}

function todayJatimItems() {
  return todayItems().filter(isJatim);
}

function todayJatimCaseSet() {
  const ids = new Set(todayJatimItems().map(item => item.case_id).filter(Boolean));
  return globalCases().filter(c => ids.has(c.case_id));
}

function renderDashboard() {
  const items = todayJatimItems();
  renderRegionsToday(items);
  renderCategories(items);
  renderLatest(items);
  renderLatestCases(items);
  initMap();
  renderMap(items);
}

function renderRegionsToday(items) {
  const target = $("regionToday");
  if (!target) return;
  const jatim = items.filter(isJatim);
  const concrete = new Map();
  let general = 0;
  jatim.forEach(item => {
    const locality = String(item.locality || "").trim();
    if (!locality) {
      general += 1;
      return;
    }
    concrete.set(locality, (concrete.get(locality) || 0) + 1);
  });

  const cases = todayJatimCaseSet();
  const caseByLocality = new Map();
  cases.forEach(c => {
    const loc = String(c.locality || getLocality(c) || "").trim();
    if (!loc) return;
    if (!caseByLocality.has(loc)) caseByLocality.set(loc, { total: 0, high: 0 });
    caseByLocality.get(loc).total += 1;
    if (getPriority(c) === "high") caseByLocality.get(loc).high += 1;
  });

  const rows = [...concrete.entries()].sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0]));
  const total = jatim.length;
  const parent = `
    <button class="region-parent" type="button" data-region-parent="Jawa Timur">
      <span><strong>Jawa Timur</strong><small>${number(total)} berita · ${number(cases.length)} kasus</small></span>
      <span class="region-parent-total">${number(rows.length)} wilayah <b>→</b></span>
    </button>`;

  const children = rows.map(([name, count]) => {
    const meta = caseByLocality.get(name) || { total: 0, high: 0 };
    return `<button class="region-row region-child" type="button" data-region="${escapeHtml(name)}">
      <span><strong>${escapeHtml(name)}</strong><small>${number(count)} berita · ${number(meta.total)} kasus</small></span>
      <span class="region-right">${meta.high ? `<span class="pill high">TINGGI ${number(meta.high)}</span>` : `<span class="pill low">TERPANTAU</span>`}<b>→</b></span>
    </button>`;
  }).join("");

  const generic = general
    ? `<button class="region-row region-child region-general" type="button" data-region="Jawa Timur (Umum)">
         <span><strong>Jawa Timur (Umum)</strong><small>${number(general)} berita tanpa kota/Polres spesifik</small></span>
         <span class="region-right"><b>→</b></span>
       </button>`
    : "";

  target.innerHTML = jatim.length ? `${parent}<div class="region-children">${children}${generic}</div>` : `<div class="empty">Tidak ada berita Jawa Timur hari ini.</div>`;

  target.querySelectorAll("[data-region]").forEach(btn => btn.addEventListener("click", () => {
    openRegionDrawer(btn.dataset.region, jatim);
  }));
  target.querySelectorAll("[data-region-parent]").forEach(btn => btn.addEventListener("click", () => {
    openRegionDrawer("Jawa Timur", jatim);
  }));
}

function openRegionDrawer(name, items) {
  const selected = String(name || "");
  let regionItems = items.filter(isJatim);
  if (selected !== "Jawa Timur") {
    regionItems = regionItems.filter(item => getFilterArea(item) === selected);
  }
  const allCases = globalCases().filter(c => regionItems.some(item => item.case_id === c.case_id));
  const title = selected === "Jawa Timur" ? "Seluruh Berita Jawa Timur" : `Berita ${selected}`;
  const grouped = new Map();
  regionItems.slice().sort((a,b)=>new Date(getItemDate(b)||0)-new Date(getItemDate(a)||0)).forEach(item => {
    const cid = item.case_id || `article-${item.id}`;
    if (!grouped.has(cid)) grouped.set(cid, []);
    grouped.get(cid).push(item);
  });

  $("drawerEyebrow").textContent = "WILAYAH";
  $("drawerContent").innerHTML = `
    <div class="drawer-title">${escapeHtml(title)}</div>
    <div class="drawer-meta">${number(regionItems.length)} berita · ${number(allCases.length)} kasus · hari ini</div>
    <div class="drawer-pills"><span class="pill low">JAWA TIMUR</span></div>
    <div class="source-list">
      <h4>Seluruh berita (${number(regionItems.length)})</h4>
      ${regionItems.length ? regionItems.map(item => {
        const url = normalizeUrl(item.url);
        return `<div class="source-row">
          <div><b>${escapeHtml(getTitle(item))}</b><div>${escapeHtml(getSource(item))}</div><small>${escapeHtml(formatDateTime(getItemDate(item)))} · ${escapeHtml(getCategory(item))}</small></div>
          <span class="source-row-actions">
            ${copyButtonMarkup(url)}
            ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="open-link-btn"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Buka</a>` : `<span class="muted">Tanpa tautan</span>`}
          </span>
        </div>`;
      }).join("") : `<div class="empty">Tidak ada berita pada wilayah ini.</div>`}
    </div>`;
  openDrawer();
}


function renderCategories(items) {
  const target = $("categories");
  if (!target) return;
  const c = { Negatif: 0, "Ungkap Kasus": 0, Positif: 0, Netral: 0 };
  items.forEach(item => {
    const s = getScope(item);
    if (s === "negative") c.Negatif++;
    else if (s === "case") c["Ungkap Kasus"]++;
    else if (s === "positive") c.Positif++;
    else c.Netral++;
  });
  const rows = Object.entries(c);
  const max = Math.max(...rows.map(x => x[1]), 1);
  target.innerHTML = rows.map(([label, count]) => `<div class="bar"><div class="bar-top"><span>${escapeHtml(label)}</span><strong>${number(count)}</strong></div><div class="bar-bg"><div class="bar-fill" style="width:${(count / max) * 100}%"></div></div></div>`).join("");
}

function articleCard(item) {
  const c = getCaseById(item.case_id);
  const attention = getEffectiveAttentionScore(item, activeCases());
  const attentionLabel = getEffectiveAttentionLabel(item, activeCases());
  const aClass = attentionClass(attention);
  const url = normalizeUrl(item.url);
  return `<article class="news-card clickable" data-article-id="${escapeHtml(item.id)}">
    <div class="news-card-top">
      <div>
        <div class="news-card-meta">${escapeHtml(getSource(item))} · ${escapeHtml(getFilterArea(item))} · ${escapeHtml(formatDateTime(getItemDate(item)))}</div>
        <h3>${escapeHtml(getTitle(item))}</h3>
        <div class="news-card-meta">${escapeHtml(getCategory(item))}${c ? ` · Terkait ${escapeHtml(c.attention_label || "Kasus")}` : " · Belum terkait Kasus"}</div>
      </div>
      <div class="badges">
        <span class="pill ${aClass}">ATENSI ${number(attention)}/100 · ${escapeHtml(attentionLabel)}</span>
        ${c ? `<span class="pill ${attentionClass(getAttentionScore(c))}">KASUS ${number(getAttentionScore(c))}/100</span>` : `<span class="pill">${escapeHtml(getScope(item).toUpperCase())}</span>`}
      </div>
    </div>
    <div class="card-actions-bottom">
      <span class="card-action">Klik untuk detail${url ? " · sumber tersedia" : ""}</span>
      <span class="card-actions-buttons">
        ${copyButtonMarkup(url)}
        ${url ? `<a class="open-link-btn" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Buka</a>` : ""}
      </span>
    </div>
  </article>`;
}

function caseCard(c, index) {
  const attention = getAttentionScore(c);
  const attentionLabel = c.attention_label || attentionBand(attention);
  const aClass = attentionClass(attention);
  const locality = getLocality(c);
  const firstSourceUrl = normalizeUrl((c.articles || []).find(a => normalizeUrl(a.url))?.url);
  return `<article class="case-card clickable" data-case-id="${escapeHtml(c.case_id)}">
    <div class="case-card-top"><span class="case-id">KASUS ${String(index).padStart(2, "0")}</span><span class="pill ${aClass}">ATENSI ${number(attention)}/100 · ${escapeHtml(attentionLabel)}</span></div>
    <strong>${escapeHtml(c.title || "Kasus")}</strong>
    <div class="news-card-meta">${escapeHtml(locality || c.region || "Belum Terpetakan")} · ${number(c.article_count || (c.articles || []).length)} sumber · update ${escapeHtml(formatDateTime(c.last_detected_at || c.last_seen || c.updated_at))}</div>
    <div class="card-actions-bottom">
      <span class="card-action">Klik untuk melihat seluruh sumber →</span>
      <span class="card-actions-buttons">
        ${copyButtonMarkup(firstSourceUrl, "Salin")}
        ${firstSourceUrl ? `<a class="open-link-btn" href="${escapeHtml(firstSourceUrl)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Sumber</a>` : ""}
      </span>
    </div>
  </article>`;
}

function renderLatest(items) {
  const target = $("latest");
  if (!target) return;
  const latest = items.slice().sort((a, b) => new Date(getItemDate(b) || 0) - new Date(getItemDate(a) || 0)).slice(0, 8);
  target.innerHTML = latest.length ? latest.map(articleCard).join("") : `<div class="empty">Belum ada berita hari ini.</div>`;
  bindArticleClicks(target, items);
  bindCopyButtons(target);
}

function renderLatestCases(items = todayJatimItems()) {
  const target = $("latestCases");
  if (!target) return;
  const ids = new Set(items.map(item => item.case_id).filter(Boolean));
  const cases = globalCases()
    .filter(c => ids.has(c.case_id))
    .slice()
    .sort((a, b) => getAttentionScore(b) - getAttentionScore(a) || new Date(b.last_detected_at || b.last_seen || 0) - new Date(a.last_detected_at || a.last_seen || 0))
    .slice(0, 6);
  target.innerHTML = cases.length ? cases.map((c, i) => caseCard(c, i + 1)).join("") : `<div class="empty">Belum ada Kasus Jatim hari ini.</div>`;
  bindCaseClicks(target, globalCases(), newsData);
}


function currentMonitoringBase() {
  return activeArchive ? (activeArchive.news?.items || []) : newsData;
}

function populateSelect(el, first, values, selected) {
  if (!el) return;
  el.innerHTML = `<option value="all">${escapeHtml(first)}</option>` + values.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("");
  if (values.includes(selected)) el.value = selected;
}

function getFacetItems(excludeId) {
  const { from, to } = currentDateBounds();
  let items = filterByDate(currentMonitoringBase(), from, to);
  const search = ($("search")?.value || "").trim().toLowerCase();
  const location = $("region")?.value || "all";
  const polres = $("polres")?.value || "all";
  const attention = $("priority")?.value || "all";
  const scope = $("scope")?.value || "all";
  const category = $("category")?.value || "all";
  const cases = activeCases();

  if (search && excludeId !== "search") {
    items = items.filter(x => [getTitle(x), getSource(x), getFilterArea(x), x.polres, getCategory(x), getScope(x), x.issue_type, x.issue_subtype].filter(Boolean).join(" ").toLowerCase().includes(search));
  }
  if (excludeId !== "region" && location !== "all") {
    if (location === "__JATIM__") items = items.filter(isJatim);
    else if (location === "__OUTSIDE__") items = items.filter(x => x.region === "LUAR JATIM");
    else if (location === "__UNKNOWN__") items = items.filter(x => x.region === "BELUM TERPETAKAN" || x.is_jatim == null);
    else items = items.filter(x => getFilterArea(x) === location);
  }
  if (excludeId !== "polres" && polres !== "all") items = items.filter(x => String(x.polres || "") === polres);
  if (excludeId !== "priority" && attention !== "all") items = items.filter(x => matchesAttentionBand(x, attention, cases));
  if (excludeId !== "scope" && scope !== "all") items = items.filter(x => getScope(x) === scope);
  if (excludeId !== "category" && category !== "all") items = items.filter(x => getCategory(x) === category);
  return items;
}

function populateRegionFilter(items, selected) {
  const el = $("region");
  if (!el) return;
  const areas = unique(items.filter(isJatim).map(getFilterArea))
    .filter(Boolean)
    .sort((a,b) => {
      if (a === "Jawa Timur (Umum)") return -1;
      if (b === "Jawa Timur (Umum)") return 1;
      return a.localeCompare(b, "id");
    });
  const outside = items.some(x => x.region === "LUAR JATIM") || items.some(x => x.is_jatim === false);
  const unknown = items.some(x => x.region === "BELUM TERPETAKAN" || x.is_jatim == null);
  const opts = [
    `<option value="all">Semua Wilayah / Area</option>`,
    items.some(isJatim) ? `<option value="__JATIM__">Jawa Timur — semua wilayah</option>` : "",
    ...areas.map(a => `<option value="${escapeHtml(a)}">↳ ${escapeHtml(a)}</option>`),
    outside ? `<option value="__OUTSIDE__">Luar Jatim</option>` : "",
    unknown ? `<option value="__UNKNOWN__">Belum Terpetakan</option>` : ""
  ];
  el.innerHTML = opts.join("");
  if (["all","__JATIM__","__OUTSIDE__","__UNKNOWN__"].includes(selected) || areas.includes(selected)) el.value = selected;
}

function populateMonitoringFilters() {
  const location = $("region")?.value || "all";
  const polres = $("polres")?.value || "all";
  const attention = $("priority")?.value || "all";
  const scope = $("scope")?.value || "all";
  const category = $("category")?.value || "all";

  const base = getFacetItems("region");
  populateRegionFilter(base, location);

  const polresItems = getFacetItems("polres");
  const polresValues = unique(polresItems.filter(isJatim).map(x => x.polres).filter(Boolean)).sort((a,b) => a.localeCompare(b,"id"));
  populateSelect($("polres"), "Polres terdeteksi", polresValues, polres);

  // Priority filter is a stable scale, not a data-dependent list.
  const p = $("priority");
  if (p) {
    p.innerHTML = [
      ["all", "Semua Skala Atensi"],
      ["0-24", "0–24 · Rendah"],
      ["25-49", "25–49 · Perlu Perhatian"],
      ["50-69", "50–69 · Atensi"],
      ["70-84", "70–84 · Atensi Tinggi"],
      ["85-100", "85–100 · Kritis"],
    ].map(([v,l]) => `<option value="${v}">${l}</option>`).join("");
    p.value = ["all","0-24","25-49","50-69","70-84","85-100"].includes(attention) ? attention : "all";
  }

  const scopes = unique(getFacetItems("scope").map(getScope)).sort();
  const labels = { negative:"Negatif", case:"Ungkap Kasus", positive:"Positif", neutral:"Netral" };
  if ($("scope")) {
    $("scope").innerHTML = `<option value="all">Semua Jenis Berita</option>` + scopes.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(labels[v] || v)}</option>`).join("");
    if (scopes.includes(scope)) $("scope").value = scope;
  }

  const categories = unique(getFacetItems("category").map(getCategory)).sort((a,b) => a.localeCompare(b,"id"));
  populateSelect($("category"), "Semua Kategori", categories, category);
}

function applyMonitoringFilters(items) {
  const { from, to } = currentDateBounds();
  let out = filterByDate(items, from, to);
  const cases = activeCases();
  const search = ($("search")?.value || "").trim().toLowerCase();
  const location = $("region")?.value || "all";
  const polres = $("polres")?.value || "all";
  const attention = $("priority")?.value || "all";
  const scope = $("scope")?.value || "all";
  const category = $("category")?.value || "all";

  if (search) out = out.filter(x => [getTitle(x), getSource(x), getFilterArea(x), x.polres, getCategory(x), getScope(x), x.issue_type, x.issue_subtype].filter(Boolean).join(" ").toLowerCase().includes(search));
  if (location !== "all") {
    if (location === "__JATIM__") out = out.filter(isJatim);
    else if (location === "__OUTSIDE__") out = out.filter(x => x.region === "LUAR JATIM");
    else if (location === "__UNKNOWN__") out = out.filter(x => x.region === "BELUM TERPETAKAN" || x.is_jatim == null);
    else out = out.filter(x => getFilterArea(x) === location);
  }
  if (polres !== "all") out = out.filter(x => String(x.polres || "") === polres);
  if (attention !== "all") out = out.filter(x => matchesAttentionBand(x, attention, cases));
  if (scope !== "all") out = out.filter(x => getScope(x) === scope);
  if (category !== "all") out = out.filter(x => getCategory(x) === category);

  return out.sort((a,b) => getEffectiveAttentionScore(b, cases) - getEffectiveAttentionScore(a, cases) || new Date(getItemDate(b)||0) - new Date(getItemDate(a)||0));
}

function getRelevantCases(items, region, polres) {
  const cases = activeCases();
  const ids = new Set(items.map(x => x.case_id).filter(Boolean));
  let result = cases.filter(c => ids.has(c.case_id));
  if (region === "__JATIM__") result = result.filter(isJatim);
  else if (region === "__OUTSIDE__") result = result.filter(c => c.region === "LUAR JATIM");
  else if (region === "__UNKNOWN__") result = result.filter(c => c.region === "BELUM TERPETAKAN" || c.is_jatim == null);
  else if (region !== "all") result = result.filter(c => getFilterArea(c) === region);
  if (polres !== "all") result = result.filter(c => String(c.polres || "") === polres);
  return result.sort((a,b) => getAttentionScore(b) - getAttentionScore(a) || new Date(b.last_detected_at || b.last_seen || 0) - new Date(a.last_detected_at || a.last_seen || 0));
}

function filterPeriodLabel() {
  const { from, to } = currentDateBounds();
  if (!from && !to) return "Semua periode";
  if (from && to && from === to) return formatDate(from);
  return `${from ? formatDate(from) : "Awal"} — ${to ? formatDate(to) : "Sekarang"}`;
}

function renderActiveFilterChips() {
  const target = $("activeFilterChips");
  if (!target) return;

  const chips = [];
  const search = ($("search")?.value || "").trim();
  const region = $("region")?.value || "all";
  const polres = $("polres")?.value || "all";
  const priority = $("priority")?.value || "all";
  const scope = $("scope")?.value || "all";
  const category = $("category")?.value || "all";
  const { from, to } = currentDateBounds();

  if (search) chips.push(`Pencarian: ${search}`);
  if (region !== "all") chips.push(region === "__JATIM__" ? "Wilayah: Jawa Timur" : region === "__OUTSIDE__" ? "Wilayah: Luar Jatim" : region === "__UNKNOWN__" ? "Wilayah: Belum Terpetakan" : `Wilayah: ${region}`);
  if (polres !== "all") chips.push(`Polres: ${polres}`);
  if (priority !== "all") { const labels = {"0-24":"0–24 Rendah","25-49":"25–49 Perlu Perhatian","50-69":"50–69 Atensi","70-84":"70–84 Atensi Tinggi","85-100":"85–100 Kritis"}; chips.push(`Skala: ${labels[priority] || priority}`); }
  if (scope !== "all") chips.push(`Jenis: ${scope === "case" ? "Ungkap Kasus" : scope[0].toUpperCase()+scope.slice(1)}`);
  if (category !== "all") chips.push(`Kategori: ${category}`);
  if (from || to) chips.push(`Periode: ${filterPeriodLabel()}`);

  target.innerHTML = chips.length
    ? `<span class="active-filter-label">Filter aktif</span>${chips.map(label => `<span class="active-filter-chip">${escapeHtml(label)}</span>`).join("")}`
    : `<span class="active-filter-empty"><i class="fa-solid fa-filter" aria-hidden="true"></i> Belum ada filter tambahan</span>`;
}

function renderMonitoring() {
  populateMonitoringFilters();

  const base = currentMonitoringBase();
  const items = applyMonitoringFilters(base);
  renderActiveFilterChips();
  const region = $("region")?.value || "all";
  const polres = $("polres")?.value || "all";
  const cases = getRelevantCases(items, region, polres);
  const { from, to } = currentDateBounds();

  if ($("resultCount")) $("resultCount").textContent = `${number(items.length)} berita · ${number(cases.length)} case`;
  if ($("resultContext")) $("resultContext").textContent = from && to ? `${from} s/d ${to}` : "Semua periode";
  if ($("monitoringContextText")) {
    const modeLabel = "Semua data";
    $("monitoringContextText").textContent = activeArchive
      ? `Snapshot ${formatDate(activeArchive.date)}.`
      : `${modeLabel} · ${from || to ? filterPeriodLabel() : "Semua periode"}.`;
  }

  const caseTarget = $("monitoringCases");
  caseTarget.innerHTML = cases.length
    ? `<div class="subsection-head"><div><h3>Kasus / Insiden</h3><div class="muted">Prioritas kasus berlaku pada satu insiden, bukan setiap artikel.</div></div></div><div class="case-grid">${cases.map((c, i) => caseCard(c, i + 1)).join("")}</div>`
    : `<div class="case-empty">Tidak ada Kasus yang memenuhi filter.</div>`;
  bindCaseClicks(caseTarget, activeCases(), activeNews());

  const list = $("list");
  list.innerHTML = items.length ? items.map(articleCard).join("") : `<div class="empty">Tidak ada berita yang cocok dengan filter.</div>`;
  bindArticleClicks(list, activeNews());
}

function setDefaultTodayRange() {
  if (!todayData?.date || !$('dateFrom') || !$('dateTo')) return;
  $('dateFrom').value = todayData.date;
  $('dateTo').value = todayData.date;
  syncQuickDateButtons("today");
}

function setQuickDate(type) {
  if (type === "all") {
    $("dateFrom").value = "";
    $("dateTo").value = "";
  } else if (type === "today") {
    setDefaultTodayRange();
    return;
  } else {
    const end = parseDate(`${todayData?.date || dateKey(new Date())}T00:00:00+07:00`) || new Date();
    const start = new Date(end);
    start.setDate(start.getDate() - (Number(type) - 1));
    $("dateFrom").value = dateKey(start);
    $("dateTo").value = todayData?.date || dateKey(end);
  }
  syncQuickDateButtons(type);
  populateMonitoringFilters();
  renderMonitoring();
}

function syncQuickDateButtons(active) {
  document.querySelectorAll("[data-quick-date]").forEach(button => button.classList.toggle("active", button.dataset.quickDate === active));
}



function bindArticleClicks(root, dataset = activeNews()) {
  root?.querySelectorAll("[data-article-id]").forEach(el => el.addEventListener("click", () => {
    const article = getArticleById(el.dataset.articleId, dataset);
    if (article) openArticleDrawer(article, dataset, activeCases());
  }));
}

function bindCaseClicks(root, caseDataset = activeCases(), newsDataset = activeNews()) {
  root?.querySelectorAll("[data-case-id]").forEach(el => el.addEventListener("click", () => {
    const c = getCaseById(el.dataset.caseId, caseDataset);
    if (c) openCaseDrawer(c, newsDataset, caseDataset);
  }));
}

function openDrawer() {
  $("detailDrawer")?.classList.add("open");
  $("detailDrawer")?.setAttribute("aria-hidden", "false");
  $("drawerOverlay")?.classList.remove("hidden");
}

function closeDrawer() {
  $("detailDrawer")?.classList.remove("open");
  $("detailDrawer")?.setAttribute("aria-hidden", "true");
  $("drawerOverlay")?.classList.add("hidden");
}

async function copyLink(url, button) {
  if (!url) return;
  const original = button?.innerHTML || "<i class=\"fa-regular fa-copy\"></i> Salin";
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
    } else {
      const ta = document.createElement("textarea");
      ta.value = url;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    if (button) {
      button.innerHTML = '<i class="fa-solid fa-check"></i> Tersalin';
      button.classList.add("copied");
      setTimeout(() => {
        button.innerHTML = original;
        button.classList.remove("copied");
      }, 1400);
    }
  } catch (error) {
    console.error("Gagal menyalin tautan", error);
    if (button) {
      button.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Gagal';
      setTimeout(() => { button.innerHTML = original; }, 1600);
    }
  }
}

function copyButtonMarkup(url, label = "Salin") {
  return url
    ? `<button type="button" class="copy-link-btn" data-copy-url="${escapeHtml(url)}"><i class="fa-regular fa-copy" aria-hidden="true"></i> ${escapeHtml(label)}</button>`
    : "";
}

function bindCopyButtons(root) {
  root?.querySelectorAll("[data-copy-url]").forEach(button => {
    button.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      copyLink(button.dataset.copyUrl, button);
    });
  });
}

function openArticleDrawer(article, dataset = activeNews(), caseDataset = activeCases()) {
  const c = getCaseById(article.case_id, caseDataset);
  const url = normalizeUrl(article.url);
  const attention = getEffectiveAttentionScore(article, caseDataset);
  const attentionLabel = getEffectiveAttentionLabel(article, caseDataset);
  $("drawerEyebrow").textContent = "DETAIL BERITA";
  $("drawerContent").innerHTML = `
    <div class="drawer-title">${escapeHtml(getTitle(article))}</div>
    <div class="drawer-meta">${escapeHtml(getSource(article))} · ${escapeHtml(formatDateTime(getItemDate(article)))}</div>
    <div class="drawer-pills">
      <span class="pill ${attentionClass(attention)}">ATENSI ${number(attention)}/100 · ${escapeHtml(attentionLabel)}</span>
      ${c ? `<span class="pill ${attentionClass(getAttentionScore(c))}">KASUS ${number(getAttentionScore(c))}/100</span>` : `<span class="pill">BELUM TERKAIT KASUS</span>`}
    </div>
    <div class="detail-grid">
      <div><span>Wilayah</span><strong>${escapeHtml(article.locality || getLocality(article) || article.region || "Belum Terpetakan")}</strong></div>
      <div><span>Polres</span><strong>${escapeHtml(article.polres || "-")}</strong></div>
      <div><span>Scope</span><strong>${escapeHtml(getScope(article))}</strong></div>
      <div><span>Kategori</span><strong>${escapeHtml(getCategory(article))}</strong></div>
      <div><span>Publikasi</span><strong>${escapeHtml(formatDateTime(article.published_at || article.collected_at))}</strong></div>
      <div><span>Ditemukan</span><strong>${escapeHtml(formatDateTime(article.collected_at))}</strong></div>
    </div>
    <div class="drawer-actions">
      ${url ? `<a class="primary-link" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Buka Berita Asli</a>` : ""}
      ${copyButtonMarkup(url, "Salin Tautan")}
      ${c ? `<button class="secondary" id="drawerCaseButton">Lihat Kasus & Semua Sumber</button>` : ""}
    </div>`;
  openDrawer();
  bindCopyButtons($("drawerContent"));
  $("drawerCaseButton")?.addEventListener("click", () => openCaseDrawer(c, dataset, caseDataset));
}

function openCaseDrawer(c, newsDataset = activeNews(), caseDataset = activeCases()) {
  if (!c) return;
  let items = caseArticles(c, newsDataset);
  if (!items.length && Array.isArray(c?.articles)) items = c.articles;
  items = items.slice().sort(
    (a, b) => new Date(getItemDate(b) || 0) - new Date(getItemDate(a) || 0)
  );
  const score = getAttentionScore(c);
  const label = c.attention_label || attentionBand(score);
  const reasons = Array.isArray(c.priority_evidence?.reasons) ? c.priority_evidence.reasons : [];
  $("drawerEyebrow").textContent = "KASUS / INSIDEN";
  $("drawerContent").innerHTML = `
    <div class="drawer-title">${escapeHtml(c.title || "Kasus")}</div>
    <div class="drawer-meta">${escapeHtml(c.locality || getLocality(c) || c.region || "Belum Terpetakan")} · ${number(c.article_count || items.length)} sumber</div>
    <div class="case-detail-head"><span class="pill ${attentionClass(score)}">ATENSI ${number(score)}/100 · ${escapeHtml(label)}</span></div>
    ${reasons.length ? `<div class="priority-reasons"><h4>Alasan atensi</h4><ul>${reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}</ul></div>` : ""}
    <div class="source-list"><h4>Seluruh sumber terkait</h4>
      ${items.length ? items.map((a, i) => {
        const u = normalizeUrl(a.url);
        return `<div class="source-row"><div><b>${number(i + 1)}. ${escapeHtml(getSource(a))}</b><div>${escapeHtml(getTitle(a))}</div><small>${escapeHtml(formatDateTime(getItemDate(a)))}</small></div><span class="source-row-actions">${copyButtonMarkup(u)}${u ? `<a class="open-link-btn" href="${escapeHtml(u)}" target="_blank" rel="noopener noreferrer"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Buka</a>` : ""}</span></div>`;
      }).join("") : `<div class="empty">Sumber detail tidak tersedia pada dataset aktif.</div>`}
    </div>`;
  openDrawer();
  bindCopyButtons($("drawerContent"));
}

function initMap() {
  if (map || !window.L || !$("jatimMap")) return;
  map = L.map("jatimMap", { zoomControl: true, tap: true }).setView([-7.75, 112.45], 8);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "&copy; OpenStreetMap contributors" }).addTo(map);
}

function renderMap(items) {
  if (!map) return;
  mapMarkers.forEach(m => m.remove());
  mapMarkers = [];
  const groups = new Map();
  items.filter(isJatim).forEach(item => {
    const r = getLocality(item);
    if (!r || !JATIM_COORDS[r]) return;
    if (!groups.has(r)) groups.set(r, { name: r, items: [], cases: new Set() });
    const g = groups.get(r);
    g.items.push(item);
    if (item.case_id) g.cases.add(item.case_id);
  });
  const cMap = new Map(globalCases().map(c => [c.case_id, c]));
  let bounds = [];
  groups.forEach(g => {
    const coords = JATIM_COORDS[g.name];
    bounds.push(coords);
    let high = 0, medium = 0;
    [...g.cases].forEach(id => {
      const c = cMap.get(id);
      const score = getAttentionScore(c);
      if (score >= 70) high++;
      else if (score >= 50) medium++;
    });
    const level = high ? "high" : medium ? "medium" : "low";
    const size = Math.min(42, 22 + Math.floor(g.items.length / 2) * 2);
    const icon = L.divIcon({ className: "", html: `<div class="pnm-marker ${level}" style="width:${size}px;height:${size}px">${number(g.items.length)}</div>`, iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
    const marker = L.marker(coords, { icon }).addTo(map);
    const relatedCases = [...g.cases].map(id => cMap.get(id)).filter(Boolean).sort((a, b) => priorityRank(b.priority) - priorityRank(a.priority));
    const top = g.items.slice().sort((a, b) => new Date(getItemDate(b) || 0) - new Date(getItemDate(a) || 0)).slice(0, 4);
    marker.bindPopup(`<div class="map-popup"><strong>${escapeHtml(g.name)}</strong><div>${number(g.items.length)} berita · ${number(g.cases.size)} kasus</div>${high ? `<div class="map-popup-high">Atensi tinggi: ${number(high)}</div>` : ""}<div class="map-popup-list">${relatedCases.slice(0, 3).map(c => `<div>• ${escapeHtml(c.title)}</div>`).join("") || top.map(a => `<div>• ${escapeHtml(getTitle(a))}</div>`).join("")}</div><button class="map-open-region" data-region="${escapeHtml(g.name)}">Lihat seluruh berita wilayah →</button></div>`);
    marker.on("popupopen", () => marker.getPopup().getElement()?.querySelector(".map-open-region")?.addEventListener("click", () => {
      openRegionDrawer(g.name, g.items);
    }));
    mapMarkers.push(marker);
  });
  $("mapCount").textContent = `${number(groups.size)} lokasi`;
  if (bounds.length) map.fitBounds(bounds, { padding: [25, 25], maxZoom: 9 });
  else map.setView([-7.75, 112.45], 8);
  setTimeout(() => map.invalidateSize(), 100);
}

async function loadArchive(date) {
  try {
    const data = await fetchJson(`data/archive/${encodeURIComponent(date)}.json`);
    activeArchive = data;
    showView("archive");
    openArchiveDetail();
  } catch (e) {
    console.error(e);
    alert(`Snapshot arsip ${date} tidak dapat dibuka.`);
  }
}

function renderArchiveList() {
  const target = $("archiveList");
  if (!target) return;
  if (!archiveFiles.length) {
    target.innerHTML = `<div class="empty">Belum ada arsip.</div>`;
    return;
  }
  target.innerHTML = archiveFiles.map(date => `<button class="archive-item" data-archive-date="${escapeHtml(date)}"><span><strong>${escapeHtml(formatDate(date))}</strong><small>Snapshot monitoring</small></span><b>→</b></button>`).join("");
  target.querySelectorAll("[data-archive-date]").forEach(btn => btn.addEventListener("click", () => loadArchive(btn.dataset.archiveDate)));
}

function closeArchiveDetail(clear = true) {
  if (clear) activeArchive = null;
  $("archiveDetail")?.classList.add("hidden");
  if ($("archiveDetail")) $("archiveDetail").hidden = true;
  $("archiveListPanel")?.classList.remove("hidden");
  if ($("archiveListPanel")) $("archiveListPanel").hidden = false;
}

function openArchiveDetail() {
  if (!activeArchive) return;
  $("archiveListPanel")?.classList.add("hidden");
  if ($("archiveListPanel")) $("archiveListPanel").hidden = true;
  $("archiveDetail")?.classList.remove("hidden");
  if ($("archiveDetail")) $("archiveDetail").hidden = false;
  $("archiveTitle").textContent = formatDate(activeArchive.date);
  $("archiveUpdated").textContent = `Update: ${formatDateTime(activeArchive.last_successful_update || activeArchive.updated_at)}`;
  archiveMode = "all";
  document.querySelectorAll("[data-archive-mode]").forEach(b => b.classList.toggle("active", b.dataset.archiveMode === "all"));
  populateArchiveFilters();
  renderArchiveNews();
}

function populateArchiveFilters() {
  const items = activeArchive?.news?.items || [];
  const region = $("archiveRegion");
  const polres = $("archivePolres");
  const category = $("archiveCategory");
  const priority = $("archivePriority");
  const currentRegion = region?.value || "all";
  const currentPolres = polres?.value || "all";
  const currentCategory = category?.value || "all";
  const currentPriority = priority?.value || "all";

  const areas = unique(items.filter(isJatim).map(getFilterArea)).filter(Boolean).sort((a,b) => {
    if (a === "Jawa Timur (Umum)") return -1;
    if (b === "Jawa Timur (Umum)") return 1;
    return a.localeCompare(b, "id");
  });
  const options = [
    `<option value="all">Semua Wilayah / Area</option>`,
    items.some(isJatim) ? `<option value="__JATIM__">Jawa Timur — semua wilayah</option>` : "",
    ...areas.map(a => `<option value="${escapeHtml(a)}">↳ ${escapeHtml(a)}</option>`),
    items.some(x => x.region === "LUAR JATIM") ? `<option value="__OUTSIDE__">Luar Jatim</option>` : "",
    items.some(x => x.region === "BELUM TERPETAKAN" || x.is_jatim == null) ? `<option value="__UNKNOWN__">Belum Terpetakan</option>` : ""
  ];
  if (region) { region.innerHTML = options.join(""); if (["all","__JATIM__","__OUTSIDE__","__UNKNOWN__"].includes(currentRegion) || areas.includes(currentRegion)) region.value=currentRegion; }

  const regionItems = currentRegion === "__JATIM__" ? items.filter(isJatim) :
    currentRegion === "__OUTSIDE__" ? items.filter(x => x.region === "LUAR JATIM") :
    currentRegion === "__UNKNOWN__" ? items.filter(x => x.region === "BELUM TERPETAKAN" || x.is_jatim == null) :
    currentRegion !== "all" ? items.filter(x => getFilterArea(x) === currentRegion) : items;
  const polresValues = unique(regionItems.filter(isJatim).map(x=>x.polres).filter(Boolean)).sort((a,b)=>a.localeCompare(b,"id"));
  populateSelect(polres, "Polres terdeteksi", polresValues, currentPolres);

  if (priority) {
    priority.innerHTML = [
      ["all","Semua Skala Atensi"],["0-24","0–24 · Rendah"],["25-49","25–49 · Perlu Perhatian"],
      ["50-69","50–69 · Atensi"],["70-84","70–84 · Atensi Tinggi"],["85-100","85–100 · Kritis"]
    ].map(([v,l])=>`<option value="${v}">${l}</option>`).join("");
    if (["all","0-24","25-49","50-69","70-84","85-100"].includes(currentPriority)) priority.value=currentPriority;
  }

  const categories = unique(items.map(getCategory)).sort((a,b)=>a.localeCompare(b,"id"));
  populateSelect(category, "Semua Kategori", categories, currentCategory);
}
function renderArchiveNews() {
  if (!activeArchive) return;
  const items = activeArchive.news?.items || [];
  const cases = activeArchive.cases?.items || [];
  let results = [...items];

  if (archiveMode === "jatim") results = results.filter(isJatim);
  if (archiveMode === "high") results = results.filter(x => getEffectiveAttentionScore(x, cases) >= 70);

  const search = ($( "archiveSearch")?.value || "").trim().toLowerCase();
  const region = $("archiveRegion")?.value || "all";
  const polres = $("archivePolres")?.value || "all";
  const priority = $("archivePriority")?.value || "all";
  const scope = $("archiveScope")?.value || "all";
  const category = $("archiveCategory")?.value || "all";

  if (search) results = results.filter(x => [getTitle(x), getSource(x), x.region, x.polres, getLocality(x), getCategory(x), getScope(x)].filter(Boolean).join(" ").toLowerCase().includes(search));
  if (region === "__JATIM__") results = results.filter(isJatim);
  else if (region === "__OUTSIDE__") results = results.filter(x => x.region === "LUAR JATIM");
  else if (region === "__UNKNOWN__") results = results.filter(x => x.region === "BELUM TERPETAKAN" || x.is_jatim == null);
  else if (region !== "all") results = results.filter(x => getFilterArea(x) === region);
  if (polres !== "all") results = results.filter(x => String(x.polres || "") === polres);
  if (priority !== "all") results = results.filter(x => matchesAttentionBand(x, priority, cases));
  if (scope !== "all") results = results.filter(x => getScope(x) === scope);
  if (category !== "all") results = results.filter(x => getCategory(x) === category);

  if ($("archiveResultCount")) $("archiveResultCount").textContent = `${number(results.length)} hasil`;
  if ($("archiveResultContext")) $("archiveResultContext").textContent = `Snapshot ${formatDate(activeArchive.date)}`;
  if ($("archiveNews")) $("archiveNews").textContent = number(items.length);
  if ($("archiveCases")) $("archiveCases").textContent = number(cases.length);
  if ($("archiveJatim")) $("archiveJatim").textContent = number(items.filter(isJatim).length);
  if ($("archiveHigh")) $("archiveHigh").textContent = number(cases.filter(c => getAttentionScore(c) >= 70).length);

  const relevantCases = cases.filter(c => results.some(i => i.case_id === c.case_id)).sort((a, b) => getAttentionScore(b) - getAttentionScore(a) || new Date(b.last_detected_at || b.last_seen || 0) - new Date(a.last_detected_at || a.last_seen || 0));
  const caseTarget = $("archiveCasesList");
  if (caseTarget) {
    caseTarget.innerHTML = relevantCases.length ? `<div class="subsection-head"><div><h3>Kasus / Insiden</h3><div class="muted">Kasus yang terkait dengan filter snapshot.</div></div></div><div class="case-grid">${relevantCases.map((c, i) => caseCard(c, i + 1)).join("")}</div>` : `<div class="case-empty">Tidak ada Kasus pada filter ini.</div>`;
    bindCaseClicks(caseTarget, cases, items);
  }

  const target = $("archiveNewsList");
  target.innerHTML = results.length ? results.map(articleCard).join("") : `<div class="empty">Tidak ada berita yang cocok.</div>`;
  bindArticleClicks(target, items);
}

function resetMonitoringFilters() {
  $("search").value = "";
  $("region").value = "all";
  $("polres").value = "all";
  $("priority").value = "all";
  $("scope").value = "all";
  $("category").value = "all";
  setDefaultTodayRange();
  populateMonitoringFilters();
  renderMonitoring();
}

function initEvents() {
  $("drawerClose")?.addEventListener("click", closeDrawer);
  $("drawerOverlay")?.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", e => { if (e.key === "Escape") { closeDrawer(); } });

  document.querySelectorAll("[data-view]").forEach(button => button.addEventListener("click", () => {
    const view = button.dataset.view;
    if (view !== "archive") {
      activeArchive = null;
      closeArchiveDetail();
    }
    showView(view);
  }));

  document.querySelectorAll("[data-open-monitoring]").forEach(button => button.addEventListener("click", () => {
    activeArchive = null;
    closeArchiveDetail();
    showView("monitoring");
  }));

  ["search", "priority", "scope", "category"].forEach(id => {
    $(id)?.addEventListener("input", () => {
      if (id === "search") populateMonitoringFilters();
      renderMonitoring();
    });
    $(id)?.addEventListener("change", () => {
      if (id === "search") populateMonitoringFilters();
      renderMonitoring();
    });
  });

  ["region", "polres", "dateFrom", "dateTo"].forEach(id => {
    $(id)?.addEventListener("input", () => {
      populateMonitoringFilters();
      renderMonitoring();
    });
    $(id)?.addEventListener("change", () => {
      populateMonitoringFilters();
      renderMonitoring();
    });
  });
  $("clearFilters")?.addEventListener("click", resetMonitoringFilters);

  $("archiveBack")?.addEventListener("click", () => {
    closeArchiveDetail();
    showView("archive");
  });

  document.querySelectorAll("[data-archive-mode]").forEach(button => button.addEventListener("click", () => {
    archiveMode = button.dataset.archiveMode;
    document.querySelectorAll("[data-archive-mode]").forEach(x => x.classList.toggle("active", x.dataset.archiveMode === archiveMode));
    renderArchiveNews();
  }));

  ["archiveSearch", "archiveRegion", "archivePolres", "archivePriority", "archiveScope", "archiveCategory"].forEach(id => {
    $(id)?.addEventListener("input", () => { if (["archiveRegion","archivePolres"].includes(id)) populateArchiveFilters(); renderArchiveNews(); });
    $(id)?.addEventListener("change", () => { if (["archiveRegion","archivePolres"].includes(id)) populateArchiveFilters(); renderArchiveNews(); });
  });

  $("archiveClear")?.addEventListener("click", () => {
    $("archiveSearch").value = "";
    $("archiveRegion").value = "all";
    $("archivePolres").value = "all";
    $("archivePriority").value = "all";
    $("archiveScope").value = "all";
    $("archiveCategory").value = "all";
    populateArchiveFilters();
    renderArchiveNews();
  });

  $("refresh")?.addEventListener("click", async () => {
    closeDrawer();
    const keepView = currentView;
    const keepArchive = activeArchive?.date || null;
    activeArchive = null;
    await loadAllData();
    if (keepArchive) await loadArchive(keepArchive);
    else showView(keepView);
  });
}

function init() {
  if (initialized) return;
  initialized = true;
  initEvents();
  showView("dashboard");
  loadAllData();
}

init();
