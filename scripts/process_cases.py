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
#
# ============================================================

MAX_CASES_TO_COMPARE = 1000
MAX_CASE_AGE_DAYS = 90

# Minimum scores for merging an article into an existing incident.
MERGE_SCORE = 0.56
STRONG_TERM_SCORE = 0.48

PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada",
    "dalam", "oleh", "ini", "itu", "seorang", "orang", "jadi", "akan",
    "telah", "adalah", "terkait", "soal", "kasus", "berita", "polisi",
    "polri", "anggota", "oknum", "diduga", "ungkap", "mengungkap",
    "tangkap", "menangkap", "ditangkap", "amankan", "diamankan",
    "tersangka", "pelaku", "korban", "kronologi", "terjadi", "atas",
    "karena", "hingga", "saat", "sebuah", "sejumlah", "kembali",
    "usai", "setelah", "sebelumnya", "terhadap", "menjadi", "dengan",
    "para", "sebagai", "yakni", "yakni", "langsung", "dalam", "hal",
    "ungkap", "pengungkapan", "penanganan", "ditemukan", "diketahui",
    "membuat", "kata", "ujar", "menurut", "terkait", "soal", "saat",
    "hari", "tahun", "bulan", "warga", "satu", "dua", "tiga", "empat",
    "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh",
}

GENERIC_CASE_WORDS = {
    "polisi", "polri", "anggota", "oknum", "kasus", "berita", "ungkap",
    "mengungkap", "tangkap", "menangkap", "ditangkap", "amankan",
    "diamankan", "tersangka", "pelaku", "korban", "diduga", "terlibat",
    "terkait", "kejadian", "peristiwa", "kronologi", "penanganan",
    "kekerasan", "penganiayaan", "narkoba", "korupsi", "pungli", "suap",
    "etik", "disiplin", "pemerasan", "penyalahgunaan", "wewenang",
    "penembakan", "tindak", "pidana", "penindakan", "mengamankan",
    "diamankan", "ditetapkan", "pemeriksaan", "diperiksa", "memeriksa",
    "ditahan", "menahan", "ditangkap", "ditangkapnya", "mengaku",
    "menyebut", "sebut", "berhasil", "berhasilnya", "terkait",
}

# Words which are often useful for identifying an incident even when
# the category changes over time.
EVENT_WORDS = {
    "intimidasi", "wartawan", "jurnalis", "pwi", "tuntutan", "permintaan",
    "maaf", "propam", "sula", "sanana", "jeju", "tuban", "pacitan",
    "tangerang", "kendari", "fasilitas", "pengadilan", "vonis", "divonis",
    "bebas", "seksual", "kekerasan", "curanmor", "pencurian", "pencuri",
    "motor", "emas", "350", "juta", "celurit", "letter", "hilang",
    "misteri", "pembunuhan", "penembakan", "narkoba", "sabu", "ganja",
    "korupsi", "pungli", "suap", "pemerasan", "penyalahgunaan",
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
        w for w in normalize(text).split()
        if len(w) >= 3 and w not in STOPWORDS
    }

def key_words(text):
    return {
        w for w in words(text)
        if w not in GENERIC_CASE_WORDS
    }

def event_words(text):
    return key_words(text) & EVENT_WORDS

def similarity(a, b):
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    aw, bw = words(a), words(b)
    inter = aw & bw
    union = aw | bw
    jaccard = len(inter) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, na, nb).ratio()
    return (jaccard * 0.65) + (sequence * 0.35)

def overlap(a, b):
    aa, bb = set(a), set(b)
    if not aa or not bb:
        return 0.0, set()
    shared = aa & bb
    return len(shared) / min(len(aa), len(bb)), shared

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
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp, path)

def load_news():
    data = load_json(NEWS_FILE, {"items": []})
    if isinstance(data, list):
        return data
    return data.get("items", []) if isinstance(data, dict) else []

def load_cases():
    data = load_json(CASE_FILE, None)
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
            "total_articles": sum(c.get("article_count", 0) for c in data if isinstance(c, dict)),
            "cases": data,
        }
    if not isinstance(data.get("cases"), list):
        data["cases"] = []
    return data

