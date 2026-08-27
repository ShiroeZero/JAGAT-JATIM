import json
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from difflib import SequenceMatcher

from analysis_engine import case_attention

NEWS_FILE = "data/news.json"
CASE_FILE = "data/case_clusters.json"

ENGINE_VERSION = "case-v6.5.3"
MAX_CASE_AGE_DAYS = 120

# Normal clustering may use one concrete event term when the
# location or Polres is the same. This is deliberately stricter
# than generic topic similarity, but permissive enough to connect
# legitimate article updates of the same incident.
MERGE_SCORE = 0.62

# Neutral/non-candidate recovery remains stricter.
RECOVERY_SCORE = 0.76

PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}

STOPWORDS = {
    "yang","dan","di","ke","dari","untuk","dengan","pada","dalam","oleh",
    "ini","itu","seorang","orang","jadi","akan","telah","adalah","terkait",
    "soal","kasus","berita","polisi","polri","anggota","oknum","diduga",
    "ungkap","mengungkap","tangkap","menangkap","ditangkap","amankan",
    "diamankan","tersangka","pelaku","korban","kronologi","terjadi","atas",
    "karena","hingga","saat","sebuah","sejumlah","kembali","usai","setelah",
    "sebelumnya","terhadap","menjadi","para","sebagai","yakni","langsung",
    "hal","pengungkapan","penanganan","ditemukan","diketahui","membuat",
    "kata","ujar","menurut","hari","tahun","bulan","warga","satu","dua",
    "tiga","empat","lima","enam","tujuh","delapan","sembilan","sepuluh",
}

GENERIC_WORDS = {
    "polisi","polri","anggota","oknum","kasus","berita","ungkap","tangkap",
    "tersangka","pelaku","korban","diduga","terkait","kejadian","peristiwa",
    "kronologi","penanganan","tindakan","penindakan","diperiksa","pemeriksaan",
    "ditahan","menahan","mengaku","menyebut","berhasil","orang","warga",
}

EVENT_WORDS = {
    "intimidasi","wartawan","jurnalis","pwi","tuntutan","permintaan","maaf",
    "propam","ancam","ancaman","bunuh","tambang","ilegal","seksual","bebas",
    "divonis","vonis","fasilitas","sula","sanana","jeju","hilang","misteri",
    "curanmor","pencurian","pencuri","motor","emas","celurit","letter",
    "penganiayaan","kekerasan","penembakan","narkoba","sabu","ganja","korupsi",
    "pungli","suap","pemerasan","penyalahgunaan","aborsi","perselingkuhan",
    "tangkap","tangkap lepas","tebusan","setoran","upeti","beking","dibeking",
    "dibeckup","intervensi","maladministrasi","calo","satpas","samsat","judi",
    "judol","sabung ayam","rokok ilegal","solar subsidi","miras","bentrok",
    "demo ricuh","kerusuhan","mako","pos polisi","molotov","pencabulan",
    "pemerkosaan","kdrt","nikah siri","asusila",
}

