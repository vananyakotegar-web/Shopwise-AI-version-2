"""
ShopWise V2/V3 Search Pipeline, NLP Intent Extraction, Strict Product Filtering & Intelligent Hybrid Search Engine.

Implements:
1. Intelligent NLP query processing (extracts brand, model, category, subcategory, product type,
   colour, material, size, RAM, storage, processor, budget_min/max, gender, specs).
2. Strict mandatory product filtering (exact brand, exact model, correct category, correct product type,
   colour, material, numerical specifications, budget bounds).
3. Hybrid search system (NLP extraction -> candidate retrieval -> mandatory filtering ->
   semantic relevance -> multi-criteria ranking -> final validation).
4. Missing results handling (transparent "No exact matching products found", no unrelated products).
"""
import logging
import re
from typing import Any

log = logging.getLogger("shopwise.pipeline")

CATS_MAP = {
    "phone": ["phone", "mobile", "smartphone", "5g phone", "cellphone"],
    "laptop": ["laptop", "notebook", "macbook", "ultrabook", "chromebook"],
    "tablet": ["tablet", "ipad", "tab"],
    "headphones": ["headphone", "headphones", "headset", "earphone", "earphones", "earbud", "earbuds", "airpod", "airpods", "airdopes", "tws", "anc", "audio"],
    "watch": ["watch", "smartwatch"],
    "television": ["television", "tv", "smart tv", "led tv", "4k tv", "oled"],
    "camera": ["camera", "dslr", "mirrorless", "vlogging camera"],
    "appliances": [
        "refrigerator", "fridge", "washing machine", "air fryer", "appliance",
        "mixer", "grinder", "coffee maker", "microwave", "oven", "toaster",
        "kettle", "blender", "juicer", "air conditioner", "vacuum", "geyser",
        "water purifier", "induction", "cooler", "fan",
    ],
    "jewelry": ["ring", "rings", "necklace", "solitaire", "jewel", "jewelry", "jewellery", "earring", "bangle", "bracelet"],
    "clothing": ["kurti", "kurtis", "kurta", "dress", "saree", "clothing", "apparel", "wear"],
    "footwear": ["shoes", "shoe", "sneakers", "sneaker", "footwear", "running shoes", "trainers", "loafers", "boots", "sandals"],
}

BRAND_ALIASES = {
    "samsung": "Samsung",
    "samsng": "Samsung",
    "galaxy": "Samsung",
    "apple": "Apple",
    "iphone": "Apple",
    "ipad": "Apple",
    "macbook": "Apple",
    "airpods": "Apple",
    "hp": "HP",
    "dell": "Dell",
    "lenovo": "Lenovo",
    "asus": "ASUS",
    "acer": "Acer",
    "msi": "MSI",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",
    "poco": "POCO",
    "oneplus": "OnePlus",
    "motorola": "Motorola",
    "moto": "Motorola",
    "realme": "Realme",
    "nothing": "Nothing",
    "google": "Google",
    "vivo": "Vivo",
    "oppo": "Oppo",
    "iqoo": "iQOO",
    "sony": "Sony",
    "jbl": "JBL",
    "boat": "boAt",
    "bose": "Bose",
    "sennheiser": "Sennheiser",
    "marshall": "Marshall",
    "lg": "LG",
    "canon": "Canon",
    "nikon": "Nikon",
    "philips": "Philips",
    "amazfit": "Amazfit",
    "noise": "Noise",
    "fire-boltt": "Fire-Boltt",
    "nike": "Nike",
    "adidas": "Adidas",
    "puma": "Puma",
    "reebok": "Reebok",
    "skechers": "Skechers",
    "new balance": "New Balance",
    "asics": "Asics",
    "giva": "GIVA",
    "candere": "Candere",
    "kalyan": "Candere",
    "tanishq": "Tanishq",
    "caratlane": "CaratLane",
    "voylla": "Voylla",
    "biba": "Biba",
    "w": "W for Woman",
    "aurelia": "Aurelia",
}

PRODUCT_TYPES = {
    "wireless earbuds": ["wireless earbuds", "wireless earbud", "earbuds", "earbud", "tws", "airpods", "airdopes", "in-ear wireless", "true wireless"],
    "headphones": ["headphones", "headphone", "headset", "on-ear", "over-ear"],
    "shoes": ["running shoes", "sneakers", "sneaker", "shoes", "shoe", "trainers", "footwear", "air max"],
    "ring": ["ring", "rings", "solitaire ring", "band"],
    "kurti": ["kurti", "kurtis", "kurta"],
    "laptop": ["laptop", "notebook", "macbook", "ultrabook"],
    "smartphone": ["smartphone", "phone", "mobile", "iphone"],
    "tablet": ["tablet", "ipad", "tab"],
    "smartwatch": ["smartwatch", "watch"],
    "tv": ["tv", "television"],
    "camera": ["camera"],
    "refrigerator": ["refrigerator", "fridge"],
    "washing machine": ["washing machine"],
    "air fryer": ["air fryer"],
}

MATERIALS = ["silver", "gold", "platinum", "diamond", "cotton", "silk", "leather", "titanium", "rayon", "polyester"]
COLOURS = [
    "red", "blue", "black", "white", "off-white", "ivory", "cream", "beige",
    "silver", "gold", "green", "yellow", "pink", "purple", "orange", "brown",
    "maroon", "navy", "grey", "gray", "lime", "violet",
]

