"""
ShopWise V3 Automatic Product-Specific Customer Review Fetcher & ABSA Sentiment Engine.

Strictly enforces:
1. Fetches actual written customer reviews separately per selected product ID & SerpAPI identifiers.
2. Uses immersive_product_page_token (google_immersive_product) when available, and google_product (reviews=1) as secondary.
3. Supports multi-page pagination (up to MAX_REVIEW_PAGES) when supported by the provider.
4. Verifies every retrieved product & review strictly belongs to the selected product and variant (zero cross-product or cross-variant mixing).
5. Extracts actual written review text, individual review rating, date, source, and reviewer name when available.
6. Keeps overall product rating (e.g. 4.3★) strictly separate from individual review ratings and ABSA sentiment percentages.
7. Uses TTL caching (available: 30m, unavailable: 2m auto-retry, error: never cached) and supports manual refresh.
8. Clearly distinguishes loading, success, unavailable ("No written customer reviews available for this product."), and error ("Unable to fetch reviews. Please try again.") — never fabricates reviews or sentiment percentages.
"""
from datetime import datetime, timezone
from typing import Any
import hashlib
import logging
import re
import time
import httpx
from ..config import SERPAPI_KEY, SERPAPI_API_BASE

log = logging.getLogger("shopwise.reviews")

# Isolated per-product TTL cache keyed by unique product + variant signature (never caches errors)
_REVIEW_CACHE: dict[str, dict[str, Any]] = {}

AVAILABLE_CACHE_TTL_SECONDS = 1800    # 30 minutes for valid retrieved reviews
UNAVAILABLE_CACHE_TTL_SECONDS = 120   # 2 minutes for unavailable reviews -> automatically retried after expiry
MAX_REVIEW_PAGES = 3                  # Fetch up to 3 pages of reviews when pagination is supported

# 8 Core Hardware & Quality Aspects for Sentiment Analysis
ASPECT_KEYWORDS = {
    "performance": ["performance", "speed", "fast", "slow", "processor", "cpu", "ram", "multitask", "compile", "gaming", "lag", "lagging", "smooth", "fluid", "boot", "chip", "responsive", "fps", "rendering"],
    "battery": ["battery", "backup", "charging", "charger", "mah", "lasts", "drain", "drains", "endurance", "hours", "watt", "charge", "stamina"],
    "camera": ["camera", "photo", "photos", "shot", "shots", "portrait", "sensor", "lens", "video", "4k", "megapixels", "zoom", "night", "selfie", "autofocus", "stabilization"],
    "display": ["display", "screen", "amoled", "oled", "120hz", "144hz", "brightness", "fhd", "nits", "bezel", "retina", "colors", "colour", "picture", "panel", "viewing angles"],
    "build": ["build", "quality", "material", "plastic", "metal", "aluminum", "titanium", "durability", "finish", "weight", "lightweight", "chassis", "body", "ergonomic", "fit", "craftsmanship", "fabric", "cotton", "silk", "silver", "gold"],
    "sound": ["sound", "audio", "speaker", "speakers", "bass", "clarity", "volume", "loud", "dolby", "anc", "mic", "noise cancellation", "vocals", "soundstage", "call quality"],
    "value": ["value", "price", "affordable", "expensive", "worth", "deal", "budget", "cost", "overpriced", "cheap", "unbeatable", "accessible"],
    "reliability": ["heating", "heats", "overheating", "hangs", "crash", "warranty", "dependable", "durable", "stable", "bug", "software", "bloatware", "tarnish", "bleed", "cooling", "sanitized", "clean", "accuracy", "tracking", "os", "ui", "problem", "problems", "issue", "issues"],
}

POSITIVE_WORDS = set(
    "great excellent good love loved smooth fast amazing best superb crisp comfortable impressive solid "
    "bright long clean lightweight durable premium awesome sharp vivid responsive silent clear loud "
    "reliable decent wonderful flawless incredible breathtaking stunning joy dependable phenomenal "
    "unmatched silky effortlessly effortless fantastic punchy vibrant unbeatable legendary cinematic "
    "magical razor flattering luxurious pure sparkles delicate sturdy breathable rich gracefully "
    "leading peerless generous sensational astonishing remarkable thoughtful sleek blazing handy "
    "quiet crispy foolproof evenly intricate butter buttery accurate seamless intuitive ample "
    "enjoyable lively resonant premier competent secure securely happy satisfied recommend recommended "
    "nice super perfect value well"
    .split()
)

NEGATIVE_WORDS = set(
    "poor bad slow heats heating overheating weak disappointing disappointed cheap issue issues laggy "
    "lagging uncomfortable drains drain flimsy average bloatware hangs expensive heavy terrible glitch "
    "worst defective blurry noisy lag stutter fragile chunky audible limited utilitarian quirk warm "
    "basic tarnish bleed bulky overpriced intrusive spam broken waste pathetic horrible problem problems "
    "stopped dead scratch scratched"
    .split()
)

