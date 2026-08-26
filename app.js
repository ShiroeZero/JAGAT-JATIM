const TODAY_URL = "data/today.json";
const CASE_URL = "data/case_clusters.json";
const NEWS_URL = "data/news.json";
const ARCHIVE_INDEX_URL = "data/archive/index.json";

const DEMO_EMAIL = "admin@propam-jatim.go.id";
const DEMO_PASSWORD = "PropamJatim2026!";

const JATIM_COORDS = {
  Surabaya: [-7.2575, 112.7521],
  Gresik: [-7.1568, 112.6551],
  Sidoarjo: [-7.4478, 112.7183],
  Mojokerto: [-7.4706, 112.4401],
  Jombang: [-7.5459, 112.2331],
  Nganjuk: [-7.6052, 111.9046],
  Madiun: [-7.6298, 111.5239],
  Magetan: [-7.6559, 111.3327],
  Ngawi: [-7.4032, 111.4461],
  Bojonegoro: [-7.1502, 111.8817],
  Tuban: [-6.8976, 112.0645],
  Lamongan: [-7.1167, 112.3333],
  Kediri: [-7.8167, 112.0167],
  Tulungagung: [-8.0657, 111.9025],
  Trenggalek: [-8.05, 111.7167],
  Blitar: [-8.0983, 112.1681],
  Malang: [-7.9819, 112.6265],
  Batu: [-7.87, 112.523],
  Pasuruan: [-7.6453, 112.9075],
  Probolinggo: [-7.7543, 113.2159],
  Lumajang: [-8.1335, 113.2248],
  Jember: [-8.1724, 113.7009],
  Bondowoso: [-7.9135, 113.8215],
  Situbondo: [-7.7062, 114.0098],
  Banyuwangi: [-8.2191, 114.3691],
  Pacitan: [-8.1949, 111.1047],
  Ponorogo: [-7.865, 111.4696],
  Sumenep: [-7.0167, 113.8667],
  Pamekasan: [-7.1568, 113.4746],
  Sampang: [-7.1872, 113.2394],
  Bangkalan: [-7.0455, 112.7351],
};

let todayData = null;
let caseData = { cases: [] };
let newsData = [];
let archiveFiles = [];
let currentView = "dashboard";
let monitoringMode = "all";
let archiveMode = "all";
let activeArchive = null;
let jatimMap = null;
let mapMarkers = [];

const $ = (id) => document.getElementById(id);

function number(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toLocaleString("id-ID") : "0";
}