KNOWN_MODELS = [
    # (pattern, normalized_model, category, required_modifiers, strict_modifiers)
    # Samsung Galaxy S-Series (order most specific first)
    (r"\b(?:galaxy\s+)?s26\s+ultra\b", "S26 Ultra", "phone", ["ultra"], True),
    (r"\b(?:galaxy\s+)?s26\s*(?:plus|\+)\b", "S26 Plus", "phone", ["plus"], True),
    (r"\b(?:galaxy\s+)?s26\b", "S26", "phone", [], True),
    (r"\b(?:galaxy\s+)?s25\s+ultra\b", "S25 Ultra", "phone", ["ultra"], True),
    (r"\b(?:galaxy\s+)?s25\s*(?:plus|\+)\b", "S25 Plus", "phone", ["plus"], True),
    (r"\b(?:galaxy\s+)?s25\s+fe\b", "S25 FE", "phone", ["fe"], True),
    (r"\b(?:galaxy\s+)?s25\b", "S25", "phone", [], True),
    (r"\b(?:galaxy\s+)?s24\s+ultra\b", "S24 Ultra", "phone", ["ultra"], True),
    (r"\b(?:galaxy\s+)?s24\s+plus\b", "S24 Plus", "phone", ["plus"], True),
    (r"\b(?:galaxy\s+)?s24\+", "S24 Plus", "phone", ["plus"], True),
    (r"\b(?:galaxy\s+)?s24\s+fe\b", "S24 FE", "phone", ["fe"], True),
    (r"\b(?:galaxy\s+)?s24\b", "S24", "phone", [], True),
    (r"\b(?:galaxy\s+)?s23\s+ultra\b", "S23 Ultra", "phone", ["ultra"], True),
    (r"\b(?:galaxy\s+)?s23\s*(?:plus|\+)\b", "S23 Plus", "phone", ["plus"], True),
    (r"\b(?:galaxy\s+)?s23\s+fe\b", "S23 FE", "phone", ["fe"], True),
    (r"\b(?:galaxy\s+)?s23\b", "S23", "phone", [], True),
    (r"\b(?:galaxy\s+)?a54\b", "A54", "phone", [], True),
    (r"\b(?:galaxy\s+)?m35\b", "M35", "phone", [], True),

    # Apple iPhone Series
    (r"\biphone\s+17\s+pro\s+max\b", "iPhone 17 Pro Max", "phone", ["pro", "max"], True),
    (r"\biphone\s+17\s+pro\b", "iPhone 17 Pro", "phone", ["pro"], True),
    (r"\biphone\s+17\s+plus\b", "iPhone 17 Plus", "phone", ["plus"], True),
    (r"\biphone\s+17\b", "iPhone 17", "phone", [], True),
    (r"\biphone\s+16\s+pro\s+max\b", "iPhone 16 Pro Max", "phone", ["pro", "max"], True),
    (r"\biphone\s+16\s+pro\b", "iPhone 16 Pro", "phone", ["pro"], True),
    (r"\biphone\s+16\s+plus\b", "iPhone 16 Plus", "phone", ["plus"], True),
    (r"\biphone\s+16e\b", "iPhone 16e", "phone", [], True),
    (r"\biphone\s+16\b", "iPhone 16", "phone", [], True),
    (r"\biphone\s+15\s+pro\s+max\b", "iPhone 15 Pro Max", "phone", ["pro", "max"], True),
    (r"\biphone\s+15\s+pro\b", "iPhone 15 Pro", "phone", ["pro"], True),
    (r"\biphone\s+15\s+plus\b", "iPhone 15 Plus", "phone", ["plus"], True),
    (r"\biphone\s+15\b", "iPhone 15", "phone", [], True),
    (r"\biphone\s+14\s+pro\s+max\b", "iPhone 14 Pro Max", "phone", ["pro", "max"], True),
    (r"\biphone\s+14\s+pro\b", "iPhone 14 Pro", "phone", ["pro"], True),
    (r"\biphone\s+14\s+plus\b", "iPhone 14 Plus", "phone", ["plus"], True),
    (r"\biphone\s+14\b", "iPhone 14", "phone", [], True),
    (r"\biphone\s+13\b", "iPhone 13", "phone", [], True),

    # Xiaomi / Redmi Note Series
    (r"\bredmi\s+note\s+14\s+pro\s*(?:\+|plus)\b", "Redmi Note 14 Pro+", "phone", ["pro", "plus"], True),
    (r"\bredmi\s+note\s+14\s+pro\+", "Redmi Note 14 Pro+", "phone", ["pro", "plus"], True),
    (r"\bredmi\s+note\s+14\s+pro\b", "Redmi Note 14 Pro", "phone", ["pro"], True),
    (r"\bredmi\s+note\s+14\b", "Redmi Note 14", "phone", [], True),
    (r"\bredmi\s+note\s+13\s+pro\s*(?:\+|plus)\b", "Redmi Note 13 Pro+", "phone", ["pro", "plus"], True),
    (r"\bredmi\s+note\s+13\s+pro\+", "Redmi Note 13 Pro+", "phone", ["pro", "plus"], True),
    (r"\bredmi\s+note\s+13\s+pro\b", "Redmi Note 13 Pro", "phone", ["pro"], True),
    (r"\bredmi\s+note\s+13\b", "Redmi Note 13", "phone", [], True),

    # Laptops
    (r"\b(?:hp\s+)?15s\b", "15s", "laptop", [], False),
    (r"\b(?:hp\s+)?pavilion\s+15\b", "Pavilion 15", "laptop", [], False),
    (r"\b(?:hp\s+)?pavilion\s+14\b", "Pavilion 14", "laptop", [], False),
    (r"\b(?:hp\s+)?pavilion\s+aero\b", "Pavilion Aero", "laptop", [], False),
    (r"\b(?:hp\s+)?pavilion\s+x360\b", "Pavilion x360", "laptop", [], False),
    (r"\b(?:hp\s+)?pavilion\b", "Pavilion", "laptop", [], False),
    (r"\b(?:ideapad\s+)?slim\s+3\b", "Slim 3", "laptop", [], False),
    (r"\bvivobook\s+15\b", "Vivobook 15", "laptop", [], False),
    (r"\baspire\s+lite\b", "Aspire Lite", "laptop", [], False),
    (r"\bloq\s+15\b", "LOQ 15", "laptop", [], False),
    (r"\bmacbook\s+air\s+m2\b", "MacBook Air M2", "laptop", [], False),

    # Footwear
    (r"\bair\s*max\s+270\b", "Air Max 270", "footwear", [], False),
    (r"\bair\s*max\s+90\b", "Air Max 90", "footwear", [], False),
    (r"\bair\s*max\s+97\b", "Air Max 97", "footwear", [], False),
    (r"\bair\s*max\s+95\b", "Air Max 95", "footwear", [], False),
    (r"\bair\s*max\s+sc\b", "Air Max SC", "footwear", [], False),
    (r"\bair\s*max\b", "Air Max", "footwear", [], False),

    # Audio & Wearables
    (r"\bwh-?1000xm5\b", "WH-1000XM5", "headphones", [], False),
    (r"\bwh-?1000xm4\b", "WH-1000XM4", "headphones", [], False),
    (r"\bwh-?ch520\b", "WH-CH520", "headphones", [], False),
    (r"\bwh-?ch720n?\b", "WH-CH720N", "headphones", [], False),
    (r"\btune\s+770nc\b", "Tune 770NC", "headphones", [], False),
    (r"\brockerz\s+450\b", "Rockerz 450", "headphones", [], False),
    (r"\bairdopes\s+141\b", "Airdopes 141", "headphones", [], False),
    (r"\bairdopes\s+170\b", "Airdopes 170", "headphones", [], False),
    (r"\bairpods\s+pro\s*(?:2)?\b", "AirPods Pro 2", "headphones", [], False),
    (r"\bgalaxy\s+watch\s+6\b", "Galaxy Watch 6", "watch", [], False),
]

ALL_MODIFIERS = ["ultra", "pro", "plus", "+", "max", "fe", "lite", "mini", "se"]

# Terms indicating accessories / spare parts / protection plans (must not pollute main product searches)
ACCESSORY_REGEX = re.compile(
    r"\b("
    r"back\s*cover|flip\s*cover|phone\s*case|mobile\s*case|clear\s*case|silicone\s*case|"
    r"leather\s*case|hard\s*case|carrying\s*case|travel\s*case|protective\s*case|"
    r"bumper\s*case|magsafe\s*case|case\s+for|cover\s+for|case\b|cover\b|bumper|"
    r"tempered\s*glass|screen\s*protector|screen\s*guard|lens\s*protector|camera\s*protector|"
    r"standing\s*grip|grip\s*case|wallet\s*case|folio|pouch|sleeve|"
    r"skin\b|decal|sticker|wrap\b|"
    r"charger\b|charging\s*cable|data\s*cable|usb\s*cable|power\s*adapter|power\s*bank|"
    r"ear\s*pads?|earpads?|ear\s*cushions?|replacement\s*ear|replacement\s*pad|"
    r"ear\s*tips?|eartips?|headband\s*cover|audio\s*cable|aux\s*cable|"
    r"keyboard\s*cover|keyboard\s*skin|laptop\s*bag|backpack|cooling\s*pad|"
    r"replacement\s*battery|battery\s*replacement|lcd\s*screen|display\s*combo|digitizer|"
    r"touch\s*screen\s*replacement|motherboard|hinge\b|fan\s*replacement|"
    r"watch\s*strap|watch\s*band|strap\s*for|band\s*for|"
    r"protection\s*plan|extended\s*warranty|insurance\s*plan|damage\s*protection|"
    r"dummy\s*phone|toy\s*phone|display\s*model|"
    r"shoelaces|shoe\s*laces|insole|insoles|shoe\s*cleaner|shoe\s*care|socks\b|"
    r"ring\s*box|jewelry\s*box|ring\s*sizer|ring\s*holder"
    r")\b",
    re.I,
)

ACCESSORY_BRANDS_OR_STORES = (
    "rhinoshield", "spigen", "caseology", "ringke", "otterbox", "casetify",
    "dbrand", "supcase", "torras", "dailyobjects", "kapaver", "glaz",
    "shinestar", "solidx", "airx", "mod nx",
)

HINDI_INSURANCE_MARKERS = ("संरक्षण योजना", "बीमा", "वारंटी")


def is_accessory_query(query: str) -> bool:
    """Returns True if the user explicitly searched for an accessory/spare part."""
    return bool(ACCESSORY_REGEX.search(query or ""))


def is_accessory_product(title: str, store: str = "") -> bool:
    """Returns True if a product listing is an accessory, spare part, or protection plan."""
    tl = (title or "").lower()
    sl = (store or "").lower()
    if ACCESSORY_REGEX.search(tl):
        return True
    if any(marker in tl for marker in HINDI_INSURANCE_MARKERS):
        return True
    if any(acc in sl for acc in ACCESSORY_BRANDS_OR_STORES):
        return True
    if any(re.search(r"\b" + re.escape(acc) + r"\b", tl) for acc in ACCESSORY_BRANDS_OR_STORES):
        return True
    # Titles starting with "For Samsung...", "Compatible with iPhone..."
    if re.match(r"^(?:for|compatible\s+with|fits)\s+", tl):
        return True
    return False


