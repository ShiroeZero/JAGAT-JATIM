/* JAGAT V6.7 — dashboard composition layer. Reuses existing data engines and drawers. */
(() => {
  const UNITS = [
    { key: "POLDA JAWA TIMUR", label: "POLDA JAWA TIMUR", polda: true },
    { key: "POLRESTABES SURABAYA", label: "POLRESTABES SURABAYA" },
    { key: "POLRESTA MALANG KOTA", label: "POLRESTA MALANG KOTA" },
    { key: "POLRESTA SIDOARJO", label: "POLRESTA SIDOARJO" },
    { key: "POLRESTA BANYUWANGI", label: "POLRESTA BANYUWANGI" },
    { key: "POLRESTA TUBAN", label: "POLRESTA TUBAN" },
    { key: "POLRESTA SUMENEP", label: "POLRESTA SUMENEP" },
    { key: "POLRES PELABUHAN TANJUNG PERAK", label: "POLRES PELABUHAN TANJUNG PERAK" },
    { key: "POLRES GRESIK", label: "POLRES GRESIK" },
    { key: "POLRES MALANG", label: "POLRES MALANG" },
    { key: "POLRES PASURUAN", label: "POLRES PASURUAN" },
    { key: "POLRES PASURUAN KOTA", label: "POLRES PASURUAN KOTA" },
    { key: "POLRES PROBOLINGGO", label: "POLRES PROBOLINGGO" },
    { key: "POLRES PROBOLINGGO KOTA", label: "POLRES PROBOLINGGO KOTA" },
    { key: "POLRES LUMAJANG", label: "POLRES LUMAJANG" },
    { key: "POLRES BATU", label: "POLRES BATU" },
    { key: "POLRES BONDOWOSO", label: "POLRES BONDOWOSO" },
    { key: "POLRES SITUBONDO", label: "POLRES SITUBONDO" },
    { key: "POLRES JEMBER", label: "POLRES JEMBER" },
    { key: "POLRES KEDIRI", label: "POLRES KEDIRI" },
    { key: "POLRES KEDIRI KOTA", label: "POLRES KEDIRI KOTA" },
    { key: "POLRES TULUNGAGUNG", label: "POLRES TULUNGAGUNG" },
    { key: "POLRES NGANJUK", label: "POLRES NGANJUK" },
    { key: "POLRES TRENGGALEK", label: "POLRES TRENGGALEK" },
    { key: "POLRES BLITAR", label: "POLRES BLITAR" },
    { key: "POLRES BLITAR KOTA", label: "POLRES BLITAR KOTA" },
    { key: "POLRES MADIUN", label: "POLRES MADIUN" },
    { key: "POLRES MADIUN KOTA", label: "POLRES MADIUN KOTA" },
    { key: "POLRES NGAWI", label: "POLRES NGAWI" },
    { key: "POLRES MAGETAN", label: "POLRES MAGETAN" },
    { key: "POLRES PONOROGO", label: "POLRES PONOROGO" },
    { key: "POLRES PACITAN", label: "POLRES PACITAN" },
    { key: "POLRES BOJONEGORO", label: "POLRES BOJONEGORO" },
    { key: "POLRES LAMONGAN", label: "POLRES LAMONGAN" },
    { key: "POLRES MOJOKERTO", label: "POLRES MOJOKERTO" },
    { key: "POLRES MOJOKERTO KOTA", label: "POLRES MOJOKERTO KOTA" },
    { key: "POLRES JOMBANG", label: "POLRES JOMBANG" },
    { key: "POLRES PAMEKASAN", label: "POLRES PAMEKASAN" },
    { key: "POLRES BANGKALAN", label: "POLRES BANGKALAN" },
    { key: "POLRES SAMPANG", label: "POLRES SAMPANG" },
  ];

  const esc = (value) => window.escapeHtml ? window.escapeHtml(value) : String(value ?? "");
  const fmt = (value) => window.number ? window.number(value) : Number(value || 0).toLocaleString("id-ID");
  const scoreFor = (item, cases) => window.getEffectiveAttentionScore ? window.getEffectiveAttentionScore(item, cases) : Number(item?.attention_score || 0);
  const scopeFor = (item) => String(item?.scope || "neutral").toLowerCase();

  function unitItems(unit, items) {
    if (unit.polda) {
      return items.filter((item) => {
        const area = String(item?.locality || item?.area_label || "").toLowerCase();
        const title = String(item?.title || "").toLowerCase();
        return area === "polda jatim" || area === "polda jawa timur" || /\b(?:polda|kapolda)\s+(?:jawa\s+timur|jatim)\b/.test(title);
      });
    }
    return items.filter((item) => String(item?.polres || "").toUpperCase() === unit.key);
  }

  function statusFor(items, cases) {
    if (!items.length) return { cls: "", label: "Belum ada data", score: 0 };
    let max = 0;
    let negative = false;
    let medium = false;
    items.forEach((item) => {
      const n = scoreFor(item, cases);
      max = Math.max(max, n);
      if (scopeFor(item) === "negative") negative = true;
      if (n >= 40 && n < 70) medium = true;
    });
    if (negative || max >= 70) return { cls: "high", label: "Perlu perhatian", score: max };
    if (medium || max >= 40) return { cls: "medium", label: "Atensi sedang", score: max };
    return { cls: "low", label: "Terpantau", score: max };
  }

  function renderUnitList(items) {
    const target = document.getElementById("regionToday");
    const cases = typeof activeCases === "function" ? activeCases() : [];
    if (!target) return;

    const rows = UNITS.map((unit) => {
      const unitItemsValue = unitItems(unit, items);
      const status = statusFor(unitItemsValue, cases);
      const caseCount = new Set(unitItemsValue.map((x) => x.case_id).filter(Boolean)).size;
      return { unit, items: unitItemsValue, status, caseCount };
    });

    target.innerHTML = `
      <div class="jagat-unit-list">
        <div class="jagat-unit-tools">
          <input id="dashboardUnitSearch" type="search" placeholder="Cari Polres / Polda..." autocomplete="off" aria-label="Cari satuan Jawa Timur">
          <span class="jagat-unit-count">40 SATUAN</span>
        </div>
        <div class="jagat-unit-scroll" id="jagatUnitScroll">
          <div class="jagat-unit-divider">Polda Jawa Timur</div>
          ${rows.filter((row) => row.unit.polda).map(renderUnitRow).join("")}
          <div class="jagat-unit-divider">39 Polres / Polresta</div>
          ${rows.filter((row) => !row.unit.polda).map(renderUnitRow).join("")}
        </div>
      </div>
    `;

    const search = document.getElementById("dashboardUnitSearch");
    if (search) {
      search.addEventListener("input", () => {
        const term = search.value.trim().toLowerCase();
        document.querySelectorAll("#jagatUnitScroll .jagat-unit-row").forEach((row) => {
          row.hidden = !!term && !row.dataset.name.includes(term);
        });
      });
    }

    target.querySelectorAll(".jagat-unit-row").forEach((row) => {
      row.addEventListener("click", () => {
        const unit = UNITS.find((x) => x.key === row.dataset.unit);
        if (unit) openUnitDrawer(unit, unitItems(unit, items));
      });
    });

    const count = document.getElementById("mapCount");
    if (count) count.textContent = "40 satuan Jatim";
  }

  function renderUnitRow(row) {
    const count = row.items.length;
    const meta = `${fmt(count)} berita${row.caseCount ? ` · ${fmt(row.caseCount)} kasus` : ""}`;
    const title = row.unit.polda ? "Unit pusat Polda Jawa Timur" : "Polres / Polresta";
    return `<button class="jagat-unit-row ${row.unit.polda ? "polda" : ""}" data-unit="${esc(row.unit.key)}" data-name="${esc(row.unit.label.toLowerCase())}" type="button">
      <span class="jagat-unit-name"><strong>${esc(row.unit.label)}</strong><small>${esc(meta)} · ${esc(title)}</small></span>
      <span class="jagat-unit-num">${count ? fmt(count) : "—"}</span>
      <i class="jagat-unit-status ${row.status.cls}" title="${esc(row.status.label)}"></i>
    </button>`;
  }

  function openUnitDrawer(unit, items) {
    if (!window.$ || !window.openDrawer) return;
    const cases = typeof activeCases === "function" ? activeCases() : [];
    const caseIds = new Set(items.map((item) => item.case_id).filter(Boolean));
    const linkedCases = cases.filter((c) => caseIds.has(c.case_id));
    const title = unit.polda ? "Polda Jawa Timur" : unit.label;
    const kind = unit.polda ? "PUSAT JAWA TIMUR" : "SATUAN KEWILAYAHAN";
    const pills = unit.polda
      ? `<span class="pill low">POLDA JATIM</span>`
      : `<span class="pill">POLRES / POLRESTA</span>`;

    $("drawerEyebrow").textContent = kind;
    $("drawerContent").innerHTML = `
      <div class="drawer-title">${esc(title)}</div>
      <div class="drawer-meta">${fmt(items.length)} berita · ${fmt(linkedCases.length)} kasus · Jawa Timur</div>
      <div class="drawer-pills">${pills}</div>
      <div class="detail-grid">
        <div><span>Berita Negatif</span><strong>${fmt(items.filter((x) => scopeFor(x) === "negative").length)}</strong></div>
        <div><span>Ungkap Kasus</span><strong>${fmt(items.filter((x) => scopeFor(x) === "case").length)}</strong></div>
        <div><span>Berita Positif</span><strong>${fmt(items.filter((x) => scopeFor(x) === "positive").length)}</strong></div>
        <div><span>Atensi Maksimum</span><strong>${fmt(Math.max(0, ...items.map((x) => scoreFor(x, cases))))}/100</strong></div>
      </div>
      <div class="source-list">
        <h4>Berita Terbaru (${fmt(items.length)})</h4>
        ${items.slice().sort((a,b) => new Date(getItemDate(b)||0) - new Date(getItemDate(a)||0)).slice(0, 12).map((item) => {
          const url = window.normalizeUrl ? window.normalizeUrl(item.url) : item.url;
          return `<div class="source-row">
            <div><b>${esc(getTitle(item))}</b><div>${esc(getSource(item))}</div><small>${esc(formatDateTime(getItemDate(item)))} · ${esc(getCategory(item))}</small></div>
            <span class="source-row-actions">${window.copyButtonMarkup ? window.copyButtonMarkup(url) : ""}${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="open-link-btn"><i class="fa-solid fa-arrow-up-right-from-square"></i> Buka</a>` : ""}</span>
          </div>`;
        }).join("") || `<div class="empty">Belum ada berita pada satuan ini.</div>`}
      </div>
    `;
    openDrawer();
    if (window.bindCopyButtons) window.bindCopyButtons($("drawerContent"));
  }

  function enhanceHeader() {
    const eyebrow = document.querySelector(".topbar .eyebrow");
    const title = document.getElementById("pageTitle");
    if (eyebrow) eyebrow.textContent = "JAGAT · MONITORING JAWA TIMUR";
    if (title && document.getElementById("dashboardView")?.offsetParent !== null) title.textContent = "Dashboard Monitoring";
    const date = document.getElementById("todayDate");
    if (date && !document.getElementById("dashboardScopeBadge")) {
      const badge = document.createElement("span");
      badge.id = "dashboardScopeBadge";
      badge.className = "dashboard-scope-badge";
      badge.textContent = "JAWA TIMUR · 40 SATUAN";
      date.parentElement?.appendChild(badge);
    }
  }

  const previousRenderRegions = window.renderRegionsToday;
  window.renderRegionsToday = function(items) {
    if (items && document.getElementById("dashboardView")) {
      renderUnitList(items);
      return;
    }
    if (typeof previousRenderRegions === "function") previousRenderRegions(items);
  };

  document.addEventListener("DOMContentLoaded", () => {
    enhanceHeader();
    setTimeout(enhanceHeader, 100);
  });
  setTimeout(enhanceHeader, 0);
})();
