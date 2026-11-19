from datetime import datetime, timezone
import hashlib
import logging
import re
from typing import Any
import httpx
from ..config import SERPAPI_KEY
from ..services.image_validator import sanitize_image_url
from ..services.pipeline import extract_product_metadata, is_accessory_product, normalize_query
from .base import extract_brand, normalize_price

log = logging.getLogger("shopwise.serpapi")


def _parse_rating(val: Any) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        r = float(val)
        return round(r, 1) if 0.0 < r <= 5.0 else 0.0
    m = re.search(r"(\d+(?:\.\d+)?)", str(val))
    if not m:
        return 0.0
    try:
        r = float(m.group(1))
        return round(r, 1) if 0.0 < r <= 5.0 else 0.0
    except ValueError:
        return 0.0


def _parse_review_count(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, int):
        return max(0, val)
    if isinstance(val, float):
        # SerpAPI occasionally returns small floats like 1.1 for 1.1k reviews
        return int(round(val * 1000)) if val < 20 and val != int(val) else max(0, int(round(val)))
    s = str(val).strip().lower().replace(",", "")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(k|m)?$", s)
    if not m:
        digits = re.findall(r"\d+", s)
        return int(digits[0]) if digits else 0
    num = float(m.group(1))
    unit = m.group(2)
    if unit == "k":
        return int(round(num * 1000))
    if unit == "m":
        return int(round(num * 1_000_000))
    return int(round(num))


def _canonical_title_key(title: str) -> str:
    """Normalizes the full product title for safe deduplication (never truncates to 5 words)."""
    cleaned = normalize_query(title).lower()
    # Strip trailing retailer suffixes like 'at nykaa', 'at etoren', '- amazon.in'
    cleaned = re.sub(r"\b(?:at|on|by)\s+[a-z0-9.\-]+\s*$", "", cleaned)
    tokens = re.findall(r"[a-z0-9]+", cleaned)
    return " ".join(tokens)


def _build_product_key(
    title: str,
    brand: str,
    meta: dict[str, Any],
    serpapi_pid: str,
    is_refurb: bool = False,
) -> str:
    """
    Generates a strict variant-level product identity key that enables genuine
    multi-store price comparison (Amazon.in vs Flipkart vs Croma for the exact
    same model/storage/colour) while preventing cross-variant or accessory bleed:
    - For recognized models (brand + model present, non-accessory): keys by exact
      (brand, category, model, storage, colour, condition) so identical variants
      across retailers combine their store offers cleanly.
    - Otherwise uses SerpAPI's canonical `product_id` or full normalized title key.
    """
    specs = meta.get("specs") or {}
    model = str(meta.get("model") or "").strip().lower()
    is_acc = bool(meta.get("is_accessory"))
    cond = "refurb" if is_refurb else "new"

    if model and brand and brand.lower() != "unknown" and not is_acc:
        storage = str(specs.get("Storage") or "").strip().lower()
        colour = str(specs.get("Colour") or "").strip().lower()
        proc = str(specs.get("Processor") or "").strip().lower()
        ram = str(specs.get("RAM") or "").strip().lower() if str(meta.get("category") or "").lower() == "laptop" else ""
        raw_key = "|".join([
            "variant",
            brand.lower(),
            str(meta.get("category") or "other").lower(),
            model,
            ram,
            storage,
            colour,
            proc,
            cond,
        ])
    elif serpapi_pid:
        raw_key = f"pid:{serpapi_pid}:{cond}"
    else:
        raw_key = "|".join([
            brand.lower(),
            str(meta.get("category") or "other").lower(),
            model,
            str(specs.get("RAM") or "").lower(),
            str(specs.get("Storage") or "").lower(),
            str(specs.get("Colour") or "").lower(),
            "acc" if is_acc else "main",
            cond,
            _canonical_title_key(title),
        ])
    return "live-" + hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:14]


