"""
Muze — Music Discovery & Recommendation
"""

import os
import requests
from io import BytesIO
from typing import Optional, List

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from spotify_client import SpotifyClient
from recommender import MusicRecommender
from rag_engine import RAGEngine
from data_manager import DataManager

st.set_page_config(
    page_title="Muze",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session state defaults ───────────────────────────────────────────────────
for _k, _v in {
    'spotify_client': None,
    'demo_mode': False,
    'theme_colors': None,
    'last_recommendations': [],
    'spotify_injected': False,
    'spotify_writer_stats': None,
    'spotify_artist_stats': None,
    'recommender': None,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─── Logo SVG (earplug/earbud-inspired) ──────────────────────────────────────
# Two oval earbuds + connecting arc wire overhead
_LOGO_SVG = """
<svg width="52" height="34" viewBox="0 0 52 34" fill="none" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="8"  cy="20" rx="6.5" ry="9"   fill="{a}" opacity="0.95"/>
  <ellipse cx="8"  cy="17" rx="3.8" ry="5"   fill="white" opacity="0.16"/>
  <ellipse cx="8"  cy="26" rx="4"   ry="2.8" fill="{a}" opacity="0.65"/>
  <ellipse cx="44" cy="20" rx="6.5" ry="9"   fill="{a}" opacity="0.95"/>
  <ellipse cx="44" cy="17" rx="3.8" ry="5"   fill="white" opacity="0.16"/>
  <ellipse cx="44" cy="26" rx="4"   ry="2.8" fill="{a}" opacity="0.65"/>
  <path d="M14.5 15 Q26 2 37.5 15"
        stroke="{a}" stroke-width="2.4" fill="none"
        stroke-linecap="round" opacity="0.72"/>
</svg>
"""


def _logo(accent: str) -> str:
    return _LOGO_SVG.replace("{a}", accent)


# ─── Color extraction ─────────────────────────────────────────────────────────

def _darken(r: int, g: int, b: int, factor: float = 0.52) -> tuple:
    return int(r * factor), int(g * factor), int(b * factor)


def _lighten_hex(hex_color: str, factor: float = 0.80) -> str:
    """Push a hex color toward white — produces a soft pastel from a dark palette."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _extract_colors(url: str, n: int = 4) -> Optional[List[str]]:
    try:
        from PIL import Image
        resp = requests.get(url, timeout=5)
        img = Image.open(BytesIO(resp.content)).convert("RGB").resize((80, 80))
        q = img.quantize(colors=max(n * 3, 12))
        pal = q.getpalette()
        out = []
        for i in range(n):
            r, g, b = _darken(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2])
            out.append(f"#{r:02x}{g:02x}{b:02x}")
        return out
    except Exception:
        return None


def _load_spotify_palette() -> Optional[List[str]]:
    """Extract dominant dark colors from top album art; cache in session state."""
    if st.session_state.theme_colors:
        return st.session_state.theme_colors
    client = st.session_state.spotify_client
    if client is None:
        return None
    if client.is_demo():
        palette = ["#1a0a2e", "#0a1828", "#0e1a0a", "#0a0a20"]
        st.session_state.theme_colors = palette
        return palette
    try:
        tracks = client.get_top_tracks(limit=5)
        colors: List[str] = []
        for t in tracks[:3]:
            # Spotify API returns track directly, not wrapped in "track" key
            track = t if isinstance(t, dict) and "album" in t else t.get("track", t)
            images = track.get("album", {}).get("images", [])
            if images:
                c = _extract_colors(images[0]["url"], n=2)  # Use first image (largest)
                if c:
                    colors.extend(c)
        if colors:
            st.session_state.theme_colors = colors[:4]
            return colors[:4]
    except Exception as e:
        st.session_state.theme_colors = None
    return None



# ─── CSS / theme ──────────────────────────────────────────────────────────────

def _build_css(colors: Optional[List[str]], accent: str) -> str:
    # Always light — warm off-white default, pastel shift when Spotify Vibes on
    vibes = bool(colors and len(colors) >= 3)
    if vibes:
        c = [_lighten_hex(x, 0.82) for x in colors[:4]]
        c = (c + [c[-1]])[:4]
    else:
        c = ["#f5f0ea", "#ede8e1", "#f2ece4", "#f8f4ef"]

    txt       = "#1c1814"
    txt_muted = "#6b6560"
    txt_faint = "#9e9892"
    # In Vibes mode: headings pick up the accent tint; links/highlights too
    heading_color = accent if vibes else txt

    return f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Outfit:wght@300;400;500;600&display=swap');

/* ── Muze theme ───────────────────────────────────── */

/* Fonts — targeted selectors only, never * so Streamlit icon elements are untouched */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] a,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
.stRadio label, .stSelectbox label, .stSlider label,
.stTextInput label, .stNumberInput label,
.stButton > button,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {{
    font-family: 'Outfit', sans-serif !important;
}}
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {{
    font-family: 'Syne', sans-serif !important;
    font-weight: 700;
    letter-spacing: -0.3px;
    color: {heading_color} !important;
}}

/* Background */
.stApp {{
    background: linear-gradient(-45deg, {c[0]}, {c[1]}, {c[2]}, {c[3]});
    background-size: 400% 400%;
    animation: muzeBg 22s ease infinite;
}}
@keyframes muzeBg {{
    0%   {{ background-position: 0%   50%; }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0%   50%; }}
}}

/* Text */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"],
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
.stRadio label, .stSelectbox label, .stSlider label,
.stTextInput label, .stNumberInput label {{
    color: {txt} !important;
}}
[data-testid="stCaptionContainer"] p {{
    color: {txt_muted} !important;
}}

[data-testid="stHeader"] {{ background: rgba(0,0,0,0) !important; }}

/* Sidebar */
[data-testid="stSidebar"] > div:first-child {{
    background: rgba(240,236,230,0.92) !important;
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(0,0,0,0.07);
}}

/* Tab bar */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: rgba(0,0,0,0.05);
    border-radius: 12px;
    padding: 4px 6px;
    gap: 4px;
    border: 1px solid rgba(0,0,0,0.08);
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    border-radius: 8px;
    color: rgba(28,24,20,0.50) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.88rem;
    font-weight: 500;
    padding: 6px 14px;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background: {accent}18 !important;
    color: {heading_color} !important;
    font-weight: 600 !important;
}}

/* Metric cards */
[data-testid="metric-container"] {{
    background: rgba(0,0,0,0.04);
    border-radius: 10px;
    border: 1px solid rgba(0,0,0,0.07);
    padding: 12px;
}}

/* All buttons — base reset for light background */
div.stButton > button,
div.stLinkButton > a {{
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600;
    border-radius: 8px;
    transition: background 0.2s, border 0.2s;
}}

/* Primary */
div.stButton > button[kind="primary"],
div.stLinkButton > a[kind="primary"] {{
    background: {accent}18;
    border: 1px solid {accent}88;
    color: {accent} !important;
}}
div.stButton > button[kind="primary"]:hover,
div.stLinkButton > a[kind="primary"]:hover {{
    background: {accent}30;
    border-color: {accent};
}}

/* Secondary / default */
div.stButton > button[kind="secondary"],
div.stButton > button:not([kind="primary"]) {{
    background: rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.18);
    color: {txt} !important;
}}
div.stButton > button[kind="secondary"]:hover,
div.stButton > button:not([kind="primary"]):hover {{
    background: rgba(0,0,0,0.10);
}}

/* Alerts */
[data-testid="stAlert"] {{
    background: rgba(0,0,0,0.03) !important;
    border-radius: 8px;
}}

hr {{ border-color: rgba(0,0,0,0.09); }}

/* Expanders */
details[data-testid="stExpander"],
div[data-testid="stExpander"] > details {{
    background: rgba(255,255,255,0.50) !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 10px !important;
    overflow: hidden;
}}
details[data-testid="stExpander"] > summary,
div[data-testid="stExpander"] > details > summary {{
    background: rgba(255,255,255,0.50) !important;
    color: {txt} !important;
    font-family: 'Outfit', sans-serif !important;
    padding: 10px 14px !important;
}}
details[data-testid="stExpander"] > summary:hover,
div[data-testid="stExpander"] > details > summary:hover {{
    background: rgba(0,0,0,0.04) !important;
}}
[data-testid="stExpanderDetails"] {{
    background: rgba(255,255,255,0.35) !important;
    padding: 8px 14px !important;
}}
details[data-testid="stExpander"] summary p,
details[data-testid="stExpander"] summary span {{
    color: {txt} !important;
}}

/* Logo */
.muze-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 8px 0 4px;
}}
.muze-wordmark {{
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -1px;
    color: {txt};
    line-height: 1;
}}
.muze-tagline {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.68rem;
    color: {txt_faint};
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-top: 3px;
    font-weight: 400;
}}
</style>"""


def _apply_theme(vibes: bool, accent: str):
    colors = _load_spotify_palette() if vibes else None
    st.markdown(_build_css(colors, accent), unsafe_allow_html=True)


def _render_header(accent: str):
    st.markdown(
        f'<div class="muze-header">'
        f'{_logo(accent)}'
        f'<div><div class="muze-wordmark">Muze</div>'
        f'<div class="muze-tagline">Music Discovery</div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


# ─── OAuth callback ──────────────────────────────────────────────────────────

def _handle_oauth_callback():
    """If Spotify redirected back with ?code=, exchange it for a token."""
    # st.query_params added in 1.30; fall back to experimental for 1.28/1.29
    try:
        params = dict(st.query_params)
    except AttributeError:
        try:
            params = {k: v[0] for k, v in st.experimental_get_query_params().items()}
        except Exception:
            return

    if "code" not in params:
        return

    code = params["code"]
    client_id     = os.environ.get("SPOTIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    redirect_uri  = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8501/callback")

    if not (client_id and client_secret):
        st.error("Spotify credentials not configured — see README.")
        return

    try:
        client = SpotifyClient(client_id, client_secret, redirect_uri)
        client.exchange_code_for_token(code)
        st.session_state.spotify_client = client
        # Reset per-session data so Spotify tracks get injected fresh
        st.session_state.recommender = None
        st.session_state.spotify_injected = False
        st.session_state.spotify_writer_stats = None
        st.session_state.spotify_artist_stats = None
        # Clear the ?code= from the URL
        try:
            st.query_params.clear()
        except Exception:
            st.experimental_set_query_params()
        st.rerun()
    except Exception as e:
        st.error(f"Spotify authorization failed: {e}")


# ─── JS patches ──────────────────────────────────────────────────────────────

def _patch_sidebar_tooltip():
    """Remove Streamlit's built-in title attribute on the sidebar collapse button."""
    components.html("""
    <script>
    (function patch() {
        var doc = window.parent.document;
        function strip() {
            doc.querySelectorAll('[data-testid="stSidebarCollapseButton"] button')
               .forEach(function(btn) { btn.removeAttribute('title'); });
        }
        strip();
        new MutationObserver(strip).observe(doc.body, { childList: true, subtree: true });
    })();
    </script>
    """, height=0)


# ─── Services ─────────────────────────────────────────────────────────────────
@st.cache_resource
def _init_base_services():
    dm = DataManager()
    rag = RAGEngine()
    rag.bulk_add_songs(dm.get_songs().to_dict("records"))
    return rag, dm


def _get_recommender(dm) -> MusicRecommender:
    """Per-session recommender so Spotify data stays user-specific."""
    if not st.session_state.get("recommender"):
        st.session_state.recommender = MusicRecommender(dm)
    return st.session_state.recommender


_SPOTIFY_GENRE_MAP = {
    "pop": "Pop", "dance pop": "Pop", "teen pop": "Pop", "synth-pop": "Pop",
    "rock": "Rock", "alternative rock": "Rock", "hard rock": "Rock", "classic rock": "Rock",
    "hip hop": "Hip-Hop", "rap": "Hip-Hop", "trap": "Hip-Hop", "hip-hop": "Hip-Hop",
    "r&b": "R&B", "soul": "R&B", "neo soul": "R&B", "rhythm and blues": "R&B",
    "electronic": "Electronic", "edm": "Electronic", "house": "Electronic",
    "techno": "Electronic", "ambient": "Electronic",
    "folk": "Folk", "singer-songwriter": "Folk", "acoustic": "Folk",
    "country": "Country",
    "jazz": "Jazz", "bossa nova": "Jazz",
    "classical": "Classical", "orchestra": "Classical",
    "indie": "Indie", "indie pop": "Indie", "indie rock": "Indie",
    "metal": "Metal", "heavy metal": "Metal", "death metal": "Metal",
}


def _map_spotify_genre(genre_list: list) -> str:
    for g in genre_list:
        g_lower = g.lower()
        for key, val in _SPOTIFY_GENRE_MAP.items():
            if key in g_lower:
                return val
    return "Pop"


def _enrich_recommender_with_spotify(client, recommender: MusicRecommender, rag_engine: RAGEngine):
    """Fetch user's Spotify top tracks and inject them into the recommender catalog."""
    if st.session_state.get("spotify_injected"):
        return

    limit = st.session_state.get("spotify_limit", 10)
    time_range = st.session_state.get("spotify_range", "medium_term")

    try:
        tracks = client.get_top_tracks(time_range=time_range, limit=limit)

        # Collect unique artist IDs for genre lookup
        artist_ids = []
        for track in tracks:
            for artist in track.get("artists", []):
                aid = artist.get("id")
                if aid and aid not in artist_ids:
                    artist_ids.append(aid)

        # Batch-fetch artist genres (Spotify allows up to 50 per call)
        genre_lookup: dict = {}
        for i in range(0, len(artist_ids), 50):
            try:
                artists_data = client.get_artists(artist_ids[i:i + 50])
                for a in artists_data:
                    genre_lookup[a["id"]] = a.get("genres", [])
            except Exception:
                pass

        songs_to_inject = []
        for track in tracks:
            title = track.get("name", "Unknown")
            primary = track.get("artists", [{}])[0]
            artist_name = primary.get("name", "Unknown")
            artist_id = primary.get("id", "")
            genre = _map_spotify_genre(genre_lookup.get(artist_id, []))
            songs_to_inject.append({
                "title": title,
                "artist": artist_name,
                "genre": genre,
                "mood": "Energetic",
                "energy": 0.65,
                "tempo_bpm": 120,
                "valence": 0.6,
                "danceability": 0.6,
                "acousticness": 0.3,
                "writer": artist_name,
            })

        recommender.inject_tracks(songs_to_inject)
        rag_engine.bulk_add_songs(songs_to_inject)
        st.session_state.spotify_injected = True
        st.session_state.spotify_injected_count = len(songs_to_inject)
    except Exception as e:
        st.session_state.spotify_injected = False


# ─── App entry ────────────────────────────────────────────────────────────────
def main():
    _handle_oauth_callback()
    rag_engine, data_manager = _init_base_services()
    recommender = _get_recommender(data_manager)

    # Inject real Spotify tracks into this session's recommender once connected
    client = st.session_state.spotify_client
    if client and not client.is_demo() and client.access_token:
        _enrich_recommender_with_spotify(client, recommender, rag_engine)

    # Sidebar: theme + connection status
    with st.sidebar:
        st.markdown("**Theme**")
        vibes_on = st.toggle(
            "Spotify Vibes",
            value=bool(st.session_state.theme_colors),
            help="Shift the background palette from your top album art",
        )
        _client = st.session_state.spotify_client
        if vibes_on and not (_client and (_client.is_demo() or _client.access_token)):
            st.caption("Connect Spotify first to use Vibes mode.")
            vibes_on = False
        if not vibes_on:
            st.session_state.theme_colors = None
        if vibes_on and not st.session_state.theme_colors:
            with st.spinner("Pulling album palette…"):
                _load_spotify_palette()

        # Derive accent from Vibes palette when available, else default green
        raw_palette = st.session_state.theme_colors if vibes_on else None
        accent = raw_palette[0] if raw_palette else "#1a7a40"

        st.markdown("---")
        client = st.session_state.spotify_client
        if client and not client.is_demo() and client.access_token:
            st.caption("🟢 Spotify connected")
            st.markdown("**Listening history**")
            spotify_limit = st.select_slider(
                "Top tracks",
                options=[5, 10, 50],
                value=st.session_state.get("spotify_limit", 10),
            )
            _RANGE_LABELS = ["Last 4 weeks", "Last 6 months", "All time"]
            _RANGE_API    = {"Last 4 weeks": "short_term", "Last 6 months": "medium_term", "All time": "long_term"}
            spotify_range = st.radio(
                "Time range",
                _RANGE_LABELS,
                index=st.session_state.get("spotify_range_idx", 1),
                label_visibility="collapsed",
            )
            # Invalidate cached Spotify data when settings change
            prev_limit = st.session_state.get("spotify_limit")
            prev_range_idx = st.session_state.get("spotify_range_idx")
            new_range_idx = _RANGE_LABELS.index(spotify_range)
            if prev_limit != spotify_limit or prev_range_idx != new_range_idx:
                st.session_state.spotify_writer_stats = None
                st.session_state.spotify_artist_stats = None
                st.session_state.spotify_injected = False
            st.session_state.spotify_limit = spotify_limit
            st.session_state.spotify_range_idx = new_range_idx
            st.session_state.spotify_range = _RANGE_API[spotify_range]
        elif client and client.is_demo():
            st.caption("🎮 Demo mode")
        else:
            st.caption("⚪ Not connected")

    _apply_theme(vibes_on, accent)
    _patch_sidebar_tooltip()
    _render_header(accent)
    st.markdown("---")

    # Top navigation tabs
    tabs = st.tabs([
        "🏠 Home",
        "🎧 Your Music",
        "🔗 Connect Spotify",
        "🎼 Recommendations",
        "✍️ Writer Credits",
        "📊 Analytics",
    ])
    with tabs[0]:
        _page_home(recommender, data_manager)
    with tabs[1]:
        _page_your_music()
    with tabs[2]:
        _page_connect()
    with tabs[3]:
        _page_recommendations(recommender, rag_engine)
    with tabs[4]:
        _page_writers(recommender, data_manager)
    with tabs[5]:
        _page_analytics(recommender, rag_engine, data_manager)


# ─── Page: Home ───────────────────────────────────────────────────────────────
def _page_home(recommender, data_manager):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
## Welcome to Muze

Your music discovery companion — finds tracks you'll love based on your
listening history, favorite songwriters, and taste profile.

### What you can do
- 🎧 **Connect Spotify** — Pull your real listening history
- ✍️ **Writer Credits** — Explore the songwriters behind your music
- 🎛️ **Tune Parameters** — Filter by mood, energy, tempo, and more
- 🔍 **Song Insights** — Contextual info on any track
- 📊 **Test & Evaluate** — Measure recommendation quality
        """)
        st.info("💡 Start by connecting Spotify or try demo mode.")

    with col2:
        st.markdown("### Quick Stats")
        st.metric("Songs in Catalog", len(data_manager.get_songs()))
        st.metric("Writers / Composers", len(data_manager.get_writers()))
        if st.button("🎮 Demo Mode", type="primary"):
            st.session_state.demo_mode = True
            st.session_state.spotify_client = SpotifyClient.demo_mode()
            st.rerun()


# ─── Page: Your Music (Spotify Listening History) ───────────────────────────
def _page_your_music():
    client = st.session_state.spotify_client
    
    if not client or client.is_demo():
        st.info("🎧 Connect Spotify to see your listening history here.")
        return
    
    st.header("🎧 Your Music")
    st.markdown("Your actual listening history from Spotify.")
    st.markdown("---")
    
    try:
        # Get user's top tracks
        limit = st.session_state.get("spotify_limit", 10)
        time_range = st.session_state.get("spotify_range", "medium_term")
        tracks = client.get_top_tracks(time_range=time_range, limit=limit)
        
        if not tracks:
            st.info("No top tracks found. Play more music on Spotify!")
            return
        
        st.markdown("### Your Top Tracks")
        for i, track in enumerate(tracks, 1):
            # Track is returned directly from Spotify API
            name = track.get("name", "Unknown")
            artists = ", ".join([a.get("name", "") for a in track.get("artists", [])])
            album = track.get("album", {}).get("name", "Unknown")
            duration_ms = track.get("duration_ms", 0)
            duration_min = duration_ms // 60000
            duration_sec = (duration_ms % 60000) // 1000
            
            with st.container():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{i}. {name}**")
                    st.markdown(f"🎤 {artists}  ·  📀 {album}")
                with c2:
                    st.caption(f"{duration_min}:{duration_sec:02d}")
                st.divider()
        
        # Get recently played
        st.markdown("### Recently Played")
        recent = client.get_recently_played(limit=10)
        for track in recent:
            name = track.get("track", {}).get("name", "Unknown")
            artists = ", ".join([a.get("name", "") for a in track.get("track", {}).get("artists", [])])
            st.caption(f"🎵 {name} — {artists}")
            
    except Exception as e:
        st.error(f"Error loading your music: {e}")


# ─── Page: Connect Spotify ────────────────────────────────────────────────────
def _page_connect():
    st.header("🔗 Connect Your Spotify Account")
    st.markdown("Link Spotify to get recommendations based on your real listening history.")
    st.markdown("---")

    client_id     = os.environ.get("SPOTIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    redirect_uri  = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8501/callback")

    col1, col2 = st.columns(2)

    with col1:
        if client_id and client_secret:
            try:
                auth_url = SpotifyClient(client_id, client_secret, redirect_uri).get_auth_url()
                st.link_button("🔗 Connect to Spotify", auth_url, type="primary")
            except Exception as e:
                st.error(f"Error building auth URL: {e}")
        else:
            st.button("🔗 Connect to Spotify", type="primary", disabled=True)
            st.caption("Spotify credentials not configured — see README.")

    with col2:
        if st.button("🎮 Use Demo Data", type="secondary"):
            st.session_state.demo_mode = True
            st.session_state.spotify_client = SpotifyClient.demo_mode()
            st.rerun()


# ─── Page: Recommendations ────────────────────────────────────────────────────
def _page_recommendations(recommender, rag_engine):
    st.header("🎼 Get Recommendations")
    st.markdown("### Tune Parameters")

    available_writers = recommender.get_available_writers()
    spotify_connected = bool(st.session_state.get("spotify_injected"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        genre = st.selectbox(
            "Genre",
            ["Any", "Pop", "Rock", "Hip-Hop", "R&B", "Electronic",
             "Folk", "Country", "Jazz", "Classical", "Indie", "Metal"],
        )
    with col2:
        mood = st.selectbox(
            "Mood", ["Any", "Happy", "Sad", "Energetic", "Calm", "Intense", "Chill"]
        )
    with col3:
        energy = st.slider("Energy Level", 0.0, 1.0, 0.5, 0.05)
    with col4:
        label = "Preferred Artists" if spotify_connected else "Preferred Writers"
        target_writers = st.multiselect(label, available_writers)

    with st.expander("🔍 Advanced Filters"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tempo = st.slider("Tempo (BPM)", 60, 200, 120)
        with c2:
            danceability = st.slider("Danceability", 0.0, 1.0, 0.5)
        with c3:
            valence = st.slider("Valence", 0.0, 1.0, 0.5)
        with c4:
            acousticness = st.slider("Acousticness", 0.0, 1.0, 0.3)

    num_recs = st.slider("Number of Results", 3, 20, 10)

    if st.button("🎵 Get Recommendations", type="primary"):
        with st.spinner("Finding tracks you'll love…"):
            prefs = {
                "genre": genre if genre != "Any" else None,
                "mood": mood if mood != "Any" else None,
                "energy": energy,
                "target_writers": target_writers,
                "tempo": tempo,
                "danceability": danceability,
                "valence": valence,
                "acousticness": acousticness,
            }
            results = recommender.recommend(prefs, num_recs)

        st.markdown("### 🎧 Your Picks")
        for i, song in enumerate(results, 1):
            with st.container():
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{i}. {song['title']}**")
                    st.markdown(f"🎤 {song['artist']}  ·  📀 {song['genre']}")
                    st.markdown(f"✍️ {song.get('writer', 'Unknown')}")
                with c2:
                    st.metric("Score", f"{song['score']:.2f}")
                st.divider()

        if results:
            st.markdown("### Song Insights")
            with st.spinner("Loading…"):
                context = rag_engine.get_song_context(results[0]["title"])
                st.info(context)

        st.session_state.last_recommendations = results


# ─── Spotify data fetchers ────────────────────────────────────────────────────

def _fetch_spotify_artist_stats(client) -> pd.DataFrame:
    """Performing-artist → songs from Spotify top tracks. Cached in session state."""
    if st.session_state.get("spotify_artist_stats") is not None:
        return st.session_state.spotify_artist_stats

    limit = st.session_state.get("spotify_limit", 10)
    time_range = st.session_state.get("spotify_range", "medium_term")
    try:
        tracks = client.get_top_tracks(time_range=time_range, limit=limit)
        artist_songs: dict = {}
        for track in tracks:
            title = track.get("name", "Unknown")
            for artist in track.get("artists", []):
                name = artist.get("name", "")
                if name:
                    artist_songs.setdefault(name, [])
                    if title not in artist_songs[name]:
                        artist_songs[name].append(title)
        rows = sorted(
            [{"artist": a, "count": len(s), "songs": s} for a, s in artist_songs.items()],
            key=lambda x: -x["count"],
        )
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        st.session_state.spotify_artist_stats = df
        return df
    except Exception as e:
        st.error(f"Could not load Spotify artist data: {e}")
        return pd.DataFrame()


def _fetch_mb_songwriter_stats(tracks: list) -> pd.DataFrame:
    """
    Look up songwriter credits via MusicBrainz for all given tracks.
    Merges roles for the same person (e.g. Composer + Lyricist → one row).
    Returns DataFrame: writer, role, count (distinct songs credited on), songs.
    """
    from musicbrainz import lookup_writers_bulk
    credits = lookup_writers_bulk(tracks, limit=len(tracks))
    if not credits:
        return pd.DataFrame()

    # name -> {roles: set, songs: set}
    writer_data: dict = {}
    for title, writers in credits.items():
        for w in writers:
            name = w["name"]
            role = w["role"]
            if name not in writer_data:
                writer_data[name] = {"roles": set(), "songs": set()}
            writer_data[name]["roles"].add(role)
            writer_data[name]["songs"].add(title)

    rows = sorted(
        [
            {
                "writer": name,
                "role": ", ".join(sorted(d["roles"])),
                "count": len(d["songs"]),
                "songs": sorted(d["songs"]),
            }
            for name, d in writer_data.items()
        ],
        key=lambda x: -x["count"],
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─── Page: Writer Credits ─────────────────────────────────────────────────────
def _page_writers(recommender, data_manager):
    st.header("✍️ Writer & Composer Credits")

    client = st.session_state.spotify_client
    spotify_connected = client and not client.is_demo() and client.access_token

    import altair as alt

    # ── Section 1: Your Top Artists (performing artists from Spotify) ─────────
    if spotify_connected:
        st.markdown("### 🎤 Your Top Artists")
        st.caption(f"Performing artists from your top {st.session_state.get('spotify_limit', 10)} Spotify tracks")
        with st.spinner("Loading…"):
            artist_stats = _fetch_spotify_artist_stats(client)
        if not artist_stats.empty:
            top_artists = artist_stats.head(10)
            chart = (
                alt.Chart(top_artists)
                .mark_bar(color="#1DB954")
                .encode(
                    x=alt.X("count", title="Songs"),
                    y=alt.Y("artist", sort="-x", title=""),
                    tooltip=["artist", "count"],
                )
                .properties(height=min(260, len(top_artists) * 30 + 40))
            )
            st.altair_chart(chart, use_container_width=True)
            for _, row in top_artists.iterrows():
                with st.expander(f"🎤 {row['artist']}  —  {row['count']} songs"):
                    for title in row.get("songs", []):
                        st.markdown(f"- {title}")
        else:
            st.info("No top tracks found — play more music on Spotify and come back!")

        st.markdown("---")

    # ── Section 2: Songwriters & Composers ───────────────────────────────────
    st.markdown("### ✍️ Songwriters & Composers")

    if spotify_connected:
        mb_df = st.session_state.get("spotify_writer_stats")

        n_tracks = st.session_state.get("spotify_limit", 10)
        est_secs = n_tracks * 3  # ~3 sec per track (3 MusicBrainz calls each)

        if mb_df is None:
            st.caption(
                f"Searches MusicBrainz for songwriter credits across all {n_tracks} loaded tracks, "
                f"then shows the top 5 most credited writers. Takes ~{est_secs} seconds."
            )
            if st.button("🔍 Load Songwriter Credits", type="primary"):
                with st.spinner(f"Looking up credits for {n_tracks} tracks via MusicBrainz… (~{est_secs} sec)"):
                    tracks = client.get_top_tracks(
                        time_range=st.session_state.get("spotify_range", "medium_term"),
                        limit=n_tracks,
                    )
                    mb_df = _fetch_mb_songwriter_stats(tracks)
                    st.session_state.spotify_writer_stats = mb_df
                st.rerun()
        elif mb_df.empty:
            st.info("No songwriter credits found in MusicBrainz for your top tracks.")
            _writer_credits_from_catalog(recommender)
        else:
            col_cap, col_btn = st.columns([5, 1])
            with col_cap:
                st.caption(f"Top 5 songwriters by distinct song count across your top {n_tracks} Spotify tracks (via MusicBrainz)")
            with col_btn:
                if st.button("↺ Refresh", type="secondary"):
                    st.session_state.spotify_writer_stats = None
                    st.rerun()
            top5 = mb_df.head(5)
            for _, row in top5.iterrows():
                role_label = f" · {row['role']}" if row.get("role") else ""
                with st.expander(f"✍️ {row['writer']}{role_label}  —  {row['count']} songs"):
                    for title in row.get("songs", []):
                        st.markdown(f"- {title}")

            st.markdown("---")
            st.markdown("### 🔍 Discover by Songwriter")
            all_writers = sorted(mb_df["writer"].unique().tolist())
            selected = st.selectbox("Choose a songwriter", all_writers)
            if selected:
                songs = mb_df[mb_df["writer"] == selected]["songs"].explode().dropna().unique()
                st.markdown(f"**Songs credited to {selected}:**")
                for title in songs:
                    st.markdown(f"- {title}")
    else:
        st.caption("Connect Spotify to load songwriter credits from MusicBrainz, or browse the catalog below.")
        _writer_credits_from_catalog(recommender)


def _writer_credits_from_catalog(recommender):
    """Fallback: show songwriter stats from the static catalog."""
    writer_stats = recommender.get_writer_statistics()
    if writer_stats.empty:
        st.info("Connect Spotify or use demo mode to populate the catalog.")
        return
    top_writers = writer_stats.head(10)
    for _, row in top_writers.iterrows():
        with st.expander(f"✍️ {row['writer']}  —  {row['count']} songs"):
            for title in row.get("songs", []):
                st.markdown(f"- {title}")
    st.markdown("---")
    st.markdown("### 🔍 Discover by Songwriter")
    all_writers = sorted(writer_stats["writer"].tolist())
    selected = st.selectbox("Choose a songwriter", all_writers)
    if selected:
        writer_songs = recommender.recommend_by_writer(selected)
        if writer_songs:
            st.markdown(f"**Songs written by {selected}:**")
            for s in writer_songs:
                st.markdown(f"- **{s['title']}** — {s.get('artist', 'Unknown')}  ·  {s.get('genre', '')}")
        else:
            st.info("No songs found for this songwriter in the catalog.")


# ─── Page: Analytics ──────────────────────────────────────────────────────────
def _page_analytics(recommender, rag_engine, data_manager):
    st.header("📊 Analytics & Testing")

    all_songs = recommender.songs if hasattr(recommender, "songs") else data_manager.get_songs()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Songs", len(all_songs))
    with c2:
        st.metric("Total Writers", all_songs["writer"].nunique() if "writer" in all_songs.columns else len(data_manager.get_writers()))
    with c3:
        st.metric("Genres", all_songs["genre"].nunique() if "genre" in all_songs.columns else len(data_manager.get_songs()["genre"].unique()))
    with c4:
        st.metric("RAG Documents", rag_engine.get_document_count())

    st.markdown("---")
    st.markdown("### 🧪 Reliability Tests")
    test_type = st.radio(
        "Test type",
        ["Consistency Test", "Confidence Scoring", "Error Handling", "Full Evaluation"],
    )
    if st.button("▶️ Run Tests", type="primary"):
        with st.spinner("Running…"):
            results = _run_tests(recommender, test_type)
        for name, result in results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            st.markdown(f"**{status}** {name} — {result['message']}")
        passed = sum(1 for r in results.values() if r["passed"])
        st.success(f"{passed}/{len(results)} tests passed")

    st.markdown("---")
    st.markdown("### 🤖 AI Confidence Scoring")
    st.caption("Model confidence for a given song in the catalog.")
    song_input = st.text_input("Song title", value="Come Here")
    if st.button("Check Confidence"):
        conf = recommender.get_confidence_score(song_input)
        st.metric("Confidence Score", f"{conf:.2%}")
        if conf > 0.8:
            st.success("High confidence — reliable recommendation")
        elif conf > 0.5:
            st.warning("Medium confidence — some uncertainty")
        else:
            st.error("Low confidence — may need more data")


# ─── Test runner ──────────────────────────────────────────────────────────────
def _run_tests(recommender, test_type: str) -> dict:
    results = {}
    if test_type in ["Consistency Test", "Full Evaluation"]:
        prefs = {"genre": "Pop", "energy": 0.5}
        r1 = recommender.recommend(prefs, 5)
        r2 = recommender.recommend(prefs, 5)
        results["Consistency"] = {
            "passed": r1 == r2,
            "message": "Consistent results on repeated calls" if r1 == r2 else "Results varied",
        }
    if test_type in ["Confidence Scoring", "Full Evaluation"]:
        conf = recommender.get_confidence_score("Come Here")
        results["Confidence Scoring"] = {
            "passed": 0 <= conf <= 1,
            "message": f"Score in valid range: {conf:.2f}",
        }
    if test_type in ["Error Handling", "Full Evaluation"]:
        try:
            result = recommender.recommend({"genre": 123}, 5)
            results["Error Handling"] = {
                "passed": isinstance(result, list),
                "message": "Invalid input handled gracefully — returned a list without crashing",
            }
        except (ValueError, TypeError) as e:
            results["Error Handling"] = {
                "passed": True,
                "message": f"Handled correctly: {type(e).__name__}",
            }
    if test_type == "Full Evaluation":
        recs1 = recommender.recommend({"genre": "Rock", "energy": 0.9}, 5)
        recs2 = recommender.recommend({"genre": "Folk", "energy": 0.2}, 5)
        results["Parameter Sensitivity"] = {
            "passed": recs1 != recs2,
            "message": "Different parameters produce different results",
        }
    return results


if __name__ == "__main__":
    main()
