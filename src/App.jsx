import { useEffect, useState, useRef } from "react";
import { api, setToken, hasToken } from "./api";

const inr = (n) => "₹" + Math.round(n || 0).toLocaleString("en-IN");

const Icons = {
  Search: (props) => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  ),
  Home: (props) => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" />
      <path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    </svg>
  ),
  Scale: (props) => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
      <path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z" />
      <path d="M7 21h10" />
      <path d="M12 3v18" />
      <path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2" />
    </svg>
  ),
  Sparkles: (props) => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
    </svg>
  ),
  Heart: ({ filled, ...props }) => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
    </svg>
  ),
  Bell: (props) => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  ),
  Clock: (props) => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  Chat: (props) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  Close: (props) => (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  ShieldCheck: (props) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  ),
  ArrowUpRight: (props) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M7 7h10v10" />
      <path d="M7 17 17 7" />
    </svg>
  ),
  Truck: (props) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2" />
      <path d="M15 18H9" />
      <path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14" />
      <circle cx="17" cy="18" r="2" />
      <circle cx="7" cy="18" r="2" />
    </svg>
  ),
};
const formatExactStar = (r) => {
  if (r === null || r === undefined || r === "" || Number(r) <= 0 || Number.isNaN(Number(r))) {
    return null;
  }
  const num = Number(r);
  return `${Number.isInteger(num) ? num.toFixed(1) : num}★`;
};

const INVALID_IMAGE_MARKERS = [
  "no-image",
  "no_image",
  "noimage",
  "placeholder",
  "spacer.gif",
  "blank.gif",
  "1x1.",
  "image-not-available",
  "photo-1544716278-ca5e3f4abd8c",
];

function getValidImageUrl(url) {
  if (typeof url !== "string") return "";
  const cleaned = url.trim();
  if (!cleaned || cleaned.length < 12 || cleaned.length > 2048) return "";
  const lower = cleaned.toLowerCase();
  if (lower === "null" || lower === "undefined" || lower === "none") return "";
  if (!/^https?:\/\/[^/\s]+\.[^/\s]+/i.test(cleaned)) return "";
  if (INVALID_IMAGE_MARKERS.some((m) => lower.includes(m))) return "";
  return cleaned;
}

function ProductImage({ src, alt, brand = "", className = "product-main-img", placeholderClassName = "product-placeholder-box" }) {
  const validSrc = getValidImageUrl(src);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
  }, [validSrc]);

  if (!validSrc || failed) {
    return (
      <div className={placeholderClassName} role="img" aria-label={alt || brand || "Product image unavailable"}>
        <span>🛍️</span>
        <small>{brand || "Image Unavailable"}</small>
      </div>
    );
  }

  return (
    <img
      key={validSrc}
      src={validSrc}
      alt={alt || "Product"}
      className={className}
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  );
}

const TOP_CATEGORIES = [
  { id: "laptop", label: "Laptops", query: "HP laptop under ₹60,000 with 16GB RAM", icon: "💻" },
  { id: "phone", label: "Smartphones", query: "Smartphone", icon: "📱" },
  { id: "tablet", label: "Tablets", query: "Tablet under ₹35,000 for study", icon: "📟" },
  { id: "headphones", label: "Headphones", query: "Sony WH-1000XM5", icon: "🎧" },
  { id: "watch", label: "Smartwatches", query: "Samsung Galaxy Watch 6", icon: "⌚" },
  { id: "television", label: "Smart TVs", query: "Sony Bravia 55-inch 4K Google TV", icon: "📺" },
  { id: "camera", label: "Cameras", query: "Sony Alpha ILCE-6400 Mirrorless Camera", icon: "📷" },
  { id: "appliances", label: "Appliances", query: "LG 260L Double Door Refrigerator", icon: "🏠" },
  { id: "jewelry", label: "Jewelry", query: "Silver ring for women", icon: "💍" },
  { id: "clothing", label: "Fashion", query: "Red cotton kurti", icon: "👗" },
];

const TRENDING_DEALS = [
  {
    id: "samsung-galaxy-s24-128gb",
    name: "Samsung Galaxy S24 5G (128GB)",
    brand: "Samsung",
    category: "Smartphones",
    rating: 4.6,
    reviewsCount: 3840,
    price: 53999,
    mrp: 74999,
    bestStore: "Flipkart",
    savingsText: "Save ₹2,000 vs Amazon",
    image: "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600&auto=format&fit=crop&q=80",
    badge: "🔥 Top Trending Deal",
    searchQuery: "Samsung S24",
  },
  {
    id: "apple-iphone-15",
    name: "Apple iPhone 15 128GB",
    brand: "Apple",
    category: "Smartphones",
    rating: 4.7,
    reviewsCount: 8920,
    price: 69900,
    mrp: 79900,
    bestStore: "Flipkart",
    savingsText: "Save ₹1,099 vs Amazon",
    image: "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
    badge: "🏆 Lowest Price Guaranteed",
    searchQuery: "iPhone 15",
  },
  {
    id: "hp-15s-i5-16gb",
    name: "HP 15s 12th Gen Intel Core i5 Laptop",
    brand: "HP",
    category: "Laptops",
    rating: 4.4,
    reviewsCount: 2940,
    price: 52999,
    mrp: 68999,
    bestStore: "Flipkart",
    savingsText: "Save ₹2,000 vs Amazon",
    image: "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format&fit=crop&q=80",
    badge: "⚡ Best Spec Value",
    searchQuery: "HP laptop i5 16GB RAM",
  },
  {
    id: "boat-airdopes-141",
    name: "boAt Airdopes 141 Bluetooth Wireless Earbuds",
    brand: "boAt",
    category: "Headphones",
    rating: 4.3,
    reviewsCount: 18450,
    price: 1099,
    mrp: 4490,
    bestStore: "Amazon.in",
    savingsText: "Save ₹200 vs Flipkart",
    image: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
    badge: "🎧 Best Selling Audio",
    searchQuery: "Boat wireless earbuds",
  },
];

