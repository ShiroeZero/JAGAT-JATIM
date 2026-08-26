import json
import os
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

NEWS_FILE = "data/news.json"
CASE_FILE = "data/case_clusters.json"

ENGINE_VERSION = "case-v4"

# ============================================================
# V4 — INCIDENT-BASED CLUSTERING
# ============================================================
#
# Important:
# - Category is NOT a hard separator.
# - A case represents one real-world incident and its updates.
# - First run after upgrading from case-v3 performs a one-time
#   rebuild of all eligible news.
# - Subsequent runs are incremental.
# - STEP 1:
#   Previously processed articles with case_id=null are allowed
#   to recover into an EXISTING case when the incident match is
#   sufficiently strong.
#
# ============================================================

MAX_CASES_TO_COMPARE = 1000
MAX_CASE_AGE_DAYS = 90

# Minimum scores for merging an article into an existing incident.
MERGE_SCORE = 0.56
STRONG_TERM_SCORE = 0.48

# Recovery is deliberately stricter than normal matching.
# IMPORTANT:
# Recovery can ONLY attach an article to an existing case.
# It NEVER creates a new case.
RECOVERY_MATCH_SCORE = 0.62

PRIORITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada",
    "dalam", "oleh", "ini", "itu", "seorang", "orang", "jadi", "akan",
    "telah", "adalah", "terkait", "soal", "kasus", "berita", "polisi",
    "polri", "anggota", "oknum", "diduga", "ungkap", "mengungkap",
    "tangkap", "menangkap", "ditangkap", "amankan", "diamankan",
    "tersangka", "pelaku", "korban", "kronologi", "terjadi", "atas",
    "karena", "hingga", "saat", "sebuah", "sejumlah", "kembali",
    "usai", "setelah", "sebelumnya", "terhadap", "menjadi", "dengan",
    "para", "sebagai", "yakni", "langsung", "hal", "pengungkapan",
    "penanganan", "ditemukan", "diketahui", "membuat", "kata", "ujar",
    "menurut", "hari", "tahun", "bulan", "warga", "satu", "dua", "tiga",
    "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh",
}

GENERIC_CASE_WORDS = {
    "polisi", "polri", "anggota", "oknum", "kasus", "berita", "ungkap",
    "mengungkap", "tangkap", "menangkap", "ditangkap", "amankan",
    "diamankan", "tersangka", "pelaku", "korban", "diduga", "terlibat",
    "terkait", "kejadian", "peristiwa", "kronologi", "penanganan",
    "kekerasan", "penganiayaan", "narkoba", "korupsi", "pungli", "suap",
    "etik", "disiplin", "pemerasan", "penyalahgunaan", "wewenang",
    "penembakan", "tindak", "pidana", "penindakan", "mengamankan",
    "ditetapkan", "pemeriksaan", "diperiksa", "memeriksa", "ditahan",
    "menahan", "ditangkapnya", "mengaku", "menyebut", "sebut",
    "berhasil", "berhasilnya",
}

# Words useful for identifying one concrete incident even when
# the classification category changes.
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
        w
        for w in normalize(text).split()
        if len(w) >= 3 and w not in STOPWORDS
    }


def key_words(text):
    return {
        w
        for w in words(text)
        if w not in GENERIC_CASE_WORDS
    }


def event_words(text):
    return key_words(text) & EVENT_WORDS


def similarity(a, b):
    na = normalize(a)
    nb = normalize(b)

    if not na or not nb:
        return 0.0

    aw = words(a)
    bw = words(b)

    inter = aw & bw
    union = aw | bw

    jaccard = len(inter) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, na, nb).ratio()

    return (jaccard * 0.65) + (sequence * 0.35)


def overlap(a, b):
    aa = set(a)
    bb = set(b)

    if not aa or not bb:
        return 0.0, set()

    shared = aa & bb

    return (
        len(shared) / min(len(aa), len(bb)),
        shared,
    )


def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    temp = path + ".tmp"

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(temp, path)


def load_news():
    data = load_json(
        NEWS_FILE,
        {"items": []},
    )

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return data.get("items", [])

    return []