class SerpApiAdapter:
    ENDPOINT = "https://serpapi.com/search.json"

    async def search(self, query: str) -> list[dict]:
        if not SERPAPI_KEY:
            return []

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(
                    self.ENDPOINT,
                    params={
                        "engine": "google_shopping",
                        "q": query,
                        "gl": "in",
                        "hl": "en",
                        "api_key": SERPAPI_KEY,
                    },
                )
                if response.status_code != 200:
                    log.warning("SerpAPI response error %d: %s", response.status_code, response.text[:200])
                    return []
                payload = response.json()
        except Exception as e:
            log.warning("SerpAPI request failed: %s", e)
            return []

        grouped: dict[str, dict] = {}
        now_iso = datetime.now(timezone.utc).isoformat()

        for item in payload.get("shopping_results", []):
            title = str(item.get("title") or "").strip()
            if not title:
                continue

            price = normalize_price(item.get("extracted_price") or item.get("price"))
            if not price or price <= 0:
                continue

            # Extract and strictly validate THIS exact shopping result's own thumbnail image
            image_url = sanitize_image_url(item.get("thumbnail") or item.get("image"))
            store = str(item.get("source") or "Google Shopping").strip()
            product_url = str(item.get("product_link") or item.get("link") or "").strip()
            delivery_text = str(item.get("delivery") or "").strip()
            second_hand = str(item.get("second_hand_condition") or "").strip()
            serpapi_pid = str(item.get("product_id") or "").strip()
            imm_token = str(item.get("immersive_product_page_token") or "").strip()
            imm_api = str(item.get("serpapi_immersive_product_api") or "").strip()
            prod_api = str(item.get("serpapi_product_api") or "").strip()
            extensions = item.get("extensions") if isinstance(item.get("extensions"), list) else []
            snippet = str(item.get("snippet") or "").strip()

            brand = extract_brand(title)
            meta = extract_product_metadata(title, extensions=extensions, snippet=snippet)
            is_acc = bool(meta["is_accessory"] or is_accessory_product(title, store))
            is_refurb = bool(second_hand) or any(
                m in f"{title} {store}".lower()
                for m in ("refurbished", "refurb", "renewed", "pre-owned", "second hand", "good condition", "cashify", "sahivalue")
            )

            pid = _build_product_key(title, brand, meta, serpapi_pid, is_refurb=is_refurb)

            existing = grouped.get(pid)
            if existing is not None:
                # Guard against accidental price-tier mismatch even on same key
                existing_prices = [o["price"] for o in existing["offers"] if o.get("price", 0) > 0]
                if existing_prices:
                    min_p = min(existing_prices)
                    ratio = max(price, min_p) / max(1.0, min(price, min_p))
                    if ratio > 1.6 or bool(existing.get("is_accessory")) != is_acc:
                        pid = "live-" + hashlib.sha1(f"{pid}:{store}:{price}:{title}".encode("utf-8")).hexdigest()[:14]
                        existing = grouped.get(pid)

            if existing is None:
                grouped[pid] = {
                    "id": pid,
                    "serpapi_product_id": serpapi_pid,
                    "immersive_product_page_token": imm_token,
                    "serpapi_immersive_product_api": imm_api,
                    "serpapi_product_api": prod_api,
                    "name": title,
                    "brand": brand,
                    "category": meta["category"],
                    "model": meta["model"],
                    "rating": _parse_rating(item.get("rating")),
                    "rating_count": _parse_review_count(item.get("reviews")),
                    "image": image_url,
                    "image_verified": bool(image_url),
                    "specs": meta["specs"],
                    "tags": meta["tags"],
                    "is_accessory": is_acc,
                    "reviews": [],
                    "offers": [],
                    "source": "live",
                    "retrieved_at": now_iso,
                }
                existing = grouped[pid]
            else:
                # Never overwrite an existing valid image with another item's image
                if not existing.get("image") and image_url:
                    existing["image"] = image_url
                    existing["image_verified"] = True
                if not existing.get("serpapi_product_id") and serpapi_pid:
                    existing["serpapi_product_id"] = serpapi_pid
                if not existing.get("immersive_product_page_token") and imm_token:
                    existing["immersive_product_page_token"] = imm_token
                if not existing.get("serpapi_immersive_product_api") and imm_api:
                    existing["serpapi_immersive_product_api"] = imm_api
                if not existing.get("serpapi_product_api") and prod_api:
                    existing["serpapi_product_api"] = prod_api
                if not existing.get("rating") and item.get("rating"):
                    existing["rating"] = _parse_rating(item.get("rating"))
                if not existing.get("rating_count") and item.get("reviews"):
                    existing["rating_count"] = _parse_review_count(item.get("reviews"))

            # Avoid duplicate identical store+price offer on same product
            dup_offer = any(
                o["store"].lower() == store.lower() and abs(o["price"] - price) < 1.0
                for o in existing["offers"]
            )
            if not dup_offer:
                existing["offers"].append(
                    {
                        "store": store,
                        "price": price,
                        "url": product_url,
                        "image": image_url,
                        "delivery": delivery_text,
                        "condition": second_hand or "New",
                        "in_stock": True,
                    }
                )

        return list(grouped.values())
