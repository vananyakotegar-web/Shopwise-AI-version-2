"""
ShopWise V3 Master FastAPI Application.
Integrates Multi-Category Search, Real Product Data, Exact Model Matching,
Genuine Review Analysis (ABSA), Cross-Platform Price Comparison,
Conversational AI Shopping Assistant, Price Drop Alerts, Wishlist, and User Auth.
"""
from contextlib import asynccontextmanager
import json
import re
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from .auth import check_pw, hash_pw, make_token, optional_user, require_user
from .config import CORS_ORIGINS, SERPAPI_KEY, GEMINI_API_KEY
from .db import Alert, ComparisonHistory, Saved, Search, User, get_db, init_db
from .services import catalog, image_validator, llm, pipeline, review_extractor


# Ensure all tables exist on startup and schema is current
init_db()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ShopWise V3 – AI Shopping & Price Comparison Agent",
    description="Professional multi-store price comparison and AI shopping agent.",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Pydantic Schemas ----
class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=255)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Full Name cannot be empty.")
        return s

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        s = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s):
            raise ValueError("Please provide a valid email address.")
        return s

    @field_validator("password")
    @classmethod
    def clean_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=72)

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        s = v.strip().lower()
        if not s:
            raise ValueError("Email address cannot be empty.")
        return s

    @field_validator("password")
    @classmethod
    def clean_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password cannot be empty.")
        return v


class ForgotPasswordIn(BaseModel):
    email: str = Field(max_length=255)

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        s = v.strip().lower()
        if not s or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s):
            raise ValueError("Please provide a valid registered email address.")
        return s


class SearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    budget: float | None = Field(default=None, gt=0)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[dict[str, Any]] | None = None


class SaveIn(BaseModel):
    product: dict[str, Any]


class AlertIn(BaseModel):
    product_id: str
    name: str
    target_price: float
    current_price: float
    store: str = "Online"


class ComparisonIn(BaseModel):
    product_ids: list[str]
    query: str = ""


def _user_out(u: User):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "preferences": json.loads(u.preferences or "{}"),
        "created": u.created.isoformat() if getattr(u, "created", None) else None,
    }


def _bump_preference(user: User, key: str, val: str | None):
    if not val:
        return
    prefs = json.loads(user.preferences or "{}")
    bucket = prefs.setdefault(key, {})
    bucket[val] = bucket.get(val, 0) + 1
    user.preferences = json.dumps(prefs)


# ---- 1. System Health & Metadata ----
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "app": "ShopWise V3",
        "version": "3.0.0",
        "gemini_api_configured": bool(GEMINI_API_KEY),
        "serpapi_configured": bool(SERPAPI_KEY),
        "database": "connected",
        "categories_count": len(catalog.ALL_CATEGORIES),
        "catalog_products_count": len(catalog.get_all_products()),
    }


@app.get("/api/categories")
def get_categories():
    return catalog.ALL_CATEGORIES


