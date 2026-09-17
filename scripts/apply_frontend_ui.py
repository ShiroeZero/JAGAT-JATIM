"""Wire the stable frontend layer without the experimental dashboard redesign."""
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "index.html"
MAP_SCRIPT_MARKER = 'map-situasional.js?v=6.7.1'
MAP_SCRIPT_TAG = f'<script defer src="{MAP_SCRIPT_MARKER}"></script>'
REGION_FIX_MARKER = 'JAGAT-REGION-STATUS-FIX-V1'
REGION_FIX_SCRIPT = r'''<script>
/* JAGAT-REGION-STATUS-FIX-V1
   A region is an aggregate. A neutral article must never look negative merely
   because another article in the same region is negative. Keep red for high
   attention; downgrade negative-only regions to an amber informational state.
*/
(() => {
  const fmt = v => Number(v || 0).toLocaleString("id-ID");
  const scope = x => String(x?.scope || "neutral").toLowerCase();

  function todayJatim() {
    try {
      return typeof todayJatimItems === "function" ? todayJatimItems() : [];
    } catch (_) {
      return [];
    }
  }

  function areaOf(x) {
    try {
      return typeof getFilterArea === "function"
        ? getFilterArea(x)
        : String(x?.locality || x?.area_label || "Jawa Timur (Umum)");
    } catch (_) {
      return String(x?.locality || x?.area_label || "Jawa Timur (Umum)");
    }
  }

  function scoreOf(x) {
    try {
      const cases = typeof todayJatimCaseSet === "function" ? todayJatimCaseSet() : [];
      return typeof getEffectiveAttentionScore === "function"
        ? getEffectiveAttentionScore(x, cases)
        : Number(x?.attention_score || 0);
    } catch (_) {
      return Number(x?.attention_score || 0);
    }
  }

  function patch() {
    const root = document.getElementById("regionToday");
    if (!root) return;
    const items = todayJatim();

    root.querySelectorAll(".region-status-card[data-region]").forEach(card => {
      const name = String(card.dataset.region || "");
      if (!name || name === "Jawa Timur (Umum)") return;
      const group = items.filter(item => areaOf(item) === name);
      if (!group.length) return;

      const negative = group.filter(x => scope(x) === "negative").length;
      const high = group.some(x => scoreOf(x) >= 70);
      const medium = group.some(x => scoreOf(x) >= 40 && scoreOf(x) < 70);

      /* High attention remains red. Negative-only is amber so the UI does not
         visually label neutral/case/positive articles as negative. */
      if (!high && negative) {
        card.classList.remove("danger");
        card.classList.add("warning");
        const label = card.querySelector(".region-status-bottom em");
        if (label) label.textContent = medium
          ? `Atensi sedang · ${fmt(negative)} negatif`
          : `Ada ${fmt(negative)} berita negatif`;
      }
    });
  }

  function boot() {
    patch();
    const root = document.getElementById("regionToday");
    if (!root) return;
    const observer = new MutationObserver(() => requestAnimationFrame(patch));
    observer.observe(root, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
</script>'''

# The experimental dashboard-modern layer is intentionally disabled.
MODERN_STYLE = re.compile(r'\s*<link[^>]+dashboard-modern\.css\?v=[^>]+>', re.I)
MODERN_SCRIPT = re.compile(r'\s*<script[^>]+dashboard-modern\.js\?v=[^>]+></script>', re.I)
OLD_SCRIPT = re.compile(r'\s*<script[^>]+satker-ui\.js\?v=[^>]+></script>', re.I)
OLD_STYLE = re.compile(r'\s*<style[^>]+id=["\']jagat-satker-ui-style["\'][^>]*>.*?</style>', re.I | re.S)


def main():
    text = INDEX.read_text(encoding="utf-8")
    original = text

    # Return the dashboard to the stable/base presentation.
    text = MODERN_STYLE.sub("", text)
    text = MODERN_SCRIPT.sub("", text)
    text = OLD_SCRIPT.sub("", text)
    text = OLD_STYLE.sub("", text)

    # Keep the stable situational map integration, but never restore the
    # experimental dashboard-modern layer.
    if MAP_SCRIPT_MARKER not in text:
        anchor = "</body>"
        if anchor not in text:
            raise SystemExit("index.html: </body> not found")
        text = text.replace(anchor, f"  {MAP_SCRIPT_TAG}\n{anchor}", 1)

    # Keep aggregate-region status semantics separate from article semantics.
    # This patch is embedded so GitHub Pages does not need another asset file.
    if REGION_FIX_MARKER not in text:
        anchor = "</body>"
        if anchor not in text:
            raise SystemExit("index.html: </body> not found")
        text = text.replace(anchor, f"  {REGION_FIX_SCRIPT}\n{anchor}", 1)

    # Update the legend/subtitle so the visual language matches the fix.
    text = text.replace(
        "Warna mengikuti kondisi berita dan tingkat atensi tertinggi pada wilayah tersebut.",
        "Warna mengikuti tingkat atensi wilayah; jumlah berita negatif ditampilkan sebagai indikator, bukan status setiap berita."
    )
    text = text.replace("Negatif / atensi tinggi", "Atensi tinggi")
    text = text.replace("Atensi sedang</span>", "Berita negatif / atensi sedang</span>")

    INDEX.write_text(text, encoding="utf-8")
    print(f"Stable frontend wiring: {'CHANGED' if text != original else 'OK'}")


if __name__ == "__main__":
    main()
