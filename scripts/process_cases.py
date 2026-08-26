import json
import os
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher

NEWS_FILE = "data/news.json"
CASE_FILE = "data/case_clusters.json"

ENGINE_VERSION = "case-v3"

# ------------------------------------------------------------
# MODE / MATCHING
# ------------------------------------------------------------

TITLE_MATCH_THRESHOLD = 0.68
STRONG_MATCH_THRESHOLD = 0.60
MAX_CASES_TO_COMPARE = 500
MAX_CASE_AGE_DAYS = 60

# Saat database case kosong tetapi news sudah pernah diproses,
# otomatis rebuild sekali dari news yang tersedia.
RECOVERY_IF_CASE_DB_EMPTY = True

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada",
    "dalam", "oleh", "ini", "itu", "seorang", "orang", "jadi", "akan",
    "telah", "adalah", "terkait", "soal", "kasus", "berita", "polisi",
    "polri", "anggota", "oknum", "diduga", "ungkap", "mengungkap",
    "tangkap", "menangkap", "ditangkap", "amankan", "diamankan",
    "tersangka", "pelaku", "korban", "kronologi", "terjadi", "dalam",
    "atas", "karena", "hingga", "saat", "dengan", "sebuah", "sejumlah",
    "kembali", "usai", "setelah", "sebelumnya", "terhadap", "soal",
}

GENERIC_CASE_WORDS = {
    "polisi", "polri", "anggota", "oknum", "kasus", "berita", "ungkap",
    "mengungkap", "tangkap", "menangkap", "ditangkap", "amankan",
    "diamankan", "tersangka", "pelaku", "korban", "diduga", "terlibat",
    "terkait", "kejadian", "peristiwa", "kronologi", "penanganan",
    "kekerasan", "penganiayaan", "narkoba", "korupsi", "pungli", "suap",
    "etik", "disiplin", "pemerasan", "penyalahgunaan", "wewenang",
}

PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}


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


def similarity(a, b):
    a_words = words(a)
    b_words = words(b)
    if not a_words or not b_words:
        return 0.0
    inter = a_words & b_words
    union = a_words | b_words
    jaccard = len(inter) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, normalize(a), normalize(b)).ratio()
    return (jaccard * 0.65) + (sequence * 0.35)


def key_overlap(a, b):
    aw = key_words(a)
    bw = key_words(b)
    if not aw or not bw:
        return 0.0, set()
    shared = aw & bw
    return len(shared) / min(len(aw), len(bw)), shared


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
        value = str(case.get("case_id", ""))
        match = re.search(r"(\d+)$", value)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"CASE-{highest + 1:06d}"


def make_case_title(news):
    return (news.get("title") or "Kasus tidak teridentifikasi")[:180]