def extract_product_metadata(title: str, extensions: list[str] | None = None, snippet: str = "") -> dict[str, Any]:
    """
    Extracts structured category, model, specs, and tags from a live shopping listing title.
    Used by SerpApiAdapter so live results carry accurate metadata instead of 'category: other'.
    """
    raw_text = " ".join(filter(None, [title, " ".join(extensions or []), snippet]))
    norm_text = normalize_query(raw_text)
    tl = norm_text.lower()
    title_norm = normalize_query(title).lower()

    accessory = is_accessory_product(title)

    # 1. Model & Category hint
    model = ""
    category = ""
    for pat, norm_name, cat_hint, _mods, _strict in KNOWN_MODELS:
        if re.search(pat, title_norm):
            model = norm_name
            category = cat_hint
            break

    # 2. Product Type
    product_type = ""
    for ptype, triggers in PRODUCT_TYPES.items():
        for trigger in triggers:
            if re.search(r"\b" + re.escape(trigger) + r"\b", title_norm):
                product_type = ptype
                break
        if product_type:
            break

    # 3. Category fallback from product type or CATS_MAP
    if not category and product_type:
        ptype_to_cat = {
            "wireless earbuds": "headphones",
            "headphones": "headphones",
            "shoes": "footwear",
            "ring": "jewelry",
            "kurti": "clothing",
            "laptop": "laptop",
            "smartphone": "phone",
            "tablet": "tablet",
            "smartwatch": "watch",
            "tv": "television",
            "camera": "camera",
            "refrigerator": "appliances",
            "washing machine": "appliances",
            "air fryer": "appliances",
        }
        category = ptype_to_cat.get(product_type, "")

    if not category:
        for cat, triggers in CATS_MAP.items():
            if any(re.search(r"\b" + re.escape(t) + r"\b", title_norm) for t in triggers):
                category = cat
                break

    # Infer phone/laptop/headphones from strong hardware markers if still missing
    if not category:
        if re.search(r"\b(?:5g|dual\s*sim|snapdragon|exynos|dimensity|ios|android|amoled|mah)\b", title_norm):
            category = "phone"
        elif re.search(r"\b(?:windows\s*1[01]|intel\s*core|ryzen\s*[3579]|ssd|inches?\s*laptop)\b", title_norm):
            category = "laptop"
        elif re.search(r"\b(?:wh-|wf-|bluetooth\s*head|over-?ear|on-?ear|anc|noise\s*cancel)\b", title_norm):
            category = "headphones"
        elif re.search(r"\b(?:925\s*silver|sterling\s*silver|solitaire|gold\s*plated|zircon)\b", title_norm):
            category = "jewelry"
        elif re.search(r"\b(?:nike|adidas|puma|running|sneaker|trainers|air\s*max)\b", title_norm):
            category = "footwear"

    if not category:
        category = "other"

    # 4. Specs extraction
    specs: dict[str, str] = {}
    if product_type:
        specs["Product Type"] = product_type.title()

    # RAM & Storage patterns like "8GB/128GB", "8GB+128GB", "8GB RAM, 256GB", "16 GB/512 GB SSD"
    combo_match = re.search(r"\b(4|6|8|12|16|24|32)\s*(?:gb)?\s*[/+]\s*(64|128|256|512|1024)\s*(?:gb)?\b", title_norm)
    if combo_match:
        specs["RAM"] = f"{combo_match.group(1)} GB"
        specs["Storage"] = f"{combo_match.group(2)} GB"
    else:
        ram_m = re.search(r"\b(4|6|8|12|16|24|32|64)\s*gb\s*(?:ram|ddr\d|lpddr\d|unified|memory)\b", title_norm)
        if ram_m:
            specs["RAM"] = f"{ram_m.group(1)} GB"
        stor_m = re.search(r"\b(64|128|256|512|1024)\s*gb\b", title_norm)
        tb_m = re.search(r"\b(1|2)\s*tb\b", title_norm)
        if tb_m:
            specs["Storage"] = f"{tb_m.group(1)} TB"
        elif stor_m:
            specs["Storage"] = f"{stor_m.group(1)} GB"

    for proc in ["i3", "i5", "i7", "i9", "ryzen 3", "ryzen 5", "ryzen 7", "ryzen 9", "m1", "m2", "m3", "m4", "snapdragon", "exynos", "dimensity"]:
        if re.search(r"\b" + re.escape(proc) + r"\b", title_norm):
            specs["Processor"] = proc.upper()
            break

    for mat in MATERIALS:
        if re.search(r"\b" + re.escape(mat) + r"\b", title_norm):
            specs["Material"] = mat.title()
            break

    for col in COLOURS:
        if col in ("silver", "gold") and category == "jewelry":
            continue
        if re.search(r"\b" + re.escape(col) + r"\b", title_norm):
            specs["Colour"] = col.title()
            break

    if re.search(r"\b(women|womens|women's|woman|girls|girl|female|ladies)\b", title_norm):
        specs["Gender"] = "Women"
    elif re.search(r"\b(men|mens|men's|man|boys|boy|male|gents)\b", title_norm):
        specs["Gender"] = "Men"

    if re.search(r"\b(wireless|bluetooth|tws|true\s+wireless)\b", title_norm):
        specs["Connectivity"] = "Wireless Bluetooth"

    # 5. Tags
    tags = [category]
    if model:
        tags.append(model.lower())
    if product_type:
        tags.append(product_type.lower())
    if specs.get("Material"):
        tags.append(specs["Material"].lower())
    if specs.get("Gender"):
        tags.append(specs["Gender"].lower())
    if specs.get("Connectivity"):
        tags.append("wireless")
    if accessory:
        tags.append("accessory")

    return {
        "category": category,
        "model": model,
        "specs": specs,
        "tags": list(dict.fromkeys(tags)),
        "is_accessory": accessory,
    }


def normalize_query(query: str) -> str:
    """Normalizes spelling variations, model spacing, and common abbreviations."""
    q = query.strip()
    # Normalize unicode currency and symbols
    q = q.replace("₹", " ₹ ").replace("Rs.", " Rs ").replace("rs.", " rs ")
    # Normalize model prefixes like 's 24' -> 's24', 's 23' -> 's23'
    q = re.sub(r"\b([sSaAmM])\s+(\d{2,3})\b", r"\1\2", q)
    # Normalize 'iphone16' -> 'iphone 16', 'note14' -> 'note 14', 'airmax' -> 'air max'
    q = re.sub(r"\b(iphone)(\d{1,2})\b", r"\1 \2", q, flags=re.I)
    q = re.sub(r"\b(note)(\d{1,2})\b", r"\1 \2", q, flags=re.I)
    q = re.sub(r"\bairmax\b", "air max", q, flags=re.I)
    # Normalize 'wh 1000xm5' -> 'wh-1000xm5'
    q = re.sub(r"\bwh\s*1000xm([345])\b", r"wh-1000xm\1", q, flags=re.I)
    q = re.sub(r"\bwh\s*ch(\d{3}n?)\b", r"wh-ch\1", q, flags=re.I)
    # Normalize '16 gb' -> '16gb'
    q = re.sub(r"\b(\d+)\s+(gb|tb)\b", r"\1\2", q, flags=re.I)
    return re.sub(r"\s+", " ", q).strip()


def extract_budget(query: str) -> tuple[float | None, float | None]:
    """Extracts budget limits from natural language queries."""
    ql = query.lower()
    b_min, b_max = None, None

    # Range: 'between 20k and 30k'
    m_between = re.search(r"between\s*(?:rs\.?|inr|₹)?\s*([\d,\.]+)\s*(k|lakh|l)?\s*(?:and|to|-)\s*(?:rs\.?|inr|₹)?\s*([\d,\.]+)\s*(k|lakh|l)?\b", ql)
    if m_between:
        def _parse(val_str, unit):
            v = float(val_str.replace(",", ""))
            if unit == "k": return v * 1000.0
            if unit in ("l", "lakh"): return v * 100000.0
            return v
        b_min = _parse(m_between.group(1), m_between.group(2))
        b_max = _parse(m_between.group(3), m_between.group(4))
        return b_min, b_max

    # Max budget: 'under ₹50,000', 'below 25k', 'less than 60000', etc.
    pattern_max = r"(?:under|below|within|less than|upto|up to|budget(?: of)?|max)\s*(?:rs\.?|inr|₹)?\s*([\d,\.]+)\s*(k|lakh|l)?\b"
    m_max = re.search(pattern_max, ql)
    if not m_max:
        m_max = re.search(r"(?:rs\.?|inr|₹)\s*([\d,\.]+)\s*(k|lakh|l)?\b", ql)

    if m_max:
        try:
            raw_val = float(m_max.group(1).replace(",", ""))
            unit = (m_max.group(2) or "").lower()
            if unit == "k":
                b_max = raw_val * 1000.0
            elif unit in ("l", "lakh"):
                b_max = raw_val * 100000.0
            else:
                b_max = raw_val
        except ValueError:
            pass

    # Min budget: 'above 20000', 'over 10k', 'min 15000'
    pattern_min = r"(?:above|over|more than|minimum|min)\s*(?:rs\.?|inr|₹)?\s*([\d,\.]+)\s*(k|lakh|l)?\b"
    m_min = re.search(pattern_min, ql)
    if m_min:
        try:
            raw_val = float(m_min.group(1).replace(",", ""))
            unit = (m_min.group(2) or "").lower()
            if unit == "k":
                b_min = raw_val * 1000.0
            elif unit in ("l", "lakh"):
                b_min = raw_val * 100000.0
            else:
                b_min = raw_val
        except ValueError:
            pass

    return b_min, b_max


