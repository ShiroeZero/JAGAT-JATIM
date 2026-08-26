<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>PNM — Polri Negative News Monitor</title>

<link rel="stylesheet" href="styles.css">

<style>
/* ============================================================
   TODAY DASHBOARD
   ============================================================ */

.today-date {
  font-size: 13px;
  color: #8b95a7;
  margin-top: 4px;
}

.update-box {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.update-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #20c77a;
  box-shadow: 0 0 10px rgba(32,199,122,.45);
}

.archive-panel {
  margin-top: 20px;
}

.archive-list {
  display: grid;
  grid-template-columns: repeat(auto-fill,minmax(180px,1fr));
  gap: 10px;
}

.archive-item {
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.025);
  border-radius: 10px;
  padding: 13px 15px;
  cursor: pointer;
  transition: .18s ease;
}

.archive-item:hover {
  background: rgba(255,255,255,.055);
  transform: translateY(-1px);
}

.archive-item.active {
  border-color: rgba(70,130,255,.65);
  background: rgba(70,130,255,.08);
}

.archive-date {
  font-weight: 700;
  font-size: 14px;
}

.archive-meta {
  margin-top: 5px;
  color: #8b95a7;
  font-size: 12px;
}

.today-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: rgba(32,199,122,.1);
  color: #37d58d;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.case-summary {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: 10px;
}

.case-mini {
  padding: 14px;
  border-radius: 10px;
  background: rgba(255,255,255,.025);
  border: 1px solid rgba(255,255,255,.07);
}

.case-mini strong {
  display: block;
  font-size: 23px;
  margin-top: 4px;
}

.case-mini span {
  font-size: 12px;
  color: #8b95a7;
}

.archive-empty {
  padding: 20px;
  text-align: center;
  color: #8b95a7;
}

.archive-view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 20px;
}

.archive-view-date {
  font-size: 14px;
  color: #8b95a7;
}

.map-placeholder {
  min-height: 260px;
  border-radius: 12px;
  border: 1px dashed rgba(255,255,255,.12);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #7e899b;
  background:
    radial-gradient(
      circle at center,
      rgba(50,100,180,.08),
      transparent 65%
    );
}

.map-placeholder strong {
  display: block;
  color: #b8c1cf;
  margin-bottom: 5px;
}

@media(max-width:800px) {
  .case-summary {
    grid-template-columns:1fr;
  }

  .update-box {
    display:none;
  }
}
</style>
</head>

<body>

<!-- ============================================================
     LOGIN
     ============================================================ -->

<div id="login" class="login-shell">

  <div class="login-card">

    <div class="brand-mark">PNM</div>

    <h1>Polri Negative News Monitor</h1>

    <p class="muted">
      Dashboard monitoring berita negatif terkait
      oknum/anggota Polri.
    </p>

    <form id="loginForm">

      <label>Email</label>

      <input
        id="email"
        type="email"
        autocomplete="username"
        required
        value="admin@propam-jatim.go.id"
      >

      <label>Password</label>

      <input
        id="password"
        type="password"
        autocomplete="current-password"
        required
      >

      <button
        class="primary"
        type="submit"
      >
        Masuk
      </button>

      <div
        id="loginError"
        class="error"
      ></div>

    </form>

    <p class="demo-note">
      Akun demo:
      <b>admin@propam-jatim.go.id</b>
      ·
      <b>PropamJatim2026!</b>
    </p>

  </div>

</div>


<!-- ============================================================
     APP
     ============================================================ -->