function formatDate(value) {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);

  return d.toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function formatDateTime(value) {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);

  return (
    d.toLocaleString("id-ID", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }) + " WIB"
  );
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeUrl(url) {
  if (!url) return "";
  const text = String(url).trim();
  if (!/^https?:\/\//i.test(text)) return "";
  return text;
}

function setStatus(text, online) {
  if ($("statusText")) $("statusText").textContent = text;
  if ($("statusDot")) {
    $("statusDot").style.background = online
      ? "var(--ok)"
      : "var(--danger)";
  }
}

function showApp() {
  $("login")?.classList.add("hidden");
  $("app")?.classList.remove("hidden");
  loadAllData();
}

$("loginForm")?.addEventListener("submit", (event) => {
  event.preventDefault();

  const email = $("email")?.value.trim();
  const password = $("password")?.value;

  if (email === DEMO_EMAIL && password === DEMO_PASSWORD) {
    sessionStorage.setItem("pnm_logged_in", "1");
    showApp();
  } else {
    if ($("loginError")) {
      $("loginError").textContent = "Email atau password salah.";
    }
  }
});

$("logout")?.addEventListener("click", () => {
  sessionStorage.removeItem("pnm_logged_in");
  location.reload();
});

if (sessionStorage.getItem("pnm_logged_in") === "1") {
  showApp();
}

async function fetchJson(url) {
  const response = await fetch(url + "?t=" + Date.now());
  if (!response.ok) {
    throw new Error(`${url} HTTP ${response.status}`);
  }
  return response.json();
}

async function loadAllData() {
  setStatus("Memuat data...", false);

  try {
    const [today, cases, news, archiveIndex] = await Promise.all([
      fetchJson(TODAY_URL),
      fetchJson(CASE_URL),
      fetchJson(NEWS_URL),
      fetchJson(ARCHIVE_INDEX_URL),
    ]);

    todayData = today || null;
    caseData = cases || { cases: [] };

    newsData = Array.isArray(news)
      ? news
      : Array.isArray(news?.items)
      ? news.items
      : [];

    archiveFiles = Array.isArray(archiveIndex)
      ? archiveIndex
      : Array.isArray(archiveIndex?.files)
      ? archiveIndex.files
      : [];

    renderAll();
    setStatus("Data aktif", true);
  } catch (error) {
    console.error(error);
    setStatus("Gagal memuat data", false);
    if ($("lastUpdated")) $("lastUpdated").textContent = "Data gagal dimuat";
  }
}

function renderAll() {
  renderHeader();
  renderDashboard();
  populateMonitoringFilters(getTodayDataset());
  renderMonitoring();
  renderArchiveList();
}

function renderHeader() {
  if (!todayData) return;

  $("todayDate").textContent = formatDate(todayData.date);

  $("lastUpdated").textContent =
    "Update terakhir: " +
    formatDateTime(
      todayData.last_successful_update || todayData.updated_at
    );

  $("sTotal").textContent = number(todayData.summary?.news_today);
  $("sCases").textContent = number(todayData.summary?.cases_today);
  $("sYoutube").textContent = number(todayData.summary?.youtube_today);
  $("sHigh").textContent = number(todayData.summary?.priority_high);

  $("sNegative").textContent = number(todayData.summary?.negative_today);
  $("sJatim").textContent = number(todayData.summary?.jatim_news);
  $("sCaseHigh").textContent = number(todayData.cases?.priority_high);
  $("sTotalCases").textContent = number(caseData?.total_cases);
}

function getTodayDataset() {
  return Array.isArray(todayData?.news?.items)
    ? todayData.news.items
    : [];
}

function getActiveNewsDataset() {
  if (activeArchive?.news?.items) {
    return activeArchive.news.items;
  }

  return getTodayDataset();
}

function getActiveCasesDataset() {
  if (activeArchive?.cases?.items) {
    return activeArchive.cases.items;
  }

  return Array.isArray(caseData?.cases) ? caseData.cases : [];
}

function getTitle(item) {
  return item?.title || "Tanpa judul";
}

function getSource(item) {
  return item?.source || item?.publisher || "Sumber tidak diketahui";
}

function getItemDate(item) {
  return item?.collected_at || item?.published_at || "";
}

function getPriority(item) {
  return String(item?.priority || "low").toLowerCase();
}

function getScope(item) {
  return String(item?.scope || "neutral").toLowerCase();
}

function getCategory(item) {
  return item?.category || "NETRAL / LAINNYA";
}

function isJatim(item) {
  return item?.is_jatim === true;
}

function isTodayItem(item) {
  const date = todayData?.date;
  if (!date) return false;

  const raw = getItemDate(item);
  if (!raw) return false;

  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return false;

  return d.toLocaleDateString("en-CA", {
    timeZone: "Asia/Jakarta",
  }) === date;
}

function localityFromPolres(polres) {
  const text = String(polres || "").toLowerCase();

  const aliases = {
    surabaya: "Surabaya",
    gresik: "Gresik",
    sidoarjo: "Sidoarjo",
    mojokerto: "Mojokerto",
    jombang: "Jombang",
    nganjuk: "Nganjuk",
    madiun: "Madiun",
    magetan: "Magetan",
    ngawi: "Ngawi",
    bojonegoro: "Bojonegoro",
    tuban: "Tuban",
    lamongan: "Lamongan",
    kediri: "Kediri",
    tulungagung: "Tulungagung",
    trenggalek: "Trenggalek",
    blitar: "Blitar",
    malang: "Malang",
    batu: "Batu",
    pasuruan: "Pasuruan",
    probolinggo: "Probolinggo",
    lumajang: "Lumajang",
    jember: "Jember",
    bondowoso: "Bondowoso",
    situbondo: "Situbondo",
    banyuwangi: "Banyuwangi",
    pacitan: "Pacitan",
    ponorogo: "Ponorogo",
    sumenep: "Sumenep",
    pamekasan: "Pamekasan",
    sampang: "Sampang",
    bangkalan: "Bangkalan",
  };

  for (const [needle, value] of Object.entries(aliases)) {
    if (text.includes(needle)) return value;
  }

  return "";
}

function getLocality(item) {
  const fromPolres = localityFromPolres(item?.polres);
  if (fromPolres) return fromPolres;

  const text = `${item?.title || ""} ${item?.location || ""} ${item?.region || ""}`.toLowerCase();

  for (const locality of Object.keys(JATIM_COORDS)) {
    if (text.includes(locality.toLowerCase())) {
      return locality;
    }
  }

  return "";
}

function getCaseById(caseId) {
  if (!caseId) return null;
  return getActiveCasesDataset().find((item) => item.case_id === caseId) || null;
}

function getArticleById(id, dataset = getActiveNewsDataset()) {
  return dataset.find((item) => item.id === id) || null;
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function renderDashboard() {
  const items = getTodayDataset();
  renderRegionsToday(items);
  renderCategories(items);
  renderLatest(items);
  renderLatestCases();
  initMap();
  renderMap(items);
}

function renderRegionsToday(items) {
  const target = $("regionToday");
  if (!target) return;

  const grouped = new Map();

  for (const item of items) {
    if (!isJatim(item)) continue;

    const locality = getLocality(item) || "Jawa Timur";
    if (!grouped.has(locality)) {
      grouped.set(locality, {
        count: 0,
        highCases: 0,
      });
    }

    grouped.get(locality).count += 1;
  }

  const caseByRegion = new Map();

  for (const caseItem of getTodayCases()) {
    const locality =
      localityFromPolres(caseItem.polres) ||
      Object.keys(JATIM_COORDS).find(
        (name) =>
          String(caseItem.title || "").toLowerCase().includes(name.toLowerCase())
      );

    if (!locality) continue;

    if (!caseByRegion.has(locality)) {
      caseByRegion.set(locality, { high: 0 });
    }

    if (String(caseItem.priority).toLowerCase() === "high") {
      caseByRegion.get(locality).high += 1;
    }
  }

  const rows = [...grouped.entries()].sort((a, b) => b[1].count - a[1].count);

  if (!rows.length) {
    target.innerHTML = `<div class="empty">Tidak ada wilayah Jawa Timur terdeteksi hari ini.</div>`;
    return;
  }

  target.innerHTML = rows
    .map(([name, value]) => {
      const high = caseByRegion.get(name)?.high || 0;

      return `
        <button class="region-row" data-region="${escapeHtml(name)}">
          <span>
            <strong>${escapeHtml(name)}</strong>
            <small>${number(value.count)} berita</small>
          </span>
          <span class="region-right">
            ${
              high
                ? `<span class="pill high">HIGH ${number(high)}</span>`
                : `<span class="pill low">TERPANTAU</span>`
            }
            <b>→</b>
          </span>
        </button>
      `;
    })
    .join("");

  target.querySelectorAll("[data-region]").forEach((button) => {
    button.addEventListener("click", () => {
      showView("monitoring");
      monitoringMode = "jatim";
      $("region").value = button.dataset.region;
      populateMonitoringFilters(getTodayDataset());
      renderMonitoring();
    });
  });
}

function getTodayCases() {
  return Array.isArray(todayData?.cases?.items) ? todayData.cases.items : [];
}

function renderCategories(items) {
  const target = $("categories");
  if (!target) return;

  const counters = {
    Negatif: 0,
    "Ungkap Kasus": 0,
    Positif: 0,
    Netral: 0,
  };

  for (const item of items) {
    const scope = getScope(item);

    if (scope === "negative") counters.Negatif += 1;
    else if (scope === "case") counters["Ungkap Kasus"] += 1;
    else if (scope === "positive") counters.Positif += 1;
    else counters.Netral += 1;
  }

  const rows = Object.entries(counters);
  const max = Math.max(...rows.map(([, count]) => count), 1);

  target.innerHTML = rows
    .map(
      ([label, count]) => `
        <div class="bar">
          <div class="bar-top">
            <span>${escapeHtml(label)}</span>
            <strong>${number(count)}</strong>
          </div>
          <div class="bar-bg">
            <div class="bar-fill" style="width:${(count / max) * 100}%"></div>
          </div>
        </div>
      `
    )
    .join("");
}

function renderLatest(items) {
  const target = $("latest");
  if (!target) return;

  const latest = [...items]
    .sort((a, b) => new Date(getItemDate(b) || 0) - new Date(getItemDate(a) || 0))
    .slice(0, 8);

  target.innerHTML = latest.length
    ? latest.map(newsCardCompact).join("")
    : `<div class="empty">Belum ada berita hari ini.</div>`;

  bindArticleClicks(target);
}

function renderLatestCases() {
  const target = $("latestCases");
  if (!target) return;

  const cases = [...getTodayCases()]
    .sort((a, b) => {
      const pa = priorityRank(a.priority);
      const pb = priorityRank(b.priority);
      return pb - pa || new Date(b.last_detected_at || 0) - new Date(a.last_detected_at || 0);
    })
    .slice(0, 6);

  target.innerHTML = cases.length
    ? cases.map(caseCardCompact).join("")
    : `<div class="empty">Belum ada case hari ini.</div>`;

  bindCaseClicks(target);
}

function priorityRank(value) {
  return { high: 3, medium: 2, low: 1 }[String(value || "low").toLowerCase()] || 1;
}

function newsCardCompact(item) {
  const url = normalizeUrl(item.url);

  return `
    <article class="news-card clickable" data-article-id="${escapeHtml(item.id)}">
      <div class="news-card-top">
        <div>
          <div class="news-card-meta">
            ${escapeHtml(getSource(item))}
            ·
            ${escapeHtml(getLocality(item) || item.region || "Indonesia")}
            ·
            ${escapeHtml(formatDateTime(getItemDate(item)))}
          </div>
          <h3>${escapeHtml(getTitle(item))}</h3>
          <div class="news-card-meta">
            ${escapeHtml(getCategory(item))}
            ${
              item.case_id
                ? ` · ${escapeHtml(item.case_id)}`
                : ""
            }
          </div>
        </div>
        <div class="badges">
          <span class="pill ${escapeHtml(getPriority(item))}">
            ${escapeHtml(getPriority(item).toUpperCase())}
          </span>
          <span class="pill">${escapeHtml(getScope(item).toUpperCase())}</span>
        </div>
      </div>
      <div class="card-action">
        ${url ? "Klik untuk detail · sumber tersedia ↗" : "Klik untuk detail"}
      </div>
    </article>
  `;
}

function caseCardCompact(item) {
  const priority = getPriority(item);
  const locality = localityFromPolres(item.polres) || getLocality({ title: item.title });

  return `
    <article class="case-card clickable" data-case-id="${escapeHtml(item.case_id)}">
      <div class="case-card-top">
        <span class="case-id">${escapeHtml(item.case_id)}</span>
        <span class="pill ${escapeHtml(priority)}">${escapeHtml(priority.toUpperCase())}</span>
      </div>
      <strong>${escapeHtml(item.title)}</strong>
      <div class="news-card-meta">
        ${escapeHtml(locality || item.region || "Indonesia")}
        · ${number(item.article_count)} sumber
      </div>
      <div class="card-action">Klik untuk melihat seluruh sumber →</div>
    </article>
  `;
}

function populateMonitoringFilters(items) {
  const regionSelect = $("region");
  const polresSelect = $("polres");
  const categorySelect = $("category");

  if (!regionSelect || !polresSelect || !categorySelect) return;

  const currentRegion = regionSelect.value;
  const currentPolres = polresSelect.value;
  const currentCategory = categorySelect.value;

  const regions = unique(
    items
      .filter(isJatim)
      .map((item) => getLocality(item))
      .sort((a, b) => a.localeCompare(b))
  );

  regionSelect.innerHTML =
    `<option value="all">Semua Wilayah</option>` +
    regions.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");

  const filteredForPolres =
    currentRegion && currentRegion !== "all"
      ? items.filter((item) => getLocality(item) === currentRegion)
      : items;

  const polres = unique(
    filteredForPolres
      .map((item) => item.polres)
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b))
  );

  polresSelect.innerHTML =
    `<option value="all">Semua Polres Terdeteksi</option>` +
    polres.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");

  const categories = unique(
    items.map(getCategory).sort((a, b) => a.localeCompare(b))
  );

  categorySelect.innerHTML =
    `<option value="all">Semua Kategori</option>` +
    categories.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");

  if ([...regionSelect.options].some((o) => o.value === currentRegion)) {
    regionSelect.value = currentRegion;
  }

  if ([...polresSelect.options].some((o) => o.value === currentPolres)) {
    polresSelect.value = currentPolres;
  }

  if ([...categorySelect.options].some((o) => o.value === currentCategory)) {
    categorySelect.value = currentCategory;
  }
}

