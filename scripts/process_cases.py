import json
import os
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

NEWS_FILE = "data/news.json"
CASE_FILE = "data/case_clusters.json"

# ============================================================
# STEP 1 REPAIR
# ============================================================
#
# case-v4.1
#
# Tujuan:
# - Membersihkan recovery false-positive dari v4 sebelumnya.
# - Rebuild case database dari news yang tersedia.
# - Setelah case terbentuk, lakukan recovery yang SANGAT ketat
#   untuk artikel non-case/neutral yang sebenarnya merupakan
#   update dari incident yang sama.
#
# ============================================================

ENGINE_VERSION = "case-v4.1"

MAX_CASES_TO_COMPARE = 1000
MAX_CASE_AGE_DAYS = 90

MERGE_SCORE = 0.56

# Recovery harus jauh lebih ketat daripada merge normal.
RECOVERY_SCORE = 0.70

PRIORITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan",
    "pada", "dalam", "oleh", "ini", "itu", "seorang",
    "orang", "jadi", "akan", "telah", "adalah", "terkait",
    "soal", "kasus", "berita", "polisi", "polri", "anggota",
    "oknum", "diduga", "ungkap", "mengungkap", "tangkap",
    "menangkap", "ditangkap", "amankan", "diamankan",
    "tersangka", "pelaku", "korban", "kronologi", "terjadi",
    "atas", "karena", "hingga", "saat", "sebuah", "sejumlah",
    "kembali", "usai", "setelah", "sebelumnya", "terhadap",
    "menjadi", "para", "sebagai", "yakni", "langsung",
    "hal", "pengungkapan", "penanganan", "ditemukan",
    "diketahui", "membuat", "kata", "ujar", "menurut",
    "hari", "tahun", "bulan", "warga", "satu", "dua",
    "tiga", "empat", "lima", "enam", "tujuh", "delapan",
    "sembilan", "sepuluh",
}

GENERIC_CASE_WORDS = {
    "polisi", "polri", "anggota", "oknum", "kasus", "berita",
    "ungkap", "mengungkap", "tangkap", "menangkap",
    "ditangkap", "amankan", "diamankan", "tersangka",
    "pelaku", "korban", "diduga", "terlibat", "terkait",
    "kejadian", "peristiwa", "kronologi", "penanganan",
    "kekerasan", "penganiayaan", "narkoba", "korupsi",
    "pungli", "suap", "etik", "disiplin", "pemerasan",
    "penyalahgunaan", "wewenang", "penembakan", "tindak",
    "pidana", "penindakan", "mengamankan", "ditetapkan",
    "pemeriksaan", "diperiksa", "memeriksa", "ditahan",
    "menahan", "ditangkapnya", "mengaku", "menyebut",
    "sebut", "berhasil", "berhasilnya",
}

EVENT_WORDS = {
    "intimidasi", "wartawan", "jurnalis", "pwi", "tuntutan",
    "permintaan", "maaf", "propam", "sula", "sanana", "jeju",
    "tuban", "pacitan", "tangerang", "kendari", "fasilitas",
    "pengadilan", "vonis", "divonis", "bebas", "seksual",
    "kekerasan", "curanmor", "pencurian", "pencuri", "motor",
    "emas", "350", "juta", "celurit", "letter", "hilang",
    "misteri", "pembunuhan", "penembakan", "narkoba", "sabu",
    "ganja", "korupsi", "pungli", "suap", "pemerasan",
    "penyalahgunaan",
}

# Lokasi konkret yang boleh dipakai sebagai identitas incident.
LOCATION_TERMS = {
    "surabaya", "gresik", "sidoarjo", "mojokerto", "jombang",
    "nganjuk", "madiun", "magetan", "ngawi", "bojonegoro",
    "tuban", "lamongan", "kediri", "tulungagung", "trenggalek",
    "blitar", "malang", "batu", "pasuruan", "probolinggo",
    "lumajang", "jember", "bondowoso", "situbondo", "banyuwangi",
    "pacitan", "ponorogo", "sumenep", "pamekasan", "sampang",
    "bangkalan", "kendari", "tangerang", "jeju", "medan",
    "madiun",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value):
    if not value:
        return None

    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception:
        return None