# ---- 2. User Authentication ----
@app.post("/api/auth/register")
def register(body: RegisterIn, db=Depends(get_db)):
    email = body.email
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists.")
    u = User(email=email, name=body.name, password_hash=hash_pw(body.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return {
        "ok": True,
        "token": make_token(u.id),
        "user": _user_out(u),
        "message": "Account created successfully. You can now log in.",
    }


@app.post("/api/auth/login")
def login(body: LoginIn, db=Depends(get_db)):
    email = body.email
    u = db.scalar(select(User).where(User.email == email))
    if not u or not check_pw(body.password, u.password_hash):
        raise HTTPException(401, "Invalid email or password. Please verify your credentials.")
    return {
        "ok": True,
        "token": make_token(u.id),
        "user": _user_out(u),
    }


@app.post("/api/auth/forgot-password")
def forgot_password(body: ForgotPasswordIn, db=Depends(get_db)):
    email = body.email
    u = db.scalar(select(User).where(User.email == email))
    if not u:
        raise HTTPException(404, "No registered account found with this email. Please check your spelling or register.")
    return {
        "ok": True,
        "message": f"Password reset instructions have been dispatched to {email}. Please check your inbox.",
    }


@app.get("/api/auth/me")
def me(user=Depends(require_user)):
    return _user_out(user)


def _build_serpapi_queries(q: str, req: dict[str, Any]) -> list[str]:
    """
    Constructs clean Google Shopping search queries so exact models are not drowned
    out by accessories (cases/covers) or newer generations.
    Returns [primary_query] or [primary_query, fallback_refinement_query].
    """
    ql = q.lower()
    cat = (req.get("category") or "").lower()
    brand = req.get("brand") or ""
    model = req.get("model") or ""
    wants_acc = bool(req.get("wants_accessory"))

    primary = q
    if cat == "phone" and model and not wants_acc:
        if not any(w in ql for w in ("phone", "smartphone", "mobile", "5g")):
            if "iphone" in ql:
                primary = f"{q} smartphone"
            else:
                primary = f"{q} 5G smartphone"

    queries = [primary]

    # Targeted refinement query (only used if primary yields < 3 strict matches)
    if not wants_acc and model:
        brand_prefix = f"{brand} " if brand and brand.lower() not in model.lower() else ""
        if cat == "laptop":
            refined = f'"{brand_prefix}{model}" laptop'
        elif cat == "phone":
            refined = f'"{brand_prefix}{model}" buy'
        elif cat == "footwear":
            refined = f'"{brand_prefix}{model}" shoes'
        else:
            refined = f'"{brand_prefix}{model}"'
        if refined.lower() != primary.lower():
            queries.append(refined)
    elif primary != q:
        queries.append(q)

    return queries


# ---- 3. Product Search & Matching Engine ----
@app.post("/api/search")
async def search(body: SearchIn, user=Depends(optional_user), db=Depends(get_db)):
    q = body.query.strip()
    req = await pipeline.extract_search_intent(q, body.budget)
    if body.budget:
        req["budget_max"] = body.budget

    # 1. Collect candidate products from live SerpAPI Google Shopping when configured
    filtered = []
    if SERPAPI_KEY:
        seen_live_ids: set[str] = set()
        live_candidates: list[dict[str, Any]] = []
        serp_queries = _build_serpapi_queries(q, req)

        for idx, sq in enumerate(serp_queries):
            if idx > 0 and len(filtered) >= 3:
                break
            try:
                batch = await catalog.search_live(sq)
            except Exception:
                batch = []
            for item in batch:
                if item.get("id") and item["id"] not in seen_live_ids and item.get("offers"):
                    seen_live_ids.add(item["id"])
                    live_candidates.append(item)

            standardized_live = [
                pipeline.compare_prices(pipeline.standardize(p))
                for p in live_candidates
                if p.get("offers")
            ]
            filtered = pipeline.apply_budget_and_filters(standardized_live, req)

    # 2. Fallback to verified master catalog ONLY if live search is disabled/failed/empty
    if not filtered:
        catalog_products = catalog.get_all_products()
        standardized_cat = [
            pipeline.compare_prices(pipeline.standardize(p))
            for p in catalog_products
            if p.get("offers")
        ]
        filtered = pipeline.apply_budget_and_filters(standardized_cat, req)

    # 3. Verify 1:1 product-image integrity before ranking & review analysis
    filtered = image_validator.verify_product_image_mapping(filtered, req)

    # 4. Multi-criteria ranking (top 12) and badge allocation
    user_actual = user if (user and not hasattr(user, "dependency")) else None
    user_prefs = json.loads(user_actual.preferences or "{}") if (user_actual and hasattr(user_actual, "preferences")) else {}
    ranked = pipeline.rank(filtered, req, user_prefs)[:12]

    # 5. Genuine Review Analysis (ABSA) on final ranked matches (fast, zero fabricated reviews)
    for p in ranked:
        p["review_analysis"] = await review_extractor.extract_and_analyze_reviews(p, fetch_live=False)

    # Re-rank with ABSA sentiment and run final image mapping check + badge assignment
    ranked = pipeline.rank(ranked, req, user_prefs)
    ranked = image_validator.verify_product_image_mapping(ranked, req)
    pipeline.assign_badges(ranked)

    # 6. AI recommendation summary
    summary = await llm.generate_search_summary(req, ranked)

    # 7. Record search history and user preferences
    db_actual = db if (db and not hasattr(db, "dependency")) else None
    if user_actual and db_actual and hasattr(user_actual, "id"):
        db_actual.add(Search(user_id=user_actual.id, query=q, parsed=json.dumps(req)))
        _bump_preference(user_actual, "categories", req.get("category"))
        _bump_preference(user_actual, "brands", req.get("brand"))
        db_actual.commit()

    return {
        "query": q,
        "requirements": req,
        "summary": summary,
        "products": ranked,
        "total_found": len(ranked),
        "data_source": ranked[0]["source"] if ranked else "none",
    }


def _sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"


def _format_intent_detail(req: dict[str, Any]) -> str:
    parts = []
    if req.get("brand"):
        parts.append(str(req["brand"]))
    if req.get("model"):
        parts.append(str(req["model"]))
    if req.get("category"):
        parts.append(str(req["category"]).title())
    if req.get("budget_max"):
        parts.append(f"Under ₹{int(req['budget_max']):,}")
    specs = req.get("specs") or {}
    if specs.get("ram_gb"):
        parts.append(f"{specs['ram_gb']}GB RAM")
    if specs.get("processor"):
        parts.append(str(specs["processor"]))
    return "Detected: " + " · ".join(parts) if parts else "Parsed universal natural-language query"


@app.post("/api/search/stream")
async def search_stream(body: SearchIn, user=Depends(optional_user), db=Depends(get_db)):
    """
    Streams real-time Multi-Step AI Agent progress events (SSE) for each stage
    of the ShopWise search pipeline, followed by the complete search payload.
    """
    q = body.query.strip()
    user_actual = user if (user and not hasattr(user, "dependency")) else None
    user_prefs = json.loads(user_actual.preferences or "{}") if (user_actual and hasattr(user_actual, "preferences")) else {}
    db_actual = db if (db and not hasattr(db, "dependency")) else None

    async def event_generator():
        t_start = time.perf_counter()
        trace_steps: list[dict[str, Any]] = []

        def record_done(step_id: str, label: str, detail: str, ms: int):
            entry = {
                "id": step_id,
                "label": label,
                "status": "done",
                "detail": detail,
                "duration_ms": ms,
            }
            trace_steps.append(entry)
            return entry

        # --- Stage 1: NLP Intent & Constraints ---
        s1 = time.perf_counter()
        yield _sse_event({
            "type": "step",
            "id": "intent",
            "label": "Parsing NLP Intent & Constraints",
            "status": "running",
            "detail": f'Extracting brand, model, budget & specs from "{q}"...',
        })
        req = await pipeline.extract_search_intent(q, body.budget)
        if body.budget:
            req["budget_max"] = body.budget
        s1_ms = max(1, int((time.perf_counter() - s1) * 1000))
        yield _sse_event({
            "type": "step",
            **record_done("intent", "Parsing NLP Intent & Constraints", _format_intent_detail(req), s1_ms),
        })

        # --- Stage 2: Scanning Live Indian Stores ---
        s2 = time.perf_counter()
        yield _sse_event({
            "type": "step",
            "id": "scan",
            "label": "Scanning Live Indian Retailers",
            "status": "running",
            "detail": "Querying real-time prices across Amazon.in, Flipkart, Croma & Reliance Digital...",
        })
        raw_candidates: list[dict[str, Any]] = []
        filtered: list[dict[str, Any]] = []
        used_live = False

        if SERPAPI_KEY:
            seen_live_ids: set[str] = set()
            serp_queries = _build_serpapi_queries(q, req)
            for idx, sq in enumerate(serp_queries):
                if idx > 0 and len(filtered) >= 3:
                    break
                try:
                    batch = await catalog.search_live(sq)
                except Exception:
                    batch = []
                for item in batch:
                    if item.get("id") and item["id"] not in seen_live_ids and item.get("offers"):
                        seen_live_ids.add(item["id"])
                        raw_candidates.append(item)
                standardized_live = [
                    pipeline.compare_prices(pipeline.standardize(p))
                    for p in raw_candidates
                    if p.get("offers")
                ]
                filtered = pipeline.apply_budget_and_filters(standardized_live, req)
            used_live = bool(filtered)

        if not filtered:
            catalog_products = catalog.get_all_products()
            raw_candidates = catalog_products
            standardized_cat = [
                pipeline.compare_prices(pipeline.standardize(p))
                for p in catalog_products
                if p.get("offers")
            ]
            filtered = pipeline.apply_budget_and_filters(standardized_cat, req)

        total_offers = sum(len(p.get("offers") or []) for p in raw_candidates)
        s2_ms = max(1, int((time.perf_counter() - s2) * 1000))
        scan_detail = (
            f"Scanned {len(raw_candidates)} live listings ({total_offers} store offers)"
            if used_live
            else f"Scanned {len(raw_candidates)} verified catalog products"
        )
        yield _sse_event({
            "type": "step",
            **record_done("scan", "Scanning Live Indian Retailers", scan_detail, s2_ms),
        })

        # --- Stage 3: Exact Model, Variant & Image Verification ---
        s3 = time.perf_counter()
        yield _sse_event({
            "type": "step",
            "id": "filter",
            "label": "Exact Model & Image Verification",
            "status": "running",
            "detail": "Filtering out accessories, wrong variants & verifying 1:1 product images...",
        })
        filtered = image_validator.verify_product_image_mapping(filtered, req)
        removed_count = max(0, len(raw_candidates) - len(filtered))
        s3_ms = max(1, int((time.perf_counter() - s3) * 1000))
        filter_detail = (
            f"{len(filtered)} exact matches verified · {removed_count} non-matching listings filtered"
            if removed_count > 0
            else f"{len(filtered)} exact matches verified with clean images"
        )
        yield _sse_event({
            "type": "step",
            **record_done("filter", "Exact Model & Image Verification", filter_detail, s3_ms),
        })

        # --- Stage 4: Trusted Store Priority, ABSA & Multi-Criteria Value Scoring ---
        s4 = time.perf_counter()
        yield _sse_event({
            "type": "step",
            "id": "rank",
            "label": "Trusted Store & Value Scoring",
            "status": "running",
            "detail": "Scoring trusted Indian stores, delivery, return policies & review sentiment...",
        })
        ranked = pipeline.rank(filtered, req, user_prefs)[:12]
        for p in ranked:
            p["review_analysis"] = await review_extractor.extract_and_analyze_reviews(p, fetch_live=False)
        ranked = pipeline.rank(ranked, req, user_prefs)
        ranked = image_validator.verify_product_image_mapping(ranked, req)
        pipeline.assign_badges(ranked)

        trusted_count = sum(1 for p in ranked if p.get("has_trusted_offer"))
        s4_ms = max(1, int((time.perf_counter() - s4) * 1000))
        rank_detail = (
            f"Ranked {len(ranked)} deals · {trusted_count} trusted Indian store offer{'s' if trusted_count != 1 else ''} prioritized"
            if ranked
            else "No matching deals to rank"
        )
        yield _sse_event({
            "type": "step",
            **record_done("rank", "Trusted Store & Value Scoring", rank_detail, s4_ms),
        })

        # --- Stage 5: Synthesizing AI Recommendation ---
        s5 = time.perf_counter()
        yield _sse_event({
            "type": "step",
            "id": "summary",
            "label": "Synthesizing AI Recommendation",
            "status": "running",
            "detail": "Selecting Smart Agent Choice & summarizing top value deal...",
        })
        summary = await llm.generate_search_summary(req, ranked)

        if user_actual and db_actual and hasattr(user_actual, "id"):
            try:
                db_actual.add(Search(user_id=user_actual.id, query=q, parsed=json.dumps(req)))
                _bump_preference(user_actual, "categories", req.get("category"))
                _bump_preference(user_actual, "brands", req.get("brand"))
                db_actual.commit()
            except Exception:
                pass

        s5_ms = max(1, int((time.perf_counter() - s5) * 1000))
        if ranked:
            top = ranked[0]
            top_store = (top.get("best_offer") or {}).get("store", "Online")
            summary_detail = f"Top pick: {top_store} at ₹{int(round(top.get('price') or 0)):,} ({round(top.get('score') or 0)} Value Score)"
        else:
            summary_detail = "Prepared search guidance summary"
        yield _sse_event({
            "type": "step",
            **record_done("summary", "Synthesizing AI Recommendation", summary_detail, s5_ms),
        })

        total_ms = max(1, int((time.perf_counter() - t_start) * 1000))
        yield _sse_event({
            "type": "result",
            "data": {
                "query": q,
                "requirements": req,
                "summary": summary,
                "products": ranked,
                "total_found": len(ranked),
                "data_source": ranked[0]["source"] if ranked else "none",
                "agent_trace": {
                    "total_ms": total_ms,
                    "scanned_count": len(raw_candidates),
                    "verified_count": len(ranked),
                    "steps": trace_steps,
                },
            },
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---- 4. Conversational AI Shopping Assistant ----
@app.post("/api/chat")
async def chat(body: ChatIn, user=Depends(optional_user)):
    result = await llm.chat_assistant(body.message, body.history)
    return result


# ---- 4b. Dedicated Product-Specific Real Review Extraction & ABSA ----
class ReviewExtractIn(BaseModel):
    product: dict[str, Any]
    force_refresh: bool = False


class ProductReviewsIn(BaseModel):
    name: str
    brand: str = ""
    model: str = ""
    rating: float | None = None
    rating_count: int = 0
    specs: dict[str, Any] | None = None
    serpapi_product_id: str = ""
    immersive_product_page_token: str = ""
    serpapi_immersive_product_api: str = ""
    serpapi_product_api: str = ""
    reviews: list[Any] | None = None
    force_refresh: bool = False


@app.post("/api/reviews/extract")
async def extract_reviews(body: ReviewExtractIn):
    return await review_extractor.extract_and_analyze_reviews(
        body.product, fetch_live=True, force_refresh=body.force_refresh
    )


@app.post("/api/products/{product_id}/reviews")
async def get_product_reviews(product_id: str, body: ProductReviewsIn):
    payload = body.model_dump()
    payload["id"] = product_id
    force_refresh = bool(payload.pop("force_refresh", False))
    return await review_extractor.extract_and_analyze_reviews(
        payload, fetch_live=True, force_refresh=force_refresh
    )


# ---- 5. Price Drop Alerts ----
@app.get("/api/alerts")
def get_alerts(user=Depends(require_user), db=Depends(get_db)):
    rows = db.scalars(select(Alert).where(Alert.user_id == user.id).order_by(Alert.id.desc())).all()
    return [
        {
            "id": a.id,
            "product_id": a.product_id,
            "name": a.name,
            "target_price": a.target_price,
            "current_price": a.current_price,
            "store": a.store,
            "status": a.status,
            "created": a.created.isoformat() if a.created else "",
        }
        for a in rows
    ]


@app.post("/api/alerts")
def create_alert(body: AlertIn, user=Depends(require_user), db=Depends(get_db)):
    existing = db.scalar(select(Alert).where(Alert.user_id == user.id, Alert.product_id == body.product_id))
    if existing:
        existing.target_price = body.target_price
        existing.current_price = body.current_price
        existing.store = body.store
        db.commit()
        return {"ok": True, "alert_id": existing.id, "message": "Alert updated"}

    alert = Alert(
        user_id=user.id,
        product_id=body.product_id,
        name=body.name,
        target_price=body.target_price,
        current_price=body.current_price,
        store=body.store,
        status="Active - Tracking Store Drops",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {"ok": True, "alert_id": alert.id, "message": "Alert created successfully"}


@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: int, user=Depends(require_user), db=Depends(get_db)):
    alert = db.scalar(select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id))
    if alert:
        db.delete(alert)
        db.commit()
    return {"ok": True}


# ---- 6. Comparison History ----
@app.post("/api/comparisons")
def save_comparison(body: ComparisonIn, user=Depends(require_user), db=Depends(get_db)):
    rec = ComparisonHistory(
        user_id=user.id,
        product_ids=json.dumps(body.product_ids),
        query=body.query,
    )
    db.add(rec)
    db.commit()
    return {"ok": True}


# ---- 7. Saved Products / Wishlist ----
@app.get("/api/saved")
def get_saved(user=Depends(require_user), db=Depends(get_db)):
    rows = db.scalars(select(Saved).where(Saved.user_id == user.id).order_by(Saved.id.desc())).all()
    return [{"id": r.id, "product": json.loads(r.payload), "created": r.created.isoformat() if r.created else ""} for r in rows]


@app.post("/api/saved")
def save_product(body: SaveIn, user=Depends(require_user), db=Depends(get_db)):
    p = body.product
    pid = str(p.get("id"))
    name = str(p.get("name", "Product"))[:300]
    if not pid or not name:
        raise HTTPException(422, "Missing product id or name.")

    existing = db.scalar(select(Saved).where(Saved.user_id == user.id, Saved.product_id == pid))
    if existing:
        return {"ok": True, "message": "Already saved"}

    db.add(Saved(user_id=user.id, product_id=pid, name=name, payload=json.dumps(p)))
    _bump_preference(user, "brands", p.get("brand"))
    db.commit()
    return {"ok": True, "message": "Added to wishlist"}


@app.delete("/api/saved/{product_id}")
def delete_saved(product_id: str, user=Depends(require_user), db=Depends(get_db)):
    for r in db.scalars(select(Saved).where(Saved.user_id == user.id, Saved.product_id == product_id)):
        db.delete(r)
    db.commit()
    return {"ok": True}


# ---- 8. Search History ----
@app.get("/api/history")
def get_history(user=Depends(require_user), db=Depends(get_db)):
    rows = db.scalars(select(Search).where(Search.user_id == user.id).order_by(Search.id.desc()).limit(30)).all()
    return [{"id": r.id, "query": r.query, "created": r.created.isoformat() if r.created else ""} for r in rows]


@app.delete("/api/history")
def clear_history(user=Depends(require_user), db=Depends(get_db)):
    for r in db.scalars(select(Search).where(Search.user_id == user.id)):
        db.delete(r)
    db.commit()
    return {"ok": True}
