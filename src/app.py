"""
Music Recommender System - Main Application
Extended from Module 3 project with Spotify integration,
writer/composer credits, and RAG capabilities.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os

from spotify_client import SpotifyClient
from recommender import MusicRecommender
from rag_engine import RAGEngine
from data_manager import DataManager

# Page configuration
st.set_page_config(
    page_title="🎵 MelodyMind - AI Music Recommender",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'spotify_client' not in st.session_state:
    st.session_state.spotify_client = None
if 'recommender' not in st.session_state:
    st.session_state.recommender = None
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = None
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {}
if 'top_writers' not in st.session_state:
    st.session_state.top_writers = []


def init_services():
    """Initialize all services"""
    data_manager = DataManager()
    
    # Initialize recommender
    recommender = MusicRecommender(data_manager)
    
    # Initialize RAG engine
    rag_engine = RAGEngine()
    
    return recommender, rag_engine, data_manager


def main():
    """Main application entry point"""
    
    # Header
    st.title("🎵 MelodyMind")
    st.markdown("### AI-Powered Music Recommendation System")
    st.markdown("---")
    
    # Sidebar for navigation
    st.sidebar.title("🎛️ Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["🏠 Home", "🔗 Connect Spotify", "🎼 Recommendations", "✍️ Writer Credits", "📊 Analytics"]
    )
    
    # Initialize services
    recommender, rag_engine, data_manager = init_services()
    
    if page == "🏠 Home":
        show_home_page(recommender, data_manager)
    elif page == "🔗 Connect Spotify":
        show_spotify_connect_page()
    elif page == "🎼 Recommendations":
        show_recommendations_page(recommender, rag_engine)
    elif page == "✍️ Writer Credits":
        show_writer_credits_page(recommender, data_manager)
    elif page == "📊 Analytics":
        show_analytics_page(recommender, rag_engine, data_manager)


def show_home_page(recommender, data_manager):
    """Home page with system overview"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Welcome to MelodyMind
        
        Your intelligent music recommendation companion that learns your taste
        and discovers new music you'll love.
        
        ### Features
        - 🎧 **Spotify Integration** - Connect your real account
        - ✍️ **Writer Credits** - See your most listened songwriters
        - 🎛️ **Parameter Tuning** - Fine-tune recommendations
        - 🤖 **AI Context** - RAG-powered song insights
        - 📊 **Reliability Testing** - Evaluate recommendation quality
        """)
        
        st.info("💡 Start by connecting your Spotify account or using demo mode!")
    
    with col2:
        st.markdown("### Quick Stats")
        songs = data_manager.get_songs()
        st.metric("Songs in Catalog", len(songs))
        
        writers = data_manager.get_writers()
        st.metric("Writers/Composers", len(writers))
        
        # Demo mode button
        if st.button("🎮 Enter Demo Mode", type="primary"):
            st.session_state.demo_mode = True
            st.rerun()


def show_spotify_connect_page():
    """Spotify OAuth connection page"""
    st.header("🔗 Connect Your Spotify Account")
    
    st.markdown("""
    Connect your Spotify account to get personalized recommendations based on
    your actual listening history.
    """)
    
    # Spotify connection form
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔐 OAuth Configuration")
        
        client_id = st.text_input("Spotify Client ID", type="password", 
                                  help="Get from developer.spotify.com")
        client_secret = st.text_input("Spotify Client Secret", type="password",
                                       help="Get from developer.spotify.com")
        redirect_uri = st.text_input("Redirect URI", 
                                     value="http://localhost:8501/callback",
                                     help="Must match Spotify app settings")
    
    with col2:
        st.markdown("### 📋 Setup Instructions")
        st.markdown("""
        1. Go to [developer.spotify.com](https://developer.spotify.com)
        2. Create a new app
        3. Add `http://localhost:8501/callback` as redirect URI
        4. Copy your Client ID and Secret
        5. Paste them above and click Connect
        """)
    
    st.markdown("---")
    
    # Connection button
    if st.button("🔗 Connect to Spotify", type="primary"):
        if client_id and client_secret:
            try:
                spotify_client = SpotifyClient(client_id, client_secret, redirect_uri)
                auth_url = spotify_client.get_auth_url()
                st.success("✅ Spotify client initialized!")
                st.markdown(f"[Click here to authorize]({auth_url})")
                st.session_state.spotify_client = spotify_client
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter your Spotify credentials")
    
    # Alternative: Demo mode
    st.markdown("### Or use Demo Mode")
    st.markdown("Use sample data to explore the system without connecting Spotify.")
    
    if st.button("🎮 Use Demo Data", type="secondary"):
        st.session_state.demo_mode = True
        st.session_state.spotify_client = SpotifyClient.demo_mode()
        st.rerun()


def show_recommendations_page(recommender, rag_engine):
    """Main recommendations page with parameter tuning"""
    st.header("🎼 Get Recommendations")
    
    # Parameter tuning section
    st.markdown("### 🎛️ Adjust Parameters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        genre = st.selectbox(
            "Genre",
            ["Any", "Pop", "Rock", "Hip-Hop", "R&B", "Electronic", "Folk", 
             "Country", "Jazz", "Classical", "Indie", "Metal"]
        )
    
    with col2:
        mood = st.selectbox(
            "Mood",
            ["Any", "Happy", "Sad", "Energetic", "Calm", "Intense", "Chill"]
        )
    
    with col3:
        energy = st.slider("Energy Level", 0.0, 1.0, 0.5, 0.05)
    
    with col4:
        target_writers = st.multiselect(
            "Preferred Writers",
            recommender.get_available_writers()
        )
    
    # Additional filters
    with st.expander("🔍 Advanced Filters"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tempo = st.slider("Tempo (BPM)", 60, 200, 120)
        with c2:
            danceability = st.slider("Danceability", 0.0, 1.0, 0.5)
        with c3:
            valence = st.slider("Valence (Mood)", 0.0, 1.0, 0.5)
        with c4:
            acousticness = st.slider("Acousticness", 0.0, 1.0, 0.3)
    
    # Get recommendations
    num_recommendations = st.slider("Number of Recommendations", 3, 20, 10)
    
    if st.button("🎵 Get Recommendations", type="primary"):
        with st.spinner("🤖 Generating recommendations..."):
            # Build preferences
            preferences = {
                'genre': genre if genre != "Any" else None,
                'mood': mood if mood != "Any" else None,
                'energy': energy,
                'target_writers': target_writers,
                'tempo': tempo,
                'danceability': danceability,
                'valence': valence,
                'acousticness': acousticness
            }
            
            # Get recommendations
            results = recommender.recommend(preferences, num_recommendations)
            
            # Display results
            st.markdown("### 🎧 Your Recommendations")
            
            for i, song in enumerate(results, 1):
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{i}. {song['title']}**")
                        st.markdown(f"   🎤 {song['artist']} | 📀 {song['genre']}")
                        st.markdown(f"   ✍️ {song.get('writer', 'Unknown')}")
                    with c2:
                        st.metric("Score", f"{song['score']:.2f}")
                    st.divider()
            
            # RAG context for top recommendation
            if results:
                st.markdown("### 🤖 AI Context")
                with st.spinner("Loading song insights..."):
                    context = rag_engine.get_song_context(results[0]['title'])
                    st.info(context)
            
            # Save to session for analytics
            st.session_state.last_recommendations = results


def show_writer_credits_page(recommender, data_manager):
    """Writer/Composer credits page"""
    st.header("✍️ Writer & Composer Credits")
    
    st.markdown("""
    Discover the songwriters and composers behind your favorite music.
    Track your most listened writers and get recommendations based on them.
    """)
    
    # Get writer stats
    writer_stats = recommender.get_writer_statistics()
    
    if not writer_stats.empty:
        # Top writers visualization
        st.markdown("### 🏆 Your Top Writers")
        
        top_writers = writer_stats.head(10)
        
        # Bar chart
        import altair as alt
        chart = alt.Chart(top_writers).mark_bar(color='#1DB954').encode(
            x=alt.X('count', title='Songs Listened'),
            y=alt.Y('writer', sort='-x', title='Writer'),
            tooltip=['writer', 'count']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
        
        # Writer details
        st.markdown("### 📝 Writer Details")
        
        for _, row in top_writers.iterrows():
            with st.expander(f"✍️ {row['writer']} ({row['count']} songs)"):
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Songs", row['count'])
                with c2:
                    if st.button(f"🎵 Recommend by {row['writer']}", 
                                key=f"rec_{row['writer']}"):
                        st.session_state.target_writers = [row['writer']]
                        # Navigate to recommendations
        
        # Recommendation by writer
        st.markdown("### 🎯 Recommend by Writer")
        selected_writer = st.selectbox("Select Writer", writer_stats['writer'].tolist())
        
        if st.button(f"Get recommendations from {selected_writer}"):
            prefs = {'target_writers': [selected_writer], 'energy': 0.5}
            results = recommender.recommend(prefs, 10)
            
            st.markdown(f"### Songs by {selected_writer}")
            for song in results:
                st.markdown(f"- **{song['title']}** - {song['artist']}")
    else:
        st.info("📊 Connect Spotify or use demo mode to see writer statistics!")


def show_analytics_page(recommender, rag_engine, data_manager):
    """Analytics and testing page"""
    st.header("📊 Analytics & Testing")
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Songs", len(data_manager.get_songs()))
    with col2:
        st.metric("Total Writers", len(data_manager.get_writers()))
    with col3:
        st.metric("Genres", len(data_manager.get_songs()['genre'].unique()))
    with col4:
        st.metric("RAG Documents", rag_engine.get_document_count())
    
    st.markdown("---")
    
    # Reliability testing section
    st.markdown("### 🧪 Run Reliability Tests")
    
    test_type = st.radio(
        "Select Test Type",
        ["Consistency Test", "Confidence Scoring", "Error Handling", "Full Evaluation"]
    )
    
    if st.button("▶️ Run Tests", type="primary"):
        with st.spinner("Running tests..."):
            results = run_tests(recommender, test_type)
            
            st.markdown("### 📋 Test Results")
            
            # Display results
            for test_name, result in results.items():
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                st.markdown(f"**{status}** {test_name}")
                st.markdown(f"   {result['message']}")
            
            # Summary
            passed = sum(1 for r in results.values() if r['passed'])
            total = len(results)
            st.success(f"🎉 {passed}/{total} tests passed!")
    
    # Confidence scoring demo
    st.markdown("### 🎯 Confidence Scoring Demo")
    
    sample_song = st.text_input("Enter a song title to check confidence", 
                                value="Come Here")
    
    if st.button("Check Confidence"):
        confidence = recommender.get_confidence_score(sample_song)
        st.metric("Confidence Score", f"{confidence:.2%}")
        
        if confidence > 0.8:
            st.success("High confidence - reliable recommendation")
        elif confidence > 0.5:
            st.warning("Medium confidence - some uncertainty")
        else:
            st.error("Low confidence - may need more data")


def run_tests(recommender, test_type):
    """Run reliability tests"""
    results = {}
    
    if test_type in ["Consistency Test", "Full Evaluation"]:
        # Test 1: Consistency
        prefs = {'genre': 'Pop', 'energy': 0.5}
        r1 = recommender.recommend(prefs, 5)
        r2 = recommender.recommend(prefs, 5)
        
        results["Consistency"] = {
            'passed': r1 == r2,
            'message': f"Got consistent results on repeated calls" if r1 == r2 else "Results varied between calls"
        }
    
    if test_type in ["Confidence Scoring", "Full Evaluation"]:
        # Test 2: Confidence scoring
        confidence = recommender.get_confidence_score("Come Here")
        results["Confidence Scoring"] = {
            'passed': 0 <= confidence <= 1,
            'message': f"Confidence score in valid range: {confidence:.2f}"
        }
    
    if test_type in ["Error Handling", "Full Evaluation"]:
        # Test 3: Error handling
        try:
            bad_prefs = {'genre': 123}  # Invalid type
            recommender.recommend(bad_prefs, 5)
            results["Error Handling"] = {
                'passed': False,
                'message': "Should have raised error for invalid input"
            }
        except (ValueError, TypeError) as e:
            results["Error Handling"] = {
                'passed': True,
                'message': f"Properly handled invalid input: {type(e).__name__}"
            }
    
    if test_type == "Full Evaluation":
        # Test 4: Parameter adjustment
        prefs1 = {'genre': 'Rock', 'energy': 0.9}
        prefs2 = {'genre': 'Folk', 'energy': 0.2}
        recs1 = recommender.recommend(prefs1, 5)
        recs2 = recommender.recommend(prefs2, 5)
        
        results["Parameter Sensitivity"] = {
            'passed': recs1 != recs2,
            'message': "Different parameters produce different results"
        }
    
    return results


if __name__ == "__main__":
    main()