function applyMonitoringFilters(items, mode = monitoringMode) {
  let result = [...items];

  if (mode === "jatim") {
    result = result.filter(isJatim);
  }

  if (mode === "high") {
    result = result.filter((item) => getPriority(item) === "high");
  }

  const search = ($("search")?.value || "").trim().toLowerCase();
  const region = $("region")?.value || "all";
  const polres = $("polres")?.value || "all";
  const priority = $("priority")?.value || "all";
  const scope = $("scope")?.value || "all";
  const category = $("category")?.value || "all";

  if (search) {
    result = result.filter((item) =>
      [
        getTitle(item),
        getSource(item),
        item.region,
        item.polres,
        item.category,
        item.scope,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(search)
    );
  }

  if (region !== "all") {
    result = result.filter((item) => getLocality(item) === region);
  }

  if (polres !== "all") {
    result = result.filter((item) => item.polres === polres);
  }

  if (priority !== "all") {
    result = result.filter((item) => getPriority(item) === priority);
  }

  if (scope !== "all") {
    result = result.filter((item) => getScope(item) === scope);
  }

  if (category !== "all") {
    result = result.filter((item) => getCategory(item) === category);
  }

  return result.sort(
    (a, b) =>
      new Date(getItemDate(b) || 0) -
      new Date(getItemDate(a) || 0)
  );
}

function renderMonitoring() {
  const items = getActiveNewsDataset();

  populateMonitoringFilters(items);

  const results = applyMonitoringFilters(items, monitoringMode);

  $("resultCount").textContent = `${number(results.length)} berita`;
  $("resultContext").textContent = activeArchive
    ? `Arsip ${formatDate(activeArchive.date)}`
    : "Hari ini";

  $("monitoringContextText").textContent = activeArchive
    ? `Snapshot ${formatDate(activeArchive.date)}`
    : "Data hari ini. Wilayah dan Polres berasal dari temuan yang benar-benar ada pada dataset aktif.";

  const target = $("list");

  target.innerHTML = results.length
    ? results.map(newsCardCompact).join("")
    : `<div class="empty">Tidak ada berita yang sesuai filter.</div>`;

  bindArticleClicks(target);
}

function bindArticleClicks(root) {
  root.querySelectorAll("[data-article-id]").forEach((element) => {
    element.addEventListener("click", () => {
      const article = getArticleById(
        element.dataset.articleId,
        getActiveNewsDataset()
      );
      if (article) openArticleDrawer(article);
    });
  });
}

function bindCaseClicks(root) {
  root.querySelectorAll("[data-case-id]").forEach((element) => {
    element.addEventListener("click", () => {
      const caseItem = getCaseById(element.dataset.caseId);
      if (caseItem) openCaseDrawer(caseItem);
    });
  });
}

function openArticleDrawer(article) {
  $("drawerEyebrow").textContent = "DETAIL BERITA";

  const url = normalizeUrl(article.url);
  const relatedCase = getCaseById(article.case_id);

  $("drawerContent").innerHTML = `
    <div class="drawer-title">${escapeHtml(getTitle(article))}</div>

    <div class="drawer-meta-block">
      <div><span>Sumber</span><strong>${escapeHtml(getSource(article))}</strong></div>
      <div><span>Waktu</span><strong>${escapeHtml(formatDateTime(getItemDate(article)))}</strong></div>
      <div><span>Wilayah</span><strong>${escapeHtml(getLocality(article) || article.region || "Indonesia")}</strong></div>
      <div><span>Polres</span><strong>${escapeHtml(article.polres || "Tidak teridentifikasi")}</strong></div>
      <div><span>Kategori</span><strong>${escapeHtml(getCategory(article))}</strong></div>
      <div><span>Jenis</span><strong>${escapeHtml(getScope(article).toUpperCase())}</strong></div>
      <div><span>Prioritas</span><strong>${escapeHtml(getPriority(article).toUpperCase())}</strong></div>
      <div><span>Case</span><strong>${escapeHtml(article.case_id || "Belum terkait Case")}</strong></div>
    </div>

    <div class="drawer-actions">
      ${
        url
          ? `<button class="primary drawer-btn" id="openSourceBtn">↗ Buka Berita Asli</button>`
          : `<div class="muted">URL sumber tidak tersedia.</div>`
      }
      ${
        relatedCase
          ? `<button class="secondary drawer-btn" id="openRelatedCaseBtn">Lihat Case & Semua Sumber</button>`
          : ""
      }
    </div>
  `;

  if (url) {
    $("openSourceBtn").addEventListener("click", () => {
      window.open(url, "_blank", "noopener,noreferrer");
    });
  }

  if (relatedCase) {
    $("openRelatedCaseBtn").addEventListener("click", () => {
      openCaseDrawer(relatedCase);
    });
  }

  openDrawer();
}

function openCaseDrawer(caseItem) {
  $("drawerEyebrow").textContent = "CASE / INCIDENT";

  const articles = [...(caseItem.articles || [])].sort(
    (a, b) =>
      new Date(a.collected_at || a.published_at || 0) -
      new Date(b.collected_at || b.published_at || 0)
  );

  $("drawerContent").innerHTML = `
    <div class="case-detail-head">
      <span class="case-id">${escapeHtml(caseItem.case_id)}</span>
      <span class="pill ${escapeHtml(getPriority(caseItem))}">
        ${escapeHtml(getPriority(caseItem).toUpperCase())}
      </span>
    </div>

    <div class="drawer-title">${escapeHtml(caseItem.title)}</div>

    <div class="drawer-meta-block">
      <div><span>Wilayah</span><strong>${escapeHtml(localityFromPolres(caseItem.polres) || caseItem.region || "Indonesia")}</strong></div>
      <div><span>Polres</span><strong>${escapeHtml(caseItem.polres || "Tidak teridentifikasi")}</strong></div>
      <div><span>Jumlah sumber</span><strong>${number(articles.length)}</strong></div>
      <div><span>Terakhir terdeteksi</span><strong>${escapeHtml(formatDateTime(caseItem.last_detected_at || caseItem.last_seen))}</strong></div>
    </div>

    <div class="drawer-subtitle">SELURUH SUMBER TERKAIT</div>

    <div class="source-list">
      ${
        articles.length
          ? articles.map((article, index) => {
              const url = normalizeUrl(article.url);

              return `
                <article class="source-item">
                  <div class="source-number">${index + 1}</div>
                  <div class="source-main">
                    <strong>${escapeHtml(article.title)}</strong>
                    <small>${escapeHtml(article.source || "Sumber tidak diketahui")} · ${escapeHtml(formatDateTime(article.collected_at || article.published_at))}</small>
                    ${
                      url
                        ? `<button class="source-link" data-url="${escapeHtml(url)}">Buka sumber ↗</button>`
                        : `<small>URL tidak tersedia</small>`
                    }
                  </div>
                </article>
              `;
            }).join("")
          : `<div class="empty">Tidak ada sumber.</div>`
      }
    </div>
  `;

  $("drawerContent").querySelectorAll("[data-url]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      window.open(button.dataset.url, "_blank", "noopener,noreferrer");
    });
  });

  openDrawer();
}