def next_case_id(cases):
    highest = 0
    for case in cases:
        match = re.search(r"(\d+)$", str(case.get("case_id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"CASE-{highest + 1:06d}"

def make_case_title(news):
    return (news.get("title") or "Kasus tidak teridentifikasi")[:180]

def case_signature(news):
    parts = [
        news.get("polres"),
        news.get("region"),
    ]
    return " ".join(str(x) for x in parts if x)

def is_case_candidate(news):
    scope = str(news.get("scope") or "").lower()
    category = str(news.get("category") or "").lower()

    if scope in {"case", "negative"}:
        return True

    negative_words = {
        "oknum", "etik", "disiplin", "penyalahgunaan", "pungli", "suap",
        "pemerasan", "penganiayaan", "narkoba", "korupsi", "kekerasan",
        "penembakan", "ditangkap", "tersangka",
    }
    return any(word in category for word in negative_words)

def same_polres(news, case):
    np = news.get("polres")
    cp = case.get("polres")
    return bool(np and cp and np == cp)

def same_region(news, case):
    nr = str(news.get("region") or "").strip().lower()
    cr = str(case.get("region") or "").strip().lower()
    return bool(nr and cr and nr == cr)

def within_time_window(news, case):
    nd = parse_dt(news.get("published_at"))
    first = parse_dt(case.get("first_seen"))
    last = parse_dt(case.get("last_seen"))

    if not nd or not first or not last:
        return True

    # Allow an incident's lifecycle to grow. For a new article we compare
    # against the nearest endpoint rather than only last_seen.
    nearest = min(
        abs((nd - first).total_seconds()),
        abs((nd - last).total_seconds()),
    ) / 86400.0

    return nearest <= MAX_CASE_AGE_DAYS

def case_key_set(case):
    keys = set(case.get("incident_terms") or [])
    if keys:
        return keys

    terms = set()
    for article in case.get("articles", []):
        terms |= key_words(article.get("title", ""))
    terms |= key_words(case.get("title", ""))
    return terms

def case_event_set(case):
    events = set(case.get("event_terms") or [])
    if events:
        return events

    events = set()
    for article in case.get("articles", []):
        events |= event_words(article.get("title", ""))
    events |= event_words(case.get("title", ""))
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

    key_score, shared_keys = overlap(nk, ck)
    event_score, shared_events = overlap(ne, ce)

    title_score = similarity(
        news.get("title", ""),
        case.get("title", ""),
    )

    # Compare against all known article titles. This is important for
    # developing stories where the latest headline can differ substantially
    # from the original headline.
    article_title_score = 0.0
    for article in case.get("articles", []):
        article_title_score = max(
            article_title_score,
            similarity(
                news.get("title", ""),
                article.get("title", ""),
            ),
        )

    # Incident identity:
    # - specific/event words are strongest
    # - shared key words are next
    # - title similarity is supporting evidence
    score = (
        event_score * 0.40
        + key_score * 0.25
        + max(title_score, article_title_score) * 0.20
    )

    if same_polres(news, case):
        score += 0.10

    if same_region(news, case):
        score += 0.02

    # Same concrete location/event terms can compensate for category changes.
    if len(shared_events) >= 2:
        score += 0.10

    # A pair with 3+ strong event terms is very likely the same incident.
    very_strong = len(shared_events) >= 3

    return min(score, 1.0), {
        "shared_keys": shared_keys,
        "shared_events": shared_events,
        "title_score": max(title_score, article_title_score),
        "very_strong": very_strong,
    }

def find_matching_case(news, cases):
    candidates = []

    sorted_cases = sorted(
        cases,
        key=lambda c: c.get("last_seen", ""),
        reverse=True,
    )

    for case in sorted_cases[:MAX_CASES_TO_COMPARE]:
        news_polres = news.get("polres")
        case_polres = case.get("polres")

        # Explicitly different Polres is still a hard boundary.
        if news_polres and case_polres and news_polres != case_polres:
            continue

        if not within_time_window(news, case):
            continue

        score, evidence = match_score(news, case)

        # Strong incident identity:
        # two or more distinctive event terms, especially when location
        # or timeline supports it, can match despite category changes.
        strong = (
            len(evidence["shared_events"]) >= 2
            and (
                evidence["title_score"] >= 0.42
                or same_polres(news, case)
                or same_region(news, case)
            )
        )

        # Three+ distinctive terms is strong enough by itself if the
        # locations are not explicitly contradictory.
        very_strong = evidence["very_strong"]

        if score >= MERGE_SCORE or strong or very_strong:
            candidates.append(
                (
                    score,
                    len(evidence["shared_events"]),
                    len(evidence["shared_keys"]),
                    case,
                    evidence,
                )
            )

    if not candidates:
        return None, 0.0, {}

    candidates.sort(
        key=lambda x: (x[0], x[1], x[2]),
        reverse=True,
    )

    best_score, _, _, best_case, evidence = candidates[0]
    return best_case, round(best_score, 4), evidence

def attach_news(case, news, score):
    news_id = news.get("id")
    if not news_id:
        return

    case.setdefault("article_ids", [])
    case.setdefault("articles", [])

    if news_id not in case["article_ids"]:
        case["article_ids"].append(news_id)

    existing_ids = {
        a.get("id")
        for a in case["articles"]
        if isinstance(a, dict)
    }

    if news_id not in existing_ids:
        case["articles"].append({
            "id": news_id,
            "title": news.get("title", ""),
            "url": news.get("url", ""),
            "published_at": news.get("published_at"),
            "source": news.get("source"),
            "match_score": round(score, 4),
        })

    case["article_count"] = len(case["article_ids"])

    published = news.get("published_at") or ""
    old_last = case.get("last_seen") or ""

    if published:
        if not old_last or published > old_last:
            case["last_seen"] = published
        if not case.get("first_seen") or published < case["first_seen"]:
            case["first_seen"] = published

    # Expand incident identity with every article added.
    case.setdefault("incident_terms", [])
    case.setdefault("event_terms", [])

    case["incident_terms"] = sorted(
        set(case["incident_terms"]) | key_words(news.get("title", ""))
    )

    case["event_terms"] = sorted(
        set(case["event_terms"]) | event_words(news.get("title", ""))
    )

    # Keep a useful title: prefer the earliest/highest-information title,
    # but do not overwrite it with every update.
    if not case.get("title"):
        case["title"] = make_case_title(news)

    # Preserve/upgrade metadata.
    if not case.get("polres") and news.get("polres"):
        case["polres"] = news.get("polres")
    if not case.get("region") and news.get("region"):
        case["region"] = news.get("region")
    if news.get("is_jatim"):
        case["is_jatim"] = True

    old_priority = case.get("priority", "low")
    new_priority = news.get("priority", "low")
    if PRIORITY_ORDER.get(new_priority, 1) > PRIORITY_ORDER.get(old_priority, 1):
        case["priority"] = new_priority

    case["updated_at"] = now_iso()

def create_case(news, cases):
    published_at = news.get("published_at") or now_iso()

    case = {
        "case_id": next_case_id(cases),
        "title": make_case_title(news),
        "category": news.get("category"),
        "scope": news.get("scope"),
        "region": news.get("region"),
        "is_jatim": news.get("is_jatim"),
        "polres": news.get("polres"),
        "priority": news.get("priority", "low"),
        "signature": case_signature(news),
        "incident_terms": sorted(key_words(news.get("title", ""))),
        "event_terms": sorted(event_words(news.get("title", ""))),
        "first_seen": published_at,
        "last_seen": published_at,
        "article_ids": [],
        "articles": [],
        "article_count": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "engine_version": ENGINE_VERSION,
    }

    attach_news(case, news, 1.0)
    cases.append(case)
    return case

def mark_processed(news, case_id):
    news["processing_status"] = "processed"
    news["case_id"] = case_id
    news["case_processed_at"] = now_iso()
    news["case_engine_version"] = ENGINE_VERSION

def mark_non_candidate(news):
    news["processing_status"] = "processed"
    news["case_id"] = None
    news["case_processed_at"] = now_iso()
    news["case_engine_version"] = ENGINE_VERSION

def reset_case_state(news):
    """Clear only case-engine fields; collector data remains untouched."""
    for item in news:
        item.pop("processing_status", None)
        item.pop("case_id", None)
        item.pop("case_processed_at", None)
        item.pop("case_engine_version", None)

def needs_rebuild(database):
    # Rebuild automatically when upgrading from V3/older.
    return database.get("engine_version") != ENGINE_VERSION


def sync_case_canonical_metadata(news, cases):
    """
    STEP 1 ONLY:
    Make case_clusters.json the canonical bridge between cases and news.

    - Rebuild case -> article links from existing case articles.
    - Recalculate case priority from every linked news item.
    - Keep the highest priority found in the incident.
    - Synchronize news.case_id back to the canonical case.
    - Do not alter collector fields or clustering decisions.
    """
    news_by_id = {
        item.get("id"): item
        for item in news
        if item.get("id")
    }

    assigned = {}

    for case in cases:
        case.setdefault("article_ids", [])
        case.setdefault("articles", [])

        unique_ids = []
        unique_articles = []
        seen_ids = set()

        for article in case.get("articles", []):
            if not isinstance(article, dict):
                continue

            article_id = article.get("id")
            if not article_id or article_id in seen_ids:
                continue

            seen_ids.add(article_id)
            unique_ids.append(article_id)

            source_news = news_by_id.get(article_id)

            if source_news:
                # Refresh the compact reference from news.json so
                # the case never becomes stale relative to the news DB.
                refreshed = {
                    "id": source_news.get("id"),
                    "title": source_news.get("title", ""),
                    "url": source_news.get("url", ""),
                    "published_at": source_news.get("published_at"),
                    "source": source_news.get("source"),
                    "priority": source_news.get("priority", "low"),
                    "scope": source_news.get("scope"),
                    "region": source_news.get("region"),
                    "polres": source_news.get("polres"),
                    "match_score": article.get("match_score", 0.0),
                }

                unique_articles.append(refreshed)

                # Canonical reverse link: news -> case.
                source_news["processing_status"] = "processed"
                source_news["case_id"] = case.get("case_id")
                source_news["case_engine_version"] = ENGINE_VERSION

                assigned[article_id] = case.get("case_id")
            else:
                # Keep the reference only when the source article is still
                # present in the case database. It will be dropped from
                # article_ids if no compact article record exists.
                unique_articles.append(article)

        case["articles"] = unique_articles
        case["article_ids"] = [
            article.get("id")
            for article in unique_articles
            if article.get("id")
        ]
        case["article_count"] = len(case["article_ids"])

        # ------------------------------------------------------------
        # Canonical priority:
        # highest priority among every linked news article wins.
        # ------------------------------------------------------------
        priorities = []

        for article in unique_articles:
            priority = str(
                article.get("priority") or "low"
            ).lower()

            if priority in PRIORITY_ORDER:
                priorities.append(priority)

        # Also inspect authoritative news.json in case an older case
        # article reference did not previously store priority.
        for article_id in case["article_ids"]:
            source_news = news_by_id.get(article_id)
            if source_news:
                priority = str(
                    source_news.get("priority") or "low"
                ).lower()

                if priority in PRIORITY_ORDER:
                    priorities.append(priority)

        if priorities:
            case["priority"] = max(
                priorities,
                key=lambda value: PRIORITY_ORDER.get(value, 1)
            )
        else:
            case["priority"] = str(
                case.get("priority") or "low"
            ).lower()

        # ------------------------------------------------------------
        # Canonical metadata from linked news.
        # Keep the strongest/most specific values without changing
        # clustering.
        # ------------------------------------------------------------
        linked_news = [
            news_by_id[article_id]
            for article_id in case["article_ids"]
            if article_id in news_by_id
        ]

        if linked_news:
            polres_values = [
                item.get("polres")
                for item in linked_news
                if item.get("polres")
            ]

            if polres_values:
                # Existing case polres wins unless empty.
                case["polres"] = (
                    case.get("polres")
                    or polres_values[0]
                )

            region_values = [
                item.get("region")
                for item in linked_news
                if item.get("region")
            ]

            if region_values and not case.get("region"):
                case["region"] = region_values[0]

            if any(
                item.get("is_jatim") is True
                for item in linked_news
            ):
                case["is_jatim"] = True

        case["updated_at"] = now_iso()

    return assigned


def save_outputs(news, cases, already_processed, pending_count, matched, created, mode, rebuilt):
    # STEP 1: synchronize the canonical Case <-> News relationship
    # immediately before writing both databases.
    sync_case_canonical_metadata(news, cases)

    # Deduplicate article IDs defensively.
    for case in cases:
        seen = set()
        unique_articles = []
        for article in case.get("articles", []):
            aid = article.get("id")
            if not aid or aid in seen:
                continue
            seen.add(aid)
            unique_articles.append(article)

        case["articles"] = unique_articles
        case["article_ids"] = [a["id"] for a in unique_articles]
        case["article_count"] = len(unique_articles)

    total_articles = sum(
        c.get("article_count", 0)
        for c in cases
        if isinstance(c, dict)
    )

    database = {
        "engine_version": ENGINE_VERSION,
        "generated_at": now_iso(),
        "total_cases": len(cases),
        "total_articles": total_articles,
        "last_run": {
            "mode": mode,
            "rebuild": rebuilt,
            "news_loaded": len(news),
            "already_processed": already_processed,
            "pending": pending_count,
            "matched_existing": matched,
            "new_cases": created,
        },
        "cases": cases,
    }

    save_json(CASE_FILE, database)

    news_database = load_json(NEWS_FILE, {})
    if isinstance(news_database, dict):
        news_database["items"] = news
        news_database["case_engine_version"] = ENGINE_VERSION
        news_database["case_engine_processed_at"] = now_iso()
        save_json(NEWS_FILE, news_database)

    return total_articles

def main():
    print("========================================")
    print("PNM CASE ENGINE V4")
    print("INCIDENT-BASED CLUSTERING")
    print("========================================")

    news = load_news()
    database = load_cases()

    existing_version = database.get("engine_version")
    existing_cases = database.get("cases", [])

    if not isinstance(existing_cases, list):
        existing_cases = []

    print(f"Total news loaded : {len(news)}")
    print(f"Existing cases    : {len(existing_cases)}")
    print(f"Existing engine   : {existing_version or 'none'}")

    # --------------------------------------------------------
    # ONE-TIME REBUILD WHEN UPGRADING TO V4
    # --------------------------------------------------------
    rebuilt = needs_rebuild(database)

    if rebuilt:
        print("========================================")
        print("V4 REBUILD MODE")
        print("Engine version berubah.")
        print("Semua case akan dibangun ulang dari")
        print("news yang tersedia agar clustering lama")
        print("yang terpecah dapat digabung.")
        print("========================================")

        reset_case_state(news)

        cases = []
        pending = []

        for item in news:
            if is_case_candidate(item):
                pending.append(item)
            else:
                mark_non_candidate(item)

        already_processed = 0
        mode = "REBUILD"

    else:
        cases = existing_cases
        pending = []

        already_processed = 0

        for item in news:
            status = item.get("processing_status")
            case_id = item.get("case_id")

            if status == "processed" and case_id:
                if any(
                    c.get("case_id") == case_id
                    for c in cases
                ):
                    already_processed += 1
                    continue

                # Stale case ID: requeue.
                item.pop("processing_status", None)
                item.pop("case_id", None)
                item.pop("case_processed_at", None)
                item.pop("case_engine_version", None)

            if status == "processed" and not case_id:
                already_processed += 1
                continue

            if not is_case_candidate(item):
                mark_non_candidate(item)
                already_processed += 1
                continue

            pending.append(item)

        mode = "INCREMENTAL"

    print(f"Mode              : {mode}")
    print(f"Already processed : {already_processed}")
    print(f"News to process   : {len(pending)}")
    print("========================================")

    matched = 0
    created = 0

    # Oldest first makes the initial case title stable and gives later
    # updates a chance to match the incident.
    pending.sort(
        key=lambda x: (
            parse_dt(x.get("published_at"))
            or datetime.max.replace(tzinfo=timezone.utc)
        )
    )

    for index, item in enumerate(pending, start=1):
        title = item.get("title", "")

        existing_case, score, evidence = find_matching_case(
            item,
            cases,
        )

        if existing_case:
            attach_news(existing_case, item, score)
            mark_processed(
                item,
                existing_case["case_id"],
            )

            matched += 1

            shared = ",".join(
                sorted(evidence.get("shared_events", set()))
            )

            action = (
                f"MATCH {existing_case['case_id']} "
                f"({score:.2f})"
            )

            if shared:
                action += f" [{shared[:70]}]"

        else:
            new_case = create_case(
                item,
                cases,
            )

            mark_processed(
                item,
                new_case["case_id"],
            )

            created += 1
            action = f"NEW {new_case['case_id']}"

        if (
            index <= 20
            or index % 25 == 0
            or index == len(pending)
        ):
            print(
                f"Processed {index}/{len(pending)} "
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
    )

    print("========================================")
    print("CASE ENGINE COMPLETE")
    print(f"Mode             : {mode}")
    print(f"Rebuild          : {'YES' if rebuilt else 'NO'}")
    print(f"Total news       : {len(news)}")
    print(f"Already processed: {already_processed}")
    print(f"Processed now    : {len(pending)}")
    print(f"Matched existing : {matched}")
    print(f"New cases        : {created}")
    print(f"Total cases      : {len(cases)}")
    print(f"Total articles   : {total_articles}")
    print(f"Output           : {CASE_FILE}")
    print("========================================")

if __name__ == "__main__":
    main()
