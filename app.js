const DEMO_EMAIL = "admin@propam-jatim.go.id";
const DEMO_PASSWORD = "PropamJatim2026!";


const POLRES_JATIM = [
    "POLRES PELABUHAN TANJUNG PERAK",
    "POLRES JEMBER",
    "POLRES KEDIRI",
    "POLRES BLITAR KOTA",
    "POLRESTABES SURABAYA",
    "POLRESTA MALANG KOTA",
    "POLRESTA SIDOARJO",
    "POLRESTA BANYUWANGI",
    "POLRESTA TUBAN",
    "POLRESTA SUMENEP",
    "POLRES GRESIK",
    "POLRES MALANG",
    "POLRES PASURUAN",
    "POLRES PASURUAN KOTA",
    "POLRES PROBOLINGGO",
    "POLRES PROBOLINGGO KOTA",
    "POLRES LUMAJANG",
    "POLRES BATU",
    "POLRES BONDOWOSO",
    "POLRES SITUBONDO",
    "POLRES KEDIRI KOTA",
    "POLRES TULUNGAGUNG",
    "POLRES NGANJUK",
    "POLRES TRENGGALEK",
    "POLRES BLITAR",
    "POLRES MADIUN",
    "POLRES MADIUN KOTA",
    "POLRES NGAWI",
    "POLRES MAGETAN",
    "POLRES PONOROGO",
    "POLRES PACITAN",
    "POLRES BOJONEGORO",
    "POLRES LAMONGAN",
    "POLRES MOJOKERTO",
    "POLRES MOJOKERTO KOTA",
    "POLRES JOMBANG",
    "POLRES PAMEKASAN",
    "POLRES BANGKALAN",
    "POLRES SAMPANG"
];


let allNews = [];
let currentView = "dashboard";


const $ = id =>
    document.getElementById(id);


