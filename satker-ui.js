/* JAGAT V6.6 — organisational satker UI layer. */
(() => {
  const POLDA = "POLDA JAWA TIMUR";
  const originalApply = window.applyMonitoringFilters;
  const byId = (id) => document.getElementById(id);

  function satkerOf(item) {
    if (item?.satker) return String(item.satker).toUpperCase();
    const title = String(item?.title || "").toLowerCase();
    return /\b(?:polda|kapolda)\s+(?:jawa\s+timur|jatim)\b/.test(title) ? POLDA : "";
  }

  function ensureFilter() {
    const region = byId("region");
    if (!region || byId("satker")) return;
    const regionGroup = region.closest(".filter-group");
    const controls = regionGroup?.querySelector(".filter-group-controls");
    if (!controls) return;
    const wrapper = document.createElement("div");
    wrapper.className = "satker-filter-wrap";
    wrapper.innerHTML = '<select id="satker" aria-label="Satker"><option value="all">Semua Satker</option><option value="POLDA JAWA TIMUR">Polda Jawa Timur</option></select>';
    controls.appendChild(wrapper);
    byId("satker").addEventListener("change", () => window.renderMonitoring?.());
  }

  function patchFilter() {
    if (!originalApply || window.__jagatSatkerPatched) return;
    window.applyMonitoringFilters = function(items) {
      let result = originalApply(items);
      const selected = byId("satker")?.value || "all";
      if (selected !== "all") result = result.filter(item => satkerOf(item) === selected);
      return result;
    };
    window.__jagatSatkerPatched = true;
  }

  function refresh() {
    ensureFilter();
    patchFilter();
  }

  document.addEventListener("DOMContentLoaded", refresh);
  setTimeout(refresh, 0);
  setTimeout(refresh, 500);
})();