function openDrawer() {
  $("drawerOverlay")?.classList.remove("hidden");
  $("detailDrawer")?.classList.add("open");
}

function closeDrawer() {
  $("drawerOverlay")?.classList.add("hidden");
  $("detailDrawer")?.classList.remove("open");
}

$("drawerClose")?.addEventListener("click", closeDrawer);
$("drawerOverlay")?.addEventListener("click", closeDrawer);

function showView(view) {
  currentView = view;

  for (const [id, viewName] of [
    ["dashboardView", "dashboard"],
    ["monitoringView", "monitoring"],
    ["reportsView", "reports"],
    ["archiveView", "archive"],
  ]) {
    $(id)?.classList.toggle("hidden", viewName !== view);
  }

  document.querySelectorAll(".nav[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });

  const titles = {
    dashboard: "Monitoring Hari Ini",
    monitoring: activeArchive ? "Monitoring Arsip" : "Monitoring",
    reports: "Laporan",
    archive: "Arsip",
  };

  $("pageTitle").textContent = titles[view] || "PNM";
  $("todayDate").textContent = activeArchive
    ? `Snapshot ${formatDate(activeArchive.date)}`
    : formatDate(todayData?.date);

  if (view === "monitoring") {
    closeArchiveDetail();
    renderMonitoring();
    setTimeout(() => jatimMap?.invalidateSize(), 100);
  }

  if (view === "dashboard") {
    activeArchive = null;
    setTimeout(() => {
      jatimMap?.invalidateSize();
      renderMap(getTodayDataset());
    }, 120);
  }
}

function setMonitoringMode(mode) {
  monitoringMode = mode;
  document.querySelectorAll(".mode-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  renderMonitoring();
}

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.view === "reports") {
      activeArchive = null;
      showView("reports");
      return;
    }

    activeArchive = null;
    showView(button.dataset.view);
  });
});