<div id="app" class="app hidden">

  <!-- ==========================================================
       SIDEBAR
       ========================================================== -->

  <aside class="sidebar">

    <div class="side-brand">
      <span>PNM</span>
      <small>NEWS MONITOR</small>
    </div>

    <nav>

      <button
        class="nav active"
        data-view="dashboard"
      >
        Dashboard
      </button>

      <button
        class="nav"
        data-view="news"
      >
        Semua Berita
      </button>

      <button
        class="nav"
        data-view="jatim"
      >
        Jawa Timur
      </button>

      <button
        class="nav"
        data-view="high"
      >
        Prioritas Tinggi
      </button>

      <button
        class="nav"
        data-view="archive"
      >
        Arsip Monitoring
      </button>

    </nav>

    <div class="side-bottom">

      <div class="collector-status">
        <span id="statusDot"></span>
        <span id="statusText">
          Memuat data...
        </span>
      </div>

      <button
        id="logout"
        class="logout"
      >
        Keluar
      </button>

    </div>

  </aside>


  <!-- ==========================================================
       MAIN
       ========================================================== -->

  <main class="main">

    <!-- TOPBAR -->

    <header class="topbar">

      <div>

        <div class="eyebrow">
          BIDANG MONITORING
        </div>

        <h2 id="pageTitle">
          Monitoring Hari Ini
        </h2>

        <div
          id="todayDate"
          class="today-date"
        >
          Memuat tanggal...
        </div>

      </div>

      <div class="top-actions">

        <div class="update-box">

          <span class="update-dot"></span>

          <span id="lastUpdated">
            Memuat update...
          </span>

        </div>

        <button
          id="refresh"
          class="secondary"
        >
          ↻ Refresh
        </button>

      </div>

    </header>


    <!-- ========================================================
         DASHBOARD TODAY
         ======================================================== -->

    <section
      id="dashboardView"
      class="view"
    >

      <div class="hero">

        <div>

          <span class="eyebrow">
            POLRI NEGATIVE NEWS MONITOR
          </span>

          <h1>
            Monitoring Hari Ini
          </h1>

          <p>
            Menampilkan kondisi monitoring pada hari berjalan.
            Data historis tersedia melalui Arsip Monitoring.
          </p>

        </div>

        <div class="hero-badge">
          TODAY
        </div>

      </div>


      <!-- ======================================================
           TODAY STATS
           ====================================================== -->

      <div class="stats">

        <div class="stat">

          <span>
            Berita Hari Ini
          </span>

          <strong id="sTotal">
            0
          </strong>

        </div>


        <div class="stat">

          <span>
            Case Hari Ini
          </span>

          <strong id="sCases">
            0
          </strong>

        </div>


        <div class="stat">

          <span>
            YouTube Hari Ini
          </span>

          <strong id="sYoutube">
            0
          </strong>

        </div>


        <div class="stat danger">

          <span>
            Prioritas Tinggi
          </span>

          <strong id="sHigh">
            0
          </strong>

        </div>

      </div>


      <!-- ======================================================
           SECONDARY STATS
           ====================================================== -->

      <div class="stats">

        <div class="stat">

          <span>
            Berita Negatif
          </span>

          <strong id="sNegative">
            0
          </strong>

        </div>


        <div class="stat">

          <span>
            Jawa Timur
          </span>

          <strong id="sJatim">
            0
          </strong>

        </div>


        <div class="stat">

          <span>
            Case Prioritas
          </span>

          <strong id="sCaseHigh">
            0
          </strong>

        </div>


        <div class="stat">

          <span>
            Database Case
          </span>

          <strong id="sTotalCases">
            0
          </strong>

        </div>

      </div>


      <!-- ======================================================
           CASE SUMMARY
           ====================================================== -->

      <section class="panel">

        <div class="panel-head">

          <div class="section-title">

            <h3>
              Kondisi Hari Ini
            </h3>

            <span class="today-badge">
              LIVE SNAPSHOT
            </span>

          </div>

        </div>

        <div class="case-summary">

          <div class="case-mini">

            <span>
              Artikel Monitoring
            </span>

            <strong id="summaryNews">
              0
            </strong>

          </div>

          <div class="case-mini">

            <span>
              Peristiwa / Case
            </span>

            <strong id="summaryCases">
              0
            </strong>

          </div>

          <div class="case-mini">

            <span>
              Konten YouTube
            </span>

            <strong id="summaryYoutube">
              0
            </strong>

          </div>

        </div>

      </section>


      <!-- ======================================================
           MAIN GRID
           ====================================================== -->

      <div class="grid2">

        <!-- BERITA -->

        <section class="panel">

          <div class="panel-head">

            <h3>
              Berita Hari Ini
            </h3>

            <button
              class="linkbtn"
              data-view="news"
            >
              Lihat semua →
            </button>

          </div>

          <div id="latest"></div>

        </section>


        <!-- CATEGORY -->

        <section class="panel">

          <div class="panel-head">

            <h3>
              Komposisi Hari Ini
            </h3>

          </div>

          <div
            id="categories"
            class="bars"
          ></div>

        </section>

      </div>


      <!-- ======================================================
           JATIM MAP
           ====================================================== -->

      <section class="panel">

        <div class="panel-head">

          <h3>
            Peta Monitoring Jawa Timur
          </h3>

          <span class="muted">
            Kondisi hari ini
          </span>

        </div>

        <div class="map-placeholder">

          <div>

            <strong>
              Peta Kerawanan Jawa Timur
            </strong>

            <span>
              Modul peta kabupaten/kota akan ditempatkan di sini.
            </span>

          </div>

        </div>

      </section>


      <!-- ======================================================
           ARCHIVE QUICK ACCESS
           ====================================================== -->

      <section class="panel archive-panel">

        <div class="panel-head">

          <h3>
            Arsip Monitoring
          </h3>

          <button
            class="linkbtn"
            data-view="archive"
          >
            Lihat semua →
          </button>

        </div>

        <div
          id="archiveQuick"
          class="archive-list"
        ></div>

      </section>

    </section>


    <!-- ========================================================
         NEWS LIST
         ======================================================== -->

    <section
      id="listView"
      class="view hidden"
    >

      <div class="filters">

        <input
          id="search"
          placeholder="Cari judul, sumber, wilayah, kategori, Polres..."
        >

        <select id="region">

          <option value="all">
            Semua Wilayah
          </option>

          <option value="jatim">
            Jawa Timur
          </option>

          <option value="outside">
            Luar Jawa Timur
          </option>

        </select>


        <select id="polres">

          <option value="all">
            Semua Polres Jatim
          </option>

        </select>


        <select id="priority">

          <option value="all">
            Semua Prioritas
          </option>

          <option value="high">
            Tinggi
          </option>

          <option value="medium">
            Sedang
          </option>

          <option value="low">
            Rendah
          </option>

        </select>


        <select id="scope">

          <option value="all">
            Semua Jenis Berita
          </option>

          <option value="negative">
            Negatif terhadap anggota/institusi
          </option>

          <option value="case">
            Ungkap kasus oleh Polri
          </option>

          <option value="positive">
            Positif/Prestasi/Kegiatan
          </option>

          <option value="neutral">
            Netral/Lainnya
          </option>

        </select>


        <select id="category">

          <option value="all">
            Semua Kategori
          </option>

        </select>


        <div>

          <label class="filter-label">
            Dari tanggal
          </label>

          <input
            id="dateFrom"
            type="date"
          >

        </div>


        <div>

          <label class="filter-label">
            Sampai tanggal
          </label>

          <input
            id="dateTo"
            type="date"
          >

        </div>


        <button
          id="clearFilters"
          class="secondary clear"
        >
          Reset Filter
        </button>

      </div>


      <div
        id="list"
        class="news-list"
      ></div>

    </section>


    <!-- ========================================================
         ARCHIVE
         ======================================================== -->

    <section
      id="archiveView"
      class="view hidden"
    >

      <div class="archive-view-header">

        <div>

          <div class="eyebrow">
            HISTORI MONITORING
          </div>

          <h2>
            Arsip Monitoring
          </h2>

          <div class="archive-view-date">
            Pilih tanggal untuk melihat snapshot monitoring.
          </div>

        </div>

      </div>


      <section class="panel">

        <div class="panel-head">

          <h3>
            Snapshot Tersedia
          </h3>

        </div>

        <div
          id="archiveList"
          class="archive-list"
        ></div>

      </section>


      <section
        id="archiveDetail"
        class="panel hidden"
      >

        <div class="panel-head">

          <div>

            <h3 id="archiveTitle">
              Arsip
            </h3>

            <div
              id="archiveUpdated"
              class="muted"
            ></div>

          </div>

          <span class="today-badge">
            ARCHIVE
          </span>

        </div>


        <div class="stats">

          <div class="stat">

            <span>
              Berita
            </span>

            <strong id="archiveNews">
              0
            </strong>

          </div>


          <div class="stat">

            <span>
              Case
            </span>

            <strong id="archiveCases">
              0
            </strong>

          </div>


          <div class="stat">

            <span>
              YouTube
            </span>

            <strong id="archiveYoutube">
              0
            </strong>

          </div>


          <div class="stat danger">

            <span>
              Prioritas
            </span>

            <strong id="archiveHigh">
              0
            </strong>

          </div>

        </div>

      </section>

    </section>

  </main>