def extract_specs_from_query(query: str) -> dict[str, Any]:
    """Extracts technical specs like RAM, Storage, CPU, display flags from query."""
    specs: dict[str, Any] = {}
    ql = query.lower()

    # RAM extraction (e.g. '16gb ram', '16 gb ram', '8gb')
    ram_explicit = re.search(r"\b(\d+)\s*(?:gb|g)\s*(?:ram|memory)\b", ql)
    if ram_explicit:
        specs["ram_gb"] = int(ram_explicit.group(1))

    # Storage extraction (e.g. '256gb', '512gb ssd', '1tb')
    storage_explicit = re.search(r"\b(\d+)\s*(?:gb|tb)\s*(?:ssd|storage|rom)?\b", ql)
    if storage_explicit:
        val = int(storage_explicit.group(1))
        if not ram_explicit and val in (8, 16, 32) and any(w in ql for w in ["laptop", "notebook", "pc"]):
            specs["ram_gb"] = val
        elif val in (64, 128, 256, 512, 1024, 1, 2):
            specs["storage_gb"] = val * 1024 if "tb" in storage_explicit.group(0) or val in (1, 2) else val
            specs["storage"] = f"{val} TB" if "tb" in storage_explicit.group(0) else f"{val} GB"

    # Processor extraction
    for proc in ["i3", "i5", "i7", "i9", "ryzen 3", "ryzen 5", "ryzen 7", "m1", "m2", "m3", "snapdragon"]:
        if re.search(r"\b" + re.escape(proc) + r"\b", ql):
            specs["processor"] = proc.upper()
            break

    # Feature tags
    if any(w in ql for w in ["gaming", "gpu", "rtx", "graphics"]):
        specs["gaming"] = True
    if any(w in ql for w in ["programming", "coding", "developer"]):
        specs["programming"] = True
    if any(w in ql for w in ["camera", "photo", "photography"]):
        specs["camera"] = True
    if any(w in ql for w in ["battery", "long lasting", "backup"]):
        specs["battery"] = True
    if any(w in ql for w in ["anc", "noise cancel", "noise cancelling"]):
        specs["anc"] = True
    if any(w in ql for w in ["amoled", "oled", "120hz", "144hz"]):
        specs["display"] = True
    if re.search(r"\b(wireless|bluetooth|tws)\b", ql):
        specs["wireless"] = True

    return specs


def parse_query_intent(query: str, explicit_budget: float | None = None) -> dict[str, Any]:
    """
    Intelligent NLP query intent extraction.
    Parses: brand, model, required & forbidden modifiers, category, subcategory,
    product type, colour, material, size, RAM, storage, processor, budget bounds, gender.
    """
    normalized = normalize_query(query)
    ql_clean = normalized.lower()

    # 1. Budget extraction
    b_min, b_max = extract_budget(ql_clean)
    if explicit_budget is not None and explicit_budget > 0:
        b_max = explicit_budget

    # 2. Brand detection
    brand = None
    for alias, canonical in BRAND_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", ql_clean):
            brand = canonical
            break

    # 3. Model & Modifiers extraction
    model = None
    model_category = None
    required_modifiers: list[str] = []
    forbidden_modifiers: list[str] = []

    wants_accessory = is_accessory_query(query)

    for pat, norm_name, cat_hint, mods, strict_mods in KNOWN_MODELS:
        if re.search(pat, ql_clean):
            model = norm_name
            model_category = cat_hint
            required_modifiers = list(mods)
            if strict_mods and not wants_accessory:
                # Modifiers user did NOT ask for become forbidden for strict main-device models
                forbidden_modifiers = [m for m in ALL_MODIFIERS if m not in required_modifiers]
            else:
                forbidden_modifiers = []
            break

    # Infer brand from unmistakable model names if brand wasn't explicitly typed
    if not brand and model:
        ml = model.lower()
        if "iphone" in ml or "macbook" in ml or "airpods" in ml:
            brand = "Apple"
        elif ml.startswith(("s26", "s25", "s24", "s23", "a54", "m35", "galaxy")):
            brand = "Samsung"
        elif "redmi" in ml:
            brand = "Xiaomi"
        elif "pavilion" in ml:
            brand = "HP"
        elif "air max" in ml:
            brand = "Nike"
        elif ml.startswith("wh-"):
            brand = "Sony"

    # 4. Product Type
    product_type = None
    for ptype, triggers in PRODUCT_TYPES.items():
        for trigger in triggers:
            if re.search(r"\b" + re.escape(trigger) + r"\b", ql_clean):
                product_type = ptype
                break
        if product_type:
            break

    # 5. Category detection
    category = model_category
    if not category and product_type:
        if product_type in ("wireless earbuds", "headphones"):
            category = "headphones"
        elif product_type in ("shoes",):
            category = "footwear"
        elif product_type in ("ring",):
            category = "jewelry"
        elif product_type in ("kurti",):
            category = "clothing"
        elif product_type in ("laptop",):
            category = "laptop"
        elif product_type in ("smartphone",):
            category = "phone"
        elif product_type in ("tablet",):
            category = "tablet"
        elif product_type in ("smartwatch",):
            category = "watch"
        elif product_type in ("tv",):
            category = "television"
        elif product_type in ("camera",):
            category = "camera"
        elif product_type in ("refrigerator", "washing machine", "air fryer"):
            category = "appliances"

    if not category:
        for cat, triggers in CATS_MAP.items():
            if any(re.search(r"\b" + re.escape(t) + r"\b", ql_clean) for t in triggers):
                category = cat
                break

    # 6. Material detection
    material = None
    for mat in MATERIALS:
        if re.search(r"\b" + re.escape(mat) + r"\b", ql_clean):
            material = mat
            break

    # 7. Colour detection
    colour = None
    for col in COLOURS:
        # Avoid treating "silver" or "gold" as colour if they are acting as material for jewelry
        if col in ("silver", "gold") and category == "jewelry":
            continue
        if re.search(r"\b" + re.escape(col) + r"\b", ql_clean):
            colour = col
            break

    # 8. Gender detection
    gender = None
    if re.search(r"\b(women|womens|women\'s|woman|girls|girl|female|ladies)\b", ql_clean):
        gender = "women"
    elif re.search(r"\b(men|mens|men\'s|man|boys|boy|male|gents)\b", ql_clean):
        gender = "men"

    # 9. Numerical Specs
    specs = extract_specs_from_query(ql_clean)

    # Keywords without stop words
    stop_words = {"under", "below", "with", "best", "for", "the", "and", "good", "need", "i", "want", "find", "all"}
    keywords = [w for w in re.findall(r"[a-z0-9]+", ql_clean) if len(w) > 1 and w not in stop_words]

    return {
        "raw_query": query,
        "brand": brand,
        "model": model,
        "required_modifiers": required_modifiers,
        "forbidden_modifiers": forbidden_modifiers,
        "category": category,
        "product_type": product_type,
        "material": material,
        "colour": colour,
        "gender": gender,
        "budget_min": b_min,
        "budget_max": b_max,
        "specs": specs,
        "keywords": keywords,
        "wants_accessory": is_accessory_query(query),
    }


def parse_query_rule(query: str) -> dict[str, Any]:
    """Compatibility wrapper returning structured intent."""
    return parse_query_intent(query)