function esc(value = "") {

    return String(value).replace(
        /[&<>"']/g,
        match => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[match]
    );
}


function relDate(iso) {

    if (!iso) {
        return "-";
    }

    const date = new Date(iso);

    if (isNaN(date)) {
        return "-";
    }

    return date.toLocaleString(
        "id-ID",
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );
}


function dateOnly(iso) {

    if (!iso) {
        return "";
    }

    const date = new Date(iso);

    if (isNaN(date)) {
        return "";
    }

    // Gunakan tanggal lokal browser.
    const year =
        date.getFullYear();

    const month =
        String(
            date.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            date.getDate()
        ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


function card(news) {

    const priority =
        news.priority || "low";

    const priorityLabel =
        priority === "high"
            ? "TINGGI"
            : priority === "medium"
                ? "SEDANG"
                : "RENDAH";


    const polresBadge =
        news.polres
            ? `<span class="pill">${esc(news.polres)}</span>`
            : (
                news.is_jatim
                    ? `<span class="pill">Polres belum teridentifikasi</span>`
                    : ""
            );


    return `
        <article class="news-card">

            <div class="news-title">
                <a
                    href="${esc(news.url || "#")}"
                    target="_blank"
                    rel="noopener"
                >
                    ${esc(news.title)}
                </a>
            </div>

            <div class="meta">

                <span>
                    ${esc(news.source || "Unknown")}
                </span>

                <span>
                    ${relDate(news.published_at)}
                </span>

                <span class="pill ${priority}">
                    ${priorityLabel}
                </span>

                <span class="pill">
                    ${esc(news.region || "Indonesia")}
                </span>

                ${polresBadge}

                <span class="pill">
                    ${esc(news.category || "Lainnya")}
                </span>

                ${
                    news.scope
                        ? `
                            <span class="pill scope-${esc(news.scope)}">
                                ${esc(
                                    news.scope_label ||
                                    news.scope
                                )}
                            </span>
                        `
                        : ""
                }

            </div>

        </article>
    `;
}


async function loadData() {

    $("statusText").textContent =
        "Mengambil data...";


    try {

        const response =
            await fetch(
                `data/news.json?t=${Date.now()}`,
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " +
                response.status
            );
        }


        const data =
            await response.json();


        allNews =
            Array.isArray(data)
                ? data
                : (
                    Array.isArray(data.items)
                        ? data.items
                        : []
                );


        allNews.sort(
            (a, b) =>
                new Date(
                    b.published_at || 0
                ) -
                new Date(
                    a.published_at || 0
                )
        );


        render();


        const updated =
            data.generated_at ||
            allNews[0]?.collected_at;


        $("lastUpdated").textContent =
            updated
                ? `Update: ${relDate(updated)}`
                : "Data aktif";


        $("statusText").textContent =
            "Collector aktif";


        $("statusDot").style.background =
            "var(--ok)";


    } catch (error) {

        $("statusText").textContent =
            "Data gagal dimuat";


        $("statusDot").style.background =
            "var(--danger)";


        console.error(
            "PNM data error:",
            error
        );
    }
}


function render() {

    const now =
        Date.now();

    const day =
        86400000;


    $("sTotal").textContent =
        allNews.length;


    $("sJatim").textContent =
        allNews.filter(
            news => news.is_jatim === true
        ).length;


    $("s24").textContent =
        allNews.filter(news => {

            const published =
                new Date(
                    news.published_at || 0
                ).getTime();

            return (
                published &&
                now - published <= day
            );

        }).length;


    $("sHigh").textContent =
        allNews.filter(
            news =>
                news.priority === "high"
        ).length;


    // ========================================================
    // CATEGORY STATISTICS
    // ========================================================

    const categories = {};


    allNews.forEach(news => {

        const category =
            news.category ||
            "NETRAL / LAINNYA";


        categories[category] =
            (
                categories[category] ||
                0
            ) + 1;

    });


    const top =
        Object.entries(
            categories
        )
        .sort(
            (a, b) =>
                b[1] - a[1]
        )
        .slice(
            0,
            8
        );


    const max =
        top[0]?.[1] ||
        1;


    $("categories").innerHTML =
        top.map(
            ([name, count]) => `
                <div class="bar">

                    <div class="bar-top">
                        <span>${esc(name)}</span>
                        <b>${count}</b>
                    </div>

                    <div class="bar-bg">
                        <div
                            class="bar-fill"
                            style="width:${count / max * 100}%"
                        ></div>
                    </div>

                </div>
            `
        ).join("")
        ||
        `
            <div class="empty">
                Belum ada data
            </div>
        `;


    // ========================================================
    // LATEST NEWS
    // ========================================================

    $("latest").innerHTML =
        allNews
            .slice(0, 8)
            .map(card)
            .join("")
        ||
        `
            <div class="empty">
                Belum ada berita.
            </div>
        `;


    // ========================================================
    // POLRES FILTER
    // ========================================================

    $("polres").innerHTML =
        `
            <option value="all">
                Semua Polres Jatim
            </option>

            <option value="unknown">
                Jatim - Polres Belum Teridentifikasi
            </option>

            ${
                POLRES_JATIM
                    .map(
                        polres =>
                            `
                                <option value="${esc(polres)}">
                                    ${esc(polres)}
                                </option>
                            `
                    )
                    .join("")
            }
        `;


    // ========================================================
    // CATEGORY FILTER
    // ========================================================

    const categoriesSorted =
        Object.keys(
            categories
        ).sort();


    $("category").innerHTML =
        `
            <option value="all">
                Semua Kategori
            </option>

            ${
                categoriesSorted
                    .map(
                        category =>
                            `
                                <option value="${esc(category)}">
                                    ${esc(category)}
                                </option>
                            `
                    )
                    .join("")
            }
        `;


    applyFilters();
}


function applyFilters() {

    let filtered =
        [...allNews];


    const query =
        (
            $("search").value ||
            ""
        )
        .trim()
        .toLowerCase();


    const region =
        $("region").value;


    const priority =
        $("priority").value;


    const category =
        $("category").value;


    const polres =
        $("polres").value;


    const scope =
        $("scope").value;


    const from =
        $("dateFrom").value;


    const to =
        $("dateTo").value;


    // ========================================================
    // SEARCH
    // ========================================================

    if (query) {

        filtered =
            filtered.filter(
                news => {

                    const searchable = [
                        news.title,
                        news.source,
                        news.region,
                        news.category,
                        news.summary,
                        news.polres,
                        news.scope_label
                    ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();


                    return searchable.includes(
                        query
                    );
                }
            );
    }


    // ========================================================
    // REGION
    // ========================================================

    if (region === "jatim") {

        filtered =
            filtered.filter(
                news =>
                    news.is_jatim === true
            );
    }


    if (region === "outside") {

        filtered =
            filtered.filter(
                news =>
                    news.is_jatim !== true
            );
    }


    // ========================================================
    // POLRES
    // ========================================================

    if (polres !== "all") {

        if (polres === "unknown") {

            filtered =
                filtered.filter(
                    news =>
                        news.is_jatim === true &&
                        !news.polres
                );

        } else {

            filtered =
                filtered.filter(
                    news =>
                        news.polres === polres
                );
        }
    }


    // ========================================================
    // SCOPE
    // ========================================================

    if (scope !== "all") {

        filtered =
            filtered.filter(
                news =>
                    news.scope === scope
            );
    }


    // ========================================================
    // PRIORITY
    // ========================================================

    if (priority !== "all") {

        filtered =
            filtered.filter(
                news =>
                    news.priority === priority
            );
    }


    // ========================================================
    // CATEGORY
    // ========================================================

    if (category !== "all") {

        filtered =
            filtered.filter(
                news =>
                    news.category === category
            );
    }


    // ========================================================
    // DATE RANGE
    // ========================================================

    if (from) {

        filtered =
            filtered.filter(
                news =>
                    dateOnly(
                        news.published_at
                    ) >= from
            );
    }


    if (to) {

        filtered =
            filtered.filter(
                news =>
                    dateOnly(
                        news.published_at
                    ) <= to
            );
    }


    // ========================================================
    // CURRENT VIEW
    // ========================================================

    if (currentView === "jatim") {

        filtered =
            filtered.filter(
                news =>
                    news.is_jatim === true
            );
    }


    if (currentView === "high") {

        filtered =
            filtered.filter(
                news =>
                    news.priority === "high"
            );
    }


    $("list").innerHTML =
        filtered
            .map(card)
            .join("")
        ||
        `
            <div class="empty">
                Tidak ada berita yang sesuai filter.
            </div>
        `;
}


function setView(view) {

    currentView =
        view;


    document
        .querySelectorAll(".nav")
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.view === view
            );

        });


    $("dashboardView")
        .classList.toggle(
            "hidden",
            view !== "dashboard"
        );


    $("listView")
        .classList.toggle(
            "hidden",
            view === "dashboard"
        );


    $("pageTitle").textContent =
        view === "dashboard"
            ? "Dashboard"
            : view === "jatim"
                ? "Jawa Timur"
                : view === "high"
                    ? "Prioritas Tinggi"
                    : "Semua Berita";


    if (view !== "dashboard") {

        applyFilters();
    }
}