</div>


<!-- ============================================================
     SCRIPT
     ============================================================ -->

<script>

/* ============================================================
   CONFIG
   ============================================================ */

const TODAY_URL = "data/today.json";
const NEWS_URL = "data/news.json";

const ARCHIVE_INDEX_URL =
  "data/archive/index.json";


/* ============================================================
   STATE
   ============================================================ */

let todayData = null;
let newsData = [];
let archiveFiles = [];

let currentView = "dashboard";


/* ============================================================
   HELPERS
   ============================================================ */

function number(value) {

  const n = Number(value);

  if (!Number.isFinite(n)) {
    return "0";
  }

  return n.toLocaleString("id-ID");
}


function formatDate(dateString) {

  if (!dateString) {
    return "-";
  }

  const d = new Date(dateString);

  if (Number.isNaN(d.getTime())) {
    return dateString;
  }

  return d.toLocaleDateString(
    "id-ID",
    {
      day: "2-digit",
      month: "long",
      year: "numeric"
    }
  );
}


function formatDateTime(dateString) {

  if (!dateString) {
    return "-";
  }

  const d = new Date(dateString);

  if (Number.isNaN(d.getTime())) {
    return dateString;
  }

  return d.toLocaleString(
    "id-ID",
    {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    }
  ) + " WIB";
}