document.querySelectorAll("[data-open-monitoring]").forEach((button) => {
  button.addEventListener("click", () => {
    activeArchive = null;
    showView("monitoring");
    setMonitoringMode(button.dataset.openMonitoring || "all");
    if (button.dataset.openMonitoring === "jatim") {
      monitoringMode = "jatim";
    }
    renderMonitoring();
  });
});

document.querySelectorAll(".mode-tab[data-mode]").forEach((button) => {
  button.addEventListener("click", () => setMonitoringMode(button.dataset.mode));
});

[
  "search",
  "region",
  "polres",
  "priority",
  "scope",
  "category",
].forEach((id) => {
  $(id)?.addEventListener("input", () => {
    if (id === "region") {
      populateMonitoringFilters(getActiveNewsDataset());
    }
    renderMonitoring();
  });

  $(id)?.addEventListener("change", () => {
    if (id === "region") {
      populateMonitoringFilters(getActiveNewsDataset());
    }
    renderMonitoring();
  });
});

$("clearFilters")?.addEventListener("click", () => {
  $("search").value = "";
  $("region").value = "all";
  $("polres").value = "all";
  $("priority").value = "all";
  $("scope").value = "all";
  $("category").value = "all";
  populateMonitoringFilters(getActiveNewsDataset());
  renderMonitoring();
});