NEGATIVE_PHRASES = [
    "not included", "fills quickly", "slightly warm", "slightly chunky", "slightly audible",
    "slightly utilitarian", "portability is limited", "still 60hz", "charger handy",
    "takes around 90", "taking around 90", "only 8gb", "upgrade to 16gb", "catches ambient",
    "requires daily", "substantial weight", "sleep tracking metrics are basic", "average in low light",
    "charging is limited", "add a basic soundbar", "slight quirk", "battery drains", "not worth",
    "stopped working", "poor battery", "heats up", "too expensive", "overheating is an issue",
]

NEGATION_WORDS = {"not", "no", "never", "hardly", "barely", "without", "zero", "free", "doesn't", "doesnt", "don't", "dont", "didn't", "didnt"}
ACCESSORY_TERMS = {"case", "cover", "back cover", "tempered glass", "screen protector", "screen guard", "pouch", "skin", "adapter", "cable", "charger only", "strap", "band only", "sleeve"}


def _clean_exact_rating(value: Any) -> float | None:
    """Preserves exact overall product rating (e.g. 4.3 -> 4.3) without fabricating defaults."""
    if value is None or value == "":
        return None
    try:
        v = float(value)
        if 0.0 < v <= 5.0:
            return round(v, 1)
    except (TypeError, ValueError):
        return None
    return None


def _build_cache_key(product: dict[str, Any]) -> str:
    """Strictly isolates cache entries per product ID + name + SerpAPI identifiers."""
    parts = [
        str(product.get("id") or "").strip().lower(),
        str(product.get("name") or "").strip().lower(),
        str(product.get("model") or "").strip().lower(),
        str(product.get("serpapi_product_id") or "").strip(),
        str(product.get("immersive_product_page_token") or "").strip()[:48],
    ]
    return "|".join(parts)


def _get_valid_cache_entry(cache_key: str) -> dict[str, Any] | None:
    """Returns cached review analysis if present and not expired; evicts expired entries."""
    entry = _REVIEW_CACHE.get(cache_key)
    if not entry:
        return None
    age = time.monotonic() - float(entry.get("cached_at", 0.0))
    ttl = float(entry.get("ttl", AVAILABLE_CACHE_TTL_SECONDS))
    if age >= ttl:
        _REVIEW_CACHE.pop(cache_key, None)
        return None
    data = dict(entry["data"])
    data["from_cache"] = True
    return data


def _store_cache_entry(cache_key: str, analysis: dict[str, Any]) -> None:
    """Stores analysis with appropriate TTL (available: 30m, unavailable: 2m, error: never cached)."""
    status = analysis.get("status")
    if status == "error":
        return
    ttl = AVAILABLE_CACHE_TTL_SECONDS if status == "available" else UNAVAILABLE_CACHE_TTL_SECONDS
    _REVIEW_CACHE[cache_key] = {
        "data": dict(analysis),
        "cached_at": time.monotonic(),
        "ttl": ttl,
    }