async def extract_search_intent(query: str, explicit_budget: float | None = None) -> dict[str, Any]:
    """
    Two-layer NLP intent extractor:
    1. Attempts LLM intent extraction (Google Gemini API) if configured.
    2. Runs deterministic high-precision rule extraction.
    3. Merges attributes to guarantee strict consistency.
    """
    rule_intent = parse_query_intent(query, explicit_budget)

    # Check Gemini API
    from .llm import extract_intent_with_gemini
    try:
        gemini_data = await extract_intent_with_gemini(query)
        if gemini_data:
            # Safely merge gemini attributes if not detected by rules
            if not rule_intent.get("brand") and gemini_data.get("brand"):
                rule_intent["brand"] = gemini_data["brand"]
            if not rule_intent.get("category") and gemini_data.get("category"):
                rule_intent["category"] = gemini_data["category"]
            if not rule_intent.get("product_type") and gemini_data.get("product_type"):
                rule_intent["product_type"] = gemini_data["product_type"]
            if not rule_intent.get("material") and gemini_data.get("material"):
                rule_intent["material"] = str(gemini_data["material"]).lower()
            if not rule_intent.get("colour") and gemini_data.get("colour"):
                rule_intent["colour"] = str(gemini_data["colour"]).lower()
            if not rule_intent.get("gender") and gemini_data.get("gender"):
                rule_intent["gender"] = str(gemini_data["gender"]).lower()
            if not rule_intent.get("budget_max") and gemini_data.get("budget_max"):
                rule_intent["budget_max"] = float(gemini_data["budget_max"])
            if gemini_data.get("ram_gb") and "ram_gb" not in rule_intent.get("specs", {}):
                rule_intent.setdefault("specs", {})["ram_gb"] = int(gemini_data["ram_gb"])
            if gemini_data.get("storage_gb") and "storage_gb" not in rule_intent.get("specs", {}):
                rule_intent.setdefault("specs", {})["storage_gb"] = int(gemini_data["storage_gb"])
    except Exception as e:
        log.warning("Gemini intent integration note: %s", e)

    return rule_intent


def _min_price_floor(req: dict) -> float:
    """
    Minimum realistic price floor (INR) for non-accessory main products.
    Prevents phone cases, protection plans, spare batteries, or replacement earpads
    from slipping into main device searches even if their title omits the word 'case'.
    """
    if req.get("wants_accessory"):
        return 0.0
    cat = (req.get("category") or "").lower()
    model = (req.get("model") or "").lower()
    brand = (req.get("brand") or "").lower()
    if cat == "phone":
        if any(flag in model for flag in ("iphone 16", "iphone 17", "iphone 15", "iphone 14", "s26", "s25", "s24", "s23")):
            return 18000.0
        return 5000.0
    if cat == "laptop":
        return 15000.0
    if cat == "footwear" and ("air max" in model or brand == "nike"):
        return 1500.0
    if cat == "headphones" and brand in ("sony", "bose", "apple", "sennheiser", "jbl"):
        return 900.0
    return 0.0


