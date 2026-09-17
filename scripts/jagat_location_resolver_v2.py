"""JAGAT V2 location/entity resolver.

Resolves location from title + Google News snippet/description + publisher,
while reusing the repository's canonical Polres/Polsek master data.
This module is intentionally deterministic and dependency-free.
"""
import re

import location_engine as base


def norm(text):
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def contains_word(text, term):
    text, term = norm(text), norm(term)
    return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None


def combined_text(title="", description="", source=""):
    # Google News may put the useful locality/institution only in the snippet.
    parts = [title, description, source]
    return norm(" ".join(str(x or "") for x in parts))


def strip_publisher_suffix(title="", source=""):
    title = str(title or "").strip()
    source = str(source or "").strip()
    if source:
        title = re.sub(r"\s+(?:-|–|—|\|)\s*" + re.escape(source) + r"\s*$", "", title, flags=re.I)
    return title.strip()


def detect_polsek(text):
    t = norm(text)
    for alias, parent in sorted(base.POLSEK_BINDINGS.items(), key=lambda x: len(x[0]), reverse=True):
        if contains_word(t, alias):
            return alias, parent, "master_polsek_binding"

    # Do not greedily consume the following verb/title words.
    m = re.search(r"\bpolsek\s+([a-z0-9-]+)\b", t, re.I)
    if m:
        return "POLSEK " + m.group(1).upper(), None, "text_polsek_unbound"
    return None, None, None


def detect_polres(text):
    t = norm(text)
    if contains_word(t, "batu bara") or contains_word(t, "polres batu bara"):
        return None, None
    found = []
    for canonical, aliases in base.POLRES_MAP.items():
        for alias in aliases:
            if contains_word(t, alias):
                found.append((len(alias), canonical, alias))
    if not found:
        return None, None
    found.sort(key=lambda x: (-x[0], x[1]))
    return found[0][1], found[0][2]


def detect_locality(text):
    t = norm(text)
    if contains_word(t, "batu bara"):
        return ""
    found = [x for x in base.JATIM_LOCATIONS if contains_word(t, x)]
    found.sort(key=len, reverse=True)
    return found[0].title() if found else ""


def detect_polda_unit(text):
    t = norm(text)
    return any(contains_word(t, term) for term in base.JATIM_PUSAT_TERMS)


def detect_location(title, description="", source=""):
    clean_title = strip_publisher_suffix(title, source)
    text = combined_text(clean_title, description, source)

    outside = [x for x in base.NON_JATIM_TERMS if contains_word(text, x)]
    if outside:
        # A direct Jatim institutional hit in the same text outranks a generic
        # outside-Jatim place mention because news snippets often mention both.
        if not detect_polres(text) and not detect_polsek(text)[1] and not detect_polda_unit(text):
            return {
                "is_jatim": False,
                "region": "LUAR JATIM",
                "locality": "",
                "area_label": "LUAR JATIM",
                "polres": None,
                "polsek": None,
                "confidence": 100,
                "evidence": outside[:6],
                "source": "title_description",
                "location_status": "LUAR_JATIM",
            }

    if detect_polda_unit(text):
        evidence = [x for x in base.JATIM_PUSAT_TERMS if contains_word(text, x)][:6]
        return {
            "is_jatim": True,
            "region": "Jawa Timur",
            "locality": "Polda Jatim",
            "area_label": "Polda Jatim",
            "polres": None,
            "polsek": None,
            "confidence": 100,
            "evidence": evidence,
            "source": "master_jatim_unit",
            "location_status": "JAWA_TIMUR",
        }

    polres, polres_evidence = detect_polres(text)
    polsek, polsek_parent, polsek_source = detect_polsek(text)
    if not polres and polsek_parent:
        polres = polsek_parent
        polres_evidence = polsek

    locality = base.POLRES_TO_LOCALITY.get(str(polres or ""), "") if polres else detect_locality(text)
    explicit = any(contains_word(text, x) for x in ("jawa timur", "jatim"))

    if polres or polsek_parent or locality or explicit:
        evidence = [x for x in (polres_evidence, polsek, locality, "Jawa Timur/Jatim" if explicit else None) if x]
        confidence = 100 if polres else 97 if polsek_parent else 95 if locality else 90
        return {
            "is_jatim": True,
            "region": "Jawa Timur",
            "locality": locality,
            "area_label": locality or "Jawa Timur (Umum)",
            "polres": polres,
            "polsek": polsek,
            "confidence": confidence,
            "evidence": list(dict.fromkeys(evidence))[:6],
            "source": "master_entity" if polres or polsek_parent else "title_description",
            "location_status": "JAWA_TIMUR",
        }

    return {
        "is_jatim": None,
        "region": "BELUM TERPETAKAN",
        "locality": "",
        "area_label": "BELUM TERPETAKAN",
        "polres": None,
        "polsek": polsek,
        "confidence": 0,
        "evidence": [polsek] if polsek else [],
        "source": "title_description",
        "location_status": "BELUM_TERPETAKAN",
    }