def load_cases():
    data = load_json(
        CASE_FILE,
        None,
    )

    if data is None:
        return {
            "engine_version": ENGINE_VERSION,
            "generated_at": now_iso(),
            "total_cases": 0,
            "total_articles": 0,
            "cases": [],
        }

    if isinstance(data, list):
        return {
            "engine_version": ENGINE_VERSION,
            "generated_at": now_iso(),
            "total_cases": len(data),
            "total_articles": sum(
                c.get("article_count", 0)
                for c in data
                if isinstance(c, dict)
            ),
            "cases": data,
        }

    if not isinstance(data.get("cases"), list):
        data["cases"] = []

    return data


def next_case_id(cases):
    highest = 0

    for case in cases:
        match = re.search(
            r"(\d+)$",
            str(case.get("case_id", "")),
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
        str(x)
        for x in parts
        if x
    )


def is_case_candidate(news):
    scope = str(
        news.get("scope") or ""
    ).lower()

    category = str(
        news.get("category") or ""
    ).lower()

    if scope in {"case", "negative"}:
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
    np = news.get("polres")
    cp = case.get("polres")

    return bool(
        np
        and cp
        and np == cp
    )


def same_region(news, case):
    nr = str(
        news.get("region") or ""
    ).strip().lower()

    cr = str(
        case.get("region") or ""
    ).strip().lower()

    return bool(
        nr
        and cr
        and nr == cr
    )


def within_time_window(news, case):
    nd = parse_dt(
        news.get("published_at")
    )

    first = parse_dt(
        case.get("first_seen")
    )

    last = parse_dt(
        case.get("last_seen")
    )

    if not nd or not first or not last:
        return True

    nearest = min(
        abs(
            (nd - first).total_seconds()
        ),
        abs(
            (nd - last).total_seconds()
        ),
    ) / 86400.0

    return nearest <= MAX_CASE_AGE_DAYS


def case_key_set(case):
    keys = set(
        case.get("incident_terms") or []
    )

    if keys:
        return keys

    terms = set()

    for article in case.get("articles", []):
        terms |= key_words(
            article.get("title", "")
        )

    terms |= key_words(
        case.get("title", "")
    )

    return terms


def case_event_set(case):
    events = set(
        case.get("event_terms") or []
    )

    if events:
        return events

    events = set()

    for article in case.get("articles", []):
        events |= event_words(
            article.get("title", "")
        )

    events |= event_words(
        case.get("title", "")
    )

    return events


def article_identity(news):
    title = news.get("title", "")

    return {
        "keys": key_words(title),
        "events": event_words(title),
        "words": words(title),
    }


def match_score(news, case):
    identity = article_identity(news)

    nk = identity["keys"]
    ne = identity["events"]

    ck = case_key_set(case)
    ce = case_event_set(case)

    key_score, shared_keys = overlap(
        nk,
        ck,
    )

    event_score, shared_events = overlap(
        ne,
        ce,
    )

    title_score = similarity(
        news.get("title", ""),
        case.get("title", ""),
    )

    article_title_score = 0.0

    for article in case.get("articles", []):
        article_title_score = max(
            article_title_score,
            similarity(
                news.get("title", ""),
                article.get("title", ""),
            ),
        )

    score = (
        event_score * 0.40
        + key_score * 0.25
        + max(
            title_score,
            article_title_score,
        ) * 0.20
    )

    if same_polres(news, case):
        score += 0.10

    if same_region(news, case):
        score += 0.02

    if len(shared_events) >= 2:
        score += 0.10

    very_strong = (
        len(shared_events) >= 3
    )

    return min(score, 1.0), {
        "shared_keys": shared_keys,
        "shared_events": shared_events,
        "title_score": max(
            title_score,
            article_title_score,
        ),
        "very_strong": very_strong,
    }