def matches_strict_filters(product: dict, req: dict) -> tuple[bool, str]:
    """
    Strictly validates whether product satisfies all mandatory search conditions:
    - Accessory / spare-part exclusion (unless user explicitly asked for one)
    - Exact brand matching
    - Exact model matching and modifier/generation exclusion
    - Correct category matching
    - Correct product type matching (including wireless headphones & footwear)
    - Correct colour and material matching (including silver vs gold-plated exclusion)
    - Respect numerical specifications (RAM, storage, processor)
    - Respect budget range (min & max)
    - Respect intended gender
    """
    p_name = normalize_query(product.get("name", "")).lower()
    p_raw_name = product.get("name", "").lower()
    p_brand = product.get("brand", "").lower()
    p_cat = product.get("category", "").lower()
    p_model = normalize_query(product.get("model", "")).lower()
    p_specs = product.get("specs") or {}
    p_specs_str = " ".join(f"{k} {v}" for k, v in p_specs.items()).lower()
    p_tags = " ".join(str(t) for t in product.get("tags") or []).lower()
    p_price = float(product.get("price", product.get("base_price", 0)) or 0)
    p_store = str((product.get("best_offer") or {}).get("store") or "")
    p_source = str(product.get("source") or "")

    # 0. Reject accessories / cases / protection plans / spare parts unless user asked for one
    if not req.get("wants_accessory"):
        if product.get("is_accessory") or is_accessory_product(p_raw_name, p_store):
            return False, f"Accessory/spare part excluded: '{product.get('name')}'"
        min_floor = _min_price_floor(req)
        if min_floor > 0 and 0 < p_price < min_floor:
            return False, f"Price ₹{p_price:,} below realistic main-product floor ₹{min_floor:,} (likely accessory/plan)"

    # 1. Exact Brand Matching
    req_brand = req.get("brand")
    if req_brand:
        canonical_req = req_brand.lower()
        brand_aliases_ok = {canonical_req}
        if canonical_req == "xiaomi":
            brand_aliases_ok.add("redmi")
        elif canonical_req == "apple":
            brand_aliases_ok.update({"iphone", "ipad", "macbook", "airpods"})
        elif canonical_req == "samsung":
            brand_aliases_ok.add("galaxy")
        if not any(b in p_brand or re.search(r"\b" + re.escape(b) + r"\b", p_name) for b in brand_aliases_ok):
            return False, f"Brand mismatch: requested '{req_brand}', got '{product.get('brand')}'"

    # 2. Correct Category Matching (Word boundary for tags to avoid 'earphones' matching 'phone')
    req_cat = req.get("category")
    if req_cat:
        cat_match = (req_cat == p_cat) or bool(re.search(r"\b" + re.escape(req_cat) + r"\b", p_tags))
        if not cat_match:
            # For live results whose category isn't in our 11 predefined buckets (p_cat == "other"),
            # allow if the live title explicitly matches core query keywords (e.g. speaker, wallet, chair)
            # and the user did not request a strict known product_type.
            allow_live_other = False
            if p_source == "live" and p_cat == "other" and not req.get("product_type"):
                core_kws = [
                    kw for kw in req.get("keywords", [])
                    if not kw.isdigit() and kw not in (
                        "under", "below", "above", "over", "men", "women", "mens", "womens",
                        "best", "good", "cheap", "new", "latest", "buy", "online",
                    )
                ]
                if core_kws and any(re.search(r"\b" + re.escape(kw) + r"\b", p_name) for kw in core_kws):
                    allow_live_other = True
            if not allow_live_other:
                return False, f"Category mismatch: requested '{req_cat}', got '{p_cat}'"

    # 3. Correct Product Type Matching
    req_ptype = req.get("product_type")
    if req_ptype:
        p_ptype = str(p_specs.get("Product Type", "")).lower()
        combined_text = (p_name + " " + p_ptype + " " + p_specs_str + " " + p_tags).lower()
        if req_ptype == "wireless earbuds":
            is_earbuds = (
                "wireless earbuds" in p_ptype or "tws" in p_ptype or "airdopes" in p_name
                or "earbuds" in p_name or "earbud" in p_name or "tws" in p_name
                or "in-ear truly wireless" in p_specs_str or "true wireless in-ear" in p_specs_str
            )
            is_headphones = ("on-ear" in combined_text or "over-ear" in combined_text or "headphones" in p_name) and "airdopes" not in p_name and "earbud" not in p_name
            if not is_earbuds or is_headphones:
                return False, "Product type mismatch: requested wireless earbuds, got headphones/other"
        elif req_ptype == "headphones":
            hp_text = (p_name + " " + p_ptype + " " + p_specs_str).lower()
            is_hp = any(w in hp_text for w in ("headphones", "headphone", "headset", "over-ear", "on-ear", "wh-1000", "wh-ch", "ult wear"))
            is_earbuds_only = (
                any(w in p_name for w in ("earbuds", "earbud", "tws", "truly wireless", "airdopes", "airpods", "wf-"))
                and "headphone" not in p_name
                and "headset" not in p_name
            )
            if not is_hp or is_earbuds_only:
                return False, "Product type mismatch: not headphones"
            # If user asked specifically for wireless headphones, reject wired-only headphones
            if req.get("specs", {}).get("wireless"):
                has_wireless = any(
                    w in hp_text
                    for w in ("wireless", "bluetooth", "wh-1000", "wh-ch", "ult wear", "anc", "tune 770", "rockerz")
                )
                is_wired_only = ("wired" in p_name) and not ("wireless" in p_name or "bluetooth" in p_name)
                if not has_wireless or is_wired_only:
                    return False, "Product type mismatch: requested wireless headphones, got wired/other"
        elif req_ptype == "shoes":
            is_shoe = (
                p_cat == "footwear"
                or any(w in combined_text for w in ("shoe", "shoes", "sneaker", "sneakers", "trainer", "trainers", "footwear", "air max", "running"))
            )
            if not is_shoe:
                return False, "Product type mismatch: not shoes/footwear"
        elif req_ptype == "smartphone":
            if p_cat != "phone" and "phone" not in combined_text and "smartphone" not in combined_text:
                return False, "Product type mismatch: not a smartphone"
        elif req_ptype == "laptop":
            if p_cat != "laptop" and "laptop" not in combined_text and "notebook" not in combined_text:
                return False, "Product type mismatch: not a laptop"
        elif req_ptype == "tablet":
            if p_cat != "tablet" and "tablet" not in combined_text and "ipad" not in combined_text:
                return False, "Product type mismatch: not a tablet"
        elif req_ptype == "smartwatch":
            if p_cat != "watch" and "watch" not in combined_text:
                return False, "Product type mismatch: not a smartwatch"
        elif req_ptype == "refrigerator":
            if "refrigerator" not in combined_text and "fridge" not in combined_text:
                return False, "Product type mismatch: not a refrigerator"
        elif req_ptype == "washing machine":
            if "washing machine" not in combined_text:
                return False, "Product type mismatch: not a washing machine"
        elif req_ptype == "air fryer":
            if "air fryer" not in combined_text:
                return False, "Product type mismatch: not an air fryer"
        elif req_ptype == "tv":
            if p_cat != "television" and "tv" not in combined_text and "television" not in combined_text:
                return False, "Product type mismatch: not a television"
        elif req_ptype == "camera":
            if p_cat != "camera" and "camera" not in combined_text:
                return False, "Product type mismatch: not a camera"
        elif req_ptype == "ring":
            if "ring" not in p_ptype and not re.search(r"\brings?\b", p_name):
                return False, "Product type mismatch: not a ring"
        elif req_ptype == "kurti":
            if not re.search(r"\b(kurti|kurtis|kurta|kurtas)\b", p_ptype + " " + p_name):
                return False, "Product type mismatch: not a kurti/kurta"

    # 4. Correct Material Matching
    req_mat = req.get("material")
    if req_mat:
        p_mat = (
            str(p_specs.get("Material", "")).lower() + " "
            + str(p_specs.get("Fabric", "")).lower() + " "
            + str(p_specs.get("Metal Type", "")).lower() + " "
            + str(p_specs.get("Stone", "")).lower() + " "
            + p_name + " " + p_tags
        )
        if not re.search(r"\b" + re.escape(req_mat) + r"\b", p_mat):
            return False, f"Material mismatch: requested '{req_mat}', not present in product"
        if req_mat == "silver":
            # Reject gold-plated / rose gold / yellow gold items when searching for silver
            gold_finish_pat = r"\b(gold[\s-]*plated|rose\s+gold|yellow\s+gold|14k\s*gold|18k\s*gold|22k\s*gold|gold\s+ring|gold\s+tone|gold\s+finish|golden)\b"
            if re.search(gold_finish_pat, p_mat):
                return False, "Material mismatch: product has gold finish/plating, not pure silver look"
            if "gold" in p_mat and "silver" not in p_mat:
                return False, "Material mismatch: product is gold, not silver"
        if req_mat == "gold":
            if "silver" in p_mat and "gold" not in p_mat:
                return False, "Material mismatch: product is silver, not gold"
        if req_mat == "cotton" and any(syn in p_mat for syn in ["silk", "rayon", "polyester"]) and "cotton" not in p_mat:
            return False, "Material mismatch: product is not cotton"

    # 5. Correct Colour Matching (strict word boundary so 'embroidered'/'flared'/'collared' never match 'red')
    req_col = req.get("colour")
    if req_col:
        p_col_spec = str(p_specs.get("Colour", "")).lower().strip()
        p_col_text = f"{p_col_spec} {p_name}"
        col_pat = r"\b" + re.escape(req_col) + r"\b"
        if not re.search(col_pat, p_col_text):
            return False, f"Colour mismatch: requested '{req_col}', product does not have exact colour word"
        # If product has an explicit Colour spec that contradicts requested colour, reject
        if p_col_spec and not re.search(col_pat, p_col_spec):
            return False, f"Colour mismatch: product colour spec is '{p_col_spec}', not '{req_col}'"
        # Reject listings whose primary/leading colour is a different conflicting colour (e.g. 'White Kurta with Red Print')
        req_pos_m = re.search(col_pat, p_name)
        if req_pos_m:
            req_pos = req_pos_m.start()
            # Treat close shades as compatible (e.g. grey/gray, off-white/white, maroon/red)
            compatible = {
                "grey": {"gray"}, "gray": {"grey"},
                "white": {"off-white", "ivory", "cream"},
                "off-white": {"white", "ivory", "cream"},
                "red": {"maroon"}, "maroon": {"red"},
                "blue": {"navy"}, "navy": {"blue"},
            }
            ok_cols = {req_col} | compatible.get(req_col, set())
            for other_col in COLOURS:
                if other_col in ok_cols:
                    continue
                other_m = re.search(r"\b" + re.escape(other_col) + r"\b", p_name)
                if other_m and other_m.start() < req_pos:
                    return False, f"Primary colour mismatch: '{other_col}' appears before '{req_col}' in '{product.get('name')}'"

    # 6. Correct Gender Matching
    req_gender = req.get("gender")
    if req_gender:
        p_gender = str(p_specs.get("Gender", "")).lower() + " " + p_name + " " + p_tags
        has_women = bool(re.search(r"\b(women|womens|women's|woman|ladies|girls|girl|female|unisex)\b", p_gender))
        has_men = bool(re.search(r"\b(men|mens|men's|man|gents|boys|boy|male|unisex)\b", p_gender))
        if p_source == "live":
            # For live retail titles (often truncated), strictly reject opposite-gender listings
            if req_gender == "women" and has_men and not has_women:
                return False, f"Gender mismatch: requested for women, got men's listing '{product.get('name')}'"
            if req_gender == "men" and has_women and not has_men:
                return False, f"Gender mismatch: requested for men, got women's listing '{product.get('name')}'"
        else:
            if req_gender == "women" and not has_women:
                return False, f"Gender mismatch: requested for women, got '{p_gender}'"
            if req_gender == "men" and not has_men:
                return False, f"Gender mismatch: requested for men, got '{p_gender}'"

    # 7. Exact Model Matching, Generation Isolation, and Forbidden Modifiers
    req_model = req.get("model")
    if req_model:
        title_and_model = f"{p_name} {p_model}"

        # Check required modifiers (e.g. 'ultra' in 'S24 Ultra', 'pro' in 'iPhone 16 Pro')
        for req_mod in req.get("required_modifiers", []):
            if req_mod == "plus":
                has_plus = bool(
                    re.search(r"\bplus\b", title_and_model)
                    or re.search(r"(?:s2\d|s\d{2}|pro|note\s*\d+|iphone\s*\d+)\s*\+", title_and_model)
                )
                if not has_plus:
                    return False, f"Model modifier mismatch: missing required modifier 'plus/+'"
            else:
                if not re.search(r"\b" + re.escape(req_mod) + r"\b", title_and_model):
                    return False, f"Model modifier mismatch: missing required modifier '{req_mod}'"

        # Check forbidden modifiers (e.g. if user asked for S24, product must NOT contain ultra, plus, fe)
        for forb_mod in req.get("forbidden_modifiers", []):
            if forb_mod == "+":
                # Only treat '+' as a model modifier when attached to a model token (NOT '8GB+128GB')
                if re.search(r"(?:s2\d|s\d{2}|pro|note\s*\d+|iphone\s*\d+|a\d{2}|m\d{2})\s*\+", p_raw_name) or "+" in p_model:
                    return False, f"Forbidden modifier '+' present in product '{product.get('name')}'"
            else:
                if re.search(r"\b" + re.escape(forb_mod) + r"\b", p_name) or re.search(r"\b" + re.escape(forb_mod) + r"\b", p_model):
                    return False, f"Forbidden modifier '{forb_mod}' present in product '{product.get('name')}'"

        # Generic base model token matching (works for ALL models: S24, iPhone 16 Pro, Redmi Note 14, Pavilion 15, Air Max, etc.)
        req_base = req_model.lower()
        mod_set = set(req.get("required_modifiers", [])) | {"+"}
        # Strip modifier words already checked above to verify core model tokens
        core_tokens = [
            tok for tok in re.findall(r"[a-z0-9]+", req_base)
            if tok not in mod_set and tok not in ("galaxy",)
        ]
        # Handle hyphenated models like WH-1000XM5 -> match either 'wh-1000xm5' or 'wh1000xm5'
        compact_target = re.sub(r"[\s-]+", "", title_and_model)
        compact_req = re.sub(r"[\s-]+", "", req_base.replace("+", "plus"))
        if compact_req not in compact_target:
            for tok in core_tokens:
                if not re.search(r"\b" + re.escape(tok) + r"\b", title_and_model):
                    # Also allow compact brand+model typos like 'samsunggalaxys24' only if exact token is inside it
                    if not (tok.startswith(("s2", "s1")) and tok in compact_target):
                        return False, f"Model mismatch: requested '{req_model}' (missing '{tok}'), got '{product.get('name')}'"

        # Cross-generation isolation: prevent e.g. S25/S26/S23 matching S24, or iPhone 15/16e matching iPhone 16
        s_gen = re.search(r"\bs(2\d)\b", req_base)
        if s_gen:
            other_s = re.findall(r"\bs(2\d)\b", title_and_model)
            if any(g != s_gen.group(1) for g in other_s):
                return False, f"Model generation mismatch: requested S{s_gen.group(1)}, got '{product.get('name')}'"

        ip_gen = re.search(r"\biphone\s+(\d{2})(e?)\b", req_base)
        if ip_gen:
            other_ip = re.findall(r"\biphone\s+(\d{2})(e?)\b", title_and_model)
            if not other_ip or any(g != (ip_gen.group(1), ip_gen.group(2)) for g in other_ip):
                return False, f"Model generation mismatch: requested iPhone {ip_gen.group(1)}{ip_gen.group(2)}, got '{product.get('name')}'"

        rn_gen = re.search(r"\bnote\s+(\d{1,2})\b", req_base)
        if rn_gen:
            other_rn = re.findall(r"\bnote\s+(\d{1,2})\b", title_and_model)
            if not other_rn or any(g != rn_gen.group(1) for g in other_rn):
                return False, f"Model generation mismatch: requested Note {rn_gen.group(1)}, got '{product.get('name')}'"

    # 8. Numerical Specs (RAM, Storage, Processor)
    spec_reqs = req.get("specs", {})
    # RAM
    req_ram = spec_reqs.get("ram_gb")
    if req_ram:
        p_ram_val = p_specs.get("RAM") or p_specs.get("Memory")
        p_ram_match = re.search(r"(\d+)\s*(?:gb|g)\b", str(p_ram_val).lower()) if p_ram_val else re.search(r"\b(\d+)\s*(?:gb|g)\s*(?:ram|memory|unified)\b", p_specs_str + " " + p_name)
        if not p_ram_match:
            return False, f"RAM requirement of {req_ram}GB not specified on product"
        p_ram = int(p_ram_match.group(1))
        if p_ram < req_ram:
            return False, f"RAM constraint violated: product has {p_ram}GB < required {req_ram}GB"

    # Storage
    req_storage = spec_reqs.get("storage_gb")
    if req_storage:
        p_storage_val = p_specs.get("Storage") or p_specs.get("ROM") or p_specs.get("SSD")
        p_storage_match = re.search(r"(\d+)\s*(?:gb|tb)\b", str(p_storage_val).lower()) if p_storage_val else (re.search(r"\b(64|128|256|512|1024)\s*gb\b", p_name) or re.search(r"\b(1|2)\s*tb\b", p_name))
        if not p_storage_match:
            return False, f"Storage requirement of {req_storage}GB not found"
        p_storage = int(p_storage_match.group(1))
        if "tb" in p_storage_match.group(0).lower():
            p_storage *= 1024
        if p_storage != req_storage:
            return False, f"Storage constraint violated: product has {p_storage}GB != required {req_storage}GB"

    # Processor
    req_proc = spec_reqs.get("processor")
    if req_proc:
        proc_str = (str(p_specs.get("Processor", "")) + " " + p_name).upper()
        if req_proc not in proc_str:
            return False, f"Processor mismatch: requested '{req_proc}', got '{p_specs.get('Processor')}'"

    # 9. Budget Constraint
    budget_max = req.get("budget_max")
    if budget_max is not None and budget_max > 0:
        if p_price > budget_max:
            return False, f"Price ₹{p_price:,} exceeds maximum budget ₹{budget_max:,}"

    budget_min = req.get("budget_min")
    if budget_min is not None and budget_min > 0:
        if p_price < budget_min:
            return False, f"Price ₹{p_price:,} below minimum budget ₹{budget_min:,}"

    # 10. Explicit target entity check (e.g. pets, vehicles, or unrelated entities)
    for kw in req.get("keywords", []):
        if kw in ("cats", "cat", "dog", "dogs", "pet", "pets", "cycle", "bike", "car"):
            combined = (p_name + " " + p_tags + " " + p_specs_str).lower()
            if not re.search(r"\b" + re.escape(kw) + r"\b", combined):
                return False, f"Explicit entity '{kw}' not supported by product"
        elif kw in ("shoes", "shoe"):
            combined = (p_name + " " + p_tags + " " + p_specs_str).lower()
            if p_cat != "footwear" and not any(w in combined for w in ("shoe", "shoes", "sneaker", "sneakers", "footwear", "air max")):
                return False, f"Explicit entity '{kw}' not supported by product"

    return True, "Passed all mandatory filters"


