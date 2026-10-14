/* JAGAT V7.0 — Laporan harian berbasis data Jatim + template resmi. */
(() => {
  const REPORT_TEMPLATES = {
    kabid: {
      label: "KABIDPROPAM POLDA JAWA TIMUR",
      recipient: "KABIDPROPAM POLDA JAWA TIMUR",
      sender: "KASUBBIDPAMINAL BIDPROPAM POLDA JAWA TIMUR"
    },
    kadenc: {
      label: "KADEN C ROPAMINAL DIVPROPAM POLRI",
      recipient: "KADEN C ROPAMINAL DIVPROPAM POLRI",
      sender: "KASUBBIDPAMINAL BIDPROPAM POLDA JAWA TIMUR"
    }
  };

  const esc = (v) => typeof escapeHtml === "function" ? escapeHtml(v) : String(v ?? "");
  const fmt = (v) => typeof number === "function" ? number(v) : Number(v || 0).toLocaleString("id-ID");
  const titleOf = (x) => typeof getTitle === "function" ? getTitle(x) : (x?.title || "Tanpa judul");
  const sourceOf = (x) => typeof getSource === "function" ? getSource(x) : (x?.source || x?.publisher || "");
  const dateOf = (x) => typeof getItemDate === "function" ? getItemDate(x) : (x?.collected_at || x?.published_at || "");
  const scopeOf = (x) => String(x?.scope || "neutral").toLowerCase();
  const urlOf = (x) => {
    const preferred = x?.original_url || x?.url;
    return typeof normalizeUrl === "function" ? normalizeUrl(preferred) : String(preferred || "");
  };

  let currentData = null;
  let currentReportText = "";
  let initialized = false;
  let selectedSimulationKeys = new Set();
  let simulationDateKey = "";

  function todayDate() {
    return (typeof todayData !== "undefined" && todayData?.date) ? todayData.date : new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Jakarta" });
  }

  function displayDate(date) {
    return new Intl.DateTimeFormat("id-ID", {
      weekday: "long", day: "2-digit", month: "long", year: "numeric", timeZone: "Asia/Jakarta"
    }).format(new Date(`${date}T12:00:00+07:00`));
  }

  function activeTodayDataset() {
    const items = typeof todayJatimItems === "function" ? todayJatimItems() : [];
    const cases = typeof globalCases === "function" ? globalCases() : [];
    return { date: todayDate(), items, cases, updated: typeof todayData !== "undefined" ? (todayData?.last_successful_update || todayData?.updated_at) : "" };
  }

  async function loadDataset(date) {
    if (date === todayDate()) return activeTodayDataset();
    const res = await fetch(`data/archive/${encodeURIComponent(date)}.json?t=${Date.now()}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Snapshot ${date} tidak tersedia (HTTP ${res.status}).`);
    const data = await res.json();
    return {
      date,
      items: Array.isArray(data?.news?.items) ? data.news.items.filter(x => x?.is_jatim === true || String(x?.region || "").toLowerCase() === "jawa timur") : [],
      cases: Array.isArray(data?.cases?.items) ? data.cases.items : [],
      updated: data?.last_successful_update || data?.updated_at || ""
    };
  }

  function uniqueArticles(items) {
    const seen = new Set();
    return items.filter(item => {
      const key = item?.id || urlOf(item) || `${titleOf(item)}|${sourceOf(item)}`;
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function sortNews(items) {
    return uniqueArticles(items).slice().sort((a, b) => {
      const scoreA = typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(a, currentData?.cases || []) : Number(a?.attention_score || 0);
      const scoreB = typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(b, currentData?.cases || []) : Number(b?.attention_score || 0);
      return scoreB - scoreA || new Date(dateOf(b) || 0) - new Date(dateOf(a) || 0);
    });
  }

  function sections(data) {
    const negative = sortNews(data.items.filter(x => scopeOf(x) === "negative"));
    const positive = sortNews(data.items.filter(x => scopeOf(x) === "positive"));
    return { negative, positive };
  }

  function linesForNews(items) {
    if (!items.length) return ["- NIHIL"];
    const out = [];
    items.forEach((item, index) => {
      out.push(`${index + 1}.  *${titleOf(item)}*`);
      const url = urlOf(item);
      if (url) out.push(`- ${url}`);
    });
    return out.length ? out : ["- NIHIL"];
  }

  function manualLines(value) {
    const text = String(value || "").trim();
    if (!text) return ["- NIHIL"];
    return text.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
  }

  function buildReport(data, templateKey) {
    const t = REPORT_TEMPLATES[templateKey];
    const { negative, positive } = sections(data);
    const hoax = manualLines(document.getElementById("reportHoax")?.value);
    const handled = manualLines(document.getElementById("reportHandled")?.value);
    const amplifiedPositive = manualLines(document.getElementById("reportPositiveAmplification")?.value);

    const lines = [
      "Kepada Yth:",
      `*${t.recipient}*`,
      "",
      "Dari:",
      `*${t.sender}*`,
      "",
      `Selamat Sore Komandan, mohon izin melaporkan kegiatan Pelaporan Mitigasi dan Amplifikasi Penanganan Berita Hoax, Berita Positif, serta Berita yang telah ditangani oleh Polda Jawa Timur, pada hari ${displayDate(data.date)}, dengan rincian sebagai berikut:`,
      "",
      "*A. PERIHAL*",
      "",
      "Laporan harian kegiatan mitigasi dan amplifikasi pemberitaan terkait isu negatif (Hoax), pemberitaan positif, serta tindak lanjut penanganan terhadap isu yang berkembang di wilayah hukum Polda Jawa Timur.",
      "",
      "*B. LINK BERITA NEGATIF*",
      "",
      ...linesForNews(negative),
      "",
      "*C. LINK BERITA POSITIF*",
      "",
      ...linesForNews(positive),
      "",
      "*D. LINK AMPLIFIKASI*",
      "",
      "LINK AMPLIFIKASI BERITA HOAX",
      ...hoax,
      "",
      "LINK AMPLIFIKASI BERITA NEGATIF TELAH DITANGANI",
      ...handled,
      "",
      "LINK AMPLIFIKASI BERITA POSITIF",
      ...amplifiedPositive
    ];
    return lines.join("\n").replace(/\n{3,}/g, "\n\n");
  }

  function renderShell() {
    const view = document.getElementById("reportsView");
    if (!view) return;
    view.innerHTML = `
      <div class="report-hero">
        <div>
          <div class="eyebrow">JAGAT · LAPORAN</div>
          <h2>Generator Laporan Harian</h2>
          <p>Susun laporan dari data pemberitaan Jawa Timur yang sudah diproses JAGAT. Format mengikuti template pelaporan yang tersedia di sistem.</p>
        </div>
        <span class="report-hero-badge">JAWA TIMUR</span>
      </div>

      <section class="panel">
        <div class="report-toolbar">
          <div class="report-field">
            <label for="reportTemplate">Format laporan</label>
            <select id="reportTemplate">
              <option value="kabid">KABIDPROPAM POLDA JAWA TIMUR</option>
              <option value="kadenc">KADEN C ROPAMINAL DIVPROPAM POLRI</option>
            </select>
          </div>
          <div class="report-field">
            <label for="reportDate">Tanggal laporan</label>
            <input id="reportDate" type="date" value="${esc(todayDate())}">
          </div>
          <div class="report-actions">
            <button id="generateReport" class="secondary report-primary" type="button"><i class="fa-solid fa-file-circle-check"></i> Buat Laporan</button>
          </div>
        </div>
      </section>

      <div id="reportSummary" class="report-summary"></div>

      <div class="report-layout">
        <section class="report-panel">
          <h3>Amplifikasi</h3>
          <div class="muted">Bagian D tidak diisi otomatis agar JAGAT tidak membuat tautan amplifikasi yang tidak pernah dicatat.</div>
          <div class="report-manual-grid">
            <div class="report-manual"><label for="reportHoax">Berita Hoax</label><textarea id="reportHoax" placeholder="Kosongkan bila NIHIL."></textarea></div>
            <div class="report-manual"><label for="reportHandled">Berita Negatif Telah Ditangani</label><textarea id="reportHandled" placeholder="Kosongkan bila NIHIL."></textarea></div>
            <div class="report-manual"><label for="reportPositiveAmplification">Berita Positif</label><textarea id="reportPositiveAmplification" placeholder="Satu tautan/baris. Kosongkan bila NIHIL."></textarea></div>
          </div>
          <div class="report-note"><strong>Catatan:</strong> data berita negatif dan positif diambil otomatis hanya dari artikel yang terpetakan sebagai Jawa Timur pada tanggal yang dipilih. Bagian amplifikasi tetap manual.</div>
        </section>

        <section class="report-panel report-preview-wrap">
          <div class="report-preview-head">
            <div><h3>Pratinjau Laporan</h3><div id="reportSourceCount" class="report-source-count">Belum dibuat</div></div>
            <div class="report-preview-actions">
              <button id="copyReport" class="secondary" type="button"><i class="fa-regular fa-copy"></i> Salin</button>
              <button id="printReport" class="secondary" type="button"><i class="fa-solid fa-print"></i> Cetak / PDF</button>
            </div>
          </div>
          <pre id="reportPreview" class="report-preview-empty">Pilih tanggal lalu tekan “Buat Laporan”.</pre>
        </section>
      </div>

      <section class="report-panel report-simulation-panel">
        <div class="report-simulation-head">
          <div>
            <div class="report-kicker">SIMULASI · EKSPOR TXT</div>
            <h3>Simulasi pencarian untuk berita terpilih</h3>
            <p class="muted">Pilih kandidat berita positif. Berkas TXT berisi nomor urut dan tautan uji pada domain khusus <code>.example</code>; berkas ini tidak menjalankan pencarian Google, membuka tautan, atau memublikasikan apa pun.</p>
          </div>
          <div class="report-simulation-actions">
            <button id="simulationAutoSelect" class="secondary" type="button"><i class="fa-solid fa-wand-magic-sparkles"></i> Pilih saran otomatis</button>
            <button id="simulationClearSelect" class="secondary" type="button">Kosongkan pilihan</button>
          </div>
        </div>
        <div class="report-simulation-meta">
          <span id="simulationSelectedCount">0 berita dipilih</span>
          <span>24.990–25.000 tautan uji per berita · 408 variasi sumber uji · 38 kabupaten/kota Jatim</span>
        </div>
        <div id="simulationCandidates" class="report-simulation-candidates">
          <div class="report-simulation-empty">Pilih tanggal dan buat laporan untuk memuat kandidat berita positif.</div>
        </div>
        <div class="report-simulation-footer">
          <div id="simulationDownloadStatus" class="muted" aria-live="polite">Belum ada berkas simulasi dibuat.</div>
          <button id="downloadSimulationTxt" class="secondary report-primary" type="button" disabled><i class="fa-solid fa-file-arrow-down"></i> Unduh TXT SIMULASI pencarian Google</button>
        </div>
      </section>
    `;

    document.getElementById("reportDate")?.addEventListener("change", () => generate());
    document.getElementById("reportTemplate")?.addEventListener("change", () => generate(false));
    document.getElementById("generateReport")?.addEventListener("click", () => generate());
    document.getElementById("copyReport")?.addEventListener("click", copyReport);
    document.getElementById("printReport")?.addEventListener("click", printReport);
    document.getElementById("simulationAutoSelect")?.addEventListener("click", selectSuggestedSimulationNews);
    document.getElementById("simulationClearSelect")?.addEventListener("click", clearSimulationSelection);
    document.getElementById("simulationCandidates")?.addEventListener("change", onSimulationCandidateChange);
    document.getElementById("downloadSimulationTxt")?.addEventListener("click", downloadSimulationTxt);
    initialized = true;
    generate(false);
  }

  function renderSummary(data) {
    const items = data.items || [];
    const negative = items.filter(x => scopeOf(x) === "negative").length;
    const positive = items.filter(x => scopeOf(x) === "positive").length;
    const cases = new Set(items.map(x => x.case_id).filter(Boolean)).size;
    const high = items.filter(x => {
      const score = typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(x, data.cases || []) : Number(x?.attention_score || 0);
      return score >= 70;
    }).length;
    const target = document.getElementById("reportSummary");
    if (!target) return;
    target.innerHTML = [
      ["Berita Jatim", items.length],
      ["Negatif", negative],
      ["Positif", positive],
      ["Atensi Tinggi", high]
    ].map(([label, value]) => `<div class="report-stat"><span>${esc(label)}</span><strong>${fmt(value)}</strong></div>`).join("");
    const sourceCount = document.getElementById("reportSourceCount");
    if (sourceCount) sourceCount.textContent = `${fmt(items.length)} berita Jatim · ${fmt(cases)} case terkait · data ${esc(data.date)}`;
  }

  const EAST_JAVA_REGENCIES = [
    "Bangkalan", "Banyuwangi", "Blitar", "Bojonegoro", "Bondowoso", "Gresik",
    "Jember", "Jombang", "Kediri", "Lamongan", "Lumajang", "Madiun",
    "Magetan", "Malang", "Mojokerto", "Nganjuk", "Ngawi", "Pacitan",
    "Pamekasan", "Pasuruan", "Ponorogo", "Probolinggo", "Sampang", "Sidoarjo",
    "Situbondo", "Sumenep", "Trenggalek", "Tuban", "Tulungagung",
    "Batu", "Blitar Kota", "Kediri Kota", "Madiun Kota", "Malang Kota",
    "Mojokerto Kota", "Pasuruan Kota", "Probolinggo Kota", "Surabaya"
  ];

  function simulationKey(item) {
    return String(item?.id || urlOf(item) || titleOf(item));
  }

  function simulationCandidates() {
    if (!currentData) return [];
    return sortNews(currentData.items.filter(item => scopeOf(item) === "positive"));
  }

  function renderSimulationCandidates(resetForDate = false) {
    const target = document.getElementById("simulationCandidates");
    if (!target) return;
    const dateKey = currentData?.date || "";
    if (resetForDate || (simulationDateKey && simulationDateKey !== dateKey)) selectedSimulationKeys = new Set();
    simulationDateKey = dateKey;
    const candidates = simulationCandidates();
    if (!candidates.length) {
      target.innerHTML = '<div class="report-simulation-empty">Tidak ada kandidat berita positif untuk tanggal ini. Periksa klasifikasi berita atau pilih tanggal lain.</div>';
      updateSimulationSelectionCount();
      return;
    }
    target.innerHTML = candidates.map((item, index) => {
      const checked = selectedSimulationKeys.has(simulationKey(item)) ? " checked" : "";
      const url = urlOf(item);
      return `<label class="report-simulation-item">
        <input type="checkbox" data-simulation-index="${index}"${checked}>
        <span class="report-simulation-item-copy">
          <strong>${esc(titleOf(item))}</strong>
          <small>${esc(sourceOf(item) || "Sumber tidak diketahui")}${url ? " · " + esc(url) : ""}</small>
        </span>
      </label>`;
    }).join("");
    updateSimulationSelectionCount();
  }

  function updateSimulationSelectionCount() {
    const count = document.getElementById("simulationSelectedCount");
    if (count) count.textContent = `${selectedSimulationKeys.size} berita dipilih`;
    const button = document.getElementById("downloadSimulationTxt");
    if (button) button.disabled = selectedSimulationKeys.size === 0;
  }

  function onSimulationCandidateChange(event) {
    const input = event.target?.closest?.("input[data-simulation-index]");
    if (!input) return;
    const item = simulationCandidates()[Number(input.dataset.simulationIndex)];
    if (!item) return;
    const key = simulationKey(item);
    if (input.checked) selectedSimulationKeys.add(key);
    else selectedSimulationKeys.delete(key);
    updateSimulationSelectionCount();
  }

  function selectSuggestedSimulationNews() {
    const candidates = simulationCandidates();
    if (!candidates.length) {
      alert("Belum ada kandidat berita positif untuk dipilih.");
      return;
    }
    selectedSimulationKeys = new Set(candidates.slice(0, Math.min(10, candidates.length)).map(simulationKey));
    renderSimulationCandidates();
    const status = document.getElementById("simulationDownloadStatus");
    if (status) status.textContent = `Saran otomatis memilih ${selectedSimulationKeys.size} berita positif teratas.`;
  }

  function clearSimulationSelection() {
    selectedSimulationKeys.clear();
    renderSimulationCandidates();
    const status = document.getElementById("simulationDownloadStatus");
    if (status) status.textContent = "Pilihan dikosongkan.";
  }

  function slug(value) {
    return String(value || "").normalize("NFKD").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  }

  function downloadSimulationTxt() {
    const candidates = simulationCandidates().filter(item => selectedSimulationKeys.has(simulationKey(item)));
    if (!candidates.length) {
      alert("Pilih minimal satu berita positif terlebih dahulu.");
      return;
    }

    const status = document.getElementById("simulationDownloadStatus");
    const button = document.getElementById("downloadSimulationTxt");
    if (button) button.disabled = true;
    if (status) status.textContent = "Menyusun tautan uji lokal…";

    try {
      const chunks = [];
      let lines = [];
      let sequence = 0;
      let total = 0;
      const perArticleCounts = [];
      const newline = String.fromCharCode(10);
      candidates.forEach((item, articleIndex) => {
        const count = 24990 + Math.floor(Math.random() * 11);
        perArticleCounts.push(count);
        total += count;
        const query = encodeURIComponent(titleOf(item));
        for (let i = 0; i < count; i++) {
          const sourceNo = ((i * 17 + articleIndex * 31) % 408) + 1;
          const regionNo = ((i * 13 + articleIndex * 7) % EAST_JAVA_REGENCIES.length);
          const source = String(sourceNo).padStart(3, "0");
          const region = slug(EAST_JAVA_REGENCIES[regionNo]);
          const url = `https://sumber-uji-${source}.example/search?q=${query}&wilayah=${region}&variasi=${(i % 408) + 1}`;
          sequence++;
          lines.push(`${sequence}. ${url}`);
          if (lines.length >= 1000) {
            chunks.push(lines.join(newline) + newline);
            lines = [];
          }
        }
      });
      if (lines.length) chunks.push(lines.join(newline) + newline);
      const blob = new Blob(chunks, { type: "text/plain;charset=utf-8" });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = `jagat-simulasi-pencarian-${currentData?.date || "tanggal"}.txt`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
      if (status) status.textContent = `TXT dibuat: ${fmt(total)} tautan uji dari ${candidates.length} berita. Jumlah per berita: ${perArticleCounts.map(fmt).join(", ")}. Tidak ada pencarian atau publikasi yang dijalankan.`;
    } catch (error) {
      console.error("JAGAT simulasi TXT:", error);
      if (status) status.textContent = "Berkas simulasi gagal dibuat. Coba pilih lebih sedikit berita.";
      alert("TXT simulasi gagal dibuat. Coba pilih lebih sedikit berita.");
    } finally {
      if (button) button.disabled = selectedSimulationKeys.size === 0;
    }
  }

  async function generate(showError = true) {
    const date = document.getElementById("reportDate")?.value || todayDate();
    const templateKey = document.getElementById("reportTemplate")?.value || "kabid";
    const preview = document.getElementById("reportPreview");
    if (!preview) return;
    try {
      preview.classList.remove("report-preview-empty");
      preview.textContent = "Memproses data laporan...";
      currentData = await loadDataset(date);
      renderSummary(currentData);
      renderSimulationCandidates();
      currentReportText = buildReport(currentData, templateKey);
      preview.textContent = currentReportText;
    } catch (error) {
      currentReportText = "";
      preview.classList.add("report-preview-empty");
      preview.textContent = error.message || "Laporan gagal dibuat.";
      if (showError) console.error("JAGAT laporan:", error);
    }
  }

  async function copyReport() {
    if (!currentReportText) return;
    try {
      await navigator.clipboard.writeText(currentReportText);
      const btn = document.getElementById("copyReport");
      if (btn) { const old = btn.innerHTML; btn.innerHTML = '<i class="fa-solid fa-check"></i> Tersalin'; setTimeout(() => btn.innerHTML = old, 1200); }
    } catch (error) {
      console.error(error);
      alert("Laporan tidak dapat disalin otomatis. Silakan blok teks pada pratinjau.");
    }
  }

  function printReport() {
    if (!currentReportText) return;
    document.body.classList.add("report-printing");
    window.print();
    setTimeout(() => document.body.classList.remove("report-printing"), 700);
  }

  function boot() {
    const reports = document.getElementById("reportsView");
    if (!reports) return;
    const observer = new MutationObserver(() => {
      const active = !reports.hidden && !reports.classList.contains("hidden");
      if (active && !initialized) renderShell();
    });
    observer.observe(reports, { attributes: true, attributeFilter: ["hidden", "class"] });
    if (!reports.hidden && !reports.classList.contains("hidden")) renderShell();
  }

  document.addEventListener("DOMContentLoaded", boot);
})();