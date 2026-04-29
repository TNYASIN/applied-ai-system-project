# Muze — Music Discovery & Recommendation System

> **Base project:** [Module 3 — Music Recommender Simulation](https://github.com/TNYASIN/ai110-module3show-musicrecommendersimulation-starter)
> The original system was a command-line weighted scoring engine that matched songs from a static 19-song catalog against user-supplied genre and mood preferences. It had no external data, no live integrations, and no reliability testing.

Muze extends that prototype into a full applied AI system: real Spotify listening history drives personalization, a RAG engine provides contextual song insights, MusicBrainz supplies verified songwriter credits, and an automated test harness measures reliability with confidence scoring.

**Live app:** [https://muze-project.streamlit.app](https://muze-project.streamlit.app)

---

## Demo Walkthrough (Loom)

> 📹 **[Watch the full walkthrough →](#)** *(add your Loom link here before submission)*

---

## What It Does

| Feature | Description |
|---|---|
| **Spotify OAuth** | Connects via Authorization Code flow to pull your real top tracks and listening history |
| **Content-Based Recommendations** | Weighted scoring across genre, mood, energy, tempo, danceability, valence, and acousticness |
| **Songwriter Credits** | Looks up actual Written-by / Composed-by credits via MusicBrainz for your top Spotify tracks |
| **RAG Song Insights** | Vector-stores song metadata; retrieves contextual descriptions for any recommended track |
| **Spotify Vibes** | Extracts dominant colors from top album art (Pillow quantization) and tints the UI palette |
| **Test Harness** | 6-test automated reliability suite with confidence scoring and JSON report export |
| **Demo Mode** | Full experience with sample data — no Spotify account needed |

---

## System Architecture

```
User (Browser)
      │
      ▼
┌─────────────────────────────────────────────────┐
│              Muze (Streamlit UI)                │
│  Home │ Your Music │ Connect │ Recs │ Writers   │
└──┬────────┬──────────────┬──────────────┬───────┘
   │        │              │              │
   ▼        ▼              ▼              ▼
Spotify  Data Manager  Recommender   RAG Engine
Client   (songs.csv)   (Scorer)      (ChromaDB /
(OAuth)                              fallback)
   │        │              │              │
   │        └──────────────┘              │
   │               │                     │
   ▼               ▼                     ▼
Spotify API    Writer Index         Song Context
Top Tracks     (writer→songs)       Retrieval
Artist Genres  Confidence Score
   │
   ▼
MusicBrainz API
(songwriter credits)

[Test Harness] ──► JSON Report
```

See [`assets/architecture.png`](assets/architecture.png) for the full diagram.

### Components

| File | Role |
|---|---|
| `src/app.py` | Streamlit UI, theming, navigation, OAuth callback |
| `src/spotify_client.py` | OAuth Authorization Code flow, Spotify Web API |
| `src/recommender.py` | Weighted scoring engine, writer index, confidence scoring |
| `src/data_manager.py` | Loads `data/songs.csv`, generates writer mappings |
| `src/rag_engine.py` | ChromaDB vector store with in-memory fallback |
| `src/musicbrainz.py` | MusicBrainz songwriter lookup (3-step: search → work → artists) |
| `src/test_harness.py` | 6-test automated reliability harness with JSON reporting |
| `data/songs.csv` | 19-song catalog with audio features |

---

## Scoring Algorithm

The recommender extends the Module 3 weighted scorer with three new signals:

| Signal | Weight | New in Muze |
|---|---|---|
| Genre match | +2.0 | |
| Mood match | +1.0 | |
| Energy closeness | `(1 − gap) × 1.5` | |
| Writer match | +1.5 | ✅ |
| Tempo match | `(1 − gap) × 0.5` | ✅ |
| Danceability match | `(1 − gap) × 0.5` | ✅ |
| Valence match | `(1 − gap) × 0.5` | ✅ |
| Acoustic bonus | +0.5 | |

---

## Sample Interactions

### 1 — Recommendations (Folk + Chill)

**Input:** Genre = Folk, Mood = Chill, Energy = 0.2, No preferred writers

**Output (top 3):**
```
1. Keep the Rain — Searows  ·  Folk        Score: 4.3
   ✍️ Written by: Sufjan Stevens

2. These Days — Nico  ·  Folk             Score: 4.1
   ✍️ Written by: Jackson Browne

3. Spacewalk Thoughts — Orbit Bloom  ·  Ambient   Score: 3.8
```

### 2 — RAG Song Insight

**Input:** Click "Get Recommendations" → "Song Insights" loads for top result

**Output:**
```
Song: Keep the Rain
Artist: Searows
Genre: Folk
Mood: Chill
Writer: Sufjan Stevens

This is a chill folk track by Searows, written by Sufjan Stevens.
The song fits into the folk genre and has a chill emotional quality.
```

### 3 — Test Harness

**Input:**
```bash
cd src && python test_harness.py
```

**Output:**
```
🎵 Running Music Recommender Test Harness...

✅ PASS  Consistency         — Consistent results on repeated calls
✅ PASS  Confidence Scoring  — Known song: 1.00, Unknown: 0.00
✅ PASS  Error Handling      — Handled 4/4 error cases gracefully
✅ PASS  Parameter Sensitivity — Different parameters produce different results
✅ PASS  Rag Functionality   — 1 document, context retrieved
✅ PASS  Writer Tracking     — Found 15 writers with statistics

Total: 6/6   Pass rate: 100.0%
```

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- A Spotify Developer account (free) — only needed for real data; demo mode works without it

### Local Setup

```bash
git clone https://github.com/TNYASIN/applied-ai-system-project.git
cd applied-ai-system-project
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd src
streamlit run app.py
```

### Spotify Integration (Streamlit Cloud)

1. Push this repo to GitHub
2. Deploy at [share.streamlit.io](https://share.streamlit.io) — set main file to `src/app.py`
3. In [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard), create an app and add your Streamlit URL as redirect URI:
   ```
   https://yourname-muze.streamlit.app/callback
   ```
4. In Streamlit Cloud → Settings → Secrets, add:
   ```toml
   SPOTIFY_CLIENT_ID = "your_client_id_here"
   SPOTIFY_CLIENT_SECRET = "your_client_secret_here"
   SPOTIFY_REDIRECT_URI = "https://yourname-muze.streamlit.app/callback"
   ```

### Running Tests

```bash
cd src
python test_harness.py          # prints report + saves test_report.json
```

---

## AI Features

### RAG (Retrieval-Augmented Generation) — Required Feature
The `RAGEngine` stores song metadata as documents in ChromaDB (vector database). When the user requests song insights, the engine performs semantic similarity search to retrieve the most relevant context before generating the description. Falls back to an in-memory dictionary store when ChromaDB is unavailable.

### MusicBrainz Songwriter Lookup — Stretch (RAG Enhancement)
Extends retrieval beyond the internal catalog to an external knowledge source. For each of the user's Spotify top tracks, the system makes a 3-step MusicBrainz API call chain (recording search → work relations → artist relations) to retrieve verified Written-by / Composed-by credits. Results are aggregated by songwriter, merged across roles (e.g. Composer + Lyricist → one entry), and ranked by distinct-song count.

### Test Harness — Stretch Feature
`test_harness.py` runs 6 automated reliability tests: consistency (same input → same output), confidence score validity, error handling (4 invalid input scenarios), parameter sensitivity, RAG functionality, and writer tracking. Results are exported to `test_report.json`. The Analytics tab in the UI exposes a subset of these tests interactively.

### Confidence Scoring — Guardrail
The recommender calculates a per-song confidence score (0–1) based on data completeness: base 0.5, +0.1 for genre+mood, +0.2 for writer credits, +0.2 for all audio features present. This lets the UI surface when a recommendation has thin backing data.

---

## Design Decisions

- **Credentials in env vars only** — Spotify keys are read from environment variables / Streamlit secrets and never exposed in the UI or source code
- **Demo mode** — all features are exercisable without a Spotify account
- **Per-session recommender** — stored in `st.session_state` (not `@st.cache_resource`) so injected Spotify tracks stay user-specific
- **MusicBrainz behind a button** — the 3-call-per-track lookup takes ~3 sec/track; running it on page load would time out, so it's triggered on demand with a time estimate shown
- **Fallback RAG** — in-memory dict store used when ChromaDB is unavailable, maintaining feature parity
- **Spotify Vibes** — album art colors extracted via Pillow quantization, darkened, then lightened to pastels so the background always stays readable

---

## Testing Summary

| Test | Result | Notes |
|---|---|---|
| Consistency | ✅ Pass | Deterministic scoring — same input always returns same ranking |
| Confidence Scoring | ✅ Pass | Known song scores 1.0; unknown songs score 0.0 |
| Error Handling | ✅ Pass | 4/4 invalid-input cases handled gracefully without crash |
| Parameter Sensitivity | ✅ Pass | Folk+low-energy and Rock+high-energy produce non-overlapping results |
| RAG Functionality | ✅ Pass | Documents stored and retrieved successfully |
| Writer Tracking | ✅ Pass | 15 writers indexed with song mappings |

**Key finding:** The recommender is reliable on the catalog but the catalog is small (19 songs), which limits recommendation diversity. Spotify injection adds real-user tracks but without audio features (Spotify deprecated that endpoint), so injected tracks default to neutral scores and rank lower than catalog songs with full feature vectors.

---

## Stretch Features Completed

| Feature | Points | Evidence |
|---|---|---|
| RAG Enhancement | +2 | External MusicBrainz source integrated into retrieval pipeline |
| Test Harness | +2 | `test_harness.py` — 6 tests, JSON report, interactive Analytics tab |
| Writer / Composer Credits | — | Songwriter credits from MusicBrainz, aggregated by distinct-song count |
| Parameter Tuning | — | 8 scoring signals, all tunable from the UI |
| Spotify Vibes | — | Dynamic UI palette from album art |

---

## Reflection

See [`model_card.md`](model_card.md) for the full AI collaboration reflection, bias analysis, and ethics discussion.

---

**GitHub:** [https://github.com/TNYASIN/applied-ai-system-project](https://github.com/TNYASIN/applied-ai-system-project)