def find_matching_case(news, cases):
    candidates = []

    sorted_cases = sorted(
        cases,
        key=lambda c: c.get(
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

        # Explicitly different Polres remains
        # a hard boundary.
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

        score, evidence = match_score(
            news,
            case,
        )

        strong = (
            len(
                evidence[
                    "shared_events"
                ]
            ) >= 2
            and (
                evidence["title_score"] >= 0.42
                or same_polres(news, case)
                or same_region(news, case)
            )
        )

        very_strong = evidence[
            "very_strong"
        ]

        if (
            score >= MERGE_SCORE
            or strong
            or very_strong
        ):
            candidates.append(
                (
                    score,
                    len(
                        evidence[
                            "shared_events"
                        ]
                    ),
                    len(
                        evidence[
                            "shared_keys"
                        ]
                    ),
                    case,
                    evidence,
                )
            )

    if not candidates:
        return None, 0.0, {}

    candidates.sort(
        key=lambda x: (
            x[0],
            x[1],
            x[2],
        ),
        reverse=True,
    )

    best_score, _, _, best_case, evidence = (
        candidates[0]
    )

    return (
        best_case,
        round(best_score, 4),
        evidence,
    )


def attach_news(case, news, score):
    news_id = news.get("id")

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
        case["article_ids"].append(
            news_id
        )

    existing_by_id = {
        article.get("id"): article
        for article in case["articles"]
        if (
            isinstance(article, dict)
            and article.get("id")
        )
    }

    article = existing_by_id.get(
        news_id,
        {},
    )

    article.update(
        {
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
    )

    if (
        news_id
        not in existing_by_id
    ):
        case["articles"].append(
            article
        )
    else:
        for index, current in enumerate(
            case["articles"]
        ):
            if current.get("id") == news_id:
                case["articles"][index] = (
                    article
                )
                break

    case["article_count"] = len(
        case["article_ids"]
    )

    published = (
        news.get("published_at")
        or ""
    )

    old_last = (
        case.get("last_seen")
        or ""
    )

    if published:
        if (
            not old_last
            or published > old_last
        ):
            case["last_seen"] = (
                published
            )

        if (
            not case.get("first_seen")
            or published
            < case["first_seen"]
        ):
            case["first_seen"] = (
                published
            )

    case.setdefault(
        "incident_terms",
        [],
    )

    case.setdefault(
        "event_terms",
        [],
    )

    case["incident_terms"] = sorted(
        set(
            case["incident_terms"]
        )
        | key_words(
            news.get(
                "title",
                "",
            )
        )
    )

    case["event_terms"] = sorted(
        set(
            case["event_terms"]
        )
        | event_words(
            news.get(
                "title",
                "",
            )
        )
    )

    if not case.get("title"):
        case["title"] = (
            make_case_title(news)
        )

    if (
        not case.get("polres")
        and news.get("polres")
    ):
        case["polres"] = news.get(
            "polres"
        )

    if (
        not case.get("region")
        and news.get("region")
    ):
        case["region"] = news.get(
            "region"
        )

    if news.get("is_jatim"):
        case["is_jatim"] = True

    old_priority = str(
        case.get("priority")
        or "low"
    ).lower()

    new_priority = str(
        news.get("priority")
        or "low"
    ).lower()

    if (
        PRIORITY_ORDER.get(
            new_priority,
            1,
        )
        >
        PRIORITY_ORDER.get(
            old_priority,
            1,
        )
    ):
        case["priority"] = (
            new_priority
        )

    case["updated_at"] = now_iso()


def synchronize_existing_cases(
    cases,
    news,
):
    """
    Backfill existing cases from the canonical news database.

    This does NOT create or destroy cases.
    It only:
    - refreshes article metadata
    - restores priority metadata
    - rebuilds incident/event terms
    - refreshes first/last seen
    - keeps Case ↔ News data consistent
    """

    news_by_id = {
        item.get("id"): item
        for item in news
        if (
            isinstance(item, dict)
            and item.get("id")
        )
    }

    linked_articles = 0
    updated_cases = 0

    for case in cases:

        old_articles = [
            article
            for article in case.get(
                "articles",
                [],
            )
            if (
                isinstance(article, dict)
                and article.get("id")
            )
        ]

        ids = []
        seen = set()
        rebuilt_articles = []

        for article in old_articles:

            article_id = article.get(
                "id"
            )

            if article_id in seen:
                continue

            seen.add(
                article_id
            )

            ids.append(
                article_id
            )

            source = news_by_id.get(
                article_id
            )

            if source:

                merged = dict(
                    article
                )

                merged.update(
                    {
                        "id": article_id,
                        "title": source.get(
                            "title",
                            article.get(
                                "title",
                                "",
                            ),
                        ),
                        "url": source.get(
                            "url",
                            article.get(
                                "url",
                                "",
                            ),
                        ),
                        "published_at":
                            source.get(
                                "published_at",
                                article.get(
                                    "published_at"
                                ),
                            ),
                        "source": source.get(
                            "source",
                            article.get(
                                "source"
                            ),
                        ),
                        "priority": source.get(
                            "priority",
                            article.get(
                                "priority",
                                "low",
                            ),
                        ),
                        "scope": source.get(
                            "scope",
                            article.get(
                                "scope"
                            ),
                        ),
                        "category": source.get(
                            "category",
                            article.get(
                                "category"
                            ),
                        ),
                        "region": source.get(
                            "region",
                            article.get(
                                "region"
                            ),
                        ),
                        "is_jatim":
                            source.get(
                                "is_jatim",
                                article.get(
                                    "is_jatim"
                                ),
                            ),
                        "polres": source.get(
                            "polres",
                            article.get(
                                "polres"
                            ),
                        ),
                    }
                )

                rebuilt_articles.append(
                    merged
                )

                linked_articles += 1

            else:
                rebuilt_articles.append(
                    dict(article)
                )

        case["articles"] = (
            rebuilt_articles
        )

        case["article_ids"] = ids

        case["article_count"] = len(
            ids
        )

        if not ids:
            continue

        all_titles = [
            article.get(
                "title",
                "",
            )
            for article
            in rebuilt_articles
            if article.get("title")
        ]

        all_titles.append(
            case.get(
                "title",
                "",
            )
        )

        incident_terms = set()
        event_terms = set()

        for title in all_titles:
            incident_terms |= (
                key_words(title)
            )

            event_terms |= (
                event_words(title)
            )

        case["incident_terms"] = sorted(
            incident_terms
        )

        case["event_terms"] = sorted(
            event_terms
        )

        priorities = [
            PRIORITY_ORDER.get(
                str(
                    article.get(
                        "priority"
                    )
                    or "low"
                ).lower(),
                1,
            )
            for article
            in rebuilt_articles
        ]

        if priorities:
            highest = max(
                priorities
            )

            case["priority"] = next(
                name
                for name, value
                in PRIORITY_ORDER.items()
                if value == highest
            )

        article_polres = [
            article.get("polres")
            for article
            in rebuilt_articles
            if article.get("polres")
        ]

        article_region = [
            article.get("region")
            for article
            in rebuilt_articles
            if article.get("region")
        ]

        if (
            not case.get("polres")
            and article_polres
        ):
            case["polres"] = (
                article_polres[0]
            )

        if (
            not case.get("region")
            and article_region
        ):
            case["region"] = (
                article_region[0]
            )

        if any(
            article.get("is_jatim")
            for article
            in rebuilt_articles
        ):
            case["is_jatim"] = True

        dates = []

        for article in rebuilt_articles:

            parsed = parse_dt(
                article.get(
                    "published_at"
                )
            )

            if parsed:
                dates.append(
                    parsed
                )

        if dates:
            case["first_seen"] = (
                min(dates).isoformat()
            )

            case["last_seen"] = (
                max(dates).isoformat()
            )

        case["updated_at"] = now_iso()

        updated_cases += 1

    return (
        updated_cases,
        linked_articles,
    )


def find_recovery_case(
    news,
    cases,
):
    """
    Match a previously processed article
    ONLY to an EXISTING case.

    A recovery match:
    - can attach an article to a case
    - can update the case priority
    - can restore case_id
    - can NOT create a new case
    """

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

    strong_recovery = (
        score >= RECOVERY_MATCH_SCORE
        or (
            len(shared_events) >= 3
            and (
                same_polres(
                    news,
                    case,
                )
                or same_region(
                    news,
                    case,
                )
            )
        )
    )

    if not strong_recovery:
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
    news["processing_status"] = (
        "processed"
    )

    news["case_id"] = case_id

    news["case_processed_at"] = (
        now_iso()
    )

    news["case_engine_version"] = (
        ENGINE_VERSION
    )


def mark_non_candidate(news):
    news["processing_status"] = (
        "processed"
    )

    news["case_id"] = None

    news["case_processed_at"] = (
        now_iso()
    )

    news["case_engine_version"] = (
        ENGINE_VERSION
    )


def reset_case_state(news):
    """
    Clear only case-engine fields.
    Collector data remains untouched.
    """

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


def needs_rebuild(database):
    return (
        database.get(
            "engine_version"
        )
        != ENGINE_VERSION
    )


def save_outputs(
    news,
    cases,
    already_processed,
    pending_count,
    matched,
    created,
    mode,
    rebuilt,
    recovery_matched=0,
):
    # Defensive deduplication.
    for case in cases:

        seen = set()

        unique_articles = []

        for article in case.get(
            "articles",
            [],
        ):

            aid = article.get(
                "id"
            )

            if not aid or aid in seen:
                continue

            seen.add(aid)

            unique_articles.append(
                article
            )

        case["articles"] = (
            unique_articles
        )

        case["article_ids"] = [
            article["id"]
            for article
            in unique_articles
        ]

        case["article_count"] = len(
            unique_articles
        )

    total_articles = sum(
        case.get(
            "article_count",
            0,
        )
        for case in cases
        if isinstance(case, dict)
    )

    database = {
        "engine_version": ENGINE_VERSION,
        "generated_at": now_iso(),
        "total_cases": len(
            cases
        ),
        "total_articles": (
            total_articles
        ),
        "last_run": {
            "mode": mode,
            "rebuild": rebuilt,
            "news_loaded": len(
                news
            ),
            "already_processed":
                already_processed,
            "pending": pending_count,
            "matched_existing":
                matched,
            "new_cases": created,
            "recovery_matched":
                recovery_matched,
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

        news_database["items"] = (
            news
        )

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
        "PNM CASE ENGINE V4"
    )

    print(
        "INCIDENT-BASED CLUSTERING"
    )

    print(
        "========================================"
    )

    news = load_news()

    database = load_cases()

    existing_version = (
        database.get(
            "engine_version"
        )
    )

    existing_cases = (
        database.get(
            "cases",
            [],
        )
    )

    if not isinstance(
        existing_cases,
        list,
    ):
        existing_cases = []

    print(
        f"Total news loaded : {len(news)}"
    )

    print(
        f"Existing cases    : {len(existing_cases)}"
    )

    print(
        f"Existing engine   : "
        f"{existing_version or 'none'}"
    )

    # --------------------------------------------------------
    # ONE-TIME V4 REBUILD
    # --------------------------------------------------------

    rebuilt = needs_rebuild(
        database
    )

    if rebuilt:

        print(
            "========================================"
        )

        print(
            "V4 REBUILD MODE"
        )

        print(
            "Engine version berubah."
        )

        print(
            "Semua case akan dibangun ulang dari"
        )

        print(
            "news yang tersedia agar clustering lama"
        )

        print(
            "yang terpecah dapat digabung."
        )

        print(
            "========================================"
        )

        reset_case_state(
            news
        )

        cases = []

        pending = []

        for item in news:

            if is_case_candidate(
                item
            ):
                pending.append(
                    item
                )
            else:
                mark_non_candidate(
                    item
                )

        already_processed = 0

        mode = "REBUILD"

        synced_cases = 0
        synced_articles = 0
        recovery_checked = 0
        recovery_matched = 0
        recovery_titles = []

    else:

        cases = existing_cases

        pending = []

        # =====================================================
        # STEP 1 — SYNCHRONIZE EXISTING CASES
        # =====================================================

        synced_cases, synced_articles = (
            synchronize_existing_cases(
                cases,
                news,
            )
        )

        # =====================================================
        # STEP 1 — RECOVERY
        # =====================================================

        recovery_checked = 0
        recovery_matched = 0
        recovery_titles = []

        already_processed = 0

        for item in news:

            status = item.get(
                "processing_status"
            )

            case_id = item.get(
                "case_id"
            )

            # -------------------------------------------------
            # Valid existing Case ID:
            # leave normal processed data alone.
            # -------------------------------------------------

            if (
                status == "processed"
                and case_id
            ):

                if any(
                    case.get(
                        "case_id"
                    ) == case_id
                    for case in cases
                ):

                    already_processed += 1

                    continue

                # Stale case ID:
                # remove only case-engine fields,
                # then allow re-processing.
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

                status = None
                case_id = None

            # -------------------------------------------------
            # PROCESSED WITHOUT CASE
            #
            # This is the important STEP 1 change.
            #
            # Previously:
            #     processed + case_id null
            #     -> immediately skipped
            #
            # Now:
            #     processed + case_id null
            #     -> try strict recovery against existing cases
            # -------------------------------------------------

            if (
                status == "processed"
                and not case_id
            ):

                recovery_checked += 1

                (
                    recovery_case,
                    recovery_score,
                    recovery_evidence,
                ) = find_recovery_case(
                    item,
                    cases,
                )

                if recovery_case:

                    attach_news(
                        recovery_case,
                        item,
                        recovery_score,
                    )

                    mark_processed(
                        item,
                        recovery_case[
                            "case_id"
                        ],
                    )

                    recovery_matched += 1

                    if len(
                        recovery_titles
                    ) < 10:

                        recovery_titles.append(
                            (
                                recovery_case[
                                    "case_id"
                                ],
                                recovery_score,
                                item.get(
                                    "title",
                                    "",
                                ),
                            )
                        )

                    continue

                # Still not connected to a case.
                # Keep it processed and outside
                # the case database.
                already_processed += 1

                continue

            # -------------------------------------------------
            # UNPROCESSED NON-CANDIDATE
            # -------------------------------------------------

            if not is_case_candidate(
                item
            ):

                mark_non_candidate(
                    item
                )

                already_processed += 1

                continue

            # -------------------------------------------------
            # NORMAL INCREMENTAL CANDIDATE
            # -------------------------------------------------

            pending.append(
                item
            )

        mode = "INCREMENTAL"

    print(
        f"Mode              : {mode}"
    )

    # Recovery information only exists in
    # meaningful form during incremental runs.
    if not rebuilt:

        print(
            "----------------------------------------"
        )

        print(
            "CASE ↔ NEWS SYNC"
        )

        print(
            f"Cases synchronized: "
            f"{synced_cases}"
        )

        print(
            f"Articles synced   : "
            f"{synced_articles}"
        )

        print(
            f"Recovery checked  : "
            f"{recovery_checked}"
        )

        print(
            f"Recovery matched  : "
            f"{recovery_matched}"
        )

        for (
            case_id,
            score,
            title,
        ) in recovery_titles:

            print(
                f"RECOVERY {case_id} "
                f"({score:.2f}) | "
                f"{title[:90]}"
            )

    print(
        f"Already processed : "
        f"{already_processed}"
    )

    print(
        f"News to process   : "
        f"{len(pending)}"
    )

    print(
        "========================================"
    )

    matched = 0
    created = 0

    # Oldest first makes the initial case title stable
    # and gives later updates a chance to match.
    pending.sort(
        key=lambda x: (
            parse_dt(
                x.get(
                    "published_at"
                )
            )
            or datetime.max.replace(
                tzinfo=timezone.utc
            )
        )
    )

    for index, item in enumerate(
        pending,
        start=1,
    ):

        title = item.get(
            "title",
            "",
        )

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

            matched += 1

            shared = ",".join(
                sorted(
                    evidence.get(
                        "shared_events",
                        set(),
                    )
                )
            )

            action = (
                f"MATCH "
                f"{existing_case['case_id']} "
                f"({score:.2f})"
            )

            if shared:
                action += (
                    f" [{shared[:70]}]"
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

            created += 1

            action = (
                f"NEW "
                f"{new_case['case_id']}"
            )

        if (
            index <= 20
            or index % 25 == 0
            or index == len(pending)
        ):

            print(
                f"Processed "
                f"{index}/{len(pending)} "
                f"| Cases: {len(cases)} "
                f"| {action} "
                f"| {title[:80]}"
            )

    total_articles = save_outputs(
        news,
        cases,
        already_processed,
        len(pending),
        matched,
        created,
        mode,
        rebuilt,
        recovery_matched
        if not rebuilt
        else 0,
    )

    print(
        "========================================"
    )

    print(
        "CASE ENGINE COMPLETE"
    )

    print(
        f"Mode             : {mode}"
    )

    print(
        f"Rebuild          : "
        f"{'YES' if rebuilt else 'NO'}"
    )

    print(
        f"Total news       : "
        f"{len(news)}"
    )

    print(
        f"Already processed: "
        f"{already_processed}"
    )

    print(
        f"Processed now    : "
        f"{len(pending)}"
    )

    print(
        f"Matched existing : "
        f"{matched}"
    )

    if not rebuilt:

        print(
            f"Recovery matched : "
            f"{recovery_matched}"
        )

    print(
        f"New cases        : "
        f"{created}"
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
