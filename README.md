ShopWise V3 – AI Shopping & Price Comparison Agent
ShopWise V3 is an AI-powered shopping research and price comparison platform inspired by the user experience of Amazon and Flipkart. It allows users to search across consumer electronics and home appliances, discover live prices across supported retailers (Amazon.in, Flipkart, Croma, Reliance Digital), extract authentic customer reviews, perform Aspect-Based Sentiment Analysis (ABSA) on 8 hardware dimensions, and interact with a conversational AI shopping assistant powered by the Google Gemini API.
---
🌟 Key Features
Amazon & Flipkart Inspired Interface:
Modern e-commerce layout with delivery location indicators, category strips, brand filters, budget selectors, customer ratings, and side-by-side comparison matrix.
Exact Model Match badges and alternative product identification.
Live Multi-Store Price Comparison:
Compares live offers across Amazon.in, Flipkart, Croma, and Reliance Digital.
Calculates lowest price, store savings ("Save ₹1,491 on Flipkart"), and stock availability.
Direct store out-links ("Buy on Store ↗").
Authentic Review & Aspect-Based Sentiment Analysis (ABSA):
Zero fabricated reviews: Analyzes genuine verified buyer reviews only.
Evaluates 8 core hardware dimensions: Performance, Battery, Camera, Display, Build Quality, Sound Quality, Price & Value, and Reliability.
Identifies praised features (Pros) and customer cautions (Cons).
If written review text is unavailable, transparently reports `status: "unavailable"` and calculates a clearly labeled star-rating satisfaction score.
Conversational AI Shopping Assistant:
Powered by Google Gemini API with multi-turn shopping intelligence.
Understands natural language requests (e.g., "Which is the best laptop for programming under ₹60,000?").
Generates interactive product recommendation cards directly in chat.
User Management & Shopping Utilities:
Secure registration and login with bcrypt password hashing and HS256 JWT tokens.
User profile with personalized brand and category preferences.
Real-time Price Drop Alerts tracking.
Saved Wishlist and Search History.
---
🚀 Quick Start (One-Click Launch)
Double-click `Start_ShopWise.bat` in the project root. It will:
Start the FastAPI backend on `http://127.0.0.1:8000`.
Start the React / Vite frontend on `http://localhost:5173`.
Open your browser to the ShopWise V3 shopping platform.
---
🛠️ Manual Setup Instructions
Prerequisites
Python 3.10+
Node.js LTS (v18+)
VS Code
1. Backend Setup
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Backend API Docs: `http://127.0.0.1:8000/docs`
Health Endpoint: `http://127.0.0.1:8000/api/health`
2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.
---
🔑 Environment Configuration (`backend/.env`)
```ini
DATABASE_URL=sqlite:///./shopwise.db
JWT_SECRET=your-secure-random-secret-key-2026
JWT_HOURS=24

# Google Gemini API Key (Get free key from https://aistudio.google.com/)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# Optional Live Search (Get key from https://serpapi.com/)
SERPAPI_KEY=

CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```
---
🧪 Automated Testing & Acceptance Verification
Run the comprehensive acceptance test runner:
```powershell
python run_acceptance_tests.py
```
Verifies all 8 mandatory acceptance criteria:
TEST 1: Exact model matching for "Samsung Galaxy S24"
TEST 2: Strict spec filtering for "HP laptop under ₹60,000 with 16GB RAM"
TEST 3: Verified model images, structured specs, and multi-store prices
TEST 4: Genuine review sentiment analysis (no fake reviews)
TEST 5: Cross-platform price comparison across Amazon, Flipkart, Croma, Reliance Digital
TEST 6: Conversational AI assistant recommendation reasoning
TEST 7: User registration, login, wishlist, price alerts, and search history
TEST 8: Error resilience to missing API keys, short queries, and invalid tokens
