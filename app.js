const TODAY_URL = "data/today.json";
const NEWS_URL = "data/news.json";
const ARCHIVE_INDEX_URL = "data/archive/index.json";

const DEMO_EMAIL = "admin@propam-jatim.go.id";
const DEMO_PASSWORD = "PropamJatim2026!";

let todayData = null;
let newsData = [];
let archiveFiles = [];
let currentView = "dashboard";
let jatimMap = null;
let mapMarkers = [];

const POLRES_JATIM = [
  "Polrestabes Surabaya",
  "Polres Gresik",
  "Polres Sidoarjo",
  "Polres Mojokerto",
  "Polres Mojokerto Kota",
  "Polres Jombang",
  "Polres Nganjuk",
  "Polres Madiun",
  "Polres Madiun Kota",
  "Polres Magetan",
  "Polres Ngawi",
  "Polres Bojonegoro",
  "Polres Tuban",
  "Polres Lamongan",
  "Polres Kediri",
  "Polres Kediri Kota",
  "Polres Tulungagung",
  "Polres Trenggalek",
  "Polres Blitar",
  "Polres Blitar Kota",
  "Polres Malang",
  "Polresta Malang Kota",
  "Polres Batu",
  "Polres Pasuruan",
  "Polres Pasuruan Kota",
  "Polres Probolinggo",
  "Polres Probolinggo Kota",
  "Polres Lumajang",
  "Polres Jember",
  "Polres Bondowoso",
  "Polres Situbondo",
  "Polres Banyuwangi",
  "Polres Pacitan",
  "Polres Ponorogo",
  "Polres Sumenep",
  "Polres Pamekasan",
  "Polres Sampang",
  "Polres Bangkalan"
];

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
  Bangkalan: [-7.0455, 112.7351]
};

const $ = (id) => document.getElementById(id);

function number(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toLocaleString("id-ID") : "0";
}

function formatDate(value) {
  if (!value) return "-";

  const d = new Date(value);

  if (Number.isNaN(d.getTime())) {
    return String(value);
  }

  return d.toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "long",
    year: "numeric"
  });
}

