import re
from typing import Any, Protocol


class ProductAdapter(Protocol):
    async def search(self, query: str) -> list[dict[str, Any]]: ...


KNOWN_BRANDS = [
    "Samsung", "Apple", "HP", "Dell", "Lenovo", "ASUS", "Acer", "MSI",
    "Xiaomi", "Redmi", "POCO", "OnePlus", "Motorola", "Sony", "JBL", "boAt",
    "Bose", "Sennheiser", "Marshall", "Skullcandy", "Beats", "Soundcore", "Anker",
    "LG", "Canon", "Nikon", "Philips", "Amazfit", "Noise", "Fire-Boltt",
    "Realme", "Nothing", "Google", "Vivo", "Oppo", "iQOO",
    "Nike", "Adidas", "Puma", "Reebok", "Skechers", "New Balance", "Asics",
    "Converse", "Vans", "Fila", "Bata", "Campus", "Woodland", "Crocs",
    "GIVA", "Candere", "Tanishq", "CaratLane", "Voylla", "Yellow Chimes", "Zavya",
    "Mia", "Malabar", "Kalyan", "Clara", "Shaya", "Swarovski",
    "Biba", "W for Woman", "Aurelia",
]

# Model/product-line prefixes that unambiguously identify a brand even when omitted in title
MODEL_TO_BRAND_HINTS = [
    (r"\b(?:iphone|ipad|macbook|airpods|apple\s+watch)\b", "Apple"),
    (r"\bgalaxy\b", "Samsung"),
    (r"\bredmi\b", "Xiaomi"),
    (r"\b(?:pavilion|victus|envy|omen|elitebook|probook)\b", "HP"),
    (r"\b(?:ideapad|thinkpad|legion|yoga|loq)\b", "Lenovo"),
    (r"\b(?:vivobook|zenbook|rog|tuf)\b", "ASUS"),
    (r"\b(?:inspiron|xps|latitude|vostro|alienware)\b", "Dell"),
    (r"\b(?:air\s*max|air\s*force|air\s*jordan|dunk\s*low)\b", "Nike"),
    (r"\b(?:wh-?1000xm|wh-?ch\d+|wf-?1000xm|ult\s+wear|bravia)\b", "Sony"),
    (r"\b(?:airdopes|rockerz|nirvana)\b", "boAt"),
]


def normalize_price(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    cleaned = str(value).replace(",", "").replace("₹", "").replace("INR", "").replace("$", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    if match:
        try:
            val = float(match.group())
            return val if val > 0 else None
        except ValueError:
            return None
    return None


def extract_brand(title: str) -> str:
    title_lower = title.lower()
    # Explicit known brands first (longest first so "New Balance" / "Yellow Chimes" match before single words)
    for b in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(b.lower()) + r"\b", title_lower):
            if b.lower() == "redmi":
                return "Xiaomi"
            return b
    # Model-line hints (e.g. "iPhone 16 Pro" -> Apple, "Galaxy S24" -> Samsung)
    for pattern, canonical in MODEL_TO_BRAND_HINTS:
        if re.search(pattern, title_lower):
            return canonical
    tokens = [t for t in re.findall(r"[A-Za-z][A-Za-z0-9&'-]*", title) if len(t) > 1]
    return tokens[0].title() if tokens else "Generic"
