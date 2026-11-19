const BASE = import.meta.env.VITE_API_URL || "";

export const setToken = (t) => {
  if (t) {
    localStorage.setItem("sw_token", t);
    localStorage.setItem("shopwise_token", t);
  } else {
    localStorage.removeItem("sw_token");
    localStorage.removeItem("shopwise_token");
  }
};

export const getToken = () => localStorage.getItem("sw_token") || localStorage.getItem("shopwise_token") || "";
export const hasToken = () => !!(getToken());

async function call(path, method = "GET", body) {
  const currentToken = getToken();
  let res;
  try {
    res = await fetch(BASE + path, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (netErr) {
    throw new Error("Unable to connect to the backend server. Please verify the server is running on http://localhost:8000.");
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    // If unauthorized on protected routes (not login/register attempts), wipe stale token
    if (res.status === 401 && path !== "/api/auth/login" && path !== "/api/auth/register") {
      setToken("");
    }
    const d = data.detail;
    throw new Error(
      typeof d === "string"
        ? d
        : Array.isArray(d)
        ? d.map((x) => x.msg || x).join(", ")
        : "An error occurred with the request."
    );
  }
  return data;
}

export const api = {
  // Health & Metadata
  health: () => call("/api/health"),
  categories: () => call("/api/categories"),

  // Auth
  register: (b) => call("/api/auth/register", "POST", b),
  login: (b) => call("/api/auth/login", "POST", b),
  me: () => call("/api/auth/me"),

  // Search
  search: (query, budget = null) => call("/api/search", "POST", { query, budget }),
  searchStream: async (query, budget = null, onStep = null) => {
    const currentToken = getToken();
    let res;
    try {
      res = await fetch(BASE + "/api/search/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
        },
        body: JSON.stringify({ query, budget }),
      });
    } catch {
      return call("/api/search", "POST", { query, budget });
    }

    if (!res.ok || !res.body) {
      return call("/api/search", "POST", { query, budget });
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let finalResult = null;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";

      for (const chunk of chunks) {
        const lines = chunk.split("\n");
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.slice(5).trim();
          if (!jsonStr) continue;
          try {
            const evt = JSON.parse(jsonStr);
            if (evt.type === "step" && typeof onStep === "function") {
              onStep(evt);
            } else if (evt.type === "result" && evt.data) {
              finalResult = evt.data;
            }
          } catch {
            // Ignore malformed SSE frame
          }
        }
      }
    }

    if (finalResult) return finalResult;
    return call("/api/search", "POST", { query, budget });
  },

  // Conversational AI Assistant
  chat: (message, history = []) => call("/api/chat", "POST", { message, history }),

  // Product-Specific Written Customer Reviews & ABSA
  extractReviews: (product, forceRefresh = false) =>
    call("/api/reviews/extract", "POST", { product, force_refresh: forceRefresh }),
  getProductReviews: (product, forceRefresh = false) =>
    call(`/api/products/${encodeURIComponent(String(product.id))}/reviews`, "POST", {
      name: product.name,
      brand: product.brand || "",
      model: product.model || "",
      rating: product.rating ?? null,
      rating_count: product.rating_count || 0,
      specs: product.specs || null,
      serpapi_product_id: product.serpapi_product_id || "",
      immersive_product_page_token: product.immersive_product_page_token || "",
      serpapi_immersive_product_api: product.serpapi_immersive_product_api || "",
      serpapi_product_api: product.serpapi_product_api || "",
      force_refresh: forceRefresh,
    }),

  // Price Drop Alerts
  alerts: () => call("/api/alerts"),
  createAlert: (b) => call("/api/alerts", "POST", b),
  deleteAlert: (id) => call(`/api/alerts/${id}`, "DELETE"),

  // Comparisons
  saveComparison: (product_ids, query = "") => call("/api/comparisons", "POST", { product_ids, query }),

  // Search History
  history: () => call("/api/history"),
  clearHistory: () => call("/api/history", "DELETE"),

  // Wishlist
  saved: () => call("/api/saved"),
  save: (product) => call("/api/saved", "POST", { product }),
  unsave: (productId) => call(`/api/saved/${encodeURIComponent(productId)}`, "DELETE"),
};