function initMap() {
  if (jatimMap || !window.L || !$("jatimMap")) return;

  jatimMap = L.map("jatimMap", {
    zoomControl: true,
    tap: true,
  }).setView([-7.75, 112.45], 8);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(jatimMap);
}

function renderMap(items) {
  if (!jatimMap) return;

  mapMarkers.forEach((marker) => marker.remove());
  mapMarkers = [];

  const groups = new Map();

  items
    .filter(isJatim)
    .forEach((item) => {
      const locality = getLocality(item);
      if (!locality || !JATIM_COORDS[locality]) return;

      if (!groups.has(locality)) {
        groups.set(locality, {
          name: locality,
          items: [],
          high: 0,
          cases: new Set(),
        });
      }

      const group = groups.get(locality);
      group.items.push(item);

      if (item.case_id) {
        group.cases.add(item.case_id);
      }
    });

  const todayCasesById = new Map(
    getActiveCasesDataset().map((item) => [item.case_id, item])
  );

  for (const group of groups.values()) {
    for (const caseId of group.cases) {
      const caseItem = todayCasesById.get(caseId);
      if (caseItem && getPriority(caseItem) === "high") {
        group.high += 1;
      }
    }
  }

  $("mapCount").textContent = `${number(groups.size)} lokasi`;

  const bounds = [];

  for (const group of groups.values()) {
    const coords = JATIM_COORDS[group.name];
    bounds.push(coords);

    const size = Math.min(40, 22 + Math.floor(group.items.length / 2) * 2);
    const level = group.high
      ? "high"
      : [...group.cases]
          .some((id) => getPriority(todayCasesById.get(id)) === "medium")
        ? "medium"
        : "low";

    const icon = L.divIcon({
      className: "",
      html: `<div class="pnm-marker ${level}" style="width:${size}px;height:${size}px">${group.items.length}</div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });

    const marker = L.marker(coords, { icon }).addTo(jatimMap);

    const topArticles = [...group.items]
      .sort(
        (a, b) =>
          new Date(getItemDate(b) || 0) -
          new Date(getItemDate(a) || 0)
      )
      .slice(0, 5);

    marker.bindPopup(`
      <div class="map-popup">
        <strong>${escapeHtml(group.name)}</strong>
        <div>${number(group.items.length)} berita · ${number(group.cases.size)} case</div>
        ${group.high ? `<div class="map-popup-high">High case: ${number(group.high)}</div>` : ""}
        <div class="map-popup-list">
          ${topArticles
            .map((item) => `<div>• ${escapeHtml(getTitle(item))}</div>`)
            .join("")}
        </div>
        <button class="map-open-region">Buka monitoring wilayah →</button>
      </div>
    `);

    marker.on("popupopen", () => {
      document.querySelectorAll(".map-open-region").forEach((button) => {
        button.onclick = () => {
          activeArchive = null;
          showView("monitoring");
          $("region").value = group.name;
          monitoringMode = "jatim";
          populateMonitoringFilters(getTodayDataset());
          renderMonitoring();
        };
      });
    });

    marker.on("click", () => marker.openPopup());
    mapMarkers.push(marker);
  }

  if (bounds.length) {
    jatimMap.fitBounds(bounds, {
      padding: [25, 25],
      maxZoom: 9,
    });
  } else {
    jatimMap.setView([-7.75, 112.45], 8);
  }

  setTimeout(() => jatimMap.invalidateSize(), 100);
}

async function loadArchive(date) {
  try {
    const data = await fetchJson(`data/archive/${encodeURIComponent(date)}.json`);
    activeArchive = data;
    openArchiveDetail();
  } catch (error) {
    console.error(error);
    alert("Snapshot arsip tidak dapat dibuka.");
  }
}

function renderArchiveList() {
  const target = $("archiveList");
  if (!target) return;

  if (!archiveFiles.length) {
    target.innerHTML = `<div class="empty">Belum ada arsip.</div>`;
    return;
  }

  target.innerHTML = archiveFiles
    .map(
      (date) => `
        <button class="archive-item" data-archive-date="${escapeHtml(date)}">
          <span>
            <strong>${escapeHtml(formatDate(date))}</strong>
            <small>Snapshot monitoring</small>
          </span>
          <b>→</b>
        </button>
      `
    )
    .join("");

  target.querySelectorAll("[data-archive-date]").forEach((button) => {
    button.addEventListener("click", () => loadArchive(button.dataset.archiveDate));
  });
}

function openArchiveDetail() {
  if (!activeArchive) return;

  $("archiveDetail").classList.remove("hidden");
  $("archiveList").parentElement.parentElement.classList.add("hidden");

  $("archiveTitle").textContent = formatDate(activeArchive.date);
  $("archiveUpdated").textContent =
    "Update: " +
    formatDateTime(activeArchive.last_successful_update || activeArchive.updated_at);

  $("archiveNews").textContent = number(activeArchive.summary?.news_today);
  $("archiveCases").textContent = number(activeArchive.summary?.cases_today);
  $("archiveJatim").textContent = number(activeArchive.summary?.jatim_news);
  $("archiveHigh").textContent = number(activeArchive.summary?.priority_high);

  activeArchiveMode = "all";
  document.querySelectorAll("[data-archive-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.archiveMode === "all");
  });

  populateArchiveFilters();
  renderArchiveNews();
}

let activeArchiveMode = "all";

function closeArchiveDetail() {
  $("archiveDetail")?.classList.add("hidden");
  const parent = $("archiveList")?.parentElement?.parentElement;
  parent?.classList.remove("hidden");
}

$("archiveBack")?.addEventListener("click", () => {
  activeArchive = null;
  closeArchiveDetail();
  showView("archive");
});

document.querySelectorAll("[data-archive-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    activeArchiveMode = button.dataset.archiveMode;
    document.querySelectorAll("[data-archive-mode]").forEach((item) => {
      item.classList.toggle(
        "active",
        item.dataset.archiveMode === activeArchiveMode
      );
    });
    renderArchiveNews();
  });
});

function populateArchiveFilters() {
  const items = activeArchive?.news?.items || [];

  const build = (element, first, values, selected) => {
    element.innerHTML =
      `<option value="all">${first}</option>` +
      values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("");

    if ([...element.options].some((option) => option.value === selected)) {
      element.value = selected;
    }
  };

  const region = $("archiveRegion");
  const polres = $("archivePolres");
  const category = $("archiveCategory");

  const regions = unique(
    items
      .filter(isJatim)
      .map(getLocality)
      .sort((a, b) => a.localeCompare(b))
  );

  const polresValues = unique(
    items
      .map((item) => item.polres)
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b))
  );

  const categoryValues = unique(
    items.map(getCategory).sort((a, b) => a.localeCompare(b))
  );

  build(region, "Semua Wilayah", regions, region.value);
  build(polres, "Semua Polres", polresValues, polres.value);
  build(category, "Semua Kategori", categoryValues, category.value);
}

function renderArchiveNews() {
  if (!activeArchive) return;

  const items = activeArchive.news?.items || [];
  let results = [...items];

  if (activeArchiveMode === "jatim") {
    results = results.filter(isJatim);
  }

  if (activeArchiveMode === "high") {
    results = results.filter((item) => getPriority(item) === "high");
  }

  const search = ($("archiveSearch").value || "").trim().toLowerCase();
  const region = $("archiveRegion").value;
  const polres = $("archivePolres").value;
  const priority = $("archivePriority").value;
  const scope = $("archiveScope").value;
  const category = $("archiveCategory").value;

  if (search) {
    results = results.filter((item) =>
      [
        getTitle(item),
        getSource(item),
        item.region,
        item.polres,
        item.category,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(search)
    );
  }

  if (region !== "all") results = results.filter((item) => getLocality(item) === region);
  if (polres !== "all") results = results.filter((item) => item.polres === polres);
  if (priority !== "all") results = results.filter((item) => getPriority(item) === priority);
  if (scope !== "all") results = results.filter((item) => getScope(item) === scope);
  if (category !== "all") results = results.filter((item) => getCategory(item) === category);

  $("archiveResultCount").textContent = `${number(results.length)} berita`;
  $("archiveResultContext").textContent = `Snapshot ${formatDate(activeArchive.date)}`;

  const target = $("archiveNewsList");
  target.innerHTML = results.length
    ? results.map(newsCardCompact).join("")
    : `<div class="empty">Tidak ada berita pada filter tersebut.</div>`;

  bindArticleClicks(target);
}

[
  "archiveSearch",
  "archiveRegion",
  "archivePolres",
  "archivePriority",
  "archiveScope",
  "archiveCategory",
].forEach((id) => {
  $(id)?.addEventListener("input", renderArchiveNews);
  $(id)?.addEventListener("change", renderArchiveNews);
});

$("archiveClear")?.addEventListener("click", () => {
  $("archiveSearch").value = "";
  $("archiveRegion").value = "all";
  $("archivePolres").value = "all";
  $("archivePriority").value = "all";
  $("archiveScope").value = "all";
  $("archiveCategory").value = "all";
  renderArchiveNews();
});

$("refresh")?.addEventListener("click", () => {
  activeArchive = null;
  loadAllData();
});

window.addEventListener("resize", () => {
  setTimeout(() => jatimMap?.invalidateSize(), 100);
});