ACRONYMS = {"ram": "RAM", "cpu": "CPU", "gpu": "GPU", "os": "OS", "ssd": "SSD", "anc": "ANC", "fhd": "FHD", "uhd": "UHD"}

# Trusted Indian retailers & official brand stores with standard Indian delivery/policy metadata
TRUSTED_INDIAN_STORE_PROFILES: list[tuple[tuple[str, ...], dict[str, str]]] = [
    (
        ("amazon",),
        {
            "default_delivery": "1–2 Days · Free Delivery",
            "return_policy": "7-Day Service Center Replacement",
            "warranty": "Official Brand Warranty",
        },
    ),
    (
        ("flipkart",),
        {
            "default_delivery": "1–3 Days · Open-Box Delivery",
            "return_policy": "7-Day Replacement Policy",
            "warranty": "Official Brand Warranty",
        },
    ),
    (
        ("croma",),
        {
            "default_delivery": "1–2 Days / Store Pickup",
            "return_policy": "7-Day Return & Replacement",
            "warranty": "Official Brand Warranty",
        },
    ),
    (
        ("reliance", "jiomart"),
        {
            "default_delivery": "1–3 Days · Free Delivery",
            "return_policy": "7-Day Replacement · ResQ Support",
            "warranty": "Official Brand Warranty",
        },
    ),
    (
        ("vijay sales", "tata cliq", "poorvika", "sangeetha", "lot mobiles", "pai international"),
        {
            "default_delivery": "2–4 Days · Pan-India Shipping",
            "return_policy": "7-Day Replacement Policy",
            "warranty": "Official Brand Warranty",
        },
    ),
    (
        ("myntra", "ajio", "nykaa", "biba", "w for woman", "westside"),
        {
            "default_delivery": "2–4 Days · Standard Delivery",
            "return_policy": "14-Day Easy Return & Exchange",
            "warranty": "Authentic Brand Guarantee",
        },
    ),
    (
        ("giva", "caratlane", "tanishq", "candere", "kalyan", "bluestone"),
        {
            "default_delivery": "2–4 Days · Insured Shipping",
            "return_policy": "15–30 Day Return & Exchange",
            "warranty": "BIS / Authenticity Certified",
        },
    ),
    (
        (
            "samsung", "apple", "hp", "dell", "lenovo", "asus", "acer", "sony", "shopatsc",
            "xiaomi", "mi.com", "oneplus", "motorola", "boat", "noise", "jbl", "lg", "canon",
            "philips", "nike", "adidas", "puma",
        ),
        {
            "default_delivery": "2–4 Days · Official Brand Shipping",
            "return_policy": "Official Brand Return Policy",
            "warranty": "Official Manufacturer Warranty",
        },
    ),
]

REFURBISHED_MARKERS = (
    "refurbished", "refurb", "renewed", "renewd", "pre-owned", "pre owned",
    "pre-loved", "second hand", "second-hand", "used", "good condition",
    "fair condition", "superb condition", "open box", "cashify", "sahivalue",
    "controlz", "ovantica", "budli", "2gud", "back market", "refurbed",
)

FOREIGN_STORE_MARKERS = (
    "ubuy", "desertcart", "etoren", "refurbed", "ebay", "walmart", "bestbuy",
    "best buy", "shopee", "aliexpress", "dx.com", "newegg", "bhphotovideo",
    "target.com", "swappa", "backmarket",
)