def normalize(text):
    text = (text or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def words(text):
    return {
        word
        for word in normalize(text).split()
        if len(word) >= 3
        and word not in STOPWORDS
    }


def key_words(text):
    return {
        word
        for word in words(text)
        if word not in GENERIC_CASE_WORDS
    }


def event_words(text):
    return key_words(text) & EVENT_WORDS


def location_words(text):
    return words(text) & LOCATION_TERMS


def similarity(a, b):
    na = normalize(a)
    nb = normalize(b)

    if not na or not nb:
        return 0.0

    aw = words(a)
    bw = words(b)

    inter = aw & bw
    union = aw | bw

    jaccard = (
        len(inter) / len(union)
        if union
        else 0.0
    )

    sequence = SequenceMatcher(
        None,
        na,
        nb,
    ).ratio()

    return (
        jaccard * 0.65
        + sequence * 0.35
    )


def overlap(a, b):
    aa = set(a)
    bb = set(b)

    if not aa or not bb:
        return 0.0, set()

    shared = aa & bb

    return (
        len(shared) / min(
            len(aa),
            len(bb),
        ),
        shared,
    )


def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return default


def save_json(path, data):
    directory = os.path.dirname(path)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True,
        )

    temp = path + ".tmp"

    with open(
        temp,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(
        temp,
        path,
    )


def load_news():
    data = load_json(
        NEWS_FILE,
        {"items": []},
    )

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return data.get(
            "items",
            [],
        )

    return []


def load_cases():
    data = load_json(
        CASE_FILE,
        None,
    )

    if data is None:
        return {
            "engine_version": ENGINE_VERSION,
            "cases": [],
        }

    if isinstance(data, list):
        return {
            "engine_version": ENGINE_VERSION,
            "cases": data,
        }

    if not isinstance(
        data.get("cases"),
        list,
    ):
        data["cases"] = []

    return data


def next_case_id(cases):
    highest = 0

    for case in cases:

        match = re.search(
            r"(\d+)$",
            str(
                case.get(
                    "case_id",
                    "",
                )
            ),
        )

        if match:
            highest = max(
                highest,
                int(match.group(1)),
            )

    return f"CASE-{highest + 1:06d}"


def make_case_title(news):
    return (
        news.get("title")
        or "Kasus tidak teridentifikasi"
    )[:180]


def case_signature(news):
    parts = [
        news.get("polres"),
        news.get("region"),
    ]

    return " ".join(
        str(part)
        for part in parts
        if part
    )


def is_case_candidate(news):
    scope = str(
        news.get("scope") or ""
    ).lower()

    category = str(
        news.get("category") or ""
    ).lower()

    if scope in {
        "case",
        "negative",
    }:
        return True

    negative_words = {
        "oknum",
        "etik",
        "disiplin",
        "penyalahgunaan",
        "pungli",
        "suap",
        "pemerasan",
        "penganiayaan",
        "narkoba",
        "korupsi",
        "kekerasan",
        "penembakan",
        "ditangkap",
        "tersangka",
    }

    return any(
        word in category
        for word in negative_words
    )


def same_polres(news, case):
    news_polres = news.get(
        "polres"
    )

    case_polres = case.get(
        "polres"
    )

    return bool(
        news_polres
        and case_polres
        and news_polres == case_polres
    )


def same_region(news, case):
    news_region = str(
        news.get("region") or ""
    ).strip().lower()

    case_region = str(
        case.get("region") or ""
    ).strip().lower()

    return bool(
        news_region
        and case_region
        and news_region == case_region
    )


def within_time_window(news, case):
    news_date = parse_dt(
        news.get(
            "published_at"
        )
    )

    first = parse_dt(
        case.get(
            "first_seen"
        )
    )

    last = parse_dt(
        case.get(
            "last_seen"
        )
    )

    if (
        not news_date
        or not first
        or not last
    ):
        return True

    nearest = min(
        abs(
            (
                news_date
                - first
            ).total_seconds()
        ),
        abs(
            (
                news_date
                - last
            ).total_seconds()
        ),
    ) / 86400.0

    return (
        nearest
        <= MAX_CASE_AGE_DAYS
    )


def case_key_set(case):
    result = set(
        case.get(
            "incident_terms",
            [],
        )
    )

    if result:
        return result

    for article in case.get(
        "articles",
        [],
    ):
        result |= key_words(
            article.get(
                "title",
                "",
            )
        )

    result |= key_words(
        case.get(
            "title",
            "",
        )
    )

    return result


def case_event_set(case):
    result = set(
        case.get(
            "event_terms",
            [],
        )
    )

    if result:
        return result

    for article in case.get(
        "articles",
        [],
    ):
        result |= event_words(
            article.get(
                "title",
                "",
            )
        )

    result |= event_words(
        case.get(
            "title",
            "",
        )
    )

    return result


def case_location_set(case):
    result = set(
        case.get(
            "location_terms",
            [],
        )
    )

    for article in case.get(
        "articles",
        [],
    ):
        result |= location_words(
            article.get(
                "title",
                "",
            )
        )

    result |= location_words(
        case.get(
            "title",
            "",
        )
    )

    if case.get(
        "polres"
    ):
        result |= location_words(
            case.get(
                "polres",
                "",
            )
        )

    return result


def match_score(news, case):
    title = news.get(
        "title",
        "",
    )

    news_keys = key_words(
        title
    )

    news_events = event_words(
        title
    )

    news_locations = location_words(
        title
    )

    case_keys = case_key_set(
        case
    )

    case_events = case_event_set(
        case
    )

    case_locations = case_location_set(
        case
    )

    key_score, shared_keys = overlap(
        news_keys,
        case_keys,
    )

    event_score, shared_events = (
        overlap(
            news_events,
            case_events,
        )
    )

    location_score, shared_locations = (
        overlap(
            news_locations,
            case_locations,
        )
    )

    title_score = similarity(
        title,
        case.get(
            "title",
            "",
        ),
    )

    article_title_score = 0.0

    for article in case.get(
        "articles",
        [],
    ):
        article_title_score = max(
            article_title_score,
            similarity(
                title,
                article.get(
                    "title",
                    "",
                ),
            ),
        )

    score = (
        event_score * 0.40
        + key_score * 0.20
        + location_score * 0.15
        + max(
            title_score,
            article_title_score,
        ) * 0.15
    )

    if same_polres(
        news,
        case,
    ):
        score += 0.08

    elif same_region(
        news,
        case,
    ):
        score += 0.02

    return min(
        score,
        1.0,
    ), {
        "shared_keys": shared_keys,
        "shared_events": shared_events,
        "shared_locations": shared_locations,
        "title_score": max(
            title_score,
            article_title_score,
        ),
    }


def find_matching_case(
    news,
    cases,
):
    candidates = []

    sorted_cases = sorted(
        cases,
        key=lambda case: case.get(
            "last_seen",
            "",
        ),
        reverse=True,
    )

    for case in sorted_cases[
        :MAX_CASES_TO_COMPARE
    ]:

        news_polres = news.get(
            "polres"
        )

        case_polres = case.get(
            "polres"
        )

        if (
            news_polres
            and case_polres
            and news_polres != case_polres
        ):
            continue

        if not within_time_window(
            news,
            case,
        ):
            continue

        score, evidence = (
            match_score(
                news,
                case,
            )
        )

        shared_events = evidence[
            "shared_events"
        ]

        shared_locations = evidence[
            "shared_locations"
        ]

        strong = (
            len(
                shared_events
            ) >= 2
            and (
                same_polres(
                    news,
                    case,
                )
                or (
                    same_region(
                        news,
                        case,
                    )
                    and len(
                        shared_locations
                    ) >= 1
                )
                or evidence[
                    "title_score"
                ] >= 0.70
            )
        )

        if (
            score >= MERGE_SCORE
            or strong
        ):
            candidates.append(
                (
                    score,
                    len(
                        shared_events
                    ),
                    len(
                        shared_locations
                    ),
                    case,
                    evidence,
                )
            )

    if not candidates:
        return (
            None,
            0.0,
            {},
        )

    candidates.sort(
        key=lambda row: (
            row[0],
            row[1],
            row[2],
        ),
        reverse=True,
    )

    (
        best_score,
        _,
        _,
        best_case,
        evidence,
    ) = candidates[0]

    return (
        best_case,
        round(
            best_score,
            4,
        ),
        evidence,
    )


def find_recovery_case(
    news,
    cases,
):
    case, score, evidence = (
        find_matching_case(
            news,
            cases,
        )
    )

    if not case:
        return (
            None,
            0.0,
            {},
        )

    shared_events = evidence.get(
        "shared_events",
        set(),
    )

    shared_locations = evidence.get(
        "shared_locations",
        set(),
    )

    title_score = evidence.get(
        "title_score",
        0.0,
    )

    # --------------------------------------------------------
    # VERY STRICT RECOVERY
    # --------------------------------------------------------
    #
    # A neutral/non-candidate article can be recovered only if:
    #
    # A. same Polres + at least 2 event terms
    #
    # OR
    #
    # B. same region + at least 2 event terms
    #    + at least 1 concrete location term
    #
    # OR
    #
    # C. very high title similarity + at least 2 event terms
    #
    # Score alone is NOT sufficient.
    # --------------------------------------------------------

    condition_a = (
        same_polres(
            news,
            case,
        )
        and len(
            shared_events
        ) >= 2
    )

    condition_b = (
        same_region(
            news,
            case,
        )
        and len(
            shared_events
        ) >= 2
        and len(
            shared_locations
        ) >= 1
    )

    condition_c = (
        title_score >= 0.78
        and len(
            shared_events
        ) >= 2
    )

    if not (
        condition_a
        or condition_b
        or condition_c
    ):
        return (
            None,
            score,
            evidence,
        )

    if score < RECOVERY_SCORE:
        return (
            None,
            score,
            evidence,
        )

    return (
        case,
        score,
        evidence,
    )


def attach_news(
    case,
    news,
    score,
):
    news_id = news.get(
        "id"
    )

    if not news_id:
        return

    case.setdefault(
        "article_ids",
        [],
    )

    case.setdefault(
        "articles",
        [],
    )

    if (
        news_id
        not in case["article_ids"]
    ):
        case[
            "article_ids"
        ].append(
            news_id
        )

    article = {
        "id": news_id,
        "title": news.get(
            "title",
            "",
        ),
        "url": news.get(
            "url",
            "",
        ),
        "published_at": news.get(
            "published_at"
        ),
        "source": news.get(
            "source"
        ),
        "match_score": round(
            score,
            4,
        ),
        "priority": news.get(
            "priority",
            "low",
        ),
        "scope": news.get(
            "scope"
        ),
        "category": news.get(
            "category"
        ),
        "region": news.get(
            "region"
        ),
        "is_jatim": news.get(
            "is_jatim"
        ),
        "polres": news.get(
            "polres"
        ),
    }

    replaced = False

    for index, current in enumerate(
        case["articles"]
    ):
        if current.get("id") == news_id:
            case[
                "articles"
            ][index] = article
            replaced = True
            break

    if not replaced:
        case[
            "articles"
        ].append(
            article
        )

    case[
        "article_count"
    ] = len(
        case["article_ids"]
    )

    published = (
        news.get(
            "published_at"
        )
        or ""
    )

    if published:
        if (
            not case.get(
                "first_seen"
            )
            or published
            < case["first_seen"]
        ):
            case[
                "first_seen"
            ] = published

        if (
            not case.get(
                "last_seen"
            )
            or published
            > case["last_seen"]
        ):
            case[
                "last_seen"
            ] = published

    case.setdefault(
        "incident_terms",
        [],
    )

    case.setdefault(
        "event_terms",
        [],
    )

    case.setdefault(
        "location_terms",
        [],
    )

    case[
        "incident_terms"
    ] = sorted(
        set(
            case[
                "incident_terms"
            ]
        )
        | key_words(
            news.get(
                "title",
                "",
            )
        )
    )

    case[
        "event_terms"
    ] = sorted(
        set(
            case[
                "event_terms"
            ]
        )
        | event_words(
            news.get(
                "title",
                "",
            )
        )
    )

    case[
        "location_terms"
    ] = sorted(
        set(
            case[
                "location_terms"
            ]
        )
        | location_words(
            news.get(
                "title",
                "",
            )
        )
    )

    if (
        not case.get(
            "title"
        )
    ):
        case[
            "title"
        ] = make_case_title(
            news
        )

    if (
        not case.get(
            "polres"
        )
        and news.get(
            "polres"
        )
    ):
        case[
            "polres"
        ] = news.get(
            "polres"
        )

    if (
        not case.get(
            "region"
        )
        and news.get(
            "region"
        )
    ):
        case[
            "region"
        ] = news.get(
            "region"
        )

    if news.get(
        "is_jatim"
    ):
        case[
            "is_jatim"
        ] = True

    current_priority = str(
        case.get(
            "priority",
            "low",
        )
    ).lower()

    article_priority = str(
        news.get(
            "priority",
            "low",
        )
    ).lower()

    if (
        PRIORITY_ORDER.get(
            article_priority,
            1,
        )
        >
        PRIORITY_ORDER.get(
            current_priority,
            1,
        )
    ):
        case[
            "priority"
        ] = article_priority

    case[
        "updated_at"
    ] = now_iso()


def create_case(
    news,
    cases,
):
    published_at = (
        news.get(
            "published_at"
        )
        or now_iso()
    )

    case = {
        "case_id": next_case_id(
            cases
        ),
        "title": make_case_title(
            news
        ),
        "category": news.get(
            "category"
        ),
        "scope": news.get(
            "scope"
        ),
        "region": news.get(
            "region"
        ),
        "is_jatim": news.get(
            "is_jatim"
        ),
        "polres": news.get(
            "polres"
        ),
        "priority": news.get(
            "priority",
            "low",
        ),
        "signature": case_signature(
            news
        ),
        "incident_terms": sorted(
            key_words(
                news.get(
                    "title",
                    "",
                )
            )
        ),
        "event_terms": sorted(
            event_words(
                news.get(
                    "title",
                    "",
                )
            )
        ),
        "location_terms": sorted(
            location_words(
                news.get(
                    "title",
                    "",
                )
            )
        ),
        "first_seen": published_at,
        "last_seen": published_at,
        "article_ids": [],
        "articles": [],
        "article_count": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "engine_version": ENGINE_VERSION,
    }

    attach_news(
        case,
        news,
        1.0,
    )

    cases.append(
        case
    )

    return case


def mark_processed(
    news,
    case_id,
):
    news[
        "processing_status"
    ] = "processed"

    news[
        "case_id"
    ] = case_id

    news[
        "case_processed_at"
    ] = now_iso()

    news[
        "case_engine_version"
    ] = ENGINE_VERSION


def mark_non_candidate(
    news
):
    news[
        "processing_status"
    ] = "processed"

    news[
        "case_id"
    ] = None

    news[
        "case_processed_at"
    ] = now_iso()

    news[
        "case_engine_version"
    ] = ENGINE_VERSION


def reset_case_state(
    news
):
    for item in news:
        item.pop(
            "processing_status",
            None,
        )

        item.pop(
            "case_id",
            None,
        )

        item.pop(
            "case_processed_at",
            None,
        )

        item.pop(
            "case_engine_version",
            None,
        )


def save_outputs(
    news,
    cases,
    mode,
    rebuild,
    recovery_checked,
    recovery_matched,
    normal_matched,
    new_cases,
):
    for case in cases:

        seen = set()

        unique_articles = []

        for article in case.get(
            "articles",
            [],
        ):
            article_id = article.get(
                "id"
            )

            if (
                not article_id
                or article_id in seen
            ):
                continue

            seen.add(
                article_id
            )

            unique_articles.append(
                article
            )

        case[
            "articles"
        ] = unique_articles

        case[
            "article_ids"
        ] = [
            article[
                "id"
            ]
            for article
            in unique_articles
        ]

        case[
            "article_count"
        ] = len(
            unique_articles
        )

    total_articles = sum(
        case.get(
            "article_count",
            0,
        )
        for case in cases
    )

    database = {
        "engine_version": ENGINE_VERSION,
        "generated_at": now_iso(),
        "total_cases": len(
            cases
        ),
        "total_articles": total_articles,
        "last_run": {
            "mode": mode,
            "rebuild": rebuild,
            "news_loaded": len(
                news
            ),
            "recovery_checked":
                recovery_checked,
            "recovery_matched":
                recovery_matched,
            "matched_existing":
                normal_matched,
            "new_cases":
                new_cases,
        },
        "cases": cases,
    }

    save_json(
        CASE_FILE,
        database,
    )

    news_database = load_json(
        NEWS_FILE,
        {},
    )

    if isinstance(
        news_database,
        dict,
    ):
        news_database[
            "items"
        ] = news

        news_database[
            "case_engine_version"
        ] = ENGINE_VERSION

        news_database[
            "case_engine_processed_at"
        ] = now_iso()

        save_json(
            NEWS_FILE,
            news_database,
        )

    return total_articles


def main():
    print(
        "========================================"
    )

    print(
        "PNM CASE ENGINE V4.1"
    )

    print(
        "STEP 1 REPAIR + INCIDENT CLUSTERING"
    )

    print(
        "========================================"
    )

    news = load_news()

    database = load_cases()

    print(
        f"Total news loaded : {len(news)}"
    )

    print(
        f"Existing cases    : "
        f"{len(database.get('cases', []))}"
    )

    existing_version = database.get(
        "engine_version"
    )

    print(
        f"Existing engine   : "
        f"{existing_version or 'none'}"
    )

    # Force one clean rebuild because v4
    # already contained false recovery matches.
    rebuild = True

    print(
        "========================================"
    )

    print(
        "V4.1 REPAIR REBUILD"
    )

    print(
        "Recovery lama akan dibersihkan."
    )

    print(
        "Case dibangun ulang dari news candidate."
    )

    print(
        "Recovery neutral dilakukan setelah case"
    )

    print(
        "terbentuk dengan aturan sangat ketat."
    )

    print(
        "========================================"
    )

    reset_case_state(
        news
    )

    cases = []

    candidates = []

    non_candidates = []

    for item in news:

        if is_case_candidate(
            item
        ):
            candidates.append(
                item
            )
        else:
            non_candidates.append(
                item
            )

    # --------------------------------------------------------
    # BUILD CLEAN CASES
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item: (
            parse_dt(
                item.get(
                    "published_at"
                )
            )
            or datetime.max.replace(
                tzinfo=timezone.utc
            )
        )
    )

    normal_matched = 0
    new_cases = 0

    print(
        f"Case candidates   : "
        f"{len(candidates)}"
    )

    for index, item in enumerate(
        candidates,
        start=1,
    ):

        existing_case, score, evidence = (
            find_matching_case(
                item,
                cases,
            )
        )

        if existing_case:

            attach_news(
                existing_case,
                item,
                score,
            )

            mark_processed(
                item,
                existing_case[
                    "case_id"
                ],
            )

            normal_matched += 1

            action = (
                f"MATCH "
                f"{existing_case['case_id']} "
                f"({score:.2f})"
            )

        else:

            new_case = create_case(
                item,
                cases,
            )

            mark_processed(
                item,
                new_case[
                    "case_id"
                ],
            )

            new_cases += 1

            action = (
                f"NEW "
                f"{new_case['case_id']}"
            )

        if (
            index <= 20
            or index % 25 == 0
            or index == len(candidates)
        ):

            print(
                f"Processed "
                f"{index}/{len(candidates)} "
                f"| Cases: {len(cases)} "
                f"| {action} "
                f"| "
                f"{item.get('title', '')[:80]}"
            )

    # --------------------------------------------------------
    # STRICT RECOVERY
    # --------------------------------------------------------

    recovery_checked = 0
    recovery_matched = 0

    print(
        "========================================"
    )

    print(
        "STRICT CASE RECOVERY"
    )

    print(
        f"Articles eligible : "
        f"{len(non_candidates)}"
    )

    print(
        "========================================"
    )

    for item in non_candidates:

        recovery_checked += 1

        (
            recovery_case,
            score,
            evidence,
        ) = find_recovery_case(
            item,
            cases,
        )

        if recovery_case:

            attach_news(
                recovery_case,
                item,
                score,
            )

            mark_processed(
                item,
                recovery_case[
                    "case_id"
                ],
            )

            recovery_matched += 1

            shared_events = ",".join(
                sorted(
                    evidence.get(
                        "shared_events",
                        set(),
                    )
                )
            )

            shared_locations = ",".join(
                sorted(
                    evidence.get(
                        "shared_locations",
                        set(),
                    )
                )
            )

            print(
                f"RECOVERY "
                f"{recovery_case['case_id']} "
                f"({score:.2f}) "
                f"[events:{shared_events}] "
                f"[locations:{shared_locations}] "
                f"| "
                f"{item.get('title', '')[:90]}"
            )

        else:

            mark_non_candidate(
                item
            )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    total_articles = save_outputs(
        news,
        cases,
        "REBUILD",
        True,
        recovery_checked,
        recovery_matched,
        normal_matched,
        new_cases,
    )

    print(
        "========================================"
    )

    print(
        "CASE ENGINE COMPLETE"
    )

    print(
        "Mode             : REBUILD"
    )

    print(
        "Rebuild          : YES"
    )

    print(
        f"Total news       : "
        f"{len(news)}"
    )

    print(
        f"Case candidates  : "
        f"{len(candidates)}"
    )

    print(
        f"Recovery checked : "
        f"{recovery_checked}"
    )

    print(
        f"Recovery matched : "
        f"{recovery_matched}"
    )

    print(
        f"Matched existing : "
        f"{normal_matched}"
    )

    print(
        f"New cases        : "
        f"{new_cases}"
    )

    print(
        f"Total cases      : "
        f"{len(cases)}"
    )

    print(
        f"Total articles   : "
        f"{total_articles}"
    )

    print(
        f"Output           : "
        f"{CASE_FILE}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