function formatDateTime(value) {
  if (!value) return "-";

  const d = new Date(value);

  if (Number.isNaN(d.getTime())) {
    return String(value);
  }

  return (
    d.toLocaleString("id-ID", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
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

function setStatus(text, online) {
  const textEl = $("statusText");
  const dotEl = $("statusDot");

  if (textEl) {
    textEl.textContent = text;
  }

  if (dotEl) {
    dotEl.style.background = online ? "#43d19e" : "#ff5c67";
  }
}

function showApp() {
  $("login").classList.add("hidden");
  $("app").classList.remove("hidden");
  loadAllData();
}

const loginForm = $("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const email = $("email").value.trim();
    const password = $("password").value;

    if (email === DEMO_EMAIL && password === DEMO_PASSWORD) {
      sessionStorage.setItem("pnm_logged_in", "1");
      showApp();
    } else {
      $("loginError").textContent = "Email atau password salah.";
    }
  });
}

if ($("logout")) {
  $("logout").addEventListener("click", () => {
    sessionStorage.removeItem("pnm_logged_in");
    location.reload();
  });
}

if (sessionStorage.getItem("pnm_logged_in") === "1") {
  showApp();
}

async function loadAllData() {
  setStatus("Memuat data...", false);

  try {
    const [todayResponse, newsResponse] = await Promise.all([
      fetch(TODAY_URL + "?t=" + Date.now()),
      fetch(NEWS_URL + "?t=" + Date.now())
    ]);

    if (!todayResponse.ok) {
      throw new Error("today.json gagal dimuat");
    }

    if (!newsResponse.ok) {
      throw new Error("news.json gagal dimuat");
    }

    todayData = await todayResponse.json();

    const newsJson = await newsResponse.json();

    newsData = Array.isArray(newsJson)
      ? newsJson
      : newsJson.items || [];

    renderToday();
    populateFilters();
    renderLatest();
    renderCategories();
    renderNewsList();

    initMap();
    renderMap();

    await loadArchives();

    setStatus("Data aktif", true);

  } catch (error) {
    console.error(error);

    setStatus("Gagal memuat data", false);

    if ($("lastUpdated")) {
      $("lastUpdated").textContent = "Data gagal dimuat";
    }
  }
}

function renderToday() {
  if (!todayData) return;

  const summary = todayData.summary || {};
  const news = todayData.news || {};
  const cases = todayData.cases || {};
  const social = todayData.social || {};

  if ($("todayDate")) {
    $("todayDate").textContent = formatDate(todayData.date);
  }

  if ($("lastUpdated")) {
    $("lastUpdated").textContent =
      "Update terakhir: " +
      formatDateTime(
        todayData.last_successful_update ||
        todayData.updated_at ||
        todayData.update_time
      );
  }

  if ($("sTotal")) {
    $("sTotal").textContent =
      number(summary.news_today ?? news.detected ?? todayData.news_count);
  }

  if ($("sCases")) {
    $("sCases").textContent =
      number(summary.cases_today ?? cases.active ?? todayData.cases_count);
  }

  if ($("sYoutube")) {
    $("sYoutube").textContent =
      number(summary.youtube_today ?? social.detected ?? todayData.youtube_count);
  }

  if ($("sHigh")) {
    $("sHigh").textContent =
      number(summary.priority_high ?? news.priority_high);
  }

  if ($("sNegative")) {
    $("sNegative").textContent =
      number(summary.negative_today ?? news.negative);
  }

  if ($("sJatim")) {
    $("sJatim").textContent =
      number(summary.jatim_news ?? news.jatim);
  }

  if ($("sCaseHigh")) {
    $("sCaseHigh").textContent =
      number(cases.priority_high);
  }

  if ($("sTotalCases")) {
    $("sTotalCases").textContent =
      number(
        todayData.database?.total_cases ??
        cases.database_total ??
        0
      );
  }

  if ($("summaryNews")) {
    $("summaryNews").textContent =
      number(news.detected);
  }

  if ($("summaryCases")) {
    $("summaryCases").textContent =
      number(cases.active);
  }

  if ($("summaryYoutube")) {
    $("summaryYoutube").textContent =
      number(social.detected);
  }
}

function getItemDate(item) {
  return (
    item.collected_at ||
    item.published_at ||
    item.pubDate ||
    item.date ||
    ""
  );
}

function todayItems() {
  const date = todayData?.date;

  if (!date) return [];

  return newsData
    .filter((item) => {
      return String(getItemDate(item)).startsWith(date);
    })
    .sort((a, b) => {
      const da = new Date(getItemDate(a) || 0);
      const db = new Date(getItemDate(b) || 0);

      return db - da;
    });
}

function getTitle(item) {
  return (
    item.title ||
    item.headline ||
    item.name ||
    "Tanpa judul"
  );
}

function getSource(item) {
  return (
    item.source ||
    item.publisher ||
    item.site ||
    "-"
  );
}

function isJatim(item) {
  if (item.is_jatim === true) return true;

  const text = [
    item.region,
    item.location,
    item.area,
    item.province,
    item.polres
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return (
    text.includes("jawa timur") ||
    text.includes("jatim") ||
    text.includes("surabaya") ||
    text.includes("sidoarjo") ||
    text.includes("malang") ||
    text.includes("gresik") ||
    text.includes("tuban") ||
    text.includes("sampang") ||
    text.includes("situbondo") ||
    text.includes("jember") ||
    text.includes("banyuwangi") ||
    text.includes("pasuruan") ||
    text.includes("probolinggo") ||
    text.includes("kediri") ||
    text.includes("blitar") ||
    text.includes("tulungagung") ||
    text.includes("trenggalek") ||
    text.includes("ponorogo") ||
    text.includes("madiun") ||
    text.includes("ngawi") ||
    text.includes("bojonegoro") ||
    text.includes("lamongan") ||
    text.includes("mojokerto") ||
    text.includes("jombang") ||
    text.includes("nganjuk") ||
    text.includes("magetan") ||
    text.includes("pacitan") ||
    text.includes("lumajang") ||
    text.includes("bondowoso") ||
    text.includes("pamekasan") ||
    text.includes("sumenep") ||
    text.includes("bangkalan")
  );
}

function getPriority(item) {
  return String(
    item.priority ||
    item.priority_level ||
    item.level ||
    ""
  ).toLowerCase();
}

function getScope(item) {
  return String(
    item.scope ||
    item.type ||
    item.scope_type ||
    ""
  ).toLowerCase();
}

function getCategory(item) {
  return (
    item.category ||
    item.kategori ||
    "-"
  );
}

function renderLatest() {
  const container = $("latest");

  if (!container) return;

  const items = todayItems().slice(0, 8);

  if (!items.length) {
    container.innerHTML =
      '<div class="archive-empty">Belum ada berita terdeteksi hari ini.</div>';
    return;
  }

  container.innerHTML = items
    .map((item) => {
      return `
        <article class="news-mini">
          <div class="news-meta">
            ${escapeHtml(isJatim(item) ? "Jawa Timur" : "Indonesia")}
            ·
            ${escapeHtml(getSource(item))}
          </div>

          <div class="news-title">
            ${escapeHtml(getTitle(item))}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderCategories() {
  const container = $("categories");

  if (!container) return;

  const news = todayData?.news || {};

  const values = [
    ["Negatif", Number(news.negative || 0)],
    ["Positif", Number(news.positive || 0)],
    ["Netral", Number(news.neutral || 0)],
    ["Ungkap Kasus", Number(news.case || news.cases || 0)]
  ];

  const max = Math.max(
    ...values.map((item) => item[1]),
    1
  );

  container.innerHTML = values
    .map(([label, value]) => {
      return `
        <div class="bar">
          <div class="bar-top">
            <span>${escapeHtml(label)}</span>
            <strong>${number(value)}</strong>
          </div>

          <div class="bar-bg">
            <div
              class="bar-fill"
              style="width:${Math.round((value / max) * 100)}%"
            ></div>
          </div>
        </div>
      `;
    })
    .join("");
}

function populateFilters() {
  const categoryEl = $("category");
  const polresEl = $("polres");

  if (categoryEl) {
    const categories = [
      ...new Set(
        newsData
          .map((item) => getCategory(item))
          .filter((value) => value && value !== "-")
      )
    ].sort((a, b) =>
      String(a).localeCompare(String(b))
    );

    categoryEl.innerHTML =
      '<option value="all">Semua Kategori</option>' +
      categories
        .map(
          (item) =>
            `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`
        )
        .join("");
  }

  if (polresEl) {
    polresEl.innerHTML =
      '<option value="all">Semua Polres Jatim</option>' +
      POLRES_JATIM
        .map(
          (item) =>
            `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`
        )
        .join("");
  }
}

function getSearchText(item) {
  return [
    getTitle(item),
    getSource(item),
    item.publisher,
    item.region,
    item.location,
    item.area,
    getCategory(item),
    item.polres,
    item.province
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function renderNewsList() {
  const container = $("list");

  if (!container) return;

  let items = [...newsData];

  const search = (
    $("search")?.value || ""
  )
    .trim()
    .toLowerCase();

  const region =
    $("region")?.value || "all";

  const polres =
    $("polres")?.value || "all";

  const priority =
    $("priority")?.value || "all";

  const scope =
    $("scope")?.value || "all";

  const category =
    $("category")?.value || "all";

  const from =
    $("dateFrom")?.value || "";

  const to =
    $("dateTo")?.value || "";

  if (search) {
    items = items.filter((item) =>
      getSearchText(item).includes(search)
    );
  }

  if (region === "jatim") {
    items = items.filter(isJatim);
  }

  if (region === "outside") {
    items = items.filter(
      (item) => !isJatim(item)
    );
  }

  if (polres !== "all") {
    items = items.filter(
      (item) =>
        String(item.polres || "") === polres
    );
  }

  if (priority !== "all") {
    items = items.filter(
      (item) =>
        getPriority(item) === priority
    );
  }

  if (scope !== "all") {
    items = items.filter(
      (item) =>
        getScope(item) === scope
    );
  }

  if (category !== "all") {
    items = items.filter(
      (item) =>
        String(getCategory(item)) === category
    );
  }

  if (from) {
    items = items.filter((item) =>
      String(getItemDate(item)).slice(0, 10) >= from
    );
  }

  if (to) {
    items = items.filter((item) =>
      String(getItemDate(item)).slice(0, 10) <= to
    );
  }

  if (currentView === "jatim") {
    items = items.filter(isJatim);
  }

  if (currentView === "high") {
    items = items.filter(
      (item) => getPriority(item) === "high"
    );
  }

  items.sort((a, b) => {
    const da = new Date(getItemDate(a) || 0);
    const db = new Date(getItemDate(b) || 0);

    return db - da;
  });

  if (!items.length) {
    container.innerHTML =
      '<div class="archive-empty">Tidak ada data yang sesuai filter.</div>';
    return;
  }

  container.innerHTML = items
    .slice(0, 200)
    .map((item) => {
      const priority = getPriority(item);

      return `
        <article class="news-card">

          <div class="news-card-top">

            <div>
              <div class="news-card-meta">
                ${escapeHtml(getSource(item))}
                ·
                ${escapeHtml(
                  item.region ||
                  item.location ||
                  (isJatim(item)
                    ? "Jawa Timur"
                    : "Indonesia")
                )}

                ${
                  item.polres
                    ? " · " +
                      escapeHtml(item.polres)
                    : ""
                }
              </div>

              <h3>
                ${escapeHtml(getTitle(item))}
              </h3>

              <div class="news-card-meta">
                ${escapeHtml(getCategory(item))}
              </div>
            </div>

            <div class="badges">

              ${
                priority
                  ? `
                    <span class="pill ${escapeHtml(priority)}">
                      ${escapeHtml(priority.toUpperCase())}
                    </span>
                  `
                  : ""
              }

              ${
                getScope(item)
                  ? `
                    <span class="pill">
                      ${escapeHtml(getScope(item))}
                    </span>
                  `
                  : ""
              }

            </div>

          </div>

        </article>
      `;
    })
    .join("");
}

function deriveMapLocations() {
  const grouped = new Map();

  todayItems()
    .filter(isJatim)
    .forEach((item) => {

      let name = "";

      if (item.polres) {
        name = String(item.polres)
          .replace(/^Polrestabes\s+/i, "")
          .replace(/^Polresta\s+/i, "")
          .replace(/^Polres\s+/i, "")
          .replace(/\s+Kota$/i, "")
          .trim();
      }

      if (!name) {
        const text = [
          item.region,
          item.location,
          item.area,
          item.province
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        name =
          Object.keys(JATIM_COORDS).find(
            (key) =>
              text.includes(
                key.toLowerCase()
              )
          ) || "";
      }

      const key =
        Object.keys(JATIM_COORDS).find(
          (key) =>
            key.toLowerCase() ===
            name.toLowerCase()
        );

      if (!key) return;

      const entry =
        grouped.get(key) || {
          name: key,
          count: 0,
          high: 0,
          medium: 0,
          low: 0,
          titles: []
        };

      entry.count++;

      const priority = getPriority(item);

      if (priority === "high") {
        entry.high++;
      } else if (priority === "medium") {
        entry.medium++;
      } else {
        entry.low++;
      }

      if (
        getTitle(item) &&
        entry.titles.length < 3
      ) {
        entry.titles.push(
          getTitle(item)
        );
      }

      grouped.set(key, entry);
    });

  return [...grouped.values()];
}

function markerLevel(item) {
  if (
    item.high >= 2 ||
    item.count >= 5
  ) {
    return "high";
  }

  if (
    item.medium >= 1 ||
    item.count >= 2
  ) {
    return "medium";
  }

  return "low";
}

function initMap() {
  if (
    jatimMap ||
    !window.L ||
    !$("jatimMap")
  ) {
    return;
  }

  jatimMap = L.map(
    "jatimMap",
    {
      zoomControl: true
    }
  ).setView(
    [-7.75, 112.45],
    8
  );

  L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      maxZoom: 18,
      attribution:
        "&copy; OpenStreetMap contributors"
    }
  ).addTo(jatimMap);
}

function renderMap() {
  if (!jatimMap) return;

  mapMarkers.forEach(
    (marker) => marker.remove()
  );

  mapMarkers = [];

  const locations =
    deriveMapLocations();

  if ($("mapCount")) {
    $("mapCount").textContent =
      `${locations.length} lokasi`;
  }

  locations.forEach((item) => {

    const level =
      markerLevel(item);

    const coords =
      JATIM_COORDS[item.name];

    if (!coords) return;

    const size =
      Math.min(
        36,
        18 + item.count * 3
      );

    const icon =
      L.divIcon({
        className: "",
        html: `
          <div
            class="pnm-marker ${level}"
            style="
              width:${size}px;
              height:${size}px
            "
          >
            ${item.count}
          </div>
        `,
        iconSize: [
          size,
          size
        ],
        iconAnchor: [
          size / 2,
          size / 2
        ]
      });

    const marker =
      L.marker(
        coords,
        { icon }
      ).addTo(jatimMap);

    const titles =
      item.titles.length
        ? `
          <ul style="padding-left:17px;margin:6px 0 0">
            ${item.titles
              .map(
                (title) =>
                  `<li>${escapeHtml(title)}</li>`
              )
              .join("")}
          </ul>
        `
        : "";

    marker.bindPopup(`
      <b>${escapeHtml(item.name)}</b>
      <br>
      ${number(item.count)} berita hari ini

      ${
        item.high
          ? `<br>Prioritas tinggi: ${number(item.high)}`
          : ""
      }

      ${titles}
    `);

    mapMarkers.push(marker);
  });

  if (locations.length) {
    const bounds =
      L.latLngBounds(
        locations.map(
          (item) =>
            JATIM_COORDS[item.name]
        )
      );

    jatimMap.fitBounds(
      bounds.pad(0.18),
      {
        maxZoom: 9
      }
    );
  } else {
    jatimMap.setView(
      [-7.75, 112.45],
      8
    );
  }

  setTimeout(() => {
    jatimMap.invalidateSize();
  }, 150);
}

async function loadArchives() {
  try {
    const response =
      await fetch(
        ARCHIVE_INDEX_URL +
        "?t=" +
        Date.now()
      );

    if (!response.ok) {
      archiveFiles = [];
    } else {
      const data =
        await response.json();

      archiveFiles =
        Array.isArray(data)
          ? data
          : data.files || [];
    }

  } catch (error) {
    console.warn(
      "Archive index tidak tersedia:",
      error
    );

    archiveFiles = [];
  }

  renderArchiveQuick();
  renderArchiveList();
}

function archiveDate(file) {
  if (typeof file === "string") {
    return file;
  }

  return file?.date || "";
}

function renderArchiveQuick() {
  const container =
    $("archiveQuick");

  if (!container) return;

  if (!archiveFiles.length) {
    container.innerHTML = `
      <div class="archive-item">
        <div class="archive-date">
          ${formatDate(todayData?.date)}
        </div>
        <div class="archive-meta">
          Snapshot hari ini
        </div>
      </div>
    `;

    return;
  }

  container.innerHTML =
    archiveFiles
      .slice(0, 5)
      .map((file) => {

        const date =
          archiveDate(file);

        return `
          <div
            class="archive-item"
            data-archive="${escapeHtml(date)}"
          >
            <div class="archive-date">
              ${formatDate(date)}
            </div>

            <div class="archive-meta">
              Buka snapshot →
            </div>
          </div>
        `;
      })
      .join("");

  container
    .querySelectorAll(
      "[data-archive]"
    )
    .forEach((element) => {
      element.addEventListener(
        "click",
        () =>
          openArchive(
            element.dataset.archive
          )
      );
    });
}

function renderArchiveList() {
  const container =
    $("archiveList");

  if (!container) return;

  if (!archiveFiles.length) {
    container.innerHTML =
      '<div class="archive-empty">Belum ada daftar arsip yang tersedia.</div>';

    return;
  }

  container.innerHTML =
    archiveFiles
      .map((file) => {

        const date =
          archiveDate(file);

        return `
          <div
            class="archive-item"
            data-archive="${escapeHtml(date)}"
          >
            <div class="archive-date">
              ${formatDate(date)}
            </div>

            <div class="archive-meta">
              Lihat snapshot monitoring →
            </div>
          </div>
        `;
      })
      .join("");

  container
    .querySelectorAll(
      "[data-archive]"
    )
    .forEach((element) => {
      element.addEventListener(
        "click",
        () =>
          openArchive(
            element.dataset.archive
          )
      );
    });
}

async function openArchive(date) {
  if (!date) return;

  try {
    const response =
      await fetch(
        `data/archive/${encodeURIComponent(
          date
        )}.json?t=${Date.now()}`
      );

    if (!response.ok) {
      throw new Error(
        "Arsip tidak ditemukan"
      );
    }

    const data =
      await response.json();

    showView("archive");

    $("archiveDetail")
      .classList.remove(
        "hidden"
      );

    $("archiveTitle")
      .textContent =
      `Monitoring ${formatDate(
        data.date
      )}`;

    $("archiveUpdated")
      .textContent =
      "Update terakhir: " +
      formatDateTime(
        data.last_successful_update ||
        data.updated_at ||
        data.update_time
      );

    $("archiveNews")
      .textContent =
      number(
        data.news?.detected
      );

    $("archiveCases")
      .textContent =
      number(
        data.cases?.active
      );

    $("archiveYoutube")
      .textContent =
      number(
        data.social?.detected
      );

    $("archiveHigh")
      .textContent =
      number(
        data.summary?.priority_high
      );

  } catch (error) {
    console.error(error);

    alert(
      "Arsip tanggal tersebut belum tersedia."
    );
  }
}

function showView(view) {
  currentView = view;

  const dashboard =
    $("dashboardView");

  const list =
    $("listView");

  const archive =
    $("archiveView");

  if (dashboard) {
    dashboard.classList.toggle(
      "hidden",
      view !== "dashboard"
    );
  }

  if (list) {
    list.classList.toggle(
      "hidden",
      !(
        view === "news" ||
        view === "jatim" ||
        view === "high"
      )
    );
  }

  if (archive) {
    archive.classList.toggle(
      "hidden",
      view !== "archive"
    );
  }

  const titles = {
    dashboard: "Monitoring Hari Ini",
    news: "Semua Berita",
    jatim: "Jawa Timur",
    high: "Prioritas Tinggi",
    archive: "Arsip Monitoring"
  };

  if ($("pageTitle")) {
    $("pageTitle").textContent =
      titles[view] ||
      "Monitoring Hari Ini";
  }

  document
    .querySelectorAll(".nav")
    .forEach((button) => {
      button.classList.toggle(
        "active",
        button.dataset.view === view
      );
    });

  if (
    view !== "dashboard" &&
    view !== "archive"
  ) {
    renderNewsList();
  }

  if (view === "dashboard") {
    setTimeout(() => {
      if (jatimMap) {
        jatimMap.invalidateSize();
        renderMap();
      }
    }, 150);
  }
}

document
  .querySelectorAll("[data-view]")
  .forEach((button) => {
    button.addEventListener(
      "click",
      () => {
        showView(
          button.dataset.view
        );
      }
    );
  });

[
  "search",
  "region",
  "polres",
  "priority",
  "scope",
  "category",
  "dateFrom",
  "dateTo"
].forEach((id) => {

  const element = $(id);

  if (!element) return;

  element.addEventListener(
    "input",
    renderNewsList
  );

  element.addEventListener(
    "change",
    renderNewsList
  );
});

if ($("clearFilters")) {
  $("clearFilters").addEventListener(
    "click",
    () => {

      ["search", "dateFrom", "dateTo"]
        .forEach((id) => {
          if ($(id)) {
            $(id).value = "";
          }
        });

      [
        "region",
        "polres",
        "priority",
        "scope",
        "category"
      ].forEach((id) => {
        if ($(id)) {
          $(id).value = "all";
        }
      });

      renderNewsList();
    }
  );
}

if ($("refresh")) {
  $("refresh").addEventListener(
    "click",
    loadAllData
  );
}
