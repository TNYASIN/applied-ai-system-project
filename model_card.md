# Model Card — Muze Applied AI System

## System Overview

Muze is a music discovery and recommendation system built on top of the Module 3 weighted-scoring music recommender. It adds Spotify OAuth integration, RAG-based song context retrieval, MusicBrainz songwriter credit lookup, and an automated test harness.

---

## AI Collaboration

### How I Used AI During Development

Claude Code (Anthropic) was used throughout this project as a pair programming assistant. Key contributions:

- **Architecture design** — helped structure the per-session recommender pattern (using `st.session_state` instead of `@st.cache_resource`) to keep Spotify-injected tracks user-specific
- **OAuth debugging** — diagnosed why the Spotify auth URL was broken (spaces in scope strings not URL-encoded) and fixed `get_auth_url()` to use `urllib.parse.urlencode`
- **CSS injection** — guided targeted CSS selectors to override Streamlit's theming without breaking its internal Material Icons rendering
- **MusicBrainz integration** — designed the 3-step API chain (recording search → work relations → artist relations) and the role-merging aggregation logic
- **Test harness** — structured the 6-test evaluation suite and confidence scoring heuristic

### One Helpful AI Suggestion

When the Spotify credits endpoint (`spclient.wg.spotify.com`) returned 403, Claude immediately identified that this is an internal Spotify API locked to first-party apps and proposed MusicBrainz as the correct alternative. This saved significant time that would have been spent debugging headers or auth scopes that could never work.

### One Flawed AI Suggestion

Claude initially suggested using `@st.cache_resource` for the `MusicRecommender` object. This is correct for stateless services, but the recommender needed to be mutated per-session (to inject the user's Spotify tracks). The cached singleton would have mixed data across all users. The fix — storing the recommender in `st.session_state` instead — required recognizing that the AI's suggestion was optimizing for the common case (caching) while missing the user-specific mutation requirement.

---

## Limitations and Biases

### Catalog Bias
The base catalog (19 songs) skews toward Western indie/folk/rock. Recommendations are limited by whatever genres are in the catalog, so users with different listening habits (K-pop, classical, hip-hop) see fewer matching results.

### Audio Feature Defaults
When Spotify tracks are injected from the user's listening history, they lack audio features (Spotify deprecated the `audio-features` endpoint for new apps). Injected tracks default to neutral values (energy=0.65, valence=0.6, etc.) which causes them to rank below fully-specified catalog songs in most scoring scenarios.

### MusicBrainz Coverage
MusicBrainz has excellent coverage for Western popular music but lower coverage for non-English tracks, regional genres, and newer releases. Songwriter lookups for K-pop, Bollywood, or underground releases frequently return no results.

### No Personalization Memory
The system has no persistent user profile. Each session starts fresh; preferences set in one visit don't carry over to the next.

---

## Potential Misuse and Safeguards

| Risk | Safeguard |
|---|---|
| Spotify credentials exposed | Keys stored in env vars / Streamlit secrets only; never rendered in UI or source |
| User listening data leaked | OAuth tokens stored only in `st.session_state` (server memory); never written to disk or logs |
| Songwriter data misattributed | MusicBrainz is community-curated and can contain errors; results are labeled "via MusicBrainz" to set expectations |

---

## What Surprised Me During Testing

- **Confidence scoring is binary in practice.** Songs with all fields populated scored 1.0; any missing field dropped the score sharply. A smoother continuous scale would be more informative.
- **Consistency is trivial to achieve but meaningless to prove.** The recommender is deterministic by design (no randomness), so the consistency test always passes. A more useful reliability metric would test accuracy against a ground-truth playlist.
- **MusicBrainz finds writers you wouldn't expect.** For "Keep the Rain" by Searows, MusicBrainz returned Sufjan Stevens — who wrote the original "Seven Swans" that Searows covered. This is accurate but surfacing cover attributions without context could confuse users.

---

## System Limitations and Future Improvements

1. **Add a live LLM for RAG** — currently the RAG engine retrieves template-based descriptions. Routing retrieved context through Claude or GPT-4 would produce genuinely useful natural-language insights.
2. **Expand the catalog** — 19 songs is too few for meaningful diversity. Integrating Last.fm or Discogs would provide thousands of tracks with full metadata.
3. **Persistent user profiles** — storing preference history (even anonymized) would allow the scoring weights to adapt over time.
4. **MusicBrainz rate limit** — the current 1 req/sec sequential approach means 50 tracks takes ~150 seconds. Batching or caching at the DB level would fix this.

---

## Portfolio Reflection: What This Project Says About Me as an AI Engineer

Muze shows that I can take an AI prototype from a class exercise and evolve it into something real — with live API integrations, a production deployment, and reliability testing. More than the features, it reflects how I think: when the Spotify credits endpoint returned 403, I didn't keep guessing at headers; I diagnosed the root cause (first-party-only API), found the right alternative (MusicBrainz), and shipped a working solution the same day. That pattern — understand the constraint, find the right tool, build incrementally — is how I approach engineering problems generally. I care about systems that are honest about what they don't know (confidence scoring, graceful fallbacks) as much as systems that work when everything goes right.

---

## Reflection: What This Project Taught Me

Building Muze taught me that **the hardest part of an applied AI system is the data plumbing**, not the model. The scoring algorithm from Module 3 took an hour to port. The OAuth flow, session state management, CSS injection, API rate limits, and deprecated endpoints consumed most of the project time.

It also taught me that **AI assistants are best at known patterns and worst at novel constraints.** Claude knew exactly how to structure a Streamlit app and how to design a RAG pipeline. But when the Spotify credits API returned 403 and we needed to reason about *why* a third-party token couldn't access a first-party endpoint, that required domain knowledge that the AI had to be prompted to apply correctly.

The test harness reinforced that **passing tests doesn't mean the system is good** — it means it's self-consistent. The real quality bar is whether the recommendations feel relevant to a real user, which no automated test in this project measures.