// ============================================================
// LOGIN
// ============================================================

$("loginForm")
    .addEventListener(
        "submit",
        event => {

            event.preventDefault();


            const email =
                $("email")
                    .value
                    .trim();


            const password =
                $("password")
                    .value;


            if (
                email === DEMO_EMAIL &&
                password === DEMO_PASSWORD
            ) {

                sessionStorage.setItem(
                    "pnm_auth",
                    "1"
                );


                $("login")
                    .classList
                    .add("hidden");


                $("app")
                    .classList
                    .remove("hidden");


                loadData();

            } else {

                $("loginError")
                    .textContent =
                    "Email atau password salah.";
            }
        }
    );


// ============================================================
// LOGOUT
// ============================================================

$("logout")
    .onclick = () => {

        sessionStorage.removeItem(
            "pnm_auth"
        );

        location.reload();
    };


// ============================================================
// NAVIGATION
// ============================================================

document
    .querySelectorAll(".nav")
    .forEach(
        button => {

            button.onclick =
                () =>
                    setView(
                        button.dataset.view
                    );
        }
    );


document
    .querySelectorAll(".linkbtn")
    .forEach(
        button => {

            button.onclick =
                () =>
                    setView(
                        button.dataset.view
                    );
        }
    );


// ============================================================
// FILTER EVENTS
// ============================================================

[
    "search",
    "region",
    "polres",
    "scope",
    "priority",
    "category",
    "dateFrom",
    "dateTo"
]
.forEach(
    id => {

        const element =
            $(id);


        if (!element) {
            return;
        }


        element.addEventListener(
            "input",
            applyFilters
        );


        element.addEventListener(
            "change",
            applyFilters
        );
    }
);


// ============================================================
// RESET FILTER
// ============================================================

$("clearFilters")
    .onclick = () => {

        $("search").value = "";

        $("region").value = "all";

        $("polres").value = "all";

        $("scope").value = "all";

        $("priority").value = "all";

        $("category").value = "all";

        $("dateFrom").value = "";

        $("dateTo").value = "";


        applyFilters();
    };


// ============================================================
// REFRESH
// ============================================================

$("refresh")
    .onclick = loadData;


// ============================================================
// AUTO LOGIN
// ============================================================

if (
    sessionStorage.getItem(
        "pnm_auth"
    ) === "1"
) {

    $("login")
        .classList
        .add("hidden");


    $("app")
        .classList
        .remove("hidden");


    loadData();
}