LOCATION_WORDS = {
    "surabaya","sidoarjo","gresik","lamongan","tuban","bojonegoro","ngawi",
    "magetan","madiun","ponorogo","pacitan","nganjuk","kediri","tulungagung",
    "blitar","trenggalek","malang","batu","pasuruan","probolinggo","lumajang",
    "jember","bondowoso","situbondo","banyuwangi","mojokerto","jombang",
    "pamekasan","bangkalan","sampang","sumenep","madura","tangerang","kendari",
    "medan","jeju","batam","palembang","lampung","bali","jakarta","semarang",
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def parse_dt(value):
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        value_dt = datetime.fromisoformat(text)
        if value_dt.tzinfo is None:
            value_dt = value_dt.replace(tzinfo=timezone.utc)
        return value_dt.astimezone(timezone.utc)
    except Exception:
        return None

def normalize(text):
    text = (text or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def tokens(text):
    return {
        token for token in normalize(text).split()
        if len(token) >= 3 and token not in STOPWORDS
    }

def rare_tokens(text):
    return tokens(text) - GENERIC_WORDS

def incident_tokens(text):
    return rare_tokens(text) & EVENT_WORDS

def location_tokens(text):
    return tokens(text) & LOCATION_WORDS

def similarity(a, b):
    a = normalize(a)
    b = normalize(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_news():
    data = load_json(NEWS_FILE, {"items": []})
    return data if isinstance(data, dict) else {"items": data if isinstance(data, list) else []}

def load_cases():
    data = load_json(CASE_FILE, None)
    if not isinstance(data, dict):
        return {"engine_version": ENGINE_VERSION, "cases": []}
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

def is_case_candidate(item):
    scope = str(item.get("scope") or "").lower()
    return scope in {"negative", "case"}

def get_date_candidates(item):
    for key in ("collected_at", "published_at"):
        value = parse_dt(item.get(key))
        if value:
            yield value

def latest_item_time(item):
    return max(get_date_candidates(item), default=None)

def case_active_today(case, today_local):
    for article in case.get("articles", []):
        for key in ("collected_at", "published_at"):
            value = parse_dt(article.get(key))
            if value and value.astimezone().date() == today_local:
                return True
    last_detected = parse_dt(case.get("last_detected_at"))
    if last_detected and last_detected.astimezone().date() == today_local:
        return True
    return False

def item_fingerprint(item):
    title = item.get("title", "")
    return {
        "rare": rare_tokens(title),
        "events": incident_tokens(title),
        "locations": location_tokens(title),
        "locality": str(item.get("locality") or "").strip().lower(),
        "title": title,
        "polres": str(item.get("polres") or "").strip().upper(),
        "region": str(item.get("region") or "").strip().lower(),
        "families": set(item.get("discovery_families") or []),
    }

def case_fingerprint(case):
    return {
        "rare": set(case.get("incident_terms", [])),
        "events": set(case.get("event_terms", [])),
        "locations": set(case.get("location_terms", [])),
        "locality": str(case.get("locality") or "").strip().lower(),
        "polres": str(case.get("polres") or "").strip().upper(),
        "region": str(case.get("region") or "").strip().lower(),
        "families": set(case.get("discovery_families") or []),
        "title": str(case.get("title") or ""),
    }

def within_window(item, case):
    new_time = latest_item_time(item)
    first = parse_dt(case.get("first_seen"))
    last = parse_dt(case.get("last_seen"))
    if not new_time or not first or not last:
        return True
    nearest = min(abs((new_time-first).total_seconds()), abs((new_time-last).total_seconds())) / 86400.0
    return nearest <= MAX_CASE_AGE_DAYS

def score_match(item, case):
    n = item_fingerprint(item)
    c = case_fingerprint(case)

    # Hard identity boundary: two different explicit Polres cannot
    # belong to the same incident merely because their headlines are similar.
    if (
        n["polres"]
        and c["polres"]
        and n["polres"] != c["polres"]
    ):
        return 0.0, {
            "shared_events": set(),
            "shared_locations": set(),
            "shared_rare": set(),
            "title": 0.0,
        }

    if not within_window(item, case):
        return 0.0, {"shared_events": set(), "shared_locations": set(), "shared_rare": set(), "title": 0.0}

    shared_events = n["events"] & c["events"]
    shared_locations = n["locations"] & c["locations"]
    shared_rare = n["rare"] & c["rare"]
    shared_families = n["families"] & c["families"]
    title_score = similarity(n["title"], c["title"])

    # Location is an identity signal, not merely a topic.
    location_bonus = 0.30 if shared_locations else 0.0
    locality_bonus = 0.12 if n["locality"] and c["locality"] and n["locality"] == c["locality"] else 0.0
    polres_bonus = 0.20 if n["polres"] and c["polres"] and n["polres"] == c["polres"] else 0.0
    region_bonus = 0.03 if n["region"] and c["region"] and n["region"] == c["region"] else 0.0

    event_score = min(len(shared_events), 3) * 0.18
    family_score = min(len(shared_families), 2) * 0.08
    rare_score = min(len(shared_rare), 4) * 0.05
    title_score_part = title_score * 0.14

    score = min(
        1.0,
        event_score
        + family_score
        + rare_score
        + title_score_part
        + location_bonus
        + locality_bonus
        + polres_bonus
        + region_bonus,
    )

    return score, {
        "shared_events": shared_events,
        "shared_locations": shared_locations,
        "shared_rare": shared_rare,
        "shared_families": shared_families,
        "title": title_score,
    }

def choose_case(item, cases, recovery=False):
    best = None

    for case in cases:
        score, evidence = score_match(item, case)
        if score <= 0:
            continue

        n = item_fingerprint(item)
        c = case_fingerprint(case)

        normal_identity = (
            len(evidence["shared_events"]) >= 1
            and (
                bool(evidence["shared_locations"])
                or bool(evidence.get("shared_families")) and bool(n["polres"] and c["polres"] and n["polres"] == c["polres"])
                or bool(n["polres"] and c["polres"] and n["polres"] == c["polres"])
                or evidence["title"] >= 0.82
            )
        )

        recovery_identity = (
            len(evidence["shared_events"]) >= 2
            and (
                bool(evidence["shared_locations"])
                or bool(n["polres"] and c["polres"] and n["polres"] == c["polres"])
                or evidence["title"] >= 0.86
            )
        )

        if recovery:
            valid = score >= RECOVERY_SCORE and recovery_identity
        else:
            valid = score >= MERGE_SCORE and normal_identity

        if not valid:
            continue

        if best is None or score > best[1]:
            best = (case, score, evidence)

    return best

def canonical_source(article):
    source = str(article.get("source") or article.get("publisher") or "").strip().lower()
    source = re.sub(r"\s+", " ", source)
    return source

def title_text_for_priority(article):
    return normalize(article.get("title", ""))


def compute_case_priority(case):
    articles = list(case.get("articles", []))
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()
    active_today = 0
    for article in articles:
        detected = parse_dt(article.get("collected_at")) or parse_dt(article.get("published_at"))
        if detected and detected.astimezone(ZoneInfo("Asia/Jakarta")).date() == today:
            active_today += 1

    result = case_attention(articles, case=case, active_today=active_today)
    case["priority"] = result["priority"]
    case["priority_score"] = result["score"]
    case["attention_score"] = result["score"]
    case["attention_label"] = result["label"]
    case["priority_breakdown"] = result["breakdown"]
    case["priority_evidence"] = result["evidence"]
    return result["priority"], result["score"]

def make_case(item, cases):
    published = latest_item_time(item) or datetime.now(timezone.utc)
    fp = item_fingerprint(item)
    return {
        "case_id": next_case_id(cases),
        "title": (item.get("title") or "Kasus tidak teridentifikasi")[:180],
        "category": item.get("category"),
        "scope": item.get("scope"),
        "region": item.get("region"),
        "locality": item.get("locality") or "",
        "is_jatim": item.get("is_jatim"),
        "polres": item.get("polres"),
        "polsek": item.get("polsek"),
        "priority": str(item.get("priority") or "low").lower(),
        "attention_score": int(item.get("attention_score") or 0),
        "attention_label": item.get("attention_label") or "Rendah",
        "signature": " ".join(x for x in (str(item.get("polres") or ""), str(item.get("region") or "")) if x),
        "incident_terms": sorted(fp["rare"]),
        "event_terms": sorted(fp["events"]),
        "location_terms": sorted(fp["locations"]),
        "discovery_families": sorted(fp["families"]),
        "first_seen": published.isoformat(),
        "last_seen": published.isoformat(),
        "last_detected_at": (
            parse_dt(item.get("collected_at"))
            or published
        ).isoformat(),
        "article_ids": [],
        "articles": [],
        "article_count": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "engine_version": ENGINE_VERSION,
    }

def attach(case, item, score):
    item_id = item.get("id")
    if not item_id:
        return

    article = {
        "id": item_id,
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "published_at": item.get("published_at"),
        "collected_at": item.get("collected_at"),
        "source": item.get("source") or item.get("publisher"),
        "match_score": round(score, 4),
        "priority": item.get("priority", "low"),
        "scope": item.get("scope"),
        "category": item.get("category"),
        "region": item.get("region"),
        "locality": item.get("locality") or "",
        "is_jatim": item.get("is_jatim") is True,
        "polres": item.get("polres"),
        "polsek": item.get("polsek"),
        "issue_type": item.get("issue_type"),
        "issue_subtype": item.get("issue_subtype"),
        "handling_status": item.get("handling_status"),
        "handling_evidence": item.get("handling_evidence", []),
        "polri_relation": item.get("polri_relation"),
        "polri_relation_points": item.get("polri_relation_points", 0),
        "polri_relation_evidence": item.get("polri_relation_evidence", []),
        "attention_score": item.get("attention_score", 0),
        "attention_label": item.get("attention_label", "Rendah"),
        "attention_components": item.get("attention_components", {}),
    }

    existing = {a.get("id"): i for i, a in enumerate(case["articles"])}
    if item_id in existing:
        case["articles"][existing[item_id]] = article
    else:
        case["articles"].append(article)
        case["article_ids"].append(item_id)

    case["article_count"] = len(case["article_ids"])

    dt_values = [parse_dt(item.get("published_at")), parse_dt(item.get("collected_at"))]
    dt_values = [x for x in dt_values if x]
    if dt_values:
        first = min(dt_values)
        last = max(dt_values)
        if not case.get("first_seen") or first.isoformat() < case["first_seen"]:
            case["first_seen"] = first.isoformat()
        if not case.get("last_seen") or last.isoformat() > case["last_seen"]:
            case["last_seen"] = last.isoformat()
        detected = parse_dt(item.get("collected_at")) or last
        if not case.get("last_detected_at") or detected.isoformat() > case["last_detected_at"]:
            case["last_detected_at"] = detected.isoformat()

    fp = item_fingerprint(item)
    case["incident_terms"] = sorted(set(case.get("incident_terms", [])) | fp["rare"])
    case["event_terms"] = sorted(set(case.get("event_terms", [])) | fp["events"])
    case["location_terms"] = sorted(set(case.get("location_terms", [])) | fp["locations"])

    if item.get("polres") and not case.get("polres"):
        case["polres"] = item.get("polres")
    if item.get("locality") and not case.get("locality"):
        case["locality"] = item.get("locality")
    if item.get("is_jatim"):
        case["is_jatim"] = True
    if not case.get("region") and item.get("region"):
        case["region"] = item.get("region")

    current = PRIORITY_ORDER.get(str(case.get("priority") or "low").lower(), 1)
    incoming = str(item.get("priority") or "low").lower()
    if PRIORITY_ORDER.get(incoming, 1) > current:
        case["priority"] = incoming

    case["updated_at"] = now_iso()

def mark_case(item, case_id):
    item["processing_status"] = "processed"
    item["case_id"] = case_id
    item["case_engine_version"] = ENGINE_VERSION
    item["case_processed_at"] = now_iso()

def mark_no_case(item):
    item["processing_status"] = "processed"
    item["case_id"] = None
    item["case_engine_version"] = ENGINE_VERSION
    item["case_processed_at"] = now_iso()

def sync_news_case_ids(news, cases):
    mapping = {}
    for case in cases:
        for aid in case.get("article_ids", []):
            mapping[aid] = case.get("case_id")
    for item in news:
        aid = item.get("id")
        if aid in mapping:
            mark_case(item, mapping[aid])

def merge_duplicate_cases(cases):
    """Consolidate cases that were created separately for the same incident."""
    changed = True
    merge_count = 0

    while changed:
        changed = False

        for i in range(len(cases)):
            if changed:
                break

            a = cases[i]
            for j in range(i + 1, len(cases)):
                b = cases[j]

                aloc = set(a.get("location_terms", []))
                bloc = set(b.get("location_terms", []))
                aevents = set(a.get("event_terms", []))
                bevents = set(b.get("event_terms", []))

                shared_locations = aloc & bloc
                shared_events = aevents & bevents
                title_score = similarity(
                    a.get("title", ""),
                    b.get("title", ""),
                )

                explicit_polres_conflict = bool(a.get("polres") and b.get("polres") and a.get("polres") != b.get("polres"))
                explicit_locality_conflict = bool(a.get("locality") and b.get("locality") and a.get("locality") != b.get("locality"))
                same_polres = (
                    a.get("polres")
                    and b.get("polres")
                    and a.get("polres") == b.get("polres")
                )
                if explicit_polres_conflict or explicit_locality_conflict:
                    continue

                identity = (
                    same_polres
                    and len(shared_events) >= 2
                ) or (
                    len(shared_locations) >= 1
                    and (
                        len(shared_events) >= 2
                        or (
                            len(shared_events) >= 1
                            and title_score >= 0.55
                        )
                    )
                )

                if not identity:
                    continue

                # Prefer the case with more articles as the survivor.
                if b.get("article_count", 0) > a.get("article_count", 0):
                    survivor, other = b, a
                else:
                    survivor, other = a, b

                existing_ids = set(survivor.get("article_ids", []))

                for article in other.get("articles", []):
                    aid = article.get("id")
                    if aid and aid not in existing_ids:
                        survivor.setdefault("article_ids", []).append(aid)
                        survivor.setdefault("articles", []).append(article)
                        existing_ids.add(aid)

                survivor["article_count"] = len(
                    survivor.get("article_ids", [])
                )
                survivor["incident_terms"] = sorted(
                    set(survivor.get("incident_terms", []))
                    | set(other.get("incident_terms", []))
                )
                survivor["event_terms"] = sorted(
                    set(survivor.get("event_terms", []))
                    | set(other.get("event_terms", []))
                )
                survivor["location_terms"] = sorted(
                    set(survivor.get("location_terms", []))
                    | set(other.get("location_terms", []))
                )

                if not survivor.get("polres") and other.get("polres"):
                    survivor["polres"] = other.get("polres")
                if not survivor.get("locality") and other.get("locality"):
                    survivor["locality"] = other.get("locality")

                if other.get("is_jatim"):
                    survivor["is_jatim"] = True

                if not survivor.get("region") and other.get("region"):
                    survivor["region"] = other.get("region")

                if (
                    other.get("first_seen")
                    and (
                        not survivor.get("first_seen")
                        or other["first_seen"] < survivor["first_seen"]
                    )
                ):
                    survivor["first_seen"] = other["first_seen"]

                if (
                    other.get("last_seen")
                    and (
                        not survivor.get("last_seen")
                        or other["last_seen"] > survivor["last_seen"]
                    )
                ):
                    survivor["last_seen"] = other["last_seen"]

                if (
                    other.get("last_detected_at")
                    and (
                        not survivor.get("last_detected_at")
                        or other["last_detected_at"] > survivor["last_detected_at"]
                    )
                ):
                    survivor["last_detected_at"] = other["last_detected_at"]

                survivor["article_count"] = len(survivor.get("article_ids", []))
                compute_case_priority(survivor)
                survivor["updated_at"] = now_iso()

                cases.remove(other)
                merge_count += 1
                changed = True
                break

    return merge_count

def main():
    news_db = load_news()
    news = news_db.get("items", [])
    old_db = load_cases()
    old_version = old_db.get("engine_version")

    print("========================================")
    print("JAGAT CASE ENGINE V6.5.3")
    print("CANONICAL INCIDENT CLUSTERING")
    print("========================================")
    print(f"Total news loaded : {len(news)}")
    print(f"Existing cases    : {len(old_db.get('cases', []))}")
    print(f"Existing engine   : {old_version or 'none'}")

    # V6 intentionally performs one clean rebuild from the current
    # news database. After V6 is stored, future runs are incremental.
    rebuild = old_version != ENGINE_VERSION

    if rebuild:
        print("Mode              : REBUILD")
        for item in news:
            item.pop("processing_status", None)
            item.pop("case_id", None)
            item.pop("case_processed_at", None)
            item.pop("case_engine_version", None)
    else:
        print("Mode              : INCREMENTAL")

    cases = []
    candidates = [i for i in news if is_case_candidate(i)]
    recovery_candidates = [i for i in news if not is_case_candidate(i)]

    # Always rebuild the current case database exactly once when the
    # engine version changes, avoiding contaminated legacy matches.
    if rebuild:
        for item in candidates:
            best = choose_case(item, cases, recovery=False)
            if best:
                case, score, _ = best
                attach(case, item, score)
                mark_case(item, case["case_id"])
            else:
                case = make_case(item, cases)
                cases.append(case)
                attach(case, item, 1.0)
                mark_case(item, case["case_id"])

        recovery_checked = 0
        recovery_matched = 0

        for item in recovery_candidates:
            recovery_checked += 1
            best = choose_case(item, cases, recovery=True)
            if best:
                case, score, evidence = best
                attach(case, item, score)
                mark_case(item, case["case_id"])
                recovery_matched += 1
                print(
                    f"RECOVERY {case['case_id']} ({score:.2f}) "
                    f"| {item.get('title','')[:110]}"
                )
            else:
                mark_no_case(item)

        matched_existing = sum(
            1 for i in candidates
            if i.get("case_id")
        ) - len(cases)
        matched_existing = max(0, matched_existing)
        new_cases = len(cases)

    else:
        # Incremental: only unprocessed records are considered, but a
        # processed/no-case neutral article may recover to an existing case
        # under the same strict identity rules.
        cases = old_db.get("cases", [])
        by_case = {c.get("case_id"): c for c in cases}
        pending = []
        recovery_checked = 0
        recovery_matched = 0
        matched_existing = 0
        new_cases = 0

        for item in news:
            case_id = item.get("case_id")
            if item.get("processing_status") == "processed" and case_id in by_case:
                continue

            if is_case_candidate(item):
                pending.append(item)
            else:
                recovery_checked += 1
                best = choose_case(item, cases, recovery=True)
                if best:
                    case, score, _ = best
                    attach(case, item, score)
                    mark_case(item, case["case_id"])
                    recovery_matched += 1
                else:
                    mark_no_case(item)

        for item in pending:
            best = choose_case(item, cases, recovery=False)
            if best:
                case, score, _ = best
                attach(case, item, score)
                mark_case(item, case["case_id"])
                matched_existing += 1
            else:
                case = make_case(item, cases)
                cases.append(case)
                attach(case, item, 1.0)
                mark_case(item, case["case_id"])
                new_cases += 1

    merged_cases = merge_duplicate_cases(cases)

    # Recalculate every case's canonical incident priority from the complete
    # set of attached articles. Article-level priority is kept untouched.
    for case in cases:
        case["article_count"] = len(case.get("article_ids", []))
        compute_case_priority(case)
        case["updated_at"] = now_iso()

    sync_news_case_ids(news, cases)

    total_articles = sum(
        int(c.get("article_count", 0) or 0)
        for c in cases
    )

    output = {
        "engine_version": ENGINE_VERSION,
        "generated_at": now_iso(),
        "total_cases": len(cases),
        "total_articles": total_articles,
        "last_run": {
            "mode": "REBUILD" if rebuild else "INCREMENTAL",
            "rebuild": rebuild,
            "news_loaded": len(news),
            "recovery_checked": recovery_checked,
            "recovery_matched": recovery_matched,
            "matched_existing": matched_existing,
            "new_cases": new_cases,
        },
        "cases": cases,
    }

    save_json(CASE_FILE, output)

    news_db["items"] = news
    news_db["case_engine_version"] = ENGINE_VERSION
    news_db["case_engine_processed_at"] = now_iso()
    save_json(NEWS_FILE, news_db)

    print("========================================")
    print("CASE ENGINE COMPLETE")
    print(f"Mode              : {'REBUILD' if rebuild else 'INCREMENTAL'}")
    print(f"Rebuild           : {'YES' if rebuild else 'NO'}")
    print(f"Total news        : {len(news)}")
    print(f"Recovery checked  : {recovery_checked}")
    print(f"Recovery matched  : {recovery_matched}")
    print(f"Matched existing  : {matched_existing}")
    print(f"Merged duplicate  : {merged_cases}")
    print(f"New cases         : {new_cases}")
    print(f"Total cases       : {len(cases)}")
    print(f"Total articles    : {total_articles}")
    print(f"Output            : {CASE_FILE}")
    print("========================================")

if __name__ == "__main__":
    main()
