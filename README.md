# Muze — Music Discovery & Recommendation

A Streamlit-based music recommendation app with Spotify integration, songwriter credits, and contextual song insights.

---

## Getting Started

### Prerequisites

- Python 3.8+
- A Spotify Developer account (free) — only needed for real listening data; the app runs in demo mode without it

### Installation

```bash
cd applied-ai-system-project
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd src
streamlit run app.py
```

---

## Spotify Setup

### 1. Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io), connect your repo, and set the main file to `src/app.py`
3. Your app URL will be something like `https://yourname-muze.streamlit.app` — note it down

### 2. Create a Spotify App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in
2. Click **Create app**, fill in any name and description
3. Under **Redirect URIs**, add your Streamlit Cloud URL with `/callback`:
   ```
   https://yourname-muze.streamlit.app/callback
   ```
4. Save and copy your **Client ID** and **Client Secret**

### 3. Add Secrets on Streamlit Cloud

In your app's Streamlit Cloud dashboard go to **Settings → Secrets** and add:

```toml
SPOTIFY_CLIENT_ID = "your_client_id_here"
SPOTIFY_CLIENT_SECRET = "your_client_secret_here"
SPOTIFY_REDIRECT_URI = "https://yourname-muze.streamlit.app/callback"
```

Streamlit Cloud encrypts these — they are never exposed in the UI or source code.

### 4. Authorize in the App

Open the **Connect Spotify** tab and click **Connect to Spotify**. You'll be redirected to Spotify's authorization page — after approving, the app handles the token exchange automatically.

---

## Features

| Feature | Description |
|---------|-------------|
| **Spotify Integration** | Connects via OAuth to pull your real top tracks and listening history |
| **Recommendations** | Content-based filtering by genre, mood, energy, tempo, danceability, and more |
| **Writer Credits** | Browse the songwriters behind your most-played tracks |
| **Song Insights** | RAG-powered contextual info on recommended songs |
| **Spotify Vibes** | Extracts dominant colors from your top album art and tints the UI palette |
| **Analytics** | Reliability tests and confidence scoring for the recommendation engine |
| **Demo Mode** | Full app experience with sample data — no Spotify account needed |

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Muze App                        │
│               (Streamlit Web Interface)             │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Spotify    │ │ Recommender │ │     RAG     │
│  Client     │ │   Engine    │ │   Engine    │
│ (OAuth/API) │ │ (Scoring)   │ │  (Context)  │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       ▼
              ┌─────────────────┐
              │  Data Manager   │
              │ (Songs/Writers) │
              └─────────────────┘
```

### Components

| File | Role |
|------|------|
| `app.py` | Streamlit UI, theming, navigation |
| `spotify_client.py` | OAuth flow and Spotify Web API calls |
| `recommender.py` | Weighted scoring engine with writer tracking |
| `data_manager.py` | Song catalog and writer data |
| `rag_engine.py` | Retrieval-Augmented Generation for song context |
| `test_harness.py` | Automated reliability tests |

---

## Scoring Algorithm

Extends the Module 3 weighted scoring system:

| Signal | Weight |
|--------|--------|
| Genre match | +2.0 |
| Mood match | +1.0 |
| Energy closeness | `(1 − gap) × 1.5` |
| Writer match | +1.5 |
| Tempo match | `(1 − gap) × 0.5` |
| Danceability match | `(1 − gap) × 0.5` |
| Valence match | `(1 − gap) × 0.5` |
| Acoustic bonus | +0.5 |

---

## Design Decisions

- **Env-var credentials** — Spotify keys never appear in the UI, reducing the risk of accidental exposure
- **Demo mode** — allows testing all features without a Spotify account
- **Spotify Vibes** — album art colors are darkened via Pillow quantization then lightened to pastels for the background gradient
- **Fallback RAG** — in-memory store used when ChromaDB is unavailable
- **Confidence scoring** — heuristic based on data completeness (genre, mood, audio features, writer info)

---

## Running Tests

```bash
cd src
python test_harness.py
```

---

## Reflection

### What I Learned
1. **OAuth flows in web apps** — handling redirect URIs, code exchange, and token expiry
2. **RAG architecture** — combining vector retrieval with generative context
3. **Streamlit theming** — CSS injection, font loading, and the limits of overriding Streamlit's own styles

### Limitations
- Demo catalog is small; real recommendations improve significantly with Spotify data
- RAG context is template-based without a live LLM; integrating Claude/OpenAI would enrich insights
- Writer data for demo songs is manually mapped

---

## Optional Stretch Features

| Feature | Status |
|---------|--------|
| RAG Enhancement | ✅ |
| Test Harness | ✅ |
| Writer / Composer Credits | ✅ |
| Parameter Tuning | ✅ |
| Spotify Vibes (dynamic theming) | ✅ |

---

**GitHub:** [https://github.com/TNYASIN/applied-ai-system-project](https://github.com/TNYASIN/applied-ai-system-project)
