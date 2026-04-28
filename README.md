# MelodyMind - Applied AI System Project

## Project Overview

This project extends the **Music Recommender Simulation** from Module 3 into a full-stack AI-powered music recommendation system. The original project was a simple content-based filtering recommender that scored songs based on user preferences.

### Original Project (Module 3)
- **Name**: Music Recommender Simulation
- **Summary**: A content-based filtering system that scores songs based on genre, mood, and energy preferences using weighted scoring logic.
- **Key Features**: Song catalog with audio features, user profile matching, weighted scoring algorithm.

### Extended System (This Project)
MelodyMind transforms the simulation into a complete applied AI system with:

1. **Web Application** - Streamlit-based UI for interactive recommendations
2. **Spotify Integration** - OAuth authentication to access real user data
3. **Writer/Composer Credits** - Track most listened songwriters
4. **Parameter Tuning** - Fine-tune recommendations with sliders
5. **RAG Engine** - Retrieval-Augmented Generation for song context
6. **Test Harness** - Automated reliability testing

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MelodyMind App                           │
│                    (Streamlit Web Interface)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Spotify     │  │  Recommender  │  │    RAG        │
│   Client      │  │    Engine     │  │    Engine     │
│  (OAuth/API)  │  │ (Scoring/ML)  │  │ (Vector Store)│
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    Data Manager    │
                │  (Songs/Writers)   │
                └─────────────────────┘
```

### Components

| Component | Description |
|-----------|-------------|
| **app.py** | Main Streamlit application with UI |
| **spotify_client.py** | Spotify OAuth and API integration |
| **recommender.py** | Enhanced scoring engine with writer tracking |
| **data_manager.py** | Song catalog and writer data management |
| **rag_engine.py** | Retrieval-Augmented Generation for context |
| **test_harness.py** | Reliability testing and evaluation |

---

## Getting Started

### Prerequisites

- Python 3.8+
- Spotify Developer Account (for OAuth)

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd applied-ai-system-project
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   # or: .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Spotify OAuth Setup

1. Go to [developer.spotify.com](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://localhost:8501/callback` as a redirect URI
4. Copy your Client ID and Client Secret

### Running the Application

```bash
cd src
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Running Tests

```bash
cd src
python test_harness.py
```

---

## Sample Interactions

### Example 1: Basic Recommendation
**Input**:
- Genre: Pop
- Mood: Happy
- Energy: 0.6

**Output**:
```
🎵 Get Recommendations

1. Come Here (Alexi Laiho) - Score: 3.0
   Reason: Matches Pop genre, Happy mood

2. These Days (Foo Fighters) - Score: 2.5
   Reason: Matches Pop genre

3. Country Roads (John Denver) - Score: 2.0
   Reason: Similar energy level
```

### Example 2: Writer-Based Recommendation
**Input**:
- Preferred Writer: Dave Grohl

**Output**:
```
🎵 Recommendations by Dave Grohl

1. These Days (Foo Fighters) - Rock, Energetic
2. Everlong (Foo Fighters) - Rock, Intense
3. My Hero (Foo Fighters) - Rock, Happy
```

### Example 3: Parameter Tuning
**Input**:
- Genre: Electronic
- Energy: 0.85
- Danceability: 0.9
- Valence: 0.8

**Output**:
```
🎵 High-Energy Electronic Recommendations

1. Electric Dreams (Synthwave Master) - Score: 3.5
2. Neon Nights (Cyber Punk) - Score: 3.2
```

---

## Design Decisions

### Why Streamlit?
- Rapid prototyping for AI applications
- Built-in support for interactive widgets
- Easy deployment and sharing

### Why ChromaDB for RAG?
- Lightweight vector database
- Easy integration with Python
- Supports semantic search

### Scoring Algorithm
The scoring system extends the Module 3 weights:
- Genre match: +2.0
- Mood match: +1.0
- Energy closeness: (1 - gap) × 1.5
- Writer match: +1.5 (new)
- Acoustic bonus: +0.5

### Trade-offs
- **Demo Mode**: Added to allow testing without Spotify credentials
- **Fallback RAG**: Simple in-memory storage when ChromaDB unavailable
- **Confidence Scoring**: Implemented as a heuristic based on data completeness

---

## Testing Summary

### Test Results
- ✅ Consistency Test: Same inputs produce same outputs
- ✅ Confidence Scoring: Valid scores in 0-1 range
- ✅ Error Handling: Proper validation of inputs
- ✅ Parameter Sensitivity: Different params → different results
- ✅ RAG Functionality: Context retrieval working
- ✅ Writer Tracking: Statistics available

**Pass Rate: 100%**

### Reliability Observations
- The recommender is highly consistent across repeated calls
- Confidence scores correlate with data completeness
- Parameter tuning produces meaningful result variations

---

## Reflection

### What I Learned
1. **AI System Design**: Building a complete system requires thinking about data flow, user experience, and error handling
2. **Spotify API**: OAuth authentication adds complexity but enables powerful personalization
3. **RAG Systems**: Retrieval-augmented generation provides valuable context beyond simple recommendations

### Limitations
- Demo mode uses limited sample data
- RAG without embeddings is a simplified implementation
- Writer data is limited to the catalog

### Potential Misuse
- Could be used to manipulate listening patterns
- Could surface inappropriate content if not properly filtered
- **Mitigation**: Add content filtering, show confidence scores

### Collaboration with AI
- **Helpful**: AI suggested the RAG architecture and test harness structure
- **Flawed**: Initial Spotify token handling needed correction for edge cases

---

## Optional Stretch Features Completed

| Feature | Status | Description |
|---------|--------|-------------|
| RAG Enhancement | ✅ +2pts | Vector-based song context retrieval |
| Test Harness | ✅ +2pts | Automated evaluation script |
| Writer Tracking | ✅ +1pt | Writer/composer credits system |
| Parameter Tuning | ✅ +1pt | Interactive parameter sliders |

---

## Portfolio Entry

This project demonstrates my ability to:
- Extend a prototype into a production-ready system
- Integrate external APIs (Spotify)
- Implement AI features (RAG, confidence scoring)
- Build comprehensive testing infrastructure
- Document and explain technical decisions

**Link to GitHub**: [https://github.com/TNYASIN/applied-ai-system-project](https://github.com/TNYASIN/applied-ai-system-project)

---

## Video Walkthrough

[Loom Video Link] - See the end-to-end system running with:
- Spotify connection flow
- Parameter-based recommendations
- Writer credits tracking
- Reliability testing demonstration