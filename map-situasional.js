/* JAGAT V6.7.1 — situational East Java administrative map.
 * Replaces the generic basemap with a dark choropleth-style operational map.
 * Source geometry: public GeoJSON administrative boundaries.
 */
(() => {
  const GEOJSON_URL = "https://raw.githubusercontent.com/AlfianAliM/Indonesia-GeoJSON/master/kab_kota.geojson";
  const JATIM_PREFIX = "35.";
  let map = null;
  let layer = null;
  let geojson = null;
  let pollTimer = null;

  const esc = (v) => typeof escapeHtml === "function" ? escapeHtml(v) : String(v ?? "");
  const fmt = (v) => typeof number === "function" ? number(v) : Number(v || 0).toLocaleString("id-ID");
  const normalize = (v) => String(v || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, " ").trim();

  function getItems() {
    try {
      return typeof todayJatimItems === "function" ? todayJatimItems() : [];
    } catch (_) { return []; }
  }

  function getCases() {
    try { return typeof activeCases === "function" ? activeCases() : []; } catch (_) { return []; }
  }

  function areaName(feature) {
    const p = feature?.properties || {};
    return p.name || p.NAME_2 || p.NAME || p.namobj || p.WADMKK || p.kab_kota || "";
  }

  function featureCode(feature) {
    const p = feature?.properties || {};
    return String(p.code || p.kode || p.KODE_KAB || p.KODE || "");
  }

  function canonicalArea(name) {
    let n = normalize(name).replace(/^kabupaten\s+/, "").replace(/^kota\s+/, "");
    const aliases = {
      "surabaya": "Surabaya",
      "malang": "Malang",
      "batu": "Batu",
      "sidoarjo": "Sidoarjo",
      "gresik": "Gresik",
      "pasuruan": "Pasuruan",
      "probolinggo": "Probolinggo",
      "lumajang": "Lumajang",
      "jember": "Jember",
      "banyuwangi": "Banyuwangi",
      "bondowoso": "Bondowoso",
      "situbondo": "Situbondo",
      "kediri": "Kediri",
      "tulungagung": "Tulungagung",
      "blitar": "Blitar",
      "nganjuk": "Nganjuk",
      "madiun": "Madiun",
      "magetan": "Magetan",
      "ngawi": "Ngawi",
      "ponorogo": "Ponorogo",
      "pacitan": "Pacitan",
      "bojonegoro": "Bojonegoro",
      "tuban": "Tuban",
      "lamongan": "Lamongan",
      "mojokerto": "Mojokerto",
      "jombang": "Jombang",
      "pamekasan": "Pamekasan",
      "bangkalan": "Bangkalan",
      "sampang": "Sampang",
      "sumenep": "Sumenep",
      "blitar kota": "Blitar",
      "kediri kota": "Kediri",
      "malang kota": "Malang",
      "madiun kota": "Madiun",
      "mojokerto kota": "Mojokerto",
      "pasuruan kota": "Pasuruan",
      "probolinggo kota": "Probolinggo",
    };
    return aliases[n] || String(name || "").replace(/^Kabupaten\s+/i, "").replace(/^Kota\s+/i, "");
  }

  function score(item, cases) {
    return typeof getEffectiveAttentionScore === "function" ? getEffectiveAttentionScore(item, cases) : Number(item?.attention_score || 0);
  }

  function statsFor(area, items, cases) {
    const target = normalize(area);
    const related = items.filter(item => normalize(typeof getLocality === "function" ? getLocality(item) : (item.locality || item.area_label || "")) === target);
    let max = 0;
    let high = 0;
    let medium = 0;
    let negative = 0;
    const caseIds = new Set();
    related.forEach(item => {
      max = Math.max(max, score(item, cases));
      if (score(item, cases) >= 70) high++;
      else if (score(item, cases) >= 40) medium++;
      if (String(item.scope || "").toLowerCase() === "negative") negative++;
      if (item.case_id) caseIds.add(item.case_id);
    });
    return { related, max, high, medium, negative, cases: caseIds.size };
  }

  function fillColor(stats) {
    if (!stats.related.length) return "#0a1b2b";
    if (stats.negative || stats.max >= 70) return "#b52f43";
    if (stats.max >= 40 || stats.medium) return "#a87828";
    return "#12658b";
  }

  function init() {
    const el = document.getElementById("jatimMap");
    if (!el || !window.L || map) return;
    el.innerHTML = "";
    map = L.map(el, { zoomControl: false, attributionControl: true, dragging: true, scrollWheelZoom: true }).setView([-7.78, 112.55], 8);
    L.control.zoom({ position: "bottomright" }).addTo(map);
    map.getContainer().classList.add("jagat-situational-map");
    fetchGeometry();
  }

  async function fetchGeometry() {
    try {
      const res = await fetch(GEOJSON_URL, { cache: "force-cache" });
      if (!res.ok) throw new Error(`GeoJSON ${res.status}`);
      const all = await res.json();
      geojson = {
        type: "FeatureCollection",
        features: (all.features || []).filter(f => featureCode(f).startsWith(JATIM_PREFIX))
      };
      render();
    } catch (error) {
      console.error("JAGAT map geometry failed", error);
      const el = document.getElementById("jatimMap");
      if (el) el.innerHTML = `<div class="jagat-map-error"><strong>Peta wilayah tidak dapat dimuat</strong><span>Data monitoring tetap berjalan normal.</span></div>`;
    }
  }

  function render() {
    if (!map || !geojson) return;
    const items = getItems();
    const cases = getCases();
    if (layer) layer.remove();

    layer = L.geoJSON(geojson, {
      style: feature => {
        const area = canonicalArea(areaName(feature));
        const stats = statsFor(area, items, cases);
        return {
          color: "#276180",
          weight: 1,
          opacity: 1,
          fillColor: fillColor(stats),
          fillOpacity: stats.related.length ? 0.82 : 0.34,
        };
      },
      onEachFeature: (feature, polygon) => {
        const area = canonicalArea(areaName(feature));
        const stats = statsFor(area, items, cases);
        polygon.bindTooltip(esc(area), { sticky: true, direction: "center", className: "jagat-map-label" });
        polygon.bindPopup(() => {
          const title = stats.related.length ? "Wilayah terpantau" : "Belum ada berita";
          const top = stats.related.slice().sort((a,b) => score(b,cases)-score(a,cases)).slice(0,3);
          return `<div class="jagat-map-popup">
            <div class="jagat-map-popup-eyebrow">JAWA TIMUR</div>
            <strong>${esc(area)}</strong>
            <span class="jagat-map-popup-status">${esc(title)}</span>
            <div class="jagat-map-popup-grid"><b>${fmt(stats.related.length)}<small>BERITA</small></b><b>${fmt(stats.cases)}<small>KASUS</small></b><b>${fmt(stats.max)}<small>ATENSI</small></b></div>
            ${top.length ? `<div class="jagat-map-popup-news">${top.map(x => `<div>• ${esc(typeof getTitle === "function" ? getTitle(x) : x.title)}</div>`).join("")}</div>` : ""}
            <button type="button" class="jagat-map-open" data-area="${esc(area)}">BUKA WILAYAH →</button>
          </div>`;
        });
        polygon.on({
          mouseover: () => polygon.setStyle({ weight: 2, color: "#57d7f0", fillOpacity: .92 }),
          mouseout: () => layer.resetStyle(polygon),
          popupopen: () => {
            const button = polygon.getPopup().getElement()?.querySelector(".jagat-map-open");
            button?.addEventListener("click", () => {
              const selected = getItems().filter(item => normalize(typeof getLocality === "function" ? getLocality(item) : (item.locality || "")) === normalize(area));
              if (typeof openRegionDrawer === "function") openRegionDrawer(area, selected);
            });
          }
        });
      }
    }).addTo(map);

    const bounds = layer.getBounds();
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [18, 18], maxZoom: 9 });
    setTimeout(() => map.invalidateSize(), 100);

    const count = document.getElementById("mapCount");
    if (count) count.textContent = `${geojson.features.length} kab/kota`;
  }

  function addPoldaStatus() {
    const host = document.getElementById("jatimMap");
    if (!host || host.querySelector(".jagat-polda-map-badge")) return;
    const badge = document.createElement("div");
    badge.className = "jagat-polda-map-badge";
    badge.innerHTML = `<span class="jagat-polda-pulse"></span><div><strong>POLDA JAWA TIMUR</strong><small>Unit pusat / fungsi Polda</small></div>`;
    host.appendChild(badge);
  }

  function boot() {
    const el = document.getElementById("jatimMap");
    if (!el) return;
    init();
    addPoldaStatus();
    if (!pollTimer) {
      let tries = 0;
      pollTimer = setInterval(() => {
        tries++;
        if (map && geojson && typeof todayJatimItems === "function") render();
        if (tries > 30) { clearInterval(pollTimer); pollTimer = null; }
      }, 1000);
    }
  }

  document.addEventListener("DOMContentLoaded", () => setTimeout(boot, 250));
  window.addEventListener("resize", () => map?.invalidateSize());
})();