const INITIAL_AGENT_STEPS = [
  {
    id: "intent",
    label: "Parsing NLP Intent & Constraints",
    status: "pending",
    detail: "Extracting brand, model, budget & hardware specs...",
    duration_ms: null,
  },
  {
    id: "scan",
    label: "Scanning Live Indian Retailers",
    status: "pending",
    detail: "Querying live prices across Amazon.in, Flipkart, Croma & Reliance Digital...",
    duration_ms: null,
  },
  {
    id: "filter",
    label: "Exact Model & Image Verification",
    status: "pending",
    detail: "Filtering accessories, wrong variants & verifying product images...",
    duration_ms: null,
  },
  {
    id: "rank",
    label: "Trusted Store & Value Scoring",
    status: "pending",
    detail: "Scoring trusted Indian stores, delivery, return policies & review sentiment...",
    duration_ms: null,
  },
  {
    id: "summary",
    label: "Synthesizing AI Recommendation",
    status: "pending",
    detail: "Selecting Smart Agent Choice & generating recommendation summary...",
    duration_ms: null,
  },
];

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("search");
  const previousViewRef = useRef("search");

  useEffect(() => {
    if (view !== "chat") {
      previousViewRef.current = view;
    }
  }, [view]);

  const closeChat = () => {
    setView(previousViewRef.current && previousViewRef.current !== "chat" ? previousViewRef.current : "search");
  };

  const [selectedProduct, setSelectedProduct] = useState(null);
  const [detailsInitialTab, setDetailsInitialTab] = useState("stores");
  const [authOpen, setAuthOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [agentSteps, setAgentSteps] = useState(INITIAL_AGENT_STEPS);
  const [error, setError] = useState("");
  const [compareList, setCompareList] = useState([]);
  const [savedIds, setSavedIds] = useState(new Set());
  const searchInputRef = useRef(null);
  const searchRequestIdRef = useRef(0);

  // Filters & Sorting State (Amazon/Flipkart Style)
  const [sortBy, setSortBy] = useState("match"); // 'match' | 'price_asc' | 'price_desc' | 'rating'
  const [selectedBrands, setSelectedBrands] = useState([]);
  const [maxPriceFilter, setMaxPriceFilter] = useState(null);
  const [minRating, setMinRating] = useState(0);
  const [exactMatchOnly, setExactMatchOnly] = useState(false);
  const [trustedStoresOnly, setTrustedStoresOnly] = useState(false);
  const [hideRefurbished, setHideRefurbished] = useState(true);

  const handleClearSearch = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    searchRequestIdRef.current += 1;
    // 1. Clear search input & URL query param
    setQuery("");
    try {
      window.history.replaceState(null, "", window.location.pathname);
    } catch {}
    // 2. Clear previous search results and suggestions
    setData(null);
    setError("");
    setLoading(false);
    // 3. Reset query-dependent filters and search states
    setSelectedBrands([]);
    setMaxPriceFilter(null);
    setMinRating(0);
    setExactMatchOnly(false);
    setTrustedStoresOnly(false);
    setHideRefurbished(true);
    setSortBy("match");
    // 4. Focus back on input ready for a new search
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  };

  // Restore active search query after page refresh so exact products & images remain intact
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const initialQ = (params.get("q") || "").trim();
      if (initialQ.length >= 2) {
        run(initialQ, true);
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (!hasToken()) return;
    api.me()
      .then((u) => {
        setUser(u);
      })
      .catch((err) => {
        console.warn("Session check failed:", err.message);
        setToken("");
        setUser(null);
      });
  }, []);

  // Favorites & Wishlist Sync (Guest LocalStorage + Server DB)
  useEffect(() => {
    if (!user) {
      try {
        const guestSaved = JSON.parse(localStorage.getItem("shopwise_guest_saved") || "[]");
        setSavedIds(new Set(guestSaved.map((p) => String(p.id))));
      } catch {
        setSavedIds(new Set());
      }
      return;
    }

    // When logged in, sync any guest-saved items to user's account
    try {
      const guestSaved = JSON.parse(localStorage.getItem("shopwise_guest_saved") || "[]");
      if (guestSaved.length > 0) {
        Promise.all(guestSaved.map((p) => api.save(p).catch(() => {}))).finally(() => {
          localStorage.removeItem("shopwise_guest_saved");
          api.saved()
            .then((rows) => setSavedIds(new Set(rows.map((r) => String(r.product.id)))))
            .catch(() => {});
        });
        return;
      }
    } catch {}

    api.saved()
      .then((rows) => setSavedIds(new Set(rows.map((r) => String(r.product.id)))))
      .catch(() => {});
  }, [user]);

  async function run(q = query, switchView = true) {
    const trimmed = (q || "").trim();
    if (!trimmed || trimmed.length < 2) {
      return setError("Please enter a product name, brand, or model to search.");
    }
    const reqId = ++searchRequestIdRef.current;
    setQuery(trimmed);
    if (switchView) setView("search");
    setLoading(true);
    setAgentSteps(
      INITIAL_AGENT_STEPS.map((s, idx) =>
        idx === 0 ? { ...s, status: "running" } : { ...s, status: "pending", duration_ms: null }
      )
    );
    setError("");
    setData(null);
    setSelectedBrands([]);
    setMaxPriceFilter(null);
    setMinRating(0);
    setExactMatchOnly(false);
    try {
      window.history.replaceState(null, "", `?q=${encodeURIComponent(trimmed)}`);
    } catch {}
    try {
      const res = await api.searchStream(trimmed, null, (stepEvt) => {
        if (reqId !== searchRequestIdRef.current) return;
        setAgentSteps((prev) =>
          prev.map((s) =>
            s.id === stepEvt.id
              ? {
                  ...s,
                  label: stepEvt.label || s.label,
                  status: stepEvt.status || s.status,
                  detail: stepEvt.detail || s.detail,
                  duration_ms: stepEvt.duration_ms ?? s.duration_ms,
                }
              : s
          )
        );
      });
      // Discard out-of-order responses from earlier searches
      if (reqId !== searchRequestIdRef.current) return;
      if (res?.agent_trace?.steps?.length) {
        setAgentSteps(res.agent_trace.steps);
      }
      setData(res);
    } catch (e) {
      if (reqId !== searchRequestIdRef.current) return;
      setError(e.message || "Failed to search products.");
    } finally {
      if (reqId === searchRequestIdRef.current) {
        setLoading(false);
      }
    }
  }

  async function toggleSave(p) {
    if (!p || !p.id) return;
    const pid = String(p.id);
    const has = savedIds.has(pid);

    if (!user) {
      // Guest mode: persist locally so favorites work instantly without being blocked
      try {
        const guestSaved = JSON.parse(localStorage.getItem("shopwise_guest_saved") || "[]");
        let updated;
        if (has) {
          updated = guestSaved.filter((item) => String(item.id) !== pid);
        } else {
          updated = [p, ...guestSaved.filter((item) => String(item.id) !== pid)];
        }
        localStorage.setItem("shopwise_guest_saved", JSON.stringify(updated));
        setSavedIds(new Set(updated.map((item) => String(item.id))));
      } catch (e) {
        console.error("Local wishlist error:", e);
      }
      return;
    }

    // Authenticated mode: persist to server database
    try {
      if (has) {
        await api.unsave(p.id);
      } else {
        await api.save(p);
      }
      setSavedIds((s) => {
        const n = new Set(s);
        has ? n.delete(pid) : n.add(pid);
        return n;
      });
    } catch (e) {
      setError(e.message || "Failed to update wishlist.");
    }
  }

  const logout = () => {
    setToken("");
    setUser(null);
    setView("search");
    setProfileOpen(false);
  };

  // Extract all available brands in current search
  const availableBrands = Array.from(new Set((data?.products || []).map((p) => p.brand))).filter(Boolean);

  // Filter Products
  let filteredProducts = (data?.products || []).filter((p) => {
    if (selectedBrands.length > 0 && !selectedBrands.includes(p.brand)) return false;
    if (maxPriceFilter && p.price > maxPriceFilter) return false;
    if (minRating > 0 && (p.rating || 0) < minRating) return false;
    if (exactMatchOnly && p.match_level !== "exact_match") return false;
    if (trustedStoresOnly && !p.has_trusted_offer) return false;
    if (hideRefurbished && p.is_refurbished) return false;
    return true;
  });

  // Sort Products
  if (sortBy === "price_asc") filteredProducts.sort((a, b) => a.price - b.price);
  else if (sortBy === "price_desc") filteredProducts.sort((a, b) => b.price - a.price);
  else if (sortBy === "rating") filteredProducts.sort((a, b) => (b.rating || 0) - (a.rating || 0));
  else filteredProducts.sort((a, b) => (b.score || 0) - (a.score || 0));

  function openProductDetails(product, tab = "stores") {
    if (!product) return;
    setSelectedProduct(product);
    setDetailsInitialTab(tab);
    setView("product_details");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function syncProductReviews(pid, revAnalysis) {
    setData((prev) =>
      prev
        ? {
            ...prev,
            products: (prev.products || []).map((item) =>
              item.id === pid
                ? {
                    ...item,
                    rating: revAnalysis?.overall_rating ?? item.rating,
                    rating_count: revAnalysis?.overall_rating_count ?? item.rating_count,
                    review_analysis: revAnalysis,
                  }
                : item
            ),
          }
        : prev
    );
    setSelectedProduct((prev) =>
      prev && prev.id === pid
        ? {
            ...prev,
            rating: revAnalysis?.overall_rating ?? prev.rating,
            rating_count: revAnalysis?.overall_rating_count ?? prev.rating_count,
            review_analysis: revAnalysis,
          }
        : prev
    );
    setCompareList((prev) =>
      prev.map((item) =>
        item.id === pid
          ? {
              ...item,
              rating: revAnalysis?.overall_rating ?? item.rating,
              rating_count: revAnalysis?.overall_rating_count ?? item.rating_count,
              review_analysis: revAnalysis,
            }
          : item
      )
    );
  }

  const isPicked = (pid) => compareList.some((item) => String(item.id) === String(pid));

  function toggleCompare(product) {
    if (!product || !product.id) return;
    const pid = String(product.id);
    setCompareList((prev) => {
      if (prev.some((item) => String(item.id) === pid)) {
        return prev.filter((item) => String(item.id) !== pid);
      }
      return [...prev, product].slice(-3);
    });
  }

  const compareItems = compareList;

  return (
    <div className="marketplace-app">
      {/* 1. TOP HEADER - MODERN GLASS AI NAVBAR */}
      <header className="ecom-top-header modern-glass-header">
        <div className="top-header-inner">
          {/* Brand Logo */}
          <div
            className="brand-logo-area"
            onClick={handleClearSearch}
            title="Back to ShopWise Home"
          >
            <div className="logo-icon-badge" aria-hidden="true">
              <span className="logo-icon-dot" />
            </div>
            <div className="logo-text-block">
              <span className="logo-main-text">
                Shop<span className="logo-accent-text">Wise</span>
                <span className="v3-pill">✨ AI</span>
              </span>
            </div>
          </div>

          {/* Pill Global AI Search Bar (Only shown on results/active pages, so homepage has ONLY the middle hero search bar!) */}
          {(data || loading || error || (query && query.trim().length > 0) || view !== "search") && (
            <form
              className="central-search-form"
              onSubmit={(e) => {
                e.preventDefault();
                run();
              }}
            >
              <span className="search-leading-icon" aria-hidden="true">
                <Icons.Search />
              </span>
              <div className="search-input-wrapper">
                <input
                  ref={searchInputRef}
                  type="text"
                  className="search-input"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      run();
                    }
                  }}
                  placeholder="Search products using AI (e.g. 'Samsung S24', 'laptop under 60000')..."
                  autoComplete="off"
                  spellCheck="false"
                />
                {query && query.length > 0 && (
                  <button
                    type="button"
                    className="search-clear-btn"
                    onClick={handleClearSearch}
                    title="Clear search"
                    aria-label="Clear search input"
                  >
                    ✕
                  </button>
                )}
              </div>
              <button
                type="submit"
                className="search-submit-btn"
                disabled={loading}
                title="Search products"
                aria-label="Search"
              >
                {loading ? <span className="search-btn-spinner"></span> : "Search"}
              </button>
            </form>
          )}

          {/* Streamlined Navigation Links */}
          <div className="top-nav-actions">
            <button
              type="button"
              className={"nav-pill-btn" + (view === "search" && !data ? " active" : "")}
              onClick={handleClearSearch}
            >
              <Icons.Home />
              <span>Home</span>
            </button>

            <button
              type="button"
              className={"nav-pill-btn" + (view === "compare" ? " active" : "")}
              onClick={() => setView("compare")}
            >
              <Icons.Scale />
              <span>Compare</span>
              {compareList.length > 0 && <span className="nav-count-chip">{compareList.length}</span>}
            </button>

            <button
              type="button"
              className={"nav-pill-btn" + (view === "chat" ? " active" : "")}
              onClick={() => (view === "chat" ? closeChat() : setView("chat"))}
              title={view === "chat" ? "Close AI Chat and return to previous page" : "Open Conversational AI Shopping Assistant"}
            >
              <Icons.Sparkles />
              <span>AI Chat</span>
            </button>

            <button
              type="button"
              className={"nav-pill-btn" + (view === "saved" ? " active" : "")}
              onClick={() => setView("saved")}
            >
              <Icons.Heart filled={savedIds.size > 0} />
              <span>Saved</span>
              {savedIds.size > 0 && <span className="nav-count-chip">{savedIds.size}</span>}
            </button>

            <button
              type="button"
              className={"nav-pill-btn" + (view === "alerts" ? " active" : "")}
              onClick={() => setView("alerts")}
            >
              <Icons.Bell />
              <span>Alerts</span>
            </button>

            {user ? (
              <div className="user-pill-group">
                <button
                  type="button"
                  className="nav-pill-btn"
                  onClick={() => setView("history")}
                >
                  <Icons.Clock />
                  <span>History</span>
                </button>
                <button
                  type="button"
                  className="user-avatar-pill"
                  onClick={() => setProfileOpen(true)}
                  title="View Profile Information"
                >
                  <span className="user-avatar-initial">
                    {(user.name || "U").charAt(0).toUpperCase()}
                  </span>
                  <span>{user.name.split(" ")[0]}</span>
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="signin-cta-pill"
                onClick={() => setAuthOpen(true)}
              >
                Sign In
              </button>
            )}
          </div>
        </div>

        {/* Clean Category Quick-Access Ribbon */}
        <nav className="ecom-category-nav">
          <div className="category-nav-inner">
            {TOP_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                type="button"
                className="category-pill-link"
                onClick={() => run(cat.query)}
              >
                <span className="cat-text">{cat.label}</span>
              </button>
            ))}
            <div className="category-live-status">
              <span className="live-dot"></span> Live Indian Stores
            </div>
          </div>
        </nav>
      </header>

      {/* 2. BODY CONTENT */}
      <main className="ecom-main-content">
        {view === "search" && (
          <>
            {error && <div className="error-alert-banner">⚠️ {error}</div>}

            {loading && (
              <AgentProgressTracker query={query} steps={agentSteps} />
            )}

            {!data && !loading && (
              <HomePage onSearch={run} onSave={toggleSave} savedIds={savedIds} />
            )}

            {data && !loading && (
              <div className="ecom-shopping-container">
                {/* Left Filter Sidebar */}
                <aside className="ecom-filter-sidebar">
                  <div className="filter-header">
                    <h3>Filter Results</h3>
                    {(selectedBrands.length > 0 || maxPriceFilter || minRating > 0 || exactMatchOnly || trustedStoresOnly || !hideRefurbished) && (
                      <button
                        className="clear-filters-btn"
                        onClick={() => {
                          setSelectedBrands([]);
                          setMaxPriceFilter(null);
                          setMinRating(0);
                          setExactMatchOnly(false);
                          setTrustedStoresOnly(false);
                          setHideRefurbished(true);
                        }}
                      >
                        Clear All
                      </button>
                    )}
                  </div>

                  {/* Store Trust & Product Condition Filters */}
                  <div className="filter-block">
                    <h4>Store & Condition</h4>
                    <label className="filter-checkbox-label" style={{ marginBottom: "6px" }}>
                      <input
                        type="checkbox"
                        checked={trustedStoresOnly}
                        onChange={(e) => setTrustedStoresOnly(e.target.checked)}
                      />
                      <span>🛡️ Trusted Indian Stores Only</span>
                    </label>
                    <label className="filter-checkbox-label">
                      <input
                        type="checkbox"
                        checked={hideRefurbished}
                        onChange={(e) => setHideRefurbished(e.target.checked)}
                      />
                      <span>✨ New Only (Hide Refurbished)</span>
                    </label>
                  </div>

                  {/* Match Precision Filter */}
                  <div className="filter-block">
                    <h4>Match Precision</h4>
                    <label className="filter-checkbox-label">
                      <input
                        type="checkbox"
                        checked={exactMatchOnly}
                        onChange={(e) => setExactMatchOnly(e.target.checked)}
                      />
                      <span>🎯 Exact Model Match Only</span>
                    </label>
                  </div>

                  {/* Brand Filter */}
                  {availableBrands.length > 1 && (
                    <div className="filter-block">
                      <h4>Brand</h4>
                      <div className="brand-options-list">
                        {availableBrands.map((b) => (
                          <label key={b} className="filter-checkbox-label">
                            <input
                              type="checkbox"
                              checked={selectedBrands.includes(b)}
                              onChange={(e) => {
                                if (e.target.checked) setSelectedBrands([...selectedBrands, b]);
                                else setSelectedBrands(selectedBrands.filter((x) => x !== b));
                              }}
                            />
                            <span>{b}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Price Budget Filters */}
                  <div className="filter-block">
                    <h4>Price Budget</h4>
                    <div className="budget-chips-group">
                      <button
                        className={"budget-pill" + (maxPriceFilter === 25000 ? " active" : "")}
                        onClick={() => setMaxPriceFilter(maxPriceFilter === 25000 ? null : 25000)}
                      >
                        Under ₹25,000
                      </button>
                      <button
                        className={"budget-pill" + (maxPriceFilter === 50000 ? " active" : "")}
                        onClick={() => setMaxPriceFilter(maxPriceFilter === 50000 ? null : 50000)}
                      >
                        Under ₹50,000
                      </button>
                      <button
                        className={"budget-pill" + (maxPriceFilter === 60000 ? " active" : "")}
                        onClick={() => setMaxPriceFilter(maxPriceFilter === 60000 ? null : 60000)}
                      >
                        Under ₹60,000
                      </button>
                      <button
                        className={"budget-pill" + (maxPriceFilter === 100000 ? " active" : "")}
                        onClick={() => setMaxPriceFilter(maxPriceFilter === 100000 ? null : 100000)}
                      >
                        Under ₹1,00,000
                      </button>
                    </div>
                  </div>

                  {/* Customer Rating Filter */}
                  <div className="filter-block">
                    <h4>Customer Rating</h4>
                    <div className="rating-filter-options">
                      <button
                        className={"rating-filter-btn" + (minRating === 4.5 ? " active" : "")}
                        onClick={() => setMinRating(minRating === 4.5 ? 0 : 4.5)}
                      >
                        ★★★★☆ 4.5 & Above
                      </button>
                      <button
                        className={"rating-filter-btn" + (minRating === 4.0 ? " active" : "")}
                        onClick={() => setMinRating(minRating === 4.0 ? 0 : 4.0)}
                      >
                        ★★★★☆ 4.0 & Above
                      </button>
                    </div>
                  </div>

                  {/* Supported Stores */}
                  <div className="filter-block stores-trust-block">
                    <h4>Stores Compared</h4>
                    <div className="store-badges-grid">
                      <div className="store-trust-item">
                        <span className="store-dot amazon"></span> Amazon.in
                      </div>
                      <div className="store-trust-item">
                        <span className="store-dot flipkart"></span> Flipkart
                      </div>
                      <div className="store-trust-item">
                        <span className="store-dot croma"></span> Croma
                      </div>
                      <div className="store-trust-item">
                        <span className="store-dot reliance"></span> Reliance Digital
                      </div>
                    </div>
                  </div>
                </aside>

                {/* Right Product Listing Area */}
                <section className="ecom-results-pane">
                  {/* AI Search Parameters Bar */}
                  <UnderstoodBar req={data.requirements} />

                  {/* Collapsible Completed AI Agent Trace */}
                  {data.agent_trace?.steps?.length > 0 && (
                    <AgentTraceBar trace={data.agent_trace} query={data.query} />
                  )}

                  {/* AI Recommendation Spotlight (Smart Agent Winner Card) */}
                  {filteredProducts.length > 0 ? (() => {
                    const topPick = filteredProducts[0];
                    const topStore = topPick.best_offer?.store || "Online";
                    const topRating = formatExactStar(topPick.rating);
                    const reasons = [
                      topPick.best_offer?.is_trusted
                        ? `Verified Trusted Indian Store (${topStore}) with ${topPick.best_offer?.return_policy || "standard buyer protection"}.`
                        : `Lowest verified live price across compared listings on ${topStore}.`,
                      topPick.savings > 0
                        ? `Saves ${inr(topPick.savings)} compared to higher-priced retailers for the same listing.`
                        : topRating
                          ? `Strong customer rating of ${topRating}${topPick.rating_count ? ` across ${Number(topPick.rating_count).toLocaleString("en-IN")} ratings` : ""}.`
                          : "Matches your exact query and specification filters.",
                    ];
                    return (
                      <div className="ai-winner-card-outer">
                        <div className="ai-winner-header">
                          <div className="ai-winner-icon-badge" aria-hidden="true">✨</div>
                          <div>
                            <span className="ai-winner-eyebrow">SHOPWISE AI ANALYSIS</span>
                            <h3 className="ai-winner-title">Smart Agent Choice Recommendation</h3>
                          </div>
                        </div>

                        <div className="ai-winner-inner-card">
                          <div className="ai-winner-left">
                            {topPick.brand && <span className="ai-winner-brand">{topPick.brand}</span>}
                            <h4
                              className="ai-winner-product-name"
                              onClick={() => openProductDetails(topPick, "stores")}
                            >
                              {topPick.name}
                            </h4>
                            <div className="ai-winner-deal-row">
                              <span className="ai-winner-deal-label">Best Deal on:</span>
                              <span className="ai-winner-store-pill">{topStore}</span>
                              {topPick.best_offer?.is_trusted && (
                                <span className="card-trusted-pill">🛡️ Trusted Store</span>
                              )}
                              <span className="ai-winner-price">{inr(topPick.price)}</span>
                            </div>

                            <div className="ai-winner-reasons">
                              <span className="ai-winner-reasons-title">WHY OUR AGENT PICKED THIS DEAL:</span>
                              {reasons.map((r, rIdx) => (
                                <div key={rIdx} className="ai-winner-reason-item">
                                  <span className="reason-check-circle">✓</span>
                                  <span>{r}</span>
                                </div>
                              ))}
                              {data.summary && (
                                <p className="ai-winner-summary-note">{renderBoldText(data.summary)}</p>
                              )}
                            </div>
                          </div>

                          <div className="ai-winner-right">
                            <div className="ai-value-score-box">
                              <span className="score-medal-icon">🏅</span>
                              <span className="score-big-number">{Math.round(topPick.score || 90)}</span>
                              <span className="score-sub-label">VALUE SCORE</span>
                            </div>
                            <div className="ai-winner-cta-stack">
                              <button
                                type="button"
                                className="winner-details-btn"
                                onClick={() => openProductDetails(topPick, "stores")}
                              >
                                View Details →
                              </button>
                              <a
                                href={topPick.best_offer?.url || "#"}
                                target="_blank"
                                rel="noreferrer"
                                className="winner-buy-btn"
                              >
                                Buy on {topStore} ↗
                              </a>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })() : (
                    <div className="ai-advisor-spotlight">
                      <div className="spotlight-header">
                        <span className="advisor-icon">🤖</span>
                        <strong>ShopWise AI Shopping Advisor Recommendation</strong>
                      </div>
                      <p>{data.summary}</p>
                    </div>
                  )}

                  {/* Results Count & Sort Bar */}
                  <div className="results-toolbar">
                    <span className="results-count-text">
                      Showing <b>{filteredProducts.length}</b> verified results for "<b>{data.query}</b>"
                    </span>
                    <div className="sort-controls">
                      <label>Sort By:</label>
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="sort-dropdown"
                      >
                        <option value="match">Featured: AI Match Score</option>
                        <option value="price_asc">Price: Low to High</option>
                        <option value="price_desc">Price: High to Low</option>
                        <option value="rating">Avg. Customer Rating</option>
                      </select>
                    </div>
                  </div>

                  {/* Product Cards List */}
                  {filteredProducts.length === 0 ? (
                    <div className="no-products-fallback">
                      <div className="no-products-icon" style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>🔍</div>
                      <h3>No exact matching products found.</h3>
                      <p>
                        We could not find any products satisfying all your mandatory requirements for "<b>{data.query}</b>".
                        Strict filtering prevented substituting unrelated or similar products without your explicit instruction.
                      </p>
                      <div className="no-products-actions">
                        <button
                          className="broaden-search-btn"
                          onClick={() => {
                            const broad = (data.requirements?.brand || "") + " " + (data.requirements?.category || "");
                            run(broad.trim() || data.query.split(" ")[0]);
                          }}
                        >
                          🌐 Broaden Search
                        </button>
                        <button
                          className="reset-btn"
                          onClick={() => {
                            setSelectedBrands([]);
                            setMaxPriceFilter(null);
                            setMinRating(0);
                            setExactMatchOnly(false);
                            setTrustedStoresOnly(false);
                            setHideRefurbished(false);
                          }}
                        >
                          Clear Filters
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="ecom-products-vertical-list">
                      {filteredProducts.map((p, idx) => (
                        <EcomProductRow
                          key={`${data?.query || ""}:${p.id}:${idx}`}
                          p={p}
                          rank={idx + 1}
                          saved={savedIds.has(String(p.id))}
                          onSave={() => toggleSave(p)}
                          picked={isPicked(p.id)}
                          onPick={() => toggleCompare(p)}
                          user={user}
                          onRequireAuth={() => setAuthOpen(true)}
                          onOpenDetails={(tab) => openProductDetails(p, tab)}
                          onReviewsLoaded={syncProductReviews}
                        />
                      ))}
                    </div>
                  )}

                  {/* Inline Side-by-Side Comparison Preview when 2+ selected */}
                  {compareItems.length >= 2 && (
                    <CompareMatrix
                      items={compareItems}
                      onRemove={(pid) => setCompareList((prev) => prev.filter((item) => String(item.id) !== String(pid)))}
                      onClear={() => setCompareList([])}
                      onOpenDetails={(prod) => openProductDetails(prod, "stores")}
                    />
                  )}
                </section>
              </div>
            )}
          </>
        )}

        {view === "compare" && (
          <CompareMatrix
            items={compareItems}
            onRemove={(pid) => setCompareList((prev) => prev.filter((item) => String(item.id) !== String(pid)))}
            onClear={() => setCompareList([])}
            onOpenDetails={(prod) => openProductDetails(prod, "stores")}
            onBackToSearch={() => setView("search")}
            fullPage={true}
          />
        )}

        {view === "product_details" && selectedProduct && (
          <ProductDetailsPage
            product={selectedProduct}
            initialTab={detailsInitialTab}
            saved={savedIds.has(String(selectedProduct.id))}
            onSave={() => toggleSave(selectedProduct)}
            picked={isPicked(selectedProduct.id)}
            onPick={() => toggleCompare(selectedProduct)}
            user={user}
            onRequireAuth={() => setAuthOpen(true)}
            onBack={() => setView("search")}
            onReviewsLoaded={syncProductReviews}
          />
        )}

        {view === "chat" && <ChatAssistant onSearchDeal={run} onClose={closeChat} />}
        {view === "saved" && <Wishlist onSave={toggleSave} user={user} onRequireAuth={() => setAuthOpen(true)} />}
        {view === "alerts" && <PriceAlerts onRequireAuth={() => setAuthOpen(true)} user={user} />}
        {view === "history" && <SearchHistory onRun={run} user={user} onRequireAuth={() => setAuthOpen(true)} />}
      </main>

      {/* Sticky Bottom Compare Tray */}
      {compareList.length > 0 && view !== "compare" && (
        <div className="floating-compare-tray" role="region" aria-label="Product comparison tray">
          <div className="compare-tray-items">
            <span className="compare-tray-label">⚖️ Compare ({compareList.length}/3):</span>
            {compareList.map((item) => (
              <div key={item.id} className="compare-tray-chip">
                <span className="compare-tray-name" title={item.name}>
                  {item.name.length > 26 ? `${item.name.slice(0, 26)}…` : item.name}
                </span>
                <span className="compare-tray-price">{inr(item.price)}</span>
                <button
                  type="button"
                  className="compare-tray-remove"
                  onClick={() => toggleCompare(item)}
                  aria-label={`Remove ${item.name} from compare`}
                >
                  ✕
                </button>
              </div>
            ))}
            {compareList.length === 1 && (
              <span className="compare-tray-hint">Select 1 more product to compare side-by-side</span>
            )}
          </div>
          <div className="compare-tray-actions">
            <button
              type="button"
              className="compare-tray-clear-btn"
              onClick={() => setCompareList([])}
            >
              Clear
            </button>
            <button
              type="button"
              className="compare-tray-go-btn"
              disabled={compareList.length < 2}
              onClick={() => {
                setView("compare");
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              Compare Now ({compareList.length}) →
            </button>
          </div>
        </div>
      )}

      {/* Sleek Circular Floating AI Assistant FAB (Toggle Open / Close) */}
      <button
        type="button"
        className={"floating-ai-agent-trigger floating-circle-fab" + (view === "chat" ? " is-open" : "")}
        onClick={() => (view === "chat" ? closeChat() : setView("chat"))}
        title={view === "chat" ? "Close Shopping Assistant" : "Ask ShopWise AI Shopping Assistant"}
        aria-label={view === "chat" ? "Close Shopping Assistant" : "Open AI Shopping Assistant"}
      >
        {view === "chat" ? (
          <Icons.Close width="22" height="22" />
        ) : (
          <>
            <Icons.Chat />
            <span className="floating-notif-dot">1</span>
          </>
        )}
      </button>

      {/* Grounded Footer */}
      <footer className="ecom-mall-footer">
        <div className="footer-grounded-bar">
          <div className="footer-brand-left">
            © 2026 SHOPWISE AI COMPARISON AGENT
          </div>
          <div className="footer-status-pills">
            <span className="footer-status-item">
              <span className="status-dot-green" /> SYSTEMS GROUNDED
            </span>
            <span className="footer-status-item">SQLITE DB ENABLED</span>
            <span className="footer-status-item">GEMINI LLM ACTIVE</span>
            <span className="footer-status-item">LIVE SERPAPI + ABSA</span>
          </div>
          <button
            type="button"
            className="footer-back-top-btn"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          >
            Back to top ↑
          </button>
        </div>
      </footer>

      {authOpen && (
        <AuthModal
          onClose={() => setAuthOpen(false)}
          onDone={(u) => {
            setUser(u);
            setAuthOpen(false);
          }}
        />
      )}

      {profileOpen && (
        <UserProfileModal
          user={user}
          onClose={() => setProfileOpen(false)}
          onLogout={logout}
          savedCount={savedIds.size}
        />
      )}
    </div>
  );
}

function AgentProgressTracker({ query, steps = [] }) {
  const doneCount = steps.filter((s) => s.status === "done").length;
  const runningIdx = steps.findIndex((s) => s.status === "running");
  const total = steps.length || 5;
  const pct = Math.min(96, Math.round(((doneCount + (runningIdx >= 0 ? 0.45 : 0)) / total) * 100));

  return (
    <section className="agent-progress-card" role="status" aria-live="polite">
      <div className="agent-progress-top">
        <div className="agent-progress-brand">
          <span className="agent-pulse-orb" aria-hidden="true">
            <Icons.Sparkles />
          </span>
          <div>
            <span className="agent-progress-eyebrow">SHOPWISE MULTI-STAGE AI AGENT</span>
            <h3 className="agent-progress-heading">
              Scouting live Indian deals for <span className="agent-query-highlight">"{query}"</span>
            </h3>
          </div>
        </div>
        <div className="agent-progress-pct-badge">{pct}%</div>
      </div>

      <div className="agent-progress-bar-track">
        <div className="agent-progress-bar-fill" style={{ width: `${Math.max(10, pct)}%` }} />
      </div>

      <ol className="agent-steps-timeline">
        {steps.map((step, idx) => (
          <li key={step.id} className={`agent-step-item status-${step.status}`}>
            <div className="agent-step-indicator" aria-hidden="true">
              {step.status === "done" ? (
                <span className="step-check-glyph">✓</span>
              ) : step.status === "running" ? (
                <span className="step-spinner-ring" />
              ) : (
                <span className="step-index-num">{idx + 1}</span>
              )}
            </div>
            <div className="agent-step-body">
              <div className="agent-step-title-row">
                <span className="agent-step-label">{step.label}</span>
                {step.status === "done" && step.duration_ms != null && (
                  <span className="agent-step-time">{step.duration_ms} ms</span>
                )}
                {step.status === "running" && (
                  <span className="agent-step-live-tag">In progress…</span>
                )}
              </div>
              <p className="agent-step-detail">{step.detail}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function AgentTraceBar({ trace, query }) {
  const [expanded, setExpanded] = useState(false);
  const steps = trace?.steps || [];
  const totalSec = trace?.total_ms ? (trace.total_ms / 1000).toFixed(2) : null;

  return (
    <div className="agent-trace-bar">
      <div className="agent-trace-summary-row">
        <div className="agent-trace-left">
          <span className="trace-done-pill">
            <Icons.Sparkles /> AI Agent Trace
          </span>
          <span className="trace-summary-text">
            Completed <b>{steps.length}/{steps.length}</b> pipeline stages
            {totalSec ? ` in ${totalSec}s` : ""}
            {trace?.scanned_count ? ` · ${trace.scanned_count} scanned → ${trace.verified_count} verified` : ""}
          </span>
        </div>
        <button
          type="button"
          className="trace-toggle-btn"
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
        >
          {expanded ? "Hide Trace ▴" : "View Agent Trace ▾"}
        </button>
      </div>

      {expanded && (
        <div className="agent-trace-drawer">
          <div className="trace-drawer-caption">
            Live execution trace for <b>"{query}"</b>
          </div>
          <ol className="agent-steps-timeline compact">
            {steps.map((step, idx) => (
              <li key={step.id || idx} className="agent-step-item status-done">
                <div className="agent-step-indicator" aria-hidden="true">
                  <span className="step-check-glyph">✓</span>
                </div>
                <div className="agent-step-body">
                  <div className="agent-step-title-row">
                    <span className="agent-step-label">{step.label}</span>
                    {step.duration_ms != null && (
                      <span className="agent-step-time">{step.duration_ms} ms</span>
                    )}
                  </div>
                  <p className="agent-step-detail">{step.detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

function UnderstoodBar({ req }) {
  if (!req) return null;
  const chips = [
    req.model && `Model: ${req.model}`,
    req.brand && `Brand: ${req.brand}`,
    req.category && `Category: ${req.category.toUpperCase()}`,
    req.product_type && `Type: ${req.product_type.toUpperCase()}`,
    req.material && `Material: ${req.material.toUpperCase()}`,
    req.colour && `Colour: ${req.colour.toUpperCase()}`,
    req.gender && `For: ${req.gender.toUpperCase()}`,
    req.budget_max && `Max Budget: ${inr(req.budget_max)}`,
    req.budget_min && `Min Budget: ${inr(req.budget_min)}`,
    req.specs?.ram_gb && `RAM: ${req.specs.ram_gb} GB`,
    req.specs?.processor && `Processor: ${req.specs.processor}`,
    (req.specs?.storage_gb || req.specs?.storage) && `Storage: ${req.specs?.storage_gb ? req.specs.storage_gb + ' GB' : req.specs?.storage}`,
  ].filter(Boolean);

  return (
    <div className="ai-param-card">
      <span className="ai-param-title">🎯 AI Parameter Extraction:</span>
      <div className="param-chips-row">
        {chips.length ? (
          chips.map((c) => <span key={c} className="param-badge">{c}</span>)
        ) : (
          <span className="param-badge">All Products / Universal Search</span>
        )}
      </div>
    </div>
  );
}

function CustomerReviewsPanel({
  product,
  onReviewsLoaded,
  autoFetch = true,
  externalState = null,
}) {
  const [internalData, setInternalData] = useState(() => {
    const existing = product?.review_analysis;
    if (
      existing &&
      String(existing.product_id || product.id) === String(product.id) &&
      (existing.status === "available" || existing.status === "unavailable")
    ) {
      return existing;
    }
    return null;
  });
  const [internalLoading, setInternalLoading] = useState(false);
  const [internalError, setInternalError] = useState("");
  const reqSeqRef = useRef(0);

  async function fetchInternalReviews(forceRefresh = false) {
    if (!product || !product.id) return;
    const seq = ++reqSeqRef.current;
    const targetId = String(product.id);
    setInternalLoading(true);
    setInternalError("");
    try {
      const res = await api.getProductReviews(product, forceRefresh);
      if (reqSeqRef.current !== seq) return;
      if (res.product_id && String(res.product_id) !== targetId) return;

      if (res.status === "error") {
        setInternalData(null);
        setInternalError("Unable to fetch reviews. Please try again.");
      } else {
        setInternalData(res);
        if (onReviewsLoaded) onReviewsLoaded(product.id, res);
      }
    } catch {
      if (reqSeqRef.current !== seq) return;
      setInternalData(null);
      setInternalError("Unable to fetch reviews. Please try again.");
    } finally {
      if (reqSeqRef.current === seq) setInternalLoading(false);
    }
  }

  useEffect(() => {
    if (externalState) return;
    reqSeqRef.current += 1;
    const existing = product?.review_analysis;
    const hasFreshForThisProduct =
      existing &&
      String(existing.product_id || product.id) === String(product.id) &&
      (existing.status === "available" || existing.status === "unavailable");

    if (hasFreshForThisProduct) {
      setInternalData(existing);
      setInternalError("");
      setInternalLoading(false);
    } else {
      setInternalData(null);
      setInternalError("");
      if (autoFetch && product?.id) {
        fetchInternalReviews(false);
      }
    }
  }, [product?.id, Boolean(externalState)]);

  const reviewData = externalState ? externalState.reviewData : internalData;
  const loading = externalState ? externalState.loading : internalLoading;
  const errorMsg = externalState ? externalState.errorMsg : internalError;
  const fetchReviews = externalState ? externalState.fetchReviews : fetchInternalReviews;

  const ra = reviewData || {};
  const exactOverallRating = formatExactStar(ra.overall_rating ?? product?.rating);
  const overallCount = ra.overall_rating_count ?? product?.rating_count ?? 0;

  return (
    <div className="reviews-absa-panel" data-product-id={product?.id}>
      {/* Selected Product & Strictly Separated Overall Rating Banner */}
      <div className="reviews-product-identity-bar">
        <div className="reviews-product-identity-left">
          <ProductImage
            src={product?.image}
            alt={product?.name}
            brand={product?.brand}
            className="reviews-product-thumb"
            placeholderClassName="reviews-product-thumb-fallback"
          />
          <div>
            <small className="reviews-scope-label">Customer Reviews Exclusively For:</small>
            <h4 className="reviews-product-heading">{product?.name}</h4>
            <div className="reviews-product-meta-row">
              {product?.brand && <span className="brand-tag">{product.brand}</span>}
              {product?.model && <span className="model-code-tag">Model: {product.model}</span>}
              <span className="product-id-chip">ID: {product?.id}</span>
            </div>
          </div>
        </div>

        <div className="overall-rating-separated-box">
          <small className="overall-rating-caption">Overall Product Rating</small>
          <div className="overall-rating-value-row">
            <span className="overall-rating-star-num">
              {exactOverallRating || "Not rated"}
            </span>
          </div>
          <small className="overall-rating-count-text">
            {overallCount > 0 ? `${overallCount.toLocaleString("en-IN")} overall ratings` : "Rating count unavailable"}
          </small>
        </div>
      </div>

      {/* State 1: Loading */}
      {loading && (
        <div className="no-review-text-box" style={{ textAlign: "center", padding: "26px" }}>
          <div className="ecom-spinner" style={{ margin: "0 auto 12px", width: "30px", height: "30px" }}></div>
          <h4>Fetching customer reviews...</h4>
          <p>Retrieving actual written reviews specifically for <b>{product?.name}</b>.</p>
        </div>
      )}

      {/* State 2: Fetch Error */}
      {!loading && errorMsg && (
        <div className="reviews-status-banner error-banner">
          <div>
            <strong>⚠️ Unable to fetch reviews. Please try again.</strong>
            <p style={{ margin: "4px 0 0", fontSize: "13px" }}>
              We could not reach the external review service for <b>{product?.name}</b>. No fake or demo reviews are displayed.
            </p>
          </div>
          <button type="button" className="confirm-alert-btn" onClick={() => fetchReviews(true)}>
            ↻ Try Again
          </button>
        </div>
      )}

      {/* State 3: Reviews Loaded Successfully (Available) */}
      {!loading && !errorMsg && ra.status === "available" && (
        <>
          <div className="reviews-status-banner success-banner">
            <div>
              <strong>✅ Reviews loaded successfully.</strong>
              <span style={{ marginLeft: "10px", fontSize: "12.5px" }}>
                Showing <b>{ra.review_count}</b> actual written review{ra.review_count === 1 ? "" : "s"} for <b>{product?.name}</b>
                {ra.source ? ` · Source: ${ra.source}` : ""}
              </span>
            </div>
            <button type="button" className="clear-filters-btn" onClick={() => fetchReviews(true)}>
              ↻ Refresh Reviews
            </button>
          </div>

          {/* AI ABSA Sentiment Analysis */}
          <div className="absa-section-wrapper">
            <div className="absa-section-heading-row">
              <h5>🤖 AI Aspect-Based Sentiment Analysis (Written Reviews Only)</h5>
              <small>Calculated exclusively from {ra.review_count} retrieved written review{ra.review_count === 1 ? "" : "s"} — separate from overall product rating</small>
            </div>

            <div className="sentiment-meter-container">
              <div className="sentiment-bar">
                <div style={{ width: `${ra.positive}%`, background: "#10B981" }} />
                <div style={{ width: `${ra.neutral}%`, background: "#94A3B8" }} />
                <div style={{ width: `${ra.negative}%`, background: "#EF4444" }} />
              </div>
              <div className="sentiment-legend-row">
                <span className="legend-pos"><b>{ra.positive}%</b> Positive ({ra.positive_count ?? 0})</span>
                <span className="legend-neu"><b>{ra.neutral}%</b> Neutral ({ra.neutral_count ?? 0})</span>
                <span className="legend-neg"><b>{ra.negative}%</b> Negative ({ra.negative_count ?? 0})</span>
                <span className="legend-source">Source: <b>{ra.source}</b></span>
              </div>
            </div>

            <div className="review-ai-consensus-quote">
              <span>“{ra.summary}”</span>
            </div>

            <div className="pros-cons-grid">
              <div className="aspect-card pros-card">
                <h5>✓ Common Pros</h5>
                {(ra.pros || []).length > 0 ? (
                  <ul>
                    {(ra.pros || []).map((pro) => <li key={pro}>{pro}</li>)}
                  </ul>
                ) : (
                  <p style={{ fontSize: "13px", color: "#475569", margin: "6px 0 0" }}>No common pros extracted from the retrieved written reviews.</p>
                )}
              </div>
              <div className="aspect-card cons-card">
                <h5>✕ Common Cons</h5>
                {(ra.cons || []).length > 0 ? (
                  <ul>
                    {(ra.cons || []).map((con) => <li key={con}>{con}</li>)}
                  </ul>
                ) : (
                  <p style={{ fontSize: "13px", color: "#475569", margin: "6px 0 0" }}>No common cons extracted from the retrieved written reviews.</p>
                )}
              </div>
            </div>

            {Object.keys(ra.aspects || {}).length > 0 && (
              <div className="absa-dimensions-box">
                <h5>Aspect-Based Feedback (ABSA):</h5>
                <div className="aspect-chips-cloud">
                  {Object.entries(ra.aspects).map(([aspect, info]) => (
                    <div key={aspect} className={"dimension-tag " + info.status.toLowerCase()} title={info.sample_quote || ""}>
                      <span className="dimension-title">{aspect.toUpperCase()}</span>
                      <span className="dimension-verdict">{info.status} ({info.mentions_count || 1})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Individual Actual Written Customer Reviews */}
          {(ra.reviews || ra.review_items || []).length > 0 && (
            <div className="real-customer-quotes-section">
              <h5>Actual Written Customer Reviews ({(ra.reviews || ra.review_items).length}):</h5>
              {(ra.reviews || ra.review_items).map((rev, i) => {
                const label = rev.sentiment_label || "Neutral";
                const badgeBg = label === "Positive" ? "#DCFCE7" : label === "Negative" ? "#FEE2E2" : "#F1F5F9";
                const badgeFg = label === "Positive" ? "#166534" : label === "Negative" ? "#991B1B" : "#475569";
                const indivStar = formatExactStar(rev.rating);
                return (
                  <div key={rev.id || i} className="single-review-quote-card">
                    <div className="quote-card-header" style={{ flexWrap: "wrap", gap: "8px" }}>
                      {indivStar && (
                        <span className="review-stars" title="Individual review rating">
                          {"★".repeat(Math.round(rev.rating))} {indivStar}
                        </span>
                      )}
                      {rev.title && <strong>{rev.title}</strong>}
                      <span className="review-sentiment-pill" style={{ background: badgeBg, color: badgeFg }}>
                        {label}
                      </span>
                      <span className="verified-badge">
                        Source:{" "}
                        {rev.source_url ? (
                          <a href={rev.source_url} target="_blank" rel="noreferrer" style={{ color: "inherit", textDecoration: "underline" }}>
                            {rev.source || "External Source"} ↗
                          </a>
                        ) : (
                          rev.source || "External Source"
                        )}
                      </span>
                      {rev.reviewer && <small style={{ color: "#475569", fontWeight: 600 }}>by {rev.reviewer}</small>}
                      {rev.date && <small style={{ color: "#64748B" }}>· {rev.date}</small>}
                    </div>
                    <p className="quote-text">"{rev.text}"</p>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* State 4: No Written Customer Reviews Available */}
      {!loading && !errorMsg && ra.status === "unavailable" && (
        <div className="no-review-text-box">
          <h4>ℹ️ No written customer reviews available for this product.</h4>
          <p>No written customer reviews were returned for <b>{product?.name}</b>.</p>
          {ra.unavailable_reason && (
            <p style={{ fontSize: "12.5px", color: "#475569", marginTop: "4px" }}>{ra.unavailable_reason}</p>
          )}
          <div className="rating-derived-metric">
            <span><b>Transparency Notice:</b> No fake reviews or fabricated sentiment percentages are displayed.</span>
            {exactOverallRating && (
              <small>
                Overall product rating ({exactOverallRating}{overallCount > 0 ? ` from ${overallCount.toLocaleString("en-IN")} ratings` : ""}) is shown above separately and is not used to fabricate written-review sentiment.
              </small>
            )}
          </div>
          <button type="button" className="confirm-alert-btn" style={{ marginTop: "10px" }} onClick={() => fetchReviews(true)}>
            ↻ Retry Fetching Reviews
          </button>
        </div>
      )}
    </div>
  );
}

function renderBoldText(text) {
  if (!text) return null;
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

function getTrustBadgeClass(offer) {
  if (offer?.is_refurbished) return "refurbished";
  if (offer?.is_trusted) return "trusted";
  if (offer?.is_foreign) return "foreign";
  return "retailer";
}

function StoreComparisonTable({ product: p, showSavingsBanner = true }) {
  const offers = p?.offers || [];
  const maxPrice = Math.max(...offers.map((o) => o.price || 0), p?.price || 1);
  const highestPrice = p?.highest_price || maxPrice;

  return (
    <div className="stores-comparison-table-wrap">
      <div className="stores-table-scroll">
        <table className="stores-table">
          <thead>
            <tr>
              <th>Platform &amp; Trust</th>
              <th>Price Comparison</th>
              <th>Live Price</th>
              <th>Delivery</th>
              <th>Return &amp; Warranty</th>
              <th>Availability &amp; Action</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((o, oIdx) => {
              const isCheapest = Boolean(o.is_cheapest) || o.price === p.price;
              const isBestValue = Boolean(o.is_best_value);
              const badgeCls = getTrustBadgeClass(o);
              const badgeLabel =
                o.store_badge ||
                (o.is_refurbished
                  ? "Refurbished / Used"
                  : o.is_trusted
                    ? "✓ Trusted Store"
                    : o.is_foreign
                      ? "International Seller"
                      : "Online Retailer");
              const saveVsMax = highestPrice > o.price ? Math.round(highestPrice - o.price) : 0;

              return (
                <tr
                  key={`${o.store}-${o.price}-${oIdx}`}
                  className={
                    isBestValue || isCheapest
                      ? "lowest-price-row"
                      : o.is_refurbished
                        ? "refurb-offer-row"
                        : ""
                  }
                >
                  <td className="store-name-cell">
                    <div className="store-name-line">
                      <strong>{o.store}</strong>
                      {isBestValue ? (
                        <span className="best-value-badge-pill">★ Best Value</span>
                      ) : isCheapest ? (
                        <span className="lowest-badge-pill">Cheapest</span>
                      ) : null}
                    </div>
                    <div className="store-badges-stack">
                      <span className={`store-trust-badge ${badgeCls}`}>{badgeLabel}</span>
                    </div>
                  </td>
                  <td>
                    <div className="price-meter-track">
                      <div
                        className="price-meter-fill"
                        style={{ width: `${Math.min(100, ((o.price || 0) / maxPrice) * 100)}%` }}
                      />
                    </div>
                  </td>
                  <td className="store-price-cell">
                    <div>{inr(o.price)}</div>
                    {saveVsMax > 0 && (
                      <div className="store-save-subtext">Save {inr(saveVsMax)}</div>
                    )}
                  </td>
                  <td className="store-delivery-cell">
                    <span>🚚 {o.delivery || "Standard Delivery"}</span>
                  </td>
                  <td className="store-policy-cell">
                    <div className="policy-return-line">
                      {o.return_policy || "Check Store Return Policy"}
                    </div>
                    <div className="policy-warranty-line">
                      {o.warranty || "Verify Seller Warranty"}
                    </div>
                  </td>
                  <td className="store-action-cell">
                    <div className="store-stock-line">
                      <span className={o.in_stock ? "stock-in-text" : "stock-out-text"}>
                        {o.in_stock ? "✓ In Stock" : "✕ Out of Stock"}
                      </span>
                    </div>
                    <a
                      href={o.url || "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="store-direct-link-btn"
                    >
                      Visit {o.store} ↗
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {showSavingsBanner && p.savings > 0 && (
        <div className="price-savings-banner">
          💰 <b>Smart Shopper Alert:</b> You save <b>{inr(p.savings)}</b> on <b>{p.name}</b> by buying from <b>{p.best_offer?.store}</b> instead of higher-priced platforms!
        </div>
      )}
    </div>
  );
}

function ProductDetailsPage({
  product: p,
  initialTab = "stores",
  saved,
  onSave,
  picked,
  onPick,
  user,
  onRequireAuth,
  onBack,
  onReviewsLoaded,
}) {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [alertSuccess, setAlertSuccess] = useState("");
  const [reviewData, setReviewData] = useState(() => {
    const existing = p?.review_analysis;
    if (
      existing &&
      String(existing.product_id || p.id) === String(p.id) &&
      existing.status === "available"
    ) {
      return existing;
    }
    return null;
  });
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const detailsReqSeqRef = useRef(0);

  async function fetchDetailsReviews(forceRefresh = false) {
    if (!p || !p.id) return;
    const seq = ++detailsReqSeqRef.current;
    const targetId = String(p.id);
    setReviewLoading(true);
    setReviewError("");
    try {
      const res = await api.getProductReviews(p, forceRefresh);
      if (detailsReqSeqRef.current !== seq) return;
      if (res.product_id && String(res.product_id) !== targetId) return;

      if (res.status === "error") {
        setReviewData(null);
        setReviewError("Unable to fetch reviews. Please try again.");
      } else {
        setReviewData(res);
        if (onReviewsLoaded) onReviewsLoaded(p.id, res);
      }
    } catch {
      if (detailsReqSeqRef.current !== seq) return;
      setReviewData(null);
      setReviewError("Unable to fetch reviews. Please try again.");
    } finally {
      if (detailsReqSeqRef.current === seq) setReviewLoading(false);
    }
  }

  useEffect(() => {
    setActiveTab(initialTab);
    setAlertSuccess("");
    detailsReqSeqRef.current += 1;
    if (!p?.id) return;

    const existing = p.review_analysis;
    const hasValidAvailable =
      existing &&
      String(existing.product_id || p.id) === String(p.id) &&
      existing.status === "available";

    if (hasValidAvailable) {
      setReviewData(existing);
      setReviewError("");
      setReviewLoading(false);
    } else {
      setReviewData(null);
      setReviewError("");
      fetchDetailsReviews(false);
    }
  }, [p?.id, initialTab]);

  if (!p) return null;

  const exactRating = formatExactStar(reviewData?.overall_rating ?? p.rating);
  const overallCount = reviewData?.overall_rating_count ?? p.rating_count ?? 0;
  const maxPrice = Math.max(...(p.offers || []).map((o) => o.price), p.price || 1);
  const estimatedMrp = Math.round((p.price || 1000) * 1.25);
  const discountPct = Math.round(((estimatedMrp - (p.price || 1000)) / estimatedMrp) * 100);
  const ra = reviewData || p.review_analysis || {};

  async function handleSetAlert() {
    if (!user) return onRequireAuth();
    const target = Math.round(p.price * 0.9);
    try {
      await api.createAlert({
        product_id: String(p.id),
        name: p.name,
        target_price: target,
        current_price: p.price,
        store: p.best_offer?.store || "Online",
      });
      setAlertSuccess(`Price drop alert set for ${inr(target)}!`);
      setTimeout(() => setAlertSuccess(""), 4000);
    } catch {
      setAlertSuccess("Failed to set alert.");
    }
  }

  return (
    <section className="product-details-page">
      <div className="details-top-breadcrumb">
        <button type="button" className="back-to-results-btn" onClick={onBack}>
          ← Back to Search Results
        </button>
        <span className="details-breadcrumb-trail">
          {p.category ? `${p.category.toUpperCase()} / ` : ""}
          {p.brand ? `${p.brand} / ` : ""}
          <b>{p.name}</b>
        </span>
      </div>

      <div className="product-details-hero-card">
        <div className="details-image-panel">
          <ProductImage
            src={p.image}
            alt={p.name}
            brand={p.brand}
            className="details-main-image"
            placeholderClassName="product-placeholder-box"
          />
          {p.score && <span className="ai-score-pill">{p.score}% AI Match</span>}
        </div>

        <div className="details-summary-panel">
          <div className="badge-row">
            {p.badge && <span className="match-tag exact">{p.badge}</span>}
            {p.model && <span className="model-code-tag">Model: {p.model}</span>}
            <span className="product-id-chip">Product ID: {p.id}</span>
          </div>

          <h1 className="details-product-title">{p.name}</h1>

          <div className="ratings-summary-row">
            {exactRating ? (
              <span className="star-rating-pill" title="Overall Product Rating">{exactRating}</span>
            ) : (
              <span className="star-rating-pill" style={{ background: "#64748B" }}>Not rated</span>
            )}
            {overallCount > 0 && (
              <span className="total-ratings-count">
                ({overallCount.toLocaleString("en-IN")} overall ratings)
              </span>
            )}
            <span className="brand-tag">{p.brand}</span>
          </div>

          <div className="live-price-cluster">
            <div className="price-primary">
              <span className="currency-symbol">₹</span>
              <span className="price-digits">{Math.round(p.price || 0).toLocaleString("en-IN")}</span>
            </div>
            <div className="mrp-and-discount">
              <span className="mrp-label">M.R.P.:</span>
              <span className="mrp-strike">{inr(estimatedMrp)}</span>
              <span className="discount-pct">({discountPct}% off)</span>
            </div>
            <span className="best-store-badge">Lowest on {p.best_offer?.store}</span>
            {p.best_offer?.is_trusted && (
              <span className="card-trusted-pill">🛡️ Trusted Indian Store</span>
            )}
            {p.is_refurbished && (
              <span className="card-refurb-pill">Refurbished / Used</span>
            )}
          </div>

          <div className="delivery-promise" style={{ marginBottom: "12px" }}>
            <span>
              🚚 {p.best_offer?.delivery || "Standard Delivery"} ·{" "}
              {p.best_offer?.return_policy || "Check Store Return Policy"}
              {p.best_offer?.warranty ? ` · ${p.best_offer.warranty}` : ""}
            </span>
          </div>

          {p.savings > 0 && (
            <div className="price-savings-banner" style={{ marginBottom: "14px" }}>
              💰 Save <b>{inr(p.savings)}</b> by buying from <b>{p.best_offer?.store}</b> compared to higher-priced retailers.
            </div>
          )}

          <div className="details-primary-actions">
            <a href={p.best_offer?.url || "#"} target="_blank" rel="noreferrer" className="action-btn-buy">
              Buy on {p.best_offer?.store} ↗
            </a>
            <button type="button" className={"action-btn-wishlist" + (saved ? " is-saved" : "")} onClick={onSave}>
              {saved ? "❤️ In Wishlist" : "🤍 Add to Wishlist"}
            </button>
            <button type="button" className="details-reviews-shortcut-btn" onClick={() => setActiveTab("reviews")}>
              ⭐ Customer Reviews {reviewLoading ? "(Fetching…)" : ra.status === "available" ? `(${ra.review_count})` : ""}
            </button>
            <label className="compare-checkbox-label">
              <input type="checkbox" checked={picked} onChange={onPick} />
              <span>Add to Compare</span>
            </label>
          </div>
        </div>
      </div>

      <div className="ecom-product-card" style={{ marginTop: "18px" }}>
        <div className="ecom-card-tabs-bar">
          <button type="button" className={"card-tab" + (activeTab === "stores" ? " active" : "")} onClick={() => setActiveTab("stores")}>
            🏪 Compare All Stores ({(p.offers || []).length})
          </button>
          <button type="button" className={"card-tab" + (activeTab === "reviews" ? " active" : "")} onClick={() => setActiveTab("reviews")}>
            ⭐ Customer Reviews {reviewLoading ? "(Fetching…)" : ra.status === "available" ? `(${ra.review_count})` : ra.status === "unavailable" ? "(0)" : ""}
          </button>
          <button type="button" className={"card-tab" + (activeTab === "specs" ? " active" : "")} onClick={() => setActiveTab("specs")}>
            ⚙️ Specifications
          </button>
          <button type="button" className={"card-tab" + (activeTab === "alerts" ? " active" : "")} onClick={() => setActiveTab("alerts")}>
            📉 Price Drop Alerts
          </button>
        </div>

        <div className="card-tab-content-panel">
          {activeTab === "stores" && (
            <StoreComparisonTable product={p} showSavingsBanner={false} />
          )}

          {activeTab === "reviews" && (
            <CustomerReviewsPanel
              key={p.id}
              product={p}
              onReviewsLoaded={onReviewsLoaded}
              autoFetch={false}
              externalState={{
                reviewData,
                loading: reviewLoading,
                errorMsg: reviewError,
                fetchReviews: fetchDetailsReviews,
              }}
            />
          )}

          {activeTab === "specs" && (
            <div className="specs-table-container">
              <div className="specs-key-value-grid">
                {Object.entries(p.specs || {}).map(([key, val]) => (
                  <div key={key} className="spec-row-item">
                    <span className="spec-label">{key}</span>
                    <span className="spec-value">{String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "alerts" && (
            <div className="price-alert-tab-panel">
              <div className="alert-callout">
                <h4>🔔 Set Real-Time Price Drop Alert</h4>
                <p>We will track Amazon, Flipkart, Croma, and Reliance Digital and notify you when the price drops below your target.</p>
                <div className="alert-action-box">
                  <button type="button" className="confirm-alert-btn" onClick={handleSetAlert}>
                    Set Alert for 10% Drop (Below {inr(p.price * 0.9)})
                  </button>
                  {alertSuccess && <span className="alert-success-msg">{alertSuccess}</span>}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function EcomProductRow({ p, rank, saved, onSave, picked, onPick, user, onRequireAuth, onOpenDetails, onReviewsLoaded }) {
  const offerCount = (p.offers || []).length;
  // Keep Rank #1 and multi-store cards expanded by default; keep 1-store cards #2+ clean & compact until clicked
  const [activeTab, setActiveTab] = useState(rank === 1 || offerCount > 1 ? "stores" : null);
  const [alertSuccess, setAlertSuccess] = useState("");
  const ra = p.review_analysis || {};
  const exactRating = formatExactStar(p.rating);
  const estimatedMrp = Math.round((p.price || 1000) * 1.25);
  const discountPct = Math.round(((estimatedMrp - (p.price || 1000)) / estimatedMrp) * 100);

  function toggleTab(tab) {
    setActiveTab((curr) => (curr === tab ? null : tab));
  }

  async function handleSetAlert() {
    if (!user) return onRequireAuth();
    const target = Math.round(p.price * 0.9);
    try {
      await api.createAlert({
        product_id: String(p.id),
        name: p.name,
        target_price: target,
        current_price: p.price,
        store: p.best_offer?.store || "Online",
      });
      setAlertSuccess(`Price drop alert set for ${inr(target)}!`);
      setTimeout(() => setAlertSuccess(""), 4000);
    } catch {
      setAlertSuccess("Failed to set alert.");
    }
  }

  return (
    <div className={"ecom-product-card clean-result-card" + (rank === 1 ? " top-recommendation-border" : "")}>
      {p.badge && <span className="top-choice-flag">{p.badge}</span>}

      <div className="card-primary-row">
        {/* Clickable Product Image Box */}
        <div
          className="product-image-container clickable-product-target"
          onClick={() => onOpenDetails && onOpenDetails("stores")}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === "Enter" && onOpenDetails) onOpenDetails("stores"); }}
          title={`View full details and reviews for ${p.name}`}
        >
          <ProductImage
            src={p.image}
            alt={p.name}
            brand={p.brand}
            className="product-main-img"
            placeholderClassName="product-placeholder-box"
          />
          <span className="ai-score-pill">{Math.round(p.score || 85)}% Match</span>
        </div>

        {/* Product Details Section */}
        <div className="product-info-container">
          <div className="clean-card-eyebrow-row">
            {p.brand && <span className="clean-brand-label">{p.brand}</span>}
            {p.match_level === "exact_match" && (
              <span className="clean-match-dot-pill">
                <span className="match-dot-green" /> Exact Match
              </span>
            )}
            {p.best_offer?.is_trusted && (
              <span className="card-trusted-pill inline-svg-pill">
                <Icons.ShieldCheck /> Trusted Indian Store
              </span>
            )}
            {p.is_refurbished && (
              <span className="card-refurb-pill">Refurbished / Used</span>
            )}
          </div>

          <h2
            className="product-title-text clickable-product-title"
            onClick={() => onOpenDetails && onOpenDetails("stores")}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === "Enter" && onOpenDetails) onOpenDetails("stores"); }}
            title={`Open product details for ${p.name}`}
          >
            {p.name}
          </h2>

          <div className="ratings-summary-row">
            {exactRating ? (
              <span className="clean-star-badge" title="Overall Product Rating">
                ★ {exactRating.replace("★", "")}
              </span>
            ) : (
              <span className="clean-star-badge muted">Not rated</span>
            )}
            {p.rating_count > 0 && (
              <span className="total-ratings-count">
                {Number(p.rating_count).toLocaleString("en-IN")} ratings
              </span>
            )}
            {p.savings > 0 && (
              <span className="card-savings-pill">Save {inr(p.savings)} across {offerCount} stores</span>
            )}
          </div>

          {/* Live Price Cluster */}
          <div className="live-price-cluster">
            <div className="price-primary">
              <span className="currency-symbol">₹</span>
              <span className="price-digits">{Math.round(p.price || 0).toLocaleString("en-IN")}</span>
            </div>
            <div className="mrp-and-discount">
              <span className="mrp-strike">{inr(estimatedMrp)}</span>
              <span className="discount-pct">{discountPct}% off</span>
            </div>
            <span className="best-store-badge">Best on {p.best_offer?.store}</span>
            {p.over_budget && (
              <span className="over-budget-tag">({inr(p.over_by)} over budget)</span>
            )}
          </div>

          {/* Multi-Store Comparison Chips (shown cleanly when 2+ stores exist) */}
          {offerCount > 1 && (
            <div className="live-stores-strip">
              {(p.offers || []).map((o, oIdx) => (
                <span
                  key={`${o.store}-${o.price}-${oIdx}`}
                  className={
                    "store-price-pill" +
                    (o.price === p.price ? " cheapest-store" : "") +
                    (o.is_trusted ? " trusted-pill" : "")
                  }
                >
                  {o.is_trusted && <span className="trusted-check-dot" title="Trusted Indian Store">✓</span>}{" "}
                  <b>{o.store}</b> · {inr(o.price)}
                </span>
              ))}
            </div>
          )}

          <div className="delivery-promise clean-delivery-line">
            <Icons.Truck />
            <span>
              {p.best_offer?.delivery || "Standard Delivery"} ·{" "}
              {p.best_offer?.return_policy || "Check Store Return Policy"}
              {p.best_offer?.warranty ? ` · ${p.best_offer.warranty}` : ""}
            </span>
          </div>
        </div>

        {/* Clean Action Column */}
        <div className="card-action-column">
          <a
            href={p.best_offer?.url || "#"}
            target="_blank"
            rel="noreferrer"
            className="action-btn-buy"
          >
            <span>Buy on {p.best_offer?.store}</span>
            <Icons.ArrowUpRight />
          </a>
          <button
            type="button"
            className="action-btn-details"
            onClick={() => onOpenDetails && onOpenDetails("stores")}
          >
            Details &amp; Reviews →
          </button>
          <div className="card-mini-action-row">
            <button
              type="button"
              className={"mini-toggle-btn" + (saved ? " is-saved" : "")}
              onClick={onSave}
              title={saved ? "Saved in Wishlist" : "Save to Wishlist"}
            >
              <Icons.Heart filled={saved} />
              <span>{saved ? "Saved" : "Save"}</span>
            </button>
            <button
              type="button"
              className={"mini-toggle-btn compare-btn" + (picked ? " is-picked" : "")}
              onClick={onPick}
              aria-pressed={picked}
              title={picked ? "Added to Compare" : "Add to Compare"}
            >
              <Icons.Scale />
              <span>{picked ? "Comparing" : "Compare"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Collapsible Tabs Bar */}
      <div className="ecom-card-tabs-bar">
        <button
          type="button"
          className={"card-tab" + (activeTab === "stores" ? " active" : "")}
          onClick={() => toggleTab("stores")}
        >
          Compare Stores ({offerCount})
        </button>
        <button
          type="button"
          className={"card-tab" + (activeTab === "reviews" ? " active" : "")}
          onClick={() => toggleTab("reviews")}
        >
          Customer Reviews {ra.status === "available" ? `(${ra.review_count})` : ra.status === "unavailable" ? "(0)" : ""}
        </button>
        <button
          type="button"
          className={"card-tab" + (activeTab === "specs" ? " active" : "")}
          onClick={() => toggleTab("specs")}
        >
          Specifications
        </button>
        <button
          type="button"
          className={"card-tab" + (activeTab === "alerts" ? " active" : "")}
          onClick={() => toggleTab("alerts")}
        >
          Price Alert
        </button>
      </div>

      {/* Tab Panels (Only mounted when a tab is open) */}
      {activeTab && (
        <div className="card-tab-content-panel">
        {/* 1. STORE COMPARISON */}
        {activeTab === "stores" && (
          <StoreComparisonTable product={p} showSavingsBanner={true} />
        )}

        {/* 2. AUTOMATIC PRODUCT-SPECIFIC REAL CUSTOMER REVIEWS & ABSA */}
        {activeTab === "reviews" && (
          <CustomerReviewsPanel
            key={p.id}
            product={p}
            onReviewsLoaded={onReviewsLoaded}
            autoFetch={true}
          />
        )}

        {/* 3. SPECIFICATIONS */}
        {activeTab === "specs" && (
          <div className="specs-table-container">
            <div className="specs-key-value-grid">
              {Object.entries(p.specs || {}).map(([key, val]) => (
                <div key={key} className="spec-row-item">
                  <span className="spec-label">{key}</span>
                  <span className="spec-value">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. PRICE DROP ALERT */}
        {activeTab === "alerts" && (
          <div className="price-alert-tab-panel">
            <div className="alert-callout">
              <h4>🔔 Set Real-Time Price Drop Alert</h4>
              <p>We will track Amazon, Flipkart, Croma, and Reliance Digital every hour and notify you when the price drops below your target.</p>
              <div className="alert-action-box">
                <button className="confirm-alert-btn" onClick={handleSetAlert}>
                  Set Alert for 10% Drop (Below {inr(p.price * 0.9)})
                </button>
                {alertSuccess && <span className="alert-success-msg">{alertSuccess}</span>}
              </div>
            </div>
          </div>
        )}
        </div>
      )}
    </div>
  );
}

function CompareMatrix({ items, onRemove, onClear, onOpenDetails, onBackToSearch, fullPage = false }) {
  if (!items || items.length < 2) {
    return (
      <section className="side-by-side-comparison-dock compare-empty-state">
        <div className="compare-empty-icon">⚖️</div>
        <h3>Compare Products Side-by-Side</h3>
        <p>
          {items?.length === 1
            ? `You have selected "${items[0].name}". Select at least 1 more product (even from a different search!) using "Add to Compare" to see a full side-by-side comparison.`
            : 'Check "Add to Compare" on any 2 or 3 products across your searches to compare live prices, trusted stores, delivery, warranty, specs, and AI review sentiment.'}
        </p>
        {onBackToSearch && (
          <button type="button" className="compare-back-btn" onClick={onBackToSearch}>
            ← Back to Search Products
          </button>
        )}
      </section>
    );
  }

  const lowestPrice = Math.min(...items.map((p) => p.price || Infinity));
  const highestScore = Math.max(...items.map((p) => p.score || 0));
  const keys = [...new Set(items.flatMap((p) => Object.keys(p.specs || {})))];

  const rows = [
    [
      "AI Value Score",
      (p) => (
        <span className={p.score === highestScore ? "compare-win-pill indigo" : "compare-val-strong"}>
          {Math.round(p.score || 85)}/100 {p.score === highestScore ? "★ Top Pick" : ""}
        </span>
      ),
    ],
    [
      "Lowest Store Price",
      (p) => (
        <span className={p.price === lowestPrice ? "compare-win-pill green" : "compare-val-strong"}>
          {inr(p.price)} {p.price === lowestPrice ? "🏆 Lowest" : ""}
        </span>
      ),
    ],
    [
      "Best Store & Trust",
      (p) => (
        <div className="compare-store-cell">
          <strong>{p.best_offer?.store || "–"}</strong>
          {p.best_offer?.store_badge && (
            <span className={`store-trust-badge ${getTrustBadgeClass(p.best_offer)}`}>
              {p.best_offer.store_badge}
            </span>
          )}
        </div>
      ),
    ],
    ["Stores Compared", (p) => `${(p.offers || []).length} live offer${(p.offers || []).length === 1 ? "" : "s"}`],
    ["Delivery", (p) => `🚚 ${p.best_offer?.delivery || "Standard Delivery"}`],
    ["Return Policy", (p) => p.best_offer?.return_policy || "Check Store Return Policy"],
    ["Warranty", (p) => p.best_offer?.warranty || "Verify Seller Warranty"],
    [
      "Customer Rating",
      (p) =>
        p.rating > 0
          ? `★ ${Number(p.rating).toFixed(1)}/5${p.rating_count ? ` (${Number(p.rating_count).toLocaleString("en-IN")})` : ""}`
          : "Not rated",
    ],
    [
      "Review Sentiment (ABSA)",
      (p) =>
        p.review_analysis?.status === "available"
          ? `${p.review_analysis.positive}% Positive (${p.review_analysis.review_count} written reviews)`
          : "Open Product Details to run live ABSA",
    ],
    ["Praised Features", (p) => p.review_analysis?.pros?.join(", ") || "–"],
    ...keys.map((k) => [k, (p) => p.specs?.[k] || "–"]),
  ];

  return (
    <section className={"side-by-side-comparison-dock" + (fullPage ? " full-page-compare" : "")}>
      <div className="dock-title-bar">
        <div>
          <h3>⚖️ Side-by-Side Product Comparison ({items.length} Products)</h3>
          <p className="dock-subtitle">Comparing live prices, trusted store status, delivery, warranty &amp; hardware specs</p>
        </div>
        <div className="dock-header-actions">
          {fullPage && onBackToSearch && (
            <button type="button" className="compare-back-btn" onClick={onBackToSearch}>
              ← Back to Search
            </button>
          )}
          <button type="button" className="close-dock-btn" onClick={onClear}>
            Clear All ✕
          </button>
        </div>
      </div>
      <div className="dock-table-wrapper">
        <table className="dock-comparison-table">
          <thead>
            <tr>
              <th>Feature / Specification</th>
              {items.map((p) => (
                <th key={p.id}>
                  <div className="dock-product-th">
                    {onRemove && (
                      <button
                        type="button"
                        className="dock-col-remove-btn"
                        onClick={() => onRemove(p.id)}
                        title={`Remove ${p.name}`}
                      >
                        ✕
                      </button>
                    )}
                    <ProductImage
                      src={p.image}
                      alt={p.name}
                      brand={p.brand}
                      className="dock-img"
                      placeholderClassName="product-placeholder-box dock-img"
                    />
                    <span className="dock-prod-name">{p.name}</span>
                    <strong className="dock-price">{inr(p.price)}</strong>
                    <div className="dock-col-actions">
                      {onOpenDetails && (
                        <button
                          type="button"
                          className="winner-details-btn"
                          onClick={() => onOpenDetails(p)}
                        >
                          Details
                        </button>
                      )}
                      <a
                        href={p.best_offer?.url || "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="winner-buy-btn"
                      >
                        Buy ↗
                      </a>
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, f]) => (
              <tr key={label}>
                <td className="row-label-cell">{label}</td>
                {items.map((p) => (
                  <td key={p.id}>{f(p)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ChatAssistant({ onSearchDeal, onClose }) {
  const [messages, setMessages] = useState([
    {
      sender: "assistant",
      text: "Hello! I am your ShopWise AI Shopping Agent. Ask me anything in natural language: find products within your budget, compare models, or analyze customer sentiment!",
      recommendations: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape" && onClose) {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  async function send(msgText = input) {
    if (!msgText.trim()) return;
    const msg = msgText.trim();
    setInput("");
    setMessages((m) => [...m, { sender: "user", text: msg, recommendations: [] }]);
    setLoading(true);
    try {
      const res = await api.chat(msg);
      setMessages((m) => [
        ...m,
        {
          sender: "assistant",
          text: res.reply,
          recommendations: res.recommendations || [],
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          sender: "assistant",
          text: "I can help search products directly! Use the top search bar to compare live store prices.",
          recommendations: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="conversational-agent-view">
      <div className="agent-header-bar">
        <div className="agent-title-info">
          <div className="agent-title-status-line">
            <span className="agent-online-pulse" title="AI Agent Active" />
            <h3>🤖 Conversational AI Shopping Assistant</h3>
          </div>
          <p>Powered by Google Gemini API & multi-store live price intelligence</p>
        </div>
        {onClose && (
          <div className="agent-header-actions">
            <button
              type="button"
              className="agent-close-btn"
              onClick={onClose}
              title="Close Shopping Assistant (Esc)"
              aria-label="Close Shopping Assistant"
            >
              <span className="agent-close-btn-text">Close Assistant</span>
              <span className="agent-close-btn-icon" aria-hidden="true">✕</span>
            </button>
          </div>
        )}
      </div>

      <div className="agent-chat-stream">
        {messages.map((m, idx) => (
          <div key={idx} className={"chat-row " + m.sender}>
            <div className="chat-bubble">
              <span className="bubble-sender">{m.sender === "assistant" ? "ShopWise AI" : "You"}</span>
              <p style={{ whiteSpace: "pre-line" }}>{m.text}</p>

              {/* Embedded Recommendation Cards */}
              {(m.recommendations || []).length > 0 && (
                <div className="chat-recommendations-grid">
                  {m.recommendations.map((card) => (
                    <div key={card.id} className="chat-deal-card">
                      <ProductImage src={card.image} alt={card.name} brand={card.brand} className="chat-deal-thumb" placeholderClassName="product-placeholder-box chat-deal-thumb" />
                      <div className="chat-deal-info">
                        <h5>{card.name}</h5>
                        <p className="chat-deal-price">
                          <strong>{inr(card.price)}</strong> on {card.store}
                        </p>
                        <button
                          className="chat-explore-btn"
                          onClick={() => onSearchDeal(card.name)}
                        >
                          View Live Deals ↗
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-row assistant">
            <div className="chat-bubble loading">
              <p>Analyzing products, comparing store prices, and reviewing specifications...</p>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Prompt Chips */}
      <div className="quick-suggestions-bar">
        <span>Try asking:</span>
        <button onClick={() => send("Which is the best laptop for programming under ₹60,000?")}>
          Best laptop for programming under ₹60,000
        </button>
        <button onClick={() => send("Compare Samsung Galaxy S24 and Apple iPhone 15")}>
          Compare S24 vs iPhone 15
        </button>
        <button onClick={() => send("Best noise cancelling headphones below ₹8,000")}>
          ANC headphones under ₹8,000
        </button>
      </div>

      <form
        className="chat-input-form"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask in natural language e.g. 'I need a smartphone under ₹25,000 with a good camera and battery'..."
        />
        <button type="submit" disabled={loading}>Send</button>
      </form>
    </section>
  );
}

function Wishlist({ onSave, user, onRequireAuth }) {
  const [rows, setRows] = useState(null);

  const load = () => {
    if (!user) {
      try {
        const guestSaved = JSON.parse(localStorage.getItem("shopwise_guest_saved") || "[]");
        setRows(guestSaved.map((p, idx) => ({ id: p.id || idx, product: p })));
      } catch {
        setRows([]);
      }
      return;
    }
    api.saved()
      .then(setRows)
      .catch((err) => {
        console.warn("Failed to load wishlist:", err);
        setRows([]);
      });
  };

  useEffect(() => { load(); }, [user]);

  if (!rows) return <p className="loading-state-text">Loading your saved products…</p>;

  return (
    <section className="dashboard-container">
      <div className="dashboard-header-flex">
        <div>
          <h2>❤️ Saved Products ({rows.length})</h2>
          <p className="dashboard-sub">Your personal bookmarks and cross-platform price tracking</p>
        </div>
        {!user && (
          <button type="button" className="guard-login-btn" style={{ padding: "8px 16px", fontSize: "12.5px" }} onClick={onRequireAuth}>
            Sign In to Sync Across Devices ☁️
          </button>
        )}
      </div>

      {!user && rows.length > 0 && (
        <div className="guest-wishlist-notice" style={{ background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "8px", padding: "10px 14px", marginBottom: "16px", fontSize: "13px", color: "#1E40AF" }}>
          <span>💡 These {rows.length} products are saved in your current browser session. </span>
          <button type="button" style={{ background: "none", border: "none", color: "#2563EB", fontWeight: "700", cursor: "pointer", padding: "0 4px", textDecoration: "underline" }} onClick={onRequireAuth}>
            Sign In or Create an Account
          </button>
          <span> to sync them across your mobile and desktop devices!</span>
        </div>
      )}

      {rows.length === 0 && (
        <div className="empty-wishlist-box" style={{ background: "#F8FAFC", border: "1.5px dashed #CBD5E1", borderRadius: "12px", padding: "36px 20px", textAlign: "center", margin: "16px 0" }}>
          <div style={{ fontSize: "36px", marginBottom: "8px" }}>🤍</div>
          <h3 style={{ fontSize: "17px", color: "#173B70", marginBottom: "4px" }}>Your wishlist is currently empty</h3>
          <p style={{ fontSize: "13px", color: "#64748B" }}>Browse products or trending deals and click <b>Add to Wishlist</b> to save items here.</p>
        </div>
      )}

      <div className="wishlist-cards-grid">
        {rows.map(({ product: p }) => (
          <div key={p.id} className="wishlist-item-card">
            <ProductImage src={p.image} alt={p.name} brand={p.brand} className="wishlist-item-img" placeholderClassName="product-placeholder-box wishlist-item-img" />
            <div className="wishlist-item-body">
              <h4>{p.name}</h4>
              <p className="wishlist-item-store">Lowest on: <b>{p.best_offer?.store || p.bestStore || "Online"}</b></p>
              <div className="wishlist-item-bottom">
                <strong style={{ color: "#172033", fontSize: "14px" }}>{inr(p.price)}</strong>
                <button
                  type="button"
                  className="remove-wishlist-btn"
                  onClick={async () => {
                    await onSave(p);
                    load();
                  }}
                  title="Remove from Wishlist"
                >
                  Remove ✕
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function PriceAlerts({ onRequireAuth, user }) {
  const [alerts, setAlerts] = useState(null);
  const load = () => {
    if (!user) return setAlerts([]);
    api.alerts().then(setAlerts).catch(() => setAlerts([]));
  };
  useEffect(() => { load(); }, [user]);

  if (!user) {
    return (
      <div className="protected-page-guard">
        <div className="guard-icon">🔔</div>
        <h3>Sign In to Track Price Drops</h3>
        <p>Set custom target prices on your favorite products across Amazon, Flipkart, Croma, and Reliance Digital.</p>
        <button className="guard-login-btn" onClick={onRequireAuth}>
          Sign In / Create Account
        </button>
      </div>
    );
  }

  if (!alerts) return <p className="loading-state-text">Loading alerts…</p>;
  return (
    <section className="dashboard-container">
      <h2>🔔 Price Drop Alerts</h2>
      <p className="dashboard-sub">We track store prices and notify you when an item drops below your target price.</p>
      {alerts.length === 0 && (
        <p className="empty-state-notice">No price alerts set. Open 'Price Drop Alerts' on any product card to create an alert.</p>
      )}
      <div className="alerts-list">
        {alerts.map((a) => (
          <div key={a.id} className="alert-row-card">
            <div>
              <strong>{a.name}</strong>
              <p>Target: <b>{inr(a.target_price)}</b> · Current: {inr(a.current_price)} ({a.store})</p>
            </div>
            <div className="alert-controls">
              <span className="status-badge-green">{a.status}</span>
              <button
                className="remove-alert-btn"
                onClick={async () => {
                  await api.deleteAlert(a.id);
                  load();
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function SearchHistory({ onRun, user, onRequireAuth }) {
  const [rows, setRows] = useState(null);
  const load = () => {
    if (!user) {
      setRows([]);
      return;
    }
    api.history().then(setRows).catch(() => setRows([]));
  };
  useEffect(() => { load(); }, [user]);

  if (!user) {
    return (
      <div className="protected-page-guard">
        <div className="guard-icon">🕒</div>
        <h3>Sign In to View Search History</h3>
        <p>Sign in to review past queries, resume comparisons, and personalize your shopping experience across sessions.</p>
        <button className="guard-login-btn" onClick={onRequireAuth}>
          Sign In / Create Account
        </button>
      </div>
    );
  }

  if (!rows) return <p className="loading-state-text">Loading history…</p>;
  return (
    <section className="dashboard-container">
      <div className="dashboard-header-flex">
        <h2>🕒 Search History</h2>
        {rows.length > 0 && (
          <button className="clear-all-link" onClick={async () => { await api.clearHistory(); load(); }}>
            Clear All History
          </button>
        )}
      </div>
      {rows.length === 0 && <p className="empty-state-notice">No past searches recorded yet.</p>}
      <div className="history-pill-list">
        {rows.map((r) => (
          <button key={r.id} className="history-query-pill" onClick={() => onRun(r.query)}>
            <span>🔍 {r.query}</span>
            <small>{new Date(r.created).toLocaleString("en-IN")}</small>
          </button>
        ))}
      </div>
    </section>
  );
}

function UserProfileModal({ user, onClose, onLogout, savedCount }) {
  if (!user) return null;
  const memberDate = user.created
    ? new Date(user.created).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })
    : "Active Member";

  return (
    <div className="auth-overlay-backdrop" onClick={onClose}>
      <div className="profile-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="auth-header-row">
          <h3>👤 My Account Profile</h3>
          <button type="button" className="auth-close-btn" onClick={onClose} title="Close">✕</button>
        </div>

        <div className="profile-avatar-row">
          <div className="profile-avatar-circle">
            {(user.name || "U").charAt(0).toUpperCase()}
          </div>
          <div className="profile-user-names">
            <h4>{user.name}</h4>
            <small>{user.email}</small>
          </div>
        </div>

        <div className="profile-info-grid">
          <div className="profile-stat-box">
            <small>Wishlist Items</small>
            <strong>{savedCount}</strong>
          </div>
          <div className="profile-stat-box">
            <small>Account Status</small>
            <strong style={{ color: "#16A34A" }}>Verified</strong>
          </div>
        </div>

        <div className="profile-detail-list">
          <div className="profile-detail-row">
            <span>User ID:</span>
            <b>#{user.id}</b>
          </div>
          <div className="profile-detail-row">
            <span>Full Name:</span>
            <b>{user.name}</b>
          </div>
          <div className="profile-detail-row">
            <span>Email Address:</span>
            <b>{user.email}</b>
          </div>
          <div className="profile-detail-row">
            <span>Member Since:</span>
            <b>{memberDate}</b>
          </div>
        </div>

        <div className="profile-actions-row">
          <button type="button" className="profile-signout-btn" onClick={onLogout}>
            Sign Out
          </button>
          <button type="button" className="profile-close-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function AuthModal({ onClose, onDone }) {
  const [mode, setMode] = useState("login"); // 'login' | 'register'
  const [f, setF] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const switchMode = (newMode) => {
    setMode(newMode);
    setErr("");
    setSuccessMsg("");
    setF({ ...f, password: "", confirmPassword: "" });
  };

  async function submit(e) {
    e.preventDefault();
    setErr("");
    setSuccessMsg("");

    const emailTrimmed = f.email.trim().toLowerCase();
    const passwordTrimmed = f.password.trim();

    if (!emailTrimmed) {
      return setErr("Please enter your email address.");
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailTrimmed)) {
      return setErr("Please enter a valid email address (e.g. name@example.com).");
    }
    if (!passwordTrimmed) {
      return setErr("Please enter your password.");
    }

    if (mode === "register") {
      const nameTrimmed = f.name.trim();
      if (!nameTrimmed) {
        return setErr("Please enter your full name.");
      }
      if (passwordTrimmed.length < 6) {
        return setErr("Password must be at least 6 characters long.");
      }
      if (f.password !== f.confirmPassword) {
        return setErr("Passwords do not match. Please verify and re-enter.");
      }

      setLoading(true);
      try {
        const r = await api.register({
          name: nameTrimmed,
          email: emailTrimmed,
          password: f.password,
        });
        setSuccessMsg(r.message || "Registration successful! Please sign in with your credentials.");
        setMode("login");
        setF({ name: "", email: emailTrimmed, password: "", confirmPassword: "" });
      } catch (x) {
        setErr(x.message || "Registration failed. Please try again.");
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(true);
      try {
        const r = await api.login({
          email: emailTrimmed,
          password: f.password,
        });
        setToken(r.token);
        onDone(r.user);
      } catch (x) {
        setErr(x.message || "Invalid email or password. Please verify your credentials.");
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <div className="auth-overlay-backdrop" onClick={onClose}>
      <form className="auth-dialog-card" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <div className="auth-header-row">
          <h3>{mode === "login" ? "Sign In to ShopWise V3" : "Create Account"}</h3>
          <button type="button" className="auth-close-btn" onClick={onClose} title="Close">✕</button>
        </div>

        {successMsg && (
          <div className="auth-success-msg">
            <span>✅</span>
            <span>{successMsg}</span>
          </div>
        )}

        {err && (
          <div className="auth-err-msg">
            <span>⚠️</span>
            <span>{err}</span>
          </div>
        )}

        {mode === "register" && (
          <label>
            Full Name
            <input
              type="text"
              value={f.name}
              onChange={set("name")}
              placeholder="e.g. John Doe"
              autoComplete="name"
              disabled={loading}
              required
            />
          </label>
        )}

        <label>
          Email Address
          <input
            type="email"
            value={f.email}
            onChange={set("email")}
            placeholder="e.g. name@example.com"
            autoComplete="email"
            disabled={loading}
            required
          />
        </label>

        <label>
          Password
          <div className="password-field-container">
            <input
              type={showPassword ? "text" : "password"}
              value={f.password}
              onChange={set("password")}
              placeholder={mode === "register" ? "At least 6 characters" : "Enter your password"}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              disabled={loading}
              required
            />
            <button
              type="button"
              className="password-toggle-btn"
              onClick={() => setShowPassword(!showPassword)}
              title={showPassword ? "Hide password" : "Show password"}
              tabIndex={-1}
            >
              {showPassword ? "🙈" : "👁️"}
            </button>
          </div>
        </label>

        {mode === "register" && (
          <label>
            Confirm Password
            <div className="password-field-container">
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={f.confirmPassword}
                onChange={set("confirmPassword")}
                placeholder="Re-enter your password"
                autoComplete="new-password"
                disabled={loading}
                required
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                title={showConfirmPassword ? "Hide password" : "Show password"}
                tabIndex={-1}
              >
                {showConfirmPassword ? "🙈" : "👁️"}
              </button>
            </div>
          </label>
        )}

        <button type="submit" className="auth-submit-btn" disabled={loading}>
          {loading ? (
            <span>{mode === "login" ? "Signing In…" : "Creating Account…"}</span>
          ) : (
            <span>{mode === "login" ? "Sign In" : "Register"}</span>
          )}
        </button>

        <button
          type="button"
          className="auth-toggle-mode-btn"
          disabled={loading}
          onClick={() => switchMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}

function HomePage({ onSearch, onSave, savedIds }) {
  const [heroInput, setHeroInput] = useState("");
  const heroInputRef = useRef(null);

  const quickSearches = [
    "Samsung S24",
    "Samsung S24 Ultra",
    "iPhone 15",
    "HP laptop i5 16GB RAM",
    "Boat wireless earbuds",
    "Laptop under ₹50,000",
  ];

  function submitHero(e) {
    if (e) e.preventDefault();
    const term = heroInput.trim();
    if (term) onSearch(term);
  }

  return (
    <div className="homepage-container">
      {/* 1. Modern Dark Indigo Gradient Hero Banner */}
      <section className="hero-banner-section">
        <div className="hero-banner-card hero-dark-gradient">
          <div className="hero-badge-pill hero-glow-badge">
            <span className="sparkle-icon">✨</span>
            <span>EMPOWERED BY GOOGLE GEMINI AI &amp; LIVE SERPAPI</span>
          </div>
          <h1 className="hero-heading hero-display-title">
            Find the Best Product Deal,
            <br />
            <span className="hero-gradient-accent">Guaranteed.</span>
          </h1>
          <p className="hero-subtitle hero-dark-subtitle">
            Search products using natural language. Our AI comparison agent instantly scans{" "}
            <b>Amazon.in, Flipkart, Croma, Reliance Digital</b> &amp; verified Indian stores with real ABSA customer review intelligence.
          </p>

          {/* Central Search Bar in the Middle */}
          <form className="hero-pill-search-form" onSubmit={submitHero}>
            <span className="hero-search-sparkle" aria-hidden="true">
              <Icons.Sparkles />
            </span>
            <input
              ref={heroInputRef}
              type="text"
              className="hero-pill-search-input"
              value={heroInput}
              onChange={(e) => setHeroInput(e.target.value)}
              placeholder="What are you shopping for? Try: 'Samsung S24' or 'laptop under 60000'..."
              autoComplete="off"
              spellCheck="false"
            />
            {heroInput && heroInput.length > 0 && (
              <button
                type="button"
                className="search-clear-btn"
                style={{ marginRight: "4px" }}
                onClick={() => {
                  setHeroInput("");
                  if (heroInputRef.current) heroInputRef.current.focus();
                }}
                title="Clear search"
                aria-label="Clear search input"
              >
                ✕
              </button>
            )}
            <button type="submit" className="hero-scout-btn" title="Scout best deals across Indian retailers">
              <span>Scout Deals</span>
              <Icons.Search />
            </button>
          </form>

          <div className="hero-quick-prompts">
            <span className="prompts-label">Trending:</span>
            <div className="prompt-chips-wrapper">
              {quickSearches.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="hero-prompt-chip"
                  onClick={() => {
                    setHeroInput(q);
                    onSearch(q);
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          <div className="hero-trust-strip">
            <span className="hero-trust-item">
              <Icons.ShieldCheck /> Verified Indian Retailers
            </span>
            <span className="hero-trust-dot" />
            <span className="hero-trust-item">
              <Icons.Sparkles /> Automatic Review ABSA
            </span>
            <span className="hero-trust-dot" />
            <span className="hero-trust-item">
              <Icons.Scale /> Cross-Store Live Comparison
            </span>
          </div>
        </div>
      </section>

      {/* 2. How Our AI Comparison Agent Works */}
      <section className="home-section why-shopwise-section">
        <div className="home-section-header text-center">
          <span className="section-eyebrow">THE SHOPWISE DIFFERENCE</span>
          <h2 className="section-title">How our AI Comparison Agent Works</h2>
          <p className="section-subtitle">Engineered to eliminate e-commerce advertising bias and fake review noise</p>
        </div>
        <div className="pillars-grid">
          <div className="pillar-card">
            <div className="pillar-icon-well">🎯</div>
            <h3>NLP Intent &amp; Model Parser</h3>
            <p>Gemini parses natural language including budget limits, RAM, storage, and exact variants so <b>Samsung S24</b> never mixes with covers or Ultra models.</p>
          </div>
          <div className="pillar-card">
            <div className="pillar-icon-well">🛡️</div>
            <h3>Trusted Indian Store Scoring</h3>
            <p>Prioritizes verified Indian retailers (Amazon.in, Flipkart, Croma, Reliance Digital) with transparent delivery, return policy, and warranty info.</p>
          </div>
          <div className="pillar-card">
            <div className="pillar-icon-well">📊</div>
            <h3>Real Customer Reviews &amp; ABSA</h3>
            <p>Automatically fetches genuine product reviews and analyzes Camera, Battery, Display, Performance, and Build Quality with zero fabricated data.</p>
          </div>
          <div className="pillar-card">
            <div className="pillar-icon-well">🔔</div>
            <h3>AI Assistant &amp; Price Guard</h3>
            <p>Chat with our AI shopping advisor or set automated price drop alerts to grab the best verified deal at the right moment.</p>
          </div>
        </div>
      </section>

      {/* 3. Explore Catalog — Category Cards */}
      <section className="home-section">
        <div className="home-section-header">
          <div>
            <span className="section-eyebrow">EXPLORE CATALOG</span>
            <h2 className="section-title">Shop by Category</h2>
            <p className="section-subtitle">Deep hardware attributes and live cross-store pricing across top Indian retail segments</p>
          </div>
        </div>
        <div className="category-cards-grid">
          {TOP_CATEGORIES.map((cat) => (
            <div
              key={cat.id}
              className="home-category-card"
              onClick={() => onSearch(cat.query)}
            >
              <div className="category-card-icon-well">{cat.icon}</div>
              <h3 className="category-card-title">{cat.label}</h3>
              <span className="category-card-action">Compare Live Prices →</span>
            </div>
          ))}
        </div>
      </section>

      {/* 4. Exclusive Finds — Trending Deals Grid */}
      <section className="home-section">
        <div className="home-section-header">
          <div>
            <span className="section-eyebrow">EXCLUSIVE FINDS</span>
            <h2 className="section-title">Top Scored Tech Products</h2>
            <p className="section-subtitle">Real-time cross-platform comparison across Amazon.in, Flipkart, Croma &amp; Reliance Digital</p>
          </div>
          <span className="live-stores-pill">
            <span className="live-dot"></span> Live Store Price Feeds
          </span>
        </div>

        <div className="trending-deals-grid">
          {TRENDING_DEALS.map((deal) => {
            const isSaved = savedIds?.has(String(deal.id));
            return (
              <div
                key={deal.id}
                className="trending-deal-card"
                onClick={() => onSearch(deal.searchQuery)}
              >
                <div className="deal-image-container">
                  <div className="deal-card-badge">{deal.badge}</div>
                  <button
                    type="button"
                    className={"deal-heart-fab" + (isSaved ? " is-saved" : "")}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSave &&
                        onSave({
                          id: deal.id,
                          name: deal.name,
                          price: deal.price,
                          brand: deal.brand,
                          image: deal.image,
                          best_offer: { store: deal.bestStore, price: deal.price },
                        });
                    }}
                    title={isSaved ? "In Wishlist (click to remove)" : "Save to Wishlist"}
                    aria-label={isSaved ? "Remove from wishlist" : "Add to wishlist"}
                  >
                    {isSaved ? "❤️" : "🤍"}
                  </button>
                  <ProductImage
                    src={deal.image}
                    alt={deal.name}
                    brand={deal.brand}
                    className="deal-img"
                    placeholderClassName="product-placeholder-box deal-img"
                  />
                </div>
                <div className="deal-body">
                  <span className="deal-brand-tag">{deal.brand}</span>
                  <h4 className="deal-title">{deal.name}</h4>
                  <div className="deal-rating-row">
                    <span className="deal-star-inline">★ {deal.rating}</span>
                    <small className="deal-reviews-count">
                      ({deal.reviewsCount.toLocaleString("en-IN")} ratings)
                    </small>
                  </div>
                  <div className="deal-savings-chip">💰 {deal.savingsText}</div>

                  <div className="deal-footer-pricing">
                    <div>
                      <span className="deal-best-from-label">BEST DEALS FROM</span>
                      <div className="deal-price-block">
                        <span className="deal-curr-price">{inr(deal.price)}</span>
                        <span className="deal-mrp-strike">{inr(deal.mrp)}</span>
                      </div>
                    </div>
                    <span className="deal-store-pill">{deal.bestStore}</span>
                  </div>

                  <button
                    type="button"
                    className="deal-compare-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSearch(deal.searchQuery);
                    }}
                  >
                    See Deals ↗
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