def get_cached_review_analysis(product_id: str, product: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Returns non-expired cached ABSA review analysis strictly for this product."""
    if product is not None:
        key = _build_cache_key(product)
        hit = _get_valid_cache_entry(key)
        if hit is not None:
            return hit
    pid = str(product_id or "").strip().lower()
    if not pid:
        return None
    for k in list(_REVIEW_CACHE.keys()):
        if k.startswith(pid + "|"):
            hit = _get_valid_cache_entry(k)
            if hit is not None and hit.get("product_id") == str(product_id):
                return hit
    return None


def build_not_fetched_placeholder(product: dict[str, Any]) -> dict[str, Any]:
    """
    Lightweight placeholder attached during /api/search so actual written reviews
    are fetched separately when the user clicks a product or opens Customer Reviews.
    """
    overall_rating = _clean_exact_rating(product.get("rating"))
    rating_count = int(product.get("rating_count") or 0)
    return {
        "product_id": str(product.get("id") or ""),
        "product_name": str(product.get("name") or "Product"),
        "status": "not_fetched",
        "status_message": "Click this product or open Customer Reviews to fetch actual written reviews.",
        "fetched": False,
        "source": None,
        "sources": [],
        "review_count": 0,
        "overall_rating": overall_rating,
        "overall_rating_count": rating_count,
        "star_rating": overall_rating or 0.0,
        "rating_count": rating_count,
        "positive": None,
        "negative": None,
        "neutral": None,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "sentiment": None,
        "sentiment_score": None,
        "summary": "Written customer reviews have not been fetched yet.",
        "pros": [],
        "cons": [],
        "aspects": {},
        "reviews": [],
        "review_items": [],
    }


def _extract_clauses(text: str) -> list[str]:
    """Splits review text into sensible sub-clauses for aspect sentiment classification."""
    return [c.strip() for c in re.split(r"[,;.\n!]|\band\b|\bbut\b|\bhowever\b|\balso\b", text.lower()) if len(c.strip()) > 3]


def _matches_exact_product_variant(
    candidate_title: str,
    target_name: str,
    target_brand: str = "",
    target_model: str = "",
    target_specs: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """
    Strictly verifies that a candidate product title matches the selected product and variant
    so reviews from other products or variants (e.g. S24 Ultra on base S24, cases, covers) are never mixed.
    """
    from .pipeline import parse_query_intent, ALL_MODIFIERS

    cand_l = str(candidate_title or "").lower().strip()
    target_l = str(target_name or "").lower().strip()
    if not cand_l or not target_l:
        return False, "Missing product title"

    target_is_acc = any(a in target_l for a in ACCESSORY_TERMS)
    cand_is_acc = any(re.search(r"\b" + re.escape(a) + r"\b", cand_l) for a in ACCESSORY_TERMS)
    if cand_is_acc and not target_is_acc:
        return False, f"Accessory listing rejected: '{candidate_title}'"

    target_intent = parse_query_intent(f"{target_brand} {target_name} {target_model}".strip())
    cand_intent = parse_query_intent(candidate_title)

    req_brand = (target_brand or target_intent.get("brand") or "").lower().strip()
    if req_brand and req_brand not in cand_l:
        if not (req_brand == "xiaomi" and "redmi" in cand_l) and not (req_brand == "apple" and "iphone" in cand_l):
            if not (req_brand == "samsung" and "galaxy" in cand_l):
                return False, f"Brand mismatch: expected '{req_brand}', got '{candidate_title}'"

    req_model = (target_intent.get("model") or "").lower().strip()
    cand_model = (cand_intent.get("model") or "").lower().strip()
    req_mods = set(target_intent.get("required_modifiers") or [])

    if req_model:
        for m in req_mods:
            if m == "+":
                if "+" not in cand_l and "plus" not in cand_l:
                    return False, f"Missing required variant modifier '{m}'"
            elif not re.search(r"\b" + re.escape(m) + r"\b", cand_l):
                return False, f"Missing required variant modifier '{m}'"

        for forb in ALL_MODIFIERS:
            if forb in req_mods:
                continue
            if forb == "+":
                if re.search(r"(?:s2[0-9]|iphone\s*\d+|note\s*\d+)\+", cand_l) or "s24+" in cand_l:
                    return False, "Forbidden '+' variant present"
            elif re.search(r"\b" + re.escape(forb) + r"\b", cand_l):
                if not re.search(r"\b" + re.escape(forb) + r"\b", target_l):
                    return False, f"Forbidden variant modifier '{forb}' in '{candidate_title}'"

        if cand_model and cand_model != req_model:
            return False, f"Different model detected: expected '{req_model}', got '{cand_model}'"

        req_base_tokens = [t for t in re.findall(r"[a-z0-9]+", req_model) if len(t) >= 2]
        cand_compact = re.sub(r"[^a-z0-9]+", "", cand_l)
        req_compact = re.sub(r"[^a-z0-9]+", "", req_model)
        if req_compact not in cand_compact and not all(t in cand_l for t in req_base_tokens):
            return False, f"Base model '{req_model}' missing from '{candidate_title}'"
    else:
        model_nums = re.findall(r"\b[a-z]*\d+[a-z0-9-]*\b", target_l)
        model_nums = [m for m in model_nums if m not in {"5g", "4g", "128gb", "256gb", "512gb", "64gb", "8gb", "16gb", "4k", "12th", "13th", "11th", "10th", "2nd"}]
        for num in model_nums[:2]:
            if num not in cand_l and num.replace("-", "") not in cand_l.replace("-", ""):
                return False, f"Model identifier '{num}' missing from '{candidate_title}'"

    target_storage = target_intent.get("specs", {}).get("storage_gb")
    if not target_storage and target_specs:
        st_match = re.search(r"(\d+)\s*(gb|tb)", str(target_specs.get("Storage", "")).lower())
        if st_match:
            val = int(st_match.group(1))
            target_storage = val * 1024 if st_match.group(2) == "tb" else val
    cand_storage = cand_intent.get("specs", {}).get("storage_gb")
    if target_storage and cand_storage and target_storage != cand_storage:
        return False, f"Storage variant mismatch: target {target_storage}GB vs candidate {cand_storage}GB"

    stop = {"the", "for", "with", "and", "5g", "4g", "in", "of", "gen", "new", "edition", "india", "wireless", "bluetooth"}
    tokens = [t for t in re.findall(r"[a-z0-9]+", target_l) if len(t) >= 2 and t not in stop]
    if tokens:
        hits = sum(1 for t in tokens if t in cand_l)
        min_required = max(1, min(2, len(tokens)))
        if hits < min_required:
            return False, f"Insufficient token overlap ({hits}/{len(tokens)})"

    return True, "Exact product and variant verified"


def _review_belongs_to_selected_product(review: dict[str, Any], target_name: str, target_model: str = "") -> bool:
    """Rejects an individual review if its own variant metadata or title names a different variant."""
    from .pipeline import parse_query_intent, ALL_MODIFIERS

    target_intent = parse_query_intent(f"{target_name} {target_model}".strip())
    req_model = (target_intent.get("model") or "").lower().strip()
    if not req_model:
        return True

    req_mods = set(target_intent.get("required_modifiers") or [])
    meta_text = " ".join(
        str(review.get(k) or "") for k in ("variant", "product_variant", "title")
    ).lower().strip()
    if not meta_text:
        return True

    for forb in ALL_MODIFIERS:
        if forb in req_mods or forb == "+":
            continue
        if re.search(r"\b" + re.escape(forb) + r"\b", meta_text):
            variant_field = str(review.get("variant") or review.get("product_variant") or "").lower()
            if forb in variant_field or req_model.split()[0] in meta_text:
                return False

    return True


def perform_absa(
    reviews: list[dict[str, Any]],
    product_name: str,
    star_rating: float | None = None,
    rating_count: int = 0,
    unavailable_reason: str | None = None,
    product_id: str = "",
    matched_product_title: str | None = None,
    variant_verified: bool = True,
    fetch_error: bool = False,
) -> dict[str, Any]:
    """
    Performs genuine Aspect-Based Sentiment Analysis (ABSA) strictly on actual retrieved written reviews.
    Keeps overall product rating strictly separate from individual review ratings and sentiment percentages.
    NEVER fabricates reviews, pros, cons, or sentiment percentages.
    """
    overall_rating = _clean_exact_rating(star_rating)
    rating_derived_pct = round((overall_rating / 5.0) * 100) if overall_rating else None

    if fetch_error:
        return {
            "product_id": product_id,
            "product_name": product_name,
            "matched_product_title": matched_product_title,
            "variant_verified": False,
            "status": "error",
            "status_message": "Unable to fetch reviews. Please try again.",
            "error_detail": unavailable_reason or "External review API request failed.",
            "fetched": True,
            "source": None,
            "sources": [],
            "review_count": 0,
            "overall_rating": overall_rating,
            "overall_rating_count": rating_count,
            "star_rating": overall_rating or 0.0,
            "rating_count": rating_count,
            "rating_based_score": rating_derived_pct,
            "positive": None,
            "negative": None,
            "neutral": None,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "sentiment": None,
            "sentiment_score": None,
            "summary": "Unable to fetch reviews. Please try again.",
            "pros": [],
            "cons": [],
            "aspects": {},
            "reviews": [],
            "review_items": [],
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    cleaned_reviews: list[dict[str, Any]] = []
    for r in reviews or []:
        if isinstance(r, dict) and isinstance(r.get("text"), str) and len(r["text"].strip()) >= 8:
            item = dict(r)
            item["product_id"] = product_id
            item["product_name"] = product_name
            cleaned_reviews.append(item)

    total_reviews = len(cleaned_reviews)

    if total_reviews == 0:
        return {
            "product_id": product_id,
            "product_name": product_name,
            "matched_product_title": matched_product_title,
            "variant_verified": variant_verified,
            "status": "unavailable",
            "status_message": "No written customer reviews available for this product.",
            "unavailable_reason": unavailable_reason or "No written customer reviews were returned for this exact product.",
            "fetched": True,
            "source": None,
            "sources": [],
            "review_count": 0,
            "overall_rating": overall_rating,
            "overall_rating_count": rating_count,
            "star_rating": overall_rating or 0.0,
            "rating_count": rating_count,
            "rating_based_score": rating_derived_pct,
            "positive": None,
            "negative": None,
            "neutral": None,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "sentiment": None,
            "sentiment_score": None,
            "summary": "No written customer reviews available for this product.",
            "pros": [],
            "cons": [],
            "aspects": {},
            "reviews": [],
            "review_items": [],
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "explanation": "No written customer reviews were available to analyze. No reviews or sentiment percentages were fabricated.",
        }

    pos_reviews = 0
    neg_reviews = 0
    neu_reviews = 0
    aspect_scores: dict[str, list[int]] = {a: [] for a in ASPECT_KEYWORDS}
    aspect_mentions: dict[str, list[str]] = {a: [] for a in ASPECT_KEYWORDS}
    pro_highlights: list[str] = []
    con_highlights: list[str] = []
    sources_seen: list[str] = []

    for rev in cleaned_reviews:
        text = rev["text"].strip()
        src = str(rev.get("source") or "").strip()
        if src and src not in sources_seen:
            sources_seen.append(src)

        clauses = _extract_clauses(text)
        review_polarity = 0

        for clause in clauses:
            tokens = re.findall(r"[a-z']+", clause)
            clause_polarity = 0
            for i, token in enumerate(tokens):
                window = set(tokens[max(0, i - 2):i])
                negation = bool(window & NEGATION_WORDS)
                if token in {"fast", "quickly"} and bool(window & {"drain", "drains", "draining", "heats", "heating", "drops"}):
                    val = -1
                else:
                    val = 1 if token in POSITIVE_WORDS else -1 if token in NEGATIVE_WORDS else 0
                clause_polarity += -val if negation else val

            for phrase in NEGATIVE_PHRASES:
                if phrase in clause:
                    clause_polarity -= 1

            review_polarity += clause_polarity

            for aspect, kws in ASPECT_KEYWORDS.items():
                if any(re.search(r"\b" + re.escape(kw) + r"\b", clause) for kw in kws):
                    aspect_scores[aspect].append(clause_polarity)
                    aspect_mentions[aspect].append(clause)

            if clause_polarity > 0 and len(clause) > 10:
                clean_p = clause.strip().capitalize()
                if clean_p not in pro_highlights:
                    pro_highlights.append(clean_p)
            elif clause_polarity < 0 and len(clause) > 10:
                clean_c = clause.strip().capitalize()
                if clean_c not in con_highlights:
                    con_highlights.append(clean_c)

        if review_polarity > 0:
            pos_reviews += 1
            rev["sentiment_label"] = "Positive"
        elif review_polarity < 0:
            neg_reviews += 1
            rev["sentiment_label"] = "Negative"
        else:
            neu_reviews += 1
            rev["sentiment_label"] = "Neutral"
        rev["sentiment_score"] = review_polarity

    pos_pct = round((pos_reviews / total_reviews) * 100)
    neg_pct = round((neg_reviews / total_reviews) * 100)
    neu_pct = max(0, 100 - (pos_pct + neg_pct))
    if pos_pct + neg_pct > 100:
        if pos_reviews >= neg_reviews:
            pos_pct = 100 - neg_pct
        else:
            neg_pct = 100 - pos_pct
        neu_pct = 0

    pros: list[str] = []
    cons: list[str] = []
    aspect_breakdown: dict[str, dict[str, Any]] = {}

    for aspect, scores in aspect_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score > 0.15:
                status = "Strong"
                pros.append(aspect.title())
            elif avg_score < -0.15:
                status = "Caution"
                cons.append(aspect.title())
            else:
                status = "Neutral"
                if min(scores) < 0 and avg_score <= 0:
                    cons.append(aspect.title())

            aspect_breakdown[aspect] = {
                "score": round(avg_score, 2),
                "status": status,
                "mentions_count": len(scores),
                "sample_quote": aspect_mentions[aspect][0].capitalize() if aspect_mentions[aspect] else "",
            }

    if not pros and pro_highlights:
        pros = [p[:70] + ("..." if len(p) > 70 else "") for p in pro_highlights[:3]]
    if not cons and con_highlights:
        cons = [c[:70] + ("..." if len(c) > 70 else "") for c in con_highlights[:3]]

    summary_parts = [
        f"Analyzed {total_reviews} written customer review{'s' if total_reviews != 1 else ''} for {product_name}: "
        f"{pos_pct}% positive ({pos_reviews}), {neu_pct}% neutral ({neu_reviews}), and {neg_pct}% negative ({neg_reviews})."
    ]
    if pros:
        summary_parts.append(f"Common pros: {', '.join(pros[:3])}.")
    if cons:
        summary_parts.append(f"Common cons: {', '.join(cons[:3])}.")
    summary_text = " ".join(summary_parts)

    sentiment_val = round((pos_pct + 0.5 * neu_pct) / 100.0, 2)
    source_label = ", ".join(sources_seen) if sources_seen else "External Review Source"

    return {
        "product_id": product_id,
        "product_name": product_name,
        "matched_product_title": matched_product_title or product_name,
        "variant_verified": variant_verified,
        "status": "available",
        "status_message": "Reviews loaded successfully.",
        "fetched": True,
        "source": source_label,
        "sources": sources_seen,
        "review_count": total_reviews,
        "overall_rating": overall_rating,
        "overall_rating_count": rating_count,
        "star_rating": overall_rating or 0.0,
        "rating_count": rating_count,
        "rating_based_score": rating_derived_pct,
        "positive": pos_pct,
        "negative": neg_pct,
        "neutral": neu_pct,
        "positive_count": pos_reviews,
        "negative_count": neg_reviews,
        "neutral_count": neu_reviews,
        "sentiment": sentiment_val,
        "sentiment_score": sentiment_val,
        "summary": summary_text,
        "pros": pros[:4],
        "cons": cons[:4],
        "aspects": aspect_breakdown,
        "reviews": cleaned_reviews,
        "review_items": cleaned_reviews,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


def _normalize_raw_serpapi_reviews(
    raw_reviews: list[dict[str, Any]],
    target_name: str,
    target_model: str = "",
    default_source: str = "Google Shopping",
) -> list[dict[str, Any]]:
    """Normalizes raw SerpAPI review objects without fabricating fields and filters wrong-variant reviews."""
    out: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    for r in raw_reviews or []:
        if not isinstance(r, dict):
            continue
        text = str(r.get("text") or r.get("content") or r.get("snippet") or "").strip()
        if len(text) < 8:
            continue
        if not _review_belongs_to_selected_product(r, target_name, target_model):
            continue

        digest = hashlib.md5(text.lower().encode()).hexdigest()[:10]
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)

        parsed_rating = _clean_exact_rating(r.get("rating"))
        source_name = str(r.get("source") or default_source).strip() or default_source
        reviewer_name = str(r.get("user_name") or r.get("author") or r.get("reviewer") or "").strip() or None
        title = str(r.get("title") or "").strip() or None
        date_str = str(r.get("date") or "").strip() or None
        source_url = str(r.get("link") or r.get("source_link") or "").strip() or None

        out.append({
            "id": f"rev-{digest}",
            "title": title,
            "text": text,
            "source": source_name,
            "source_url": source_url,
            "reviewer": reviewer_name,
            "rating": parsed_rating,
            "date": date_str,
        })
    return out


def _merge_unique_reviews(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = {r.get("id") or hashlib.md5(r.get("text", "").lower().encode()).hexdigest()[:10] for r in existing}
    merged = list(existing)
    for r in incoming:
        key = r.get("id") or hashlib.md5(r.get("text", "").lower().encode()).hexdigest()[:10]
        if key not in seen:
            seen.add(key)
            merged.append(r)
    return merged


def _extract_next_page_request(
    payload: dict[str, Any],
    base_endpoint: str,
    engine: str,
    api_key: str,
    extra_params: dict[str, str],
) -> tuple[str, dict[str, str]] | None:
    pagination = payload.get("serpapi_pagination") or {}
    prod_res = payload.get("product_results") or {}
    rev_res = payload.get("reviews_results") or {}

    next_token = (
        pagination.get("next_page_token")
        or rev_res.get("next_page_token")
        or prod_res.get("more_reviews_token")
        or payload.get("more_reviews_token")
    )
    if next_token:
        params = dict(extra_params)
        params["engine"] = engine
        params["next_page_token"] = str(next_token)
        params["api_key"] = api_key
        return base_endpoint, params

    next_url = pagination.get("next")
    if isinstance(next_url, str) and next_url.startswith("http"):
        return next_url, {"api_key": api_key}

    return None


async def fetch_serpapi_reviews(
    product_title: str,
    brand: str = "",
    model: str = "",
    specs: dict[str, Any] | None = None,
    serpapi_product_id: str = "",
    immersive_token: str = "",
) -> dict[str, Any]:
    """
    Fetches actual written customer reviews strictly for the selected product via SerpAPI:
    1. Uses immersive_product_page_token (google_immersive_product) when available.
    2. Falls back to product_id (google_product, reviews=1) when available.
    3. If neither identifier was passed, resolves them via google_shopping using strict variant verification.
    4. Handles pagination (up to MAX_REVIEW_PAGES) when supported.
    5. Verifies the returned product title matches the selected product before accepting any reviews.
    """
    if not SERPAPI_KEY:
        return {
            "state": "empty",
            "reviews": [],
            "matched_title": None,
            "overall_rating": None,
            "overall_rating_count": None,
            "pages_fetched": 0,
            "note": "Live review provider (SERPAPI_KEY) is not configured.",
        }

    endpoint = SERPAPI_API_BASE or "https://serpapi.com/search.json"
    pid = str(serpapi_product_id or "").strip()
    token = str(immersive_token or "").strip()
    matched_title: str | None = None
    live_overall_rating: float | None = None
    live_rating_count: int | None = None
    pages_fetched = 0

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            if not token and not pid:
                shop_resp = await client.get(
                    endpoint,
                    params={
                        "engine": "google_shopping",
                        "q": product_title,
                        "gl": "in",
                        "hl": "en",
                        "api_key": SERPAPI_KEY,
                    },
                )
                if shop_resp.status_code != 200:
                    return {
                        "state": "error",
                        "reviews": [],
                        "matched_title": None,
                        "overall_rating": None,
                        "overall_rating_count": None,
                        "pages_fetched": 0,
                        "note": f"SerpAPI google_shopping returned HTTP {shop_resp.status_code}.",
                    }
                shopping_results = shop_resp.json().get("shopping_results", [])
                for item in shopping_results:
                    item_title = str(item.get("title") or "")
                    ok, _ = _matches_exact_product_variant(item_title, product_title, brand, model, specs)
                    if not ok:
                        continue
                    cand_token = str(item.get("immersive_product_page_token") or "").strip()
                    cand_pid = str(item.get("product_id") or "").strip()
                    if cand_token or cand_pid:
                        token = token or cand_token
                        pid = pid or cand_pid
                        matched_title = matched_title or item_title
                        live_overall_rating = live_overall_rating or _clean_exact_rating(item.get("rating"))
                        if item.get("reviews"):
                            try:
                                live_rating_count = int(str(item.get("reviews")).replace(",", ""))
                            except (TypeError, ValueError):
                                pass
                            break

            collected: list[dict[str, Any]] = []
            had_api_error = False
            last_error_note = ""

            # Primary: google_immersive_product (uses immersive_product_page_token + pagination)
            if token:
                next_req: tuple[str, dict[str, str]] | None = (
                    endpoint,
                    {
                        "engine": "google_immersive_product",
                        "page_token": token,
                        "gl": "in",
                        "hl": "en",
                        "api_key": SERPAPI_KEY,
                    },
                )
                page_num = 0
                while next_req and page_num < MAX_REVIEW_PAGES:
                    req_url, req_params = next_req
                    imm_resp = await client.get(req_url, params=req_params)
                    if imm_resp.status_code != 200:
                        if page_num == 0:
                            had_api_error = True
                            last_error_note = f"SerpAPI google_immersive_product returned HTTP {imm_resp.status_code}."
                        break

                    page_num += 1
                    pages_fetched += 1
                    imm_data = imm_resp.json()
                    prod_res = imm_data.get("product_results") or {}
                    returned_title = str(prod_res.get("title") or matched_title or "").strip()

                    if page_num == 1 and returned_title:
                        title_ok, mismatch_reason = _matches_exact_product_variant(
                            returned_title, product_title, brand, model, specs
                        )
                        if not title_ok:
                            log.info("Rejected mismatched immersive product '%s' for '%s': %s", returned_title, product_title, mismatch_reason)
                            break

                    matched_title = returned_title or matched_title
                    live_overall_rating = _clean_exact_rating(prod_res.get("rating")) or live_overall_rating
                    if prod_res.get("reviews") is not None:
                        try:
                            live_rating_count = int(str(prod_res.get("reviews")).replace(",", ""))
                        except (TypeError, ValueError):
                            pass

                    raw_imm = (
                        prod_res.get("user_reviews")
                        or imm_data.get("reviews_results", {}).get("reviews")
                        or []
                    )
                    normalized_page = _normalize_raw_serpapi_reviews(
                        raw_imm, product_title, model, default_source="Google Shopping"
                    )
                    collected = _merge_unique_reviews(collected, normalized_page)

                    next_req = _extract_next_page_request(
                        imm_data,
                        endpoint,
                        "google_immersive_product",
                        SERPAPI_KEY,
                        {"page_token": token, "gl": "in", "hl": "en"},
                    )

            # Secondary: google_product (uses product_id + reviews=1 + pagination)
            if not collected and pid:
                next_req = (
                    endpoint,
                    {
                        "engine": "google_product",
                        "product_id": pid,
                        "reviews": "1",
                        "gl": "in",
                        "hl": "en",
                        "api_key": SERPAPI_KEY,
                    },
                )
                page_num = 0
                while next_req and page_num < MAX_REVIEW_PAGES:
                    req_url, req_params = next_req
                    prod_resp = await client.get(req_url, params=req_params)
                    if prod_resp.status_code != 200:
                        if page_num == 0:
                            had_api_error = True
                            last_error_note = f"SerpAPI google_product returned HTTP {prod_resp.status_code}."
                        break

                    page_num += 1
                    pages_fetched += 1
                    prod_data = prod_resp.json()
                    prod_res = prod_data.get("product_results") or {}
                    returned_title = str(prod_res.get("title") or matched_title or "").strip()

                    if page_num == 1 and returned_title:
                        title_ok, mismatch_reason = _matches_exact_product_variant(
                            returned_title, product_title, brand, model, specs
                        )
                        if not title_ok:
                            log.info("Rejected mismatched google_product '%s' for '%s': %s", returned_title, product_title, mismatch_reason)
                            break

                    matched_title = returned_title or matched_title
                    live_overall_rating = _clean_exact_rating(prod_res.get("rating")) or live_overall_rating
                    if prod_res.get("reviews") is not None:
                        try:
                            live_rating_count = int(str(prod_res.get("reviews")).replace(",", ""))
                        except (TypeError, ValueError):
                            pass

                    raw_prod = prod_data.get("reviews_results", {}).get("reviews") or []
                    normalized_page = _normalize_raw_serpapi_reviews(
                        raw_prod, product_title, model, default_source="Google Product Reviews"
                    )
                    collected = _merge_unique_reviews(collected, normalized_page)

                    next_req = _extract_next_page_request(
                        prod_data,
                        endpoint,
                        "google_product",
                        SERPAPI_KEY,
                        {"product_id": pid, "reviews": "1", "gl": "in", "hl": "en"},
                    )

            if collected:
                return {
                    "state": "ok",
                    "reviews": collected,
                    "matched_title": matched_title,
                    "overall_rating": live_overall_rating,
                    "overall_rating_count": live_rating_count,
                    "pages_fetched": pages_fetched,
                    "note": f"Fetched {len(collected)} verified written customer reviews across {pages_fetched} page(s).",
                }

            if had_api_error:
                return {
                    "state": "error",
                    "reviews": [],
                    "matched_title": matched_title,
                    "overall_rating": live_overall_rating,
                    "overall_rating_count": live_rating_count,
                    "pages_fetched": pages_fetched,
                    "note": last_error_note,
                }

            return {
                "state": "empty",
                "reviews": [],
                "matched_title": matched_title,
                "overall_rating": live_overall_rating,
                "overall_rating_count": live_rating_count,
                "pages_fetched": pages_fetched,
                "note": "No written customer reviews were returned by external review sources for this exact product.",
            }
    except Exception as e:
        log.warning("Live SerpAPI review fetch failed for '%s': %s", product_title, e)
        return {
            "state": "error",
            "reviews": [],
            "matched_title": None,
            "overall_rating": None,
            "overall_rating_count": None,
            "pages_fetched": pages_fetched,
            "note": f"Network or API error while fetching customer reviews: {e}",
        }


async def extract_and_analyze_reviews(
    product: dict[str, Any],
    fetch_live: bool = True,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Master Automatic Product-Specific Review Extractor & ABSA Analyzer:
    - If fetch_live=False (used during /api/search), returns cached reviews if valid or a lightweight
      'not_fetched' placeholder without blocking search or fabricating reviews.
    - If fetch_live=True (used when opening Product Details / Customer Reviews), checks TTL cache
      (unless force_refresh=True), fetches real written reviews from SerpAPI (with pagination & strict
      variant verification), runs ABSA, and caches results with appropriate TTL.
    """
    pid = str(product.get("id", "")).strip()
    cache_key = _build_cache_key(product)

    if not force_refresh and pid:
        cached = _get_valid_cache_entry(cache_key)
        if cached is not None:
            return cached

    if not fetch_live:
        return build_not_fetched_placeholder(product)

    p_name = str(product.get("name") or "Product").strip()
    p_brand = str(product.get("brand") or "").strip()
    p_model = str(product.get("model") or "").strip()
    p_specs = product.get("specs") if isinstance(product.get("specs"), dict) else None
    overall_rating = _clean_exact_rating(product.get("rating"))
    overall_rating_count = int(product.get("rating_count") or 0)

    extracted: list[dict[str, Any]] = []
    matched_title: str | None = None
    unavailable_reason: str | None = None
    fetch_error = False
    pages_fetched = 0

    # 1. Accept real written review items only if explicitly provided in the request payload
    supplied = product.get("reviews") or []
    if isinstance(supplied, list) and supplied:
        for idx, r in enumerate(supplied):
            if isinstance(r, dict) and isinstance(r.get("text"), str) and len(r["text"].strip()) >= 8:
                if not _review_belongs_to_selected_product(r, p_name, p_model):
                    continue
                extracted.append({
                    "id": str(r.get("id") or f"rev-{idx + 1}"),
                    "title": r.get("title"),
                    "text": r["text"].strip(),
                    "source": str(r.get("source") or "Customer Review").strip(),
                    "source_url": r.get("source_url") or r.get("link"),
                    "reviewer": r.get("reviewer") or r.get("author"),
                    "rating": _clean_exact_rating(r.get("rating")),
                    "date": r.get("date"),
                })
        if extracted:
            matched_title = p_name
            pages_fetched = 1

    # 2. Fetch actual written customer reviews live from SerpAPI
    if not extracted:
        fetch_res = await fetch_serpapi_reviews(
            product_title=p_name,
            brand=p_brand,
            model=p_model,
            specs=p_specs,
            serpapi_product_id=str(product.get("serpapi_product_id") or ""),
            immersive_token=str(product.get("immersive_product_page_token") or ""),
        )
        matched_title = fetch_res.get("matched_title")
        pages_fetched = int(fetch_res.get("pages_fetched") or 0)
        if fetch_res.get("overall_rating") is not None:
            overall_rating = fetch_res["overall_rating"]
        if fetch_res.get("overall_rating_count"):
            overall_rating_count = int(fetch_res["overall_rating_count"])

        if fetch_res["state"] == "ok":
            extracted = fetch_res["reviews"]
        elif fetch_res["state"] == "error":
            fetch_error = True
            unavailable_reason = fetch_res.get("note")
        else:
            unavailable_reason = fetch_res.get("note")

    analysis = perform_absa(
        extracted,
        product_name=p_name,
        star_rating=overall_rating,
        rating_count=overall_rating_count,
        unavailable_reason=unavailable_reason,
        product_id=pid,
        matched_product_title=matched_title,
        variant_verified=not fetch_error,
        fetch_error=fetch_error,
    )
    analysis["pages_fetched"] = pages_fetched
    analysis["from_cache"] = False

    if pid:
        _store_cache_entry(cache_key, analysis)
    return analysis