def enrich_offer_metadata(offer: dict, product_name: str = "") -> dict:
    """
    Enriches a retailer offer with Trusted Indian Store status, condition flags,
    real SerpAPI delivery text (when provided), and standard Indian return/warranty metadata.
    """
    o = dict(offer)
    store_raw = str(o.get("store") or "Online").strip()
    store_l = store_raw.lower()
    url_l = str(o.get("url") or "").lower()
    name_l = str(product_name or "").lower()
    cond_l = str(o.get("condition") or "").lower()

    is_foreign = any(m in store_l or m in url_l for m in FOREIGN_STORE_MARKERS)
    is_refurbished = (
        any(re.search(r"\b" + re.escape(m) + r"\b", f"{store_l} {cond_l}") for m in REFURBISHED_MARKERS)
        or any(
            re.search(r"\b" + re.escape(m) + r"\b", name_l)
            for m in ("refurbished", "refurb", "renewed", "pre-owned", "second hand", "second-hand", "good condition", "used")
        )
    )

    matched_profile = None
    if not is_foreign and not is_refurbished:
        for patterns, profile in TRUSTED_INDIAN_STORE_PROFILES:
            if any(re.search(r"\b" + re.escape(pat) + r"\b", store_l) for pat in patterns):
                matched_profile = profile
                break

    is_trusted = matched_profile is not None
    live_delivery = str(o.get("delivery") or "").strip()

    if is_refurbished:
        badge = "Refurbished / Used"
        delivery = live_delivery or "3–6 Days · Seller Delivery"
        return_policy = "Check Refurbished Return Policy"
        warranty = "Seller Warranty (Verify)"
    elif is_foreign:
        badge = "International Seller"
        delivery = live_delivery or "7–14 Days · Intl. Shipping"
        return_policy = "International Return Policy"
        warranty = "Verify India Warranty"
    elif is_trusted:
        badge = "✓ Trusted Store"
        delivery = live_delivery or matched_profile["default_delivery"]
        return_policy = matched_profile["return_policy"]
        warranty = matched_profile["warranty"]
    else:
        badge = "Online Retailer"
        delivery = live_delivery or "3–5 Days · Standard Delivery"
        return_policy = "Check Store Return Policy"
        warranty = "Verify Seller Warranty"

    o["is_trusted"] = is_trusted
    o["is_refurbished"] = is_refurbished
    o["is_foreign"] = is_foreign
    o["store_badge"] = badge
    o["delivery"] = delivery
    o["return_policy"] = return_policy
    o["warranty"] = warranty
    return o


def normalize_spec_key(k: str) -> str:
    kl = str(k).strip().lower()
    return ACRONYMS.get(kl, str(k).strip().title())


def standardize(p: dict) -> dict:
    p["specs"] = {normalize_spec_key(k): str(v).strip() for k, v in (p.get("specs") or {}).items()}
    p["tags"] = [str(t).lower() for t in (p.get("tags") or [])]
    enriched = [
        enrich_offer_metadata(o, p.get("name", ""))
        for o in (p.get("offers") or [])
        if o.get("price", 0) > 0
    ]
    # Sort offers: cheapest price first, preferring trusted Indian stores on close/equal prices
    p["offers"] = sorted(enriched, key=lambda o: (o.get("is_refurbished", False), o.get("is_foreign", False), o["price"], not o.get("is_trusted", False)))
    return p


def compare_prices(p: dict) -> dict:
    """Calculates lowest price across stores, trusted store priority, price differences, and discount values."""
    offers = p.get("offers", [])
    if not offers:
        p["best_offer"] = {"store": "Online", "price": 0, "url": "", "in_stock": False, "is_trusted": False}
        p["price"] = 0
        p["savings"] = 0
        p["lowest_price"] = 0
        p["highest_price"] = 0
        p["has_trusted_offer"] = False
        p["is_refurbished"] = False
        p["is_foreign_only"] = False
        p["best_trusted_offer"] = None
        return p

    # Select lowest price offer (prefer brand-new offers if any exist alongside refurbished ones),
    # and identify best trusted Indian store offer
    new_offers = [o for o in offers if not o.get("is_refurbished")]
    pool_for_best = new_offers if new_offers else offers
    best = min(pool_for_best, key=lambda o: (o["price"], not o.get("is_trusted", False)))
    trusted_offers = [o for o in offers if o.get("is_trusted")]
    best_trusted = min(trusted_offers, key=lambda o: o["price"]) if trusted_offers else None

    for o in offers:
        o["is_cheapest"] = (o["price"] == best["price"] and o.get("is_refurbished") == best.get("is_refurbished"))
        o["is_best_value"] = bool(best_trusted and o is best_trusted) or (not best_trusted and o is best)

    p["best_offer"] = best
    p["best_trusted_offer"] = best_trusted
    p["has_trusted_offer"] = bool(trusted_offers)
    p["is_refurbished"] = all(o.get("is_refurbished", False) for o in offers) or any(
        re.search(r"\b" + re.escape(m) + r"\b", str(p.get("name", "")).lower())
        for m in ("refurbished", "refurb", "renewed", "pre-owned", "second hand", "second-hand", "good condition", "used")
    )
    p["is_foreign_only"] = all(o.get("is_foreign", False) for o in offers)
    p["price"] = best["price"]
    p["lowest_price"] = best["price"]
    p["highest_price"] = max(o["price"] for o in offers)
    p["savings"] = max(0, p["highest_price"] - p["lowest_price"])
    return p


def apply_budget_and_filters(products: list[dict], req: dict) -> list[dict]:
    """
    Strictly applies mandatory product filters.
    Discards any products violating brand, model, category, product type,
    material, colour, numerical specifications, or budget limits.
    """
    filtered = []
    for p in products:
        ok, reason = matches_strict_filters(p, req)
        if not ok:
            continue

        p["over_budget"] = False
        p["over_by"] = 0
        p["ram_compliant"] = True
        p["relevance_score"] = 1.0
        p["match_level"] = "exact_match"

        filtered.append(p)

    return filtered


def rank(products: list[dict], req: dict, prefs: dict) -> list[dict]:
    """
    Multi-criteria ranking for matching products:
    - Price competitiveness
    - Star rating
    - Review sentiment
    - Exact model alignment
    """
    if not products:
        return []

    prices = [p["price"] for p in products if p["price"] > 0]
    lo = min(prices) if prices else 0
    hi = max(prices) if prices else 1

    brands = prefs.get("brands", {}) if isinstance(prefs, dict) else {}
    pref_brand = max(brands, key=brands.get) if brands else None

    trusted_retailers = (
        "amazon", "flipkart", "croma", "reliance", "vijay sales", "tata cliq",
        "jiomart", "myntra", "ajio", "nykaa", "giva", "caratlane", "tanishq",
        "nike", "samsung", "apple", "hp", "sony", "xiaomi", "mi.com", "shopatsc",
    )
    req_gender = (req.get("gender") or "").lower()

    for p in products:
        price_s = 1.0 if hi == lo else max(0.0, 1.0 - (p["price"] - lo) / (hi - lo))
        raw_rating = float(p.get("rating") or 0.0)
        has_real_rating = raw_rating > 0.0
        rating_s = min(1.0, raw_rating / 5.0) if has_real_rating else 0.25

        ra = p.get("review_analysis", {})
        has_text_reviews = ra.get("status") == "available" and ra.get("sentiment") is not None
        sent_s = float(ra.get("sentiment", 0.8)) if has_text_reviews else rating_s
        rel_s = p.get("relevance_score", 1.0)
        brand_bonus = 0.05 if pref_brand and str(p.get("brand", "")).lower() == str(pref_brand).lower() else 0.0

        retailer_bonus = 0.06 if p.get("has_trusted_offer") else 0.0
        gender_bonus = 0.03 if req_gender and req_gender in (p.get("name", "").lower()) else 0.0
        refurb_penalty = -0.14 if p.get("is_refurbished") else 0.0
        foreign_penalty = -0.10 if p.get("is_foreign_only") else 0.0

        total_score = (0.25 * price_s) + (0.20 * rating_s) + (0.35 * rel_s) + (0.20 * sent_s) + brand_bonus + retailer_bonus + gender_bonus + refurb_penalty + foreign_penalty
        p["score"] = round(max(5.0, min(99.0, total_score * 100)), 1)
        p["breakdown"] = {
            "price": round(price_s, 2),
            "rating": round(rating_s, 2) if has_real_rating else "Not rated",
            "relevance": round(rel_s, 2),
            "reviews": round(sent_s, 2) if has_text_reviews else (f"{round(rating_s * 100)}% (Rating based)" if has_real_rating else "No rating data"),
        }

    return sorted(
        products,
        key=lambda p: (
            p.get("match_level") == "exact_match",
            not bool(p.get("is_refurbished", False)),
            bool(p.get("has_trusted_offer", False)),
            bool(p.get("image_verified", bool(p.get("image")))),
            float(p.get("rating") or 0.0) > 0.0,
            p["score"],
        ),
        reverse=True,
    )


def assign_badges(ranked: list[dict]):
    """Assigns explainable recommendation badges to top matching products."""
    if not ranked:
        return

    ranked[0]["badge"] = "🏆 Best Overall Choice"

    # Best Budget candidate
    if len(ranked) > 1:
        cheapest = min(ranked, key=lambda p: p["price"])
        if cheapest != ranked[0]:
            cheapest["badge"] = "💰 Best Budget Choice"

    for p in ranked[1:]:
        if not p.get("badge"):
            if "16 GB" in str(p.get("specs", {}).get("RAM", "")) or (p.get("rating", 0) >= 4.5):
                p["badge"] = "⚡ Top Performance"
                break