function escapeHtml(value) {

  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


/* ============================================================
   LOGIN
   ============================================================ */

const login =
  document.getElementById("login");

const app =
  document.getElementById("app");

const loginForm =
  document.getElementById("loginForm");

const loginError =
  document.getElementById("loginError");


loginForm.addEventListener(
  "submit",
  function(event) {

    event.preventDefault();

    const email =
      document.getElementById("email").value.trim();

    const password =
      document.getElementById("password").value;

    if (
      email === "admin@propam-jatim.go.id"
      &&
      password === "PropamJatim2026!"
    ) {

      sessionStorage.setItem(
        "pnm_logged_in",
        "1"
      );

      showApp();

    } else {

      loginError.textContent =
        "Email atau password salah.";

    }

  }
);


function showApp() {

  login.classList.add("hidden");
  app.classList.remove("hidden");

  loadAllData();

}


if (
  sessionStorage.getItem(
    "pnm_logged_in"
  ) === "1"
) {

  showApp();

}


/* ============================================================
   LOGOUT
   ============================================================ */

document
  .getElementById("logout")
  .addEventListener(
    "click",
    function() {

      sessionStorage.removeItem(
        "pnm_logged_in"
      );

      location.reload();

    }
  );


/* ============================================================
   LOAD DATA
   ============================================================ */

async function loadAllData() {

  setStatus(
    "Memuat data...",
    false
  );

  try {

    const [
      todayResponse,
      newsResponse
    ] = await Promise.all([
      fetch(
        TODAY_URL + "?t=" + Date.now()
      ),
      fetch(
        NEWS_URL + "?t=" + Date.now()
      )
    ]);

    if (!todayResponse.ok) {
      throw new Error(
        "today.json gagal dimuat"
      );
    }

    if (!newsResponse.ok) {
      throw new Error(
        "news.json gagal dimuat"
      );
    }

    todayData =
      await todayResponse.json();

    const newsJson =
      await newsResponse.json();

    newsData =
      Array.isArray(newsJson)
        ? newsJson
        : (
            newsJson.items || []
          );

    renderToday();

    renderLatest();

    renderCategories();

    renderNewsList();

    await loadArchives();

    setStatus(
      "Data aktif",
      true
    );

  } catch (error) {

    console.error(error);

    setStatus(
      "Gagal memuat data",
      false
    );

    document.getElementById(
      "lastUpdated"
    ).textContent =
      "Data gagal dimuat";

  }

}


/* ============================================================
   STATUS
   ============================================================ */

function setStatus(
  text,
  online
) {

  document.getElementById(
    "statusText"
  ).textContent = text;

  const dot =
    document.getElementById(
      "statusDot"
    );

  if (online) {

    dot.style.background =
      "#20c77a";

  } else {

    dot.style.background =
      "#d94b4b";

  }

}


/* ============================================================
   RENDER TODAY
   ============================================================ */

function renderToday() {

  if (!todayData) {
    return;
  }

  const summary =
    todayData.summary || {};

  const news =
    todayData.news || {};

  const cases =
    todayData.cases || {};

  const social =
    todayData.social || {};


  document.getElementById(
    "todayDate"
  ).textContent =
    formatDate(
      todayData.date
    );


  document.getElementById(
    "lastUpdated"
  ).textContent =
    "Update terakhir: "
    +
    formatDateTime(
      todayData.last_successful_update
      ||
      todayData.updated_at
    );


  document.getElementById(
    "sTotal"
  ).textContent =
    number(
      summary.news_today
      ??
      news.detected
    );


  document.getElementById(
    "sCases"
  ).textContent =
    number(
      summary.cases_today
      ??
      cases.active
    );


  document.getElementById(
    "sYoutube"
  ).textContent =
    number(
      summary.youtube_today
      ??
      social.detected
    );


  document.getElementById(
    "sHigh"
  ).textContent =
    number(
      summary.priority_high
    );


  document.getElementById(
    "sNegative"
  ).textContent =
    number(
      summary.negative_today
      ??
      news.negative
    );


  document.getElementById(
    "sJatim"
  ).textContent =
    number(
      summary.jatim_news
      ??
      news.jatim
    );


  document.getElementById(
    "sCaseHigh"
  ).textContent =
    number(
      cases.priority_high
    );


  document.getElementById(
    "sTotalCases"
  ).textContent =
    number(
      todayData.database?.total_cases
      ??
      cases.database_total
      ??
      0
    );


  document.getElementById(
    "summaryNews"
  ).textContent =
    number(
      news.detected
    );


  document.getElementById(
    "summaryCases"
  ).textContent =
    number(
      cases.active
    );


  document.getElementById(
    "summaryYoutube"
  ).textContent =
    number(
      social.detected
    );

}


/* ============================================================
   LATEST NEWS
   ============================================================ */

function renderLatest() {

  const container =
    document.getElementById(
      "latest"
    );

  if (!newsData.length) {

    container.innerHTML =
      '<div class="archive-empty">Tidak ada berita.</div>';

    return;

  }

  const today =
    todayData?.date;

  const items =
    newsData
      .filter(item => {

        const time =
          item.collected_at
          ||
          item.published_at;

        if (!time || !today) {
          return false;
        }

        return time.startsWith(
          today
        );

      })
      .sort(
        (
          a,
          b
        ) => {

          const da =
            new Date(
              a.collected_at
              ||
              a.published_at
            );

          const db =
            new Date(
              b.collected_at
              ||
              b.published_at
            );

          return db - da;

        }
      )
      .slice(
        0,
        8
      );

  if (!items.length) {

    container.innerHTML =
      '<div class="archive-empty">Belum ada berita terdeteksi hari ini.</div>';

    return;

  }

  container.innerHTML =
    items.map(
      item => {

        const title =
          escapeHtml(
            item.title
            ||
            "Tanpa judul"
          );

        const source =
          escapeHtml(
            item.source
            ||
            item.publisher
            ||
            "-"
          );

        const region =
          item.is_jatim
            ? "Jawa Timur"
            : "Indonesia";

        return `
          <article
            style="
              padding:12px 0;
              border-bottom:1px solid rgba(255,255,255,.06);
            "
          >

            <div
              style="
                font-size:12px;
                color:#8b95a7;
                margin-bottom:5px;
              "
            >
              ${escapeHtml(region)}
              ·
              ${source}
            </div>

            <div
              style="
                font-weight:650;
                line-height:1.45;
              "
            >
              ${title}
            </div>

          </article>
        `;

      }
    ).join("");

}


/* ============================================================
   CATEGORIES
   ============================================================ */

function renderCategories() {

  const container =
    document.getElementById(
      "categories"
    );

  if (!todayData) {
    return;
  }

  const news =
    todayData.news || {};

  const values = [
    {
      label: "Negatif",
      value: Number(
        news.negative || 0
      )
    },
    {
      label: "Positif",
      value: Number(
        news.positive || 0
      )
    },
    {
      label: "Netral",
      value: Number(
        news.neutral || 0
      )
    }
  ];

  const max =
    Math.max(
      ...values.map(
        x => x.value
      ),
      1
    );

  container.innerHTML =
    values.map(
      item => {

        const width =
          Math.round(
            item.value
            /
            max
            *
            100
          );

        return `
          <div
            style="
              margin-bottom:14px;
            "
          >

            <div
              style="
                display:flex;
                justify-content:space-between;
                margin-bottom:5px;
                font-size:13px;
              "
            >
              <span>
                ${escapeHtml(item.label)}
              </span>

              <strong>
                ${number(item.value)}
              </strong>

            </div>

            <div
              style="
                height:7px;
                background:rgba(255,255,255,.07);
                border-radius:99px;
                overflow:hidden;
              "
            >

              <div
                style="
                  width:${width}%;
                  height:100%;
                  background:rgba(80,130,255,.8);
                  border-radius:99px;
                "
              ></div>

            </div>

          </div>
        `;

      }
    ).join("");

}


/* ============================================================
   NEWS LIST
   ============================================================ */

function renderNewsList() {

  const container =
    document.getElementById(
      "list"
    );

  if (!container) {
    return;
  }

  let items =
    [...newsData];

  const search =
    (
      document.getElementById(
        "search"
      )?.value
      ||
      ""
    )
      .toLowerCase()
      .trim();

  const region =
    document.getElementById(
      "region"
    )?.value
    ||
    "all";

  const priority =
    document.getElementById(
      "priority"
    )?.value
    ||
    "all";

  const scope =
    document.getElementById(
      "scope"
    )?.value
    ||
    "all";

  const category =
    document.getElementById(
      "category"
    )?.value
    ||
    "all";


  if (search) {

    items =
      items.filter(
        item => {

          const text = [
            item.title,
            item.source,
            item.publisher,
            item.region,
            item.category,
            item.polres
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return text.includes(
            search
          );

        }
      );

  }


  if (region === "jatim") {

    items =
      items.filter(
        item =>
          item.is_jatim === true
      );

  }


  if (region === "outside") {

    items =
      items.filter(
        item =>
          item.is_jatim !== true
      );

  }


  if (priority !== "all") {

    items =
      items.filter(
        item =>
          String(
            item.priority || ""
          ).toLowerCase()
          ===
          priority
      );

  }


  if (scope !== "all") {

    items =
      items.filter(
        item =>
          String(
            item.scope || ""
          ).toLowerCase()
          ===
          scope
      );

  }


  if (category !== "all") {

    items =
      items.filter(
        item =>
          String(
            item.category || ""
          )
          ===
          category
      );

  }


  if (!items.length) {

    container.innerHTML =
      '<div class="archive-empty">Tidak ada data yang sesuai filter.</div>';

    return;

  }


  container.innerHTML =
    items
      .slice(
        0,
        100
      )
      .map(
        item => {

          return `
            <article
              class="panel"
              style="margin-bottom:10px;"
            >

              <div
                style="
                  font-size:12px;
                  color:#8b95a7;
                  margin-bottom:6px;
                "
              >
                ${escapeHtml(
                  item.source
                  ||
                  item.publisher
                  ||
                  "-"
                )}
                ·
                ${escapeHtml(
                  item.region
                  ||
                  "Indonesia"
                )}
              </div>

              <h3
                style="
                  margin:0 0 8px;
                "
              >
                ${escapeHtml(
                  item.title
                  ||
                  "Tanpa judul"
                )}
              </h3>

              <div
                style="
                  font-size:12px;
                  color:#8b95a7;
                "
              >
                ${escapeHtml(
                  item.category
                  ||
                  "-"
                )}
              </div>

            </article>
          `;

        }
      )
      .join("");

}


/* ============================================================
   ARCHIVE
   ============================================================ */

async function loadArchives() {

  const quick =
    document.getElementById(
      "archiveQuick"
    );

  const list =
    document.getElementById(
      "archiveList"
    );


  try {

    /*
     * archive/index.json belum dibuat oleh workflow.
     * Untuk sementara kita mencoba membaca daftar
     * menggunakan GitHub API / fallback.
     */

    const response =
      await fetch(
        ARCHIVE_INDEX_URL
        + "?t="
        + Date.now()
      );

    if (
      response.ok
    ) {

      const data =
        await response.json();

      archiveFiles =
        Array.isArray(data)
          ? data
          : (
              data.files
              ||
              []
            );

    } else {

      archiveFiles = [];

    }

  } catch {

    archiveFiles = [];

  }


  /*
   * today selalu tersedia sebagai quick reference.
   */

  renderArchiveQuick();

  renderArchiveList();

}


function renderArchiveQuick() {

  const container =
    document.getElementById(
      "archiveQuick"
    );

  if (!container) {
    return;
  }


  if (!archiveFiles.length) {

    container.innerHTML = `
      <div class="archive-item">
        <div class="archive-date">
          ${formatDate(
            todayData?.date
          )}
        </div>

        <div class="archive-meta">
          Hari ini
        </div>
      </div>
    `;

    return;

  }


  container.innerHTML =
    archiveFiles
      .slice(
        0,
        5
      )
      .map(
        file => {

          const date =
            typeof file === "string"
              ? file
              : file.date;

          return `
            <div
              class="archive-item"
              onclick="openArchive('${date}')"
            >

              <div class="archive-date">
                ${formatDate(date)}
              </div>

              <div class="archive-meta">
                Buka snapshot →
              </div>

            </div>
          `;

        }
      )
      .join("");

}


function renderArchiveList() {

  const container =
    document.getElementById(
      "archiveList"
    );

  if (!container) {
    return;
  }


  if (!archiveFiles.length) {

    container.innerHTML = `
      <div class="archive-empty">
        Arsip akan muncul setelah snapshot
        harian berikutnya tersedia.
      </div>
    `;

    return;

  }


  container.innerHTML =
    archiveFiles
      .map(
        file => {

          const date =
            typeof file === "string"
              ? file
              : file.date;

          return `
            <div
              class="archive-item"
              onclick="openArchive('${date}')"
            >

              <div class="archive-date">
                ${formatDate(date)}
              </div>

              <div class="archive-meta">
                Lihat snapshot monitoring →
              </div>

            </div>
          `;

        }
      )
      .join("");

}


async function openArchive(date) {

  if (!date) {
    return;
  }

  try {

    const response =
      await fetch(
        `data/archive/${date}.json?t=${Date.now()}`
      );

    if (!response.ok) {
      throw new Error(
        "Arsip tidak ditemukan"
      );
    }

    const data =
      await response.json();

    showView(
      "archive"
    );

    document.getElementById(
      "archiveDetail"
    ).classList.remove(
      "hidden"
    );

    document.getElementById(
      "archiveTitle"
    ).textContent =
      `Monitoring ${formatDate(data.date)}`;

    document.getElementById(
      "archiveUpdated"
    ).textContent =
      "Update terakhir: "
      +
      formatDateTime(
        data.last_successful_update
        ||
        data.updated_at
      );

    document.getElementById(
      "archiveNews"
    ).textContent =
      number(
        data.news?.detected
      );

    document.getElementById(
      "archiveCases"
    ).textContent =
      number(
        data.cases?.active
      );

    document.getElementById(
      "archiveYoutube"
    ).textContent =
      number(
        data.social?.detected
      );

    document.getElementById(
      "archiveHigh"
    ).textContent =
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


/* ============================================================
   NAVIGATION
   ============================================================ */

function showView(view) {

  currentView =
    view;

  const dashboard =
    document.getElementById(
      "dashboardView"
    );

  const list =
    document.getElementById(
      "listView"
    );

  const archive =
    document.getElementById(
      "archiveView"
    );


  dashboard.classList.add(
    "hidden"
  );

  list.classList.add(
    "hidden"
  );

  archive.classList.add(
    "hidden"
  );


  if (
    view === "dashboard"
  ) {

    dashboard.classList.remove(
      "hidden"
    );

    document.getElementById(
      "pageTitle"
    ).textContent =
      "Monitoring Hari Ini";

  }


  if (
    view === "news"
    ||
    view === "jatim"
    ||
    view === "high"
  ) {

    list.classList.remove(
      "hidden"
    );

    document.getElementById(
      "pageTitle"
    ).textContent =
      view === "jatim"
        ? "Jawa Timur"
        : view === "high"
          ? "Prioritas Tinggi"
          : "Semua Berita";

    renderNewsList();

  }


  if (
    view === "archive"
  ) {

    archive.classList.remove(
      "hidden"
    );

    document.getElementById(
      "pageTitle"
    ).textContent =
      "Arsip Monitoring";

  }


  document
    .querySelectorAll(
      ".nav"
    )
    .forEach(
      button => {

        button.classList.toggle(
          "active",
          button.dataset.view
          ===
          view
        );

      }
    );

}


function setupNavigation() {

  document
    .querySelectorAll(
      "[data-view]"
    )
    .forEach(
      button => {

        button.addEventListener(
          "click",
          function() {

            showView(
              this.dataset.view
            );

          }
        );

      }
    );

}


setupNavigation();


/* ============================================================
   FILTER EVENTS
   ============================================================ */

[
  "search",
  "region",
  "polres",
  "priority",
  "scope",
  "category",
  "dateFrom",
  "dateTo"
].forEach(
  id => {

    const element =
      document.getElementById(
        id
      );

    if (element) {

      element.addEventListener(
        "input",
        renderNewsList
      );

      element.addEventListener(
        "change",
        renderNewsList
      );

    }

  }
);


document
  .getElementById(
    "clearFilters"
  )
  ?.addEventListener(
    "click",
    function() {

      [
        "search",
        "region",
        "polres",
        "priority",
        "scope",
        "category",
        "dateFrom",
        "dateTo"
      ].forEach(
        id => {

          const element =
            document.getElementById(
              id
            );

          if (!element) {
            return;
          }

          if (
            element.tagName
            ===
            "SELECT"
          ) {

            element.value =
              "all";

          } else {

            element.value =
              "";

          }

        }
      );

      renderNewsList();

    }
  );


/* ============================================================
   REFRESH
   ============================================================ */

document
  .getElementById(
    "refresh"
  )
  .addEventListener(
    "click",
    function() {

      loadAllData();

    }
  );

</script>

</body>
</html>
