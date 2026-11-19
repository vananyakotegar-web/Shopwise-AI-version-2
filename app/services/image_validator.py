"""
ShopWise Product Image Validation & Integrity Module.

Ensures:
1. Every product image URL is syntactically valid, uses http/https, and is not a tracking pixel or generic placeholder.
2. Each product keeps the exact image associated with its own shopping listing (1:1 provenance).
3. Distinct product models or unrelated products never share the same image URL.
4. No random or unrelated product image is ever assigned as a fallback; if a verified image
   is unavailable, the image field is left empty ("") so the frontend renders a clean placeholder.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

INVALID_URL_SUBSTRINGS = (
    "no-image",
    "no_image",
    "noimage",
    "placeholder",
    "spacer.gif",
    "blank.gif",
    "pixel.gif",
    "transparent.png",
    "1x1.",
    "default_avatar",
    "image-not-available",
    "image_not_available",
    "coming-soon",
)

# Known non-product / wrong stock photo IDs that must never be used for electronics/products
BLOCKED_IMAGE_URLS = (
    "photo-1544716278-ca5e3f4abd8c",  # Open book stock photo previously misused for HP laptops
)


def is_valid_image_url(url: Any) -> bool:
    """Validates that a product image URL is a legitimate http(s) image link."""
    if not isinstance(url, str):
        return False

    cleaned = url.strip()
    if not cleaned or len(cleaned) < 12 or len(cleaned) > 2048:
        return False

    lower = cleaned.lower()
    if lower in ("null", "none", "undefined", "n/a", "#"):
        return False
    if lower.startswith(("data:", "javascript:", "blob:", "about:", "file:")):
        return False
    if any(ch in cleaned for ch in ("\n", "\r", "\t", " ")):
        return False
    if any(bad in lower for bad in INVALID_URL_SUBSTRINGS):
        return False
    if any(blocked in lower for blocked in BLOCKED_IMAGE_URLS):
        return False

    try:
        parsed = urlparse(cleaned)
    except Exception:
        return False

    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    if not host or "." not in host or host in ("localhost", "127.0.0.1", "0.0.0.0"):
        return False

    return True


def sanitize_image_url(url: Any) -> str:
    """Returns a trimmed, validated image URL or '' if invalid."""
    if not is_valid_image_url(url):
        return ""
    return str(url).strip()


def _canonical_model_family(product: dict[str, Any]) -> str:
    """
    Computes a canonical identity key representing the exact product model/item.
    Two products with different model keys must NOT share the same image URL.
    Storage/RAM variants of the exact same model (e.g. S24 128GB vs S24 256GB)
    are distinguished by full product identity unless no distinct image exists.
    """
    brand = str(product.get("brand") or "").strip().lower()
    model = str(product.get("model") or "").strip().lower()
    cat = str(product.get("category") or "").strip().lower()
    if model:
        # Strip storage/variant suffixes from model codes like SM-S921B-256 -> sm-s921b
        norm_model = re.sub(r"-(?:64|128|256|512|1024)(?:gb)?$", "", model)
        return f"{cat}|{brand}|{norm_model}"

    name = str(product.get("name") or "").strip().lower()
    # Remove storage/ram tokens for family check, keep model tokens intact
    core = re.sub(r"\b\d+\s*(?:gb|tb|mah|mp|w)\b", "", name)
    tokens = re.findall(r"[a-z0-9]+", core)[:6]
    return f"{cat}|{brand}|{' '.join(tokens)}"


def verify_product_image_mapping(
    products: list[dict[str, Any]],
    req: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Final verification pass over ranked/filtered products before returning API response:
    1. Sanitizes every product image URL and offer image URL.
    2. Ensures live products keep their own listing's image (preserving 1:1 mapping).
    3. Rejects duplicate images reused across distinct unrelated models or items:
       - If the same image URL appears on a different model/product, checks whether the
         product has an unused verified image among its own offers; otherwise clears
         image to '' so the UI displays a clean placeholder instead of a mismatched photo.
    4. Sets `image_verified` boolean and `image_source` metadata on each product.
    """
    used_image_by_family: dict[str, str] = {}
    used_image_exact_count: dict[str, int] = {}

    for p in products:
        family = _canonical_model_family(p)

        # Sanitize offer-level images while preserving each offer's own image
        offer_images: list[str] = []
        for offer in p.get("offers") or []:
            if "image" in offer:
                offer["image"] = sanitize_image_url(offer.get("image"))
                if offer["image"]:
                    offer_images.append(offer["image"])

        # Validate primary product image (never invent or copy from another product)
        img = sanitize_image_url(p.get("image"))

        # If product image is missing, only check its OWN best_offer / offers
        if not img:
            best_img = sanitize_image_url((p.get("best_offer") or {}).get("image"))
            if best_img:
                img = best_img
            elif offer_images:
                img = offer_images[0]

        if img:
            existing_family = used_image_by_family.get(img)
            if existing_family is not None and existing_family != family:
                # Different model/product trying to reuse another product's image!
                # Try to find an unused image from THIS product's own offers.
                replacement = ""
                for cand in offer_images:
                    cand_fam = used_image_by_family.get(cand)
                    if cand_fam is None or cand_fam == family:
                        replacement = cand
                        break
                img = replacement

        if img:
            used_image_by_family[img] = family
            used_image_exact_count[img] = used_image_exact_count.get(img, 0) + 1

        p["image"] = img
        p["image_verified"] = bool(img)

    return products