def case_signature(news):
    parts = [
        news.get("polres"),
        news.get("region"),
        news.get("category"),
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


def within_time_window(news, case):
    nd = parse_dt(news.get("published_at"))
    cd = parse_dt(case.get("last_seen"))
    if not nd or not cd:
        return True
    days = abs((nd - cd).total_seconds()) / 86400
    return days <= MAX_CASE_AGE_DAYS


def find_matching_case(news, cases):
    title = news.get("title", "")
    signature = case_signature(news)
    news_keys = key_words(title)
    news_polres = news.get("polres")
    candidates = []

    sorted_cases = sorted(
        cases,
        key=lambda c: c.get("last_seen", ""),
        reverse=True,
    )

    for case in sorted_cases[:MAX_CASES_TO_COMPARE]:
        case_polres = case.get("polres")

        # Different explicitly known Polres = different operational context.
        if news_polres and case_polres and news_polres != case_polres:
            continue

        if not within_time_window(news, case):
            continue

        case_title = case.get("title", "")
        title_score = similarity(title, case_title)
        key_score, shared = key_overlap(title, case_title)
        signature_score = similarity(signature, case.get("signature", ""))

        # Shared specific words are more useful than generic category words.
        score = (title_score * 0.60) + (key_score * 0.30) + (signature_score * 0.10)

        if same_polres(news, case):
            score += 0.05

        # Strong match: at least 2 specific shared terms and decent title similarity.
        strong = len(shared) >= 2 and title_score >= STRONG_MATCH_THRESHOLD

        candidates.append((score, title_score, key_score, strong, case, shared))

    if not candidates:
        return None, 0.0

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, title_score, key_score, strong, best_case, shared = candidates[0]

    if best_score >= TITLE_MATCH_THRESHOLD or strong:
        return best_case, round(best_score, 4)

    return None, round(best_score, 4)


def attach_news(case, news, score):
    news_id = news.get("id")
    if not news_id:
        return

    case.setdefault("article_ids", [])
    case.setdefault("articles", [])

    if news_id not in case["article_ids"]:
        case["article_ids"].append(news_id)

    existing_ids = {a.get("id") for a in case["articles"] if isinstance(a, dict)}
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
    case["last_seen"] = max(old_last, published)

    if not case.get("first_seen") or (published and published < case["first_seen"]):
        case["first_seen"] = published


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


def needs_recovery(news, cases):
    if not RECOVERY_IF_CASE_DB_EMPTY or cases:
        return False

    # Case DB kosong + ada berita yang pernah diberi case_id = data case pernah hilang.
    stale_case_ids = sum(1 for n in news if n.get("case_id"))
    return stale_case_ids > 0


def reset_for_recovery(news):
    """Reset only case-engine state; never touch collector fields."""
    reset = 0
    for item in news:
        if is_case_candidate(item):
            item.pop("processing_status", None)
            item.pop("case_id", None)
            item.pop("case_processed_at", None)
            item.pop("case_engine_version", None)
            reset += 1
        else:
            mark_non_candidate(item)
    return reset


def save_outputs(news, cases, already_processed, pending_count, matched, created, mode):
    total_articles = sum(c.get("article_count", 0) for c in cases)
    database = {
        "engine_version": ENGINE_VERSION,
        "generated_at": now_iso(),
        "total_cases": len(cases),
        "total_articles": total_articles,
        "last_run": {
            "mode": mode,
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
    print("PNM CASE ENGINE V3")
    print("RECOVERY + INCREMENTAL")
    print("========================================")

    news = load_news()
    database = load_cases()
    cases = database.get("cases", [])
    if not isinstance(cases, list):
        cases = []

    print(f"Total news loaded : {len(news)}")
    print(f"Existing cases    : {len(cases)}")

    recovery = needs_recovery(news, cases)
    if recovery:
        reset_count = reset_for_recovery(news)
        print("========================================")
        print("RECOVERY MODE AKTIF")
        print("Case database kosong tetapi news memiliki")
        print("case_id lama. State case akan dibangun ulang.")
        print(f"Candidate reset   : {reset_count}")
        print("========================================")
        already_processed = 0
    else:
        already_processed = 0

    pending = []
    for item in news:
        status = item.get("processing_status")
        case_id = item.get("case_id")

        if status == "processed" and case_id:
            # Hanya valid jika case_id memang ada di database.
            if any(c.get("case_id") == case_id for c in cases):
                already_processed += 1
                continue
            # Stale case_id: masukkan kembali ke queue.
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

    mode = "RECOVERY" if recovery else "INCREMENTAL"

    print(f"Mode              : {mode}")
    print(f"Already processed : {already_processed}")
    print(f"News to process   : {len(pending)}")
    print("========================================")

    matched = 0
    created = 0

    for index, item in enumerate(pending, start=1):
        title = item.get("title", "")
        existing_case, score = find_matching_case(item, cases)

        if existing_case:
            attach_news(existing_case, item, score)
            existing_case["updated_at"] = now_iso()

            old_priority = existing_case.get("priority", "low")
            new_priority = item.get("priority", "low")
            if PRIORITY_ORDER.get(new_priority, 1) > PRIORITY_ORDER.get(old_priority, 1):
                existing_case["priority"] = new_priority

            mark_processed(item, existing_case["case_id"])
            matched += 1
            action = f"MATCH {existing_case['case_id']} ({score:.2f})"
        else:
            new_case = create_case(item, cases)
            mark_processed(item, new_case["case_id"])
            created += 1
            action = f"NEW {new_case['case_id']}"

        # Jangan terlalu banyak log di GitHub Actions.
        if index <= 20 or index % 25 == 0 or index == len(pending):
            print(f"Processed {index}/{len(pending)} | Cases: {len(cases)} | {action} | {title[:80]}")

    total_articles = save_outputs(
        news,
        cases,
        already_processed,
        len(pending),
        matched,
        created,
        mode,
    )

    print("========================================")
    print("CASE ENGINE COMPLETE")
    print(f"Mode             : {mode}")
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
