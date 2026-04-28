"""
Music Recommender - Enhanced from Module 3 project
Now includes writer/composer credits and parameter-based recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MusicRecommender:
    """
    Enhanced music recommender with:
    - Content-based filtering (from Module 3)
    - Writer/Composer credits tracking
    - Parameter-based tuning
    - Confidence scoring
    """
    
    # Scoring weights (from Module 3)
    WEIGHTS = {
        'genre_match': 2.0,
        'mood_match': 1.0,
        'energy_closeness': 1.5,
        'acoustic_bonus': 0.5,
        'writer_match': 1.5,
        'tempo_match': 0.5,
        'danceability_match': 0.5,
        'valence_match': 0.5
    }
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.songs = data_manager.get_songs()
        self.writers = data_manager.get_writers()
        self._build_writer_index()
    
    def _build_writer_index(self):
        """Build index for writer/composer lookups"""
        self.writer_to_songs = {}
        
        for _, song in self.songs.iterrows():
            writer = song.get('writer', 'Unknown')
            if writer and writer != 'Unknown':
                if writer not in self.writer_to_songs:
                    self.writer_to_songs[writer] = []
                self.writer_to_songs[writer].append(song['title'])
        
        logger.info(f"Built writer index with {len(self.writer_to_songs)} writers")
    
    def recommend(self, preferences: Dict, num_results: int = 10) -> List[Dict]:
        """
        Get music recommendations based on user preferences.
        
        Args:
            preferences: Dict with genre, mood, energy, target_writers, etc.
            num_results: Number of recommendations to return
            
        Returns:
            List of recommended songs with scores
        """
        # Validate preferences
        if not isinstance(preferences, dict):
            logger.warning(f"Invalid preferences type: {type(preferences)}")
            preferences = {}
        
        results = []
        
        for _, song in self.songs.iterrows():
            score = self._score_song(song, preferences)
            
            if score > 0:  # Only include songs with positive scores
                results.append({
                    'title': song['title'],
                    'artist': song['artist'],
                    'genre': song['genre'],
                    'mood': song['mood'],
                    'energy': song['energy'],
                    'score': score,
                    'writer': song.get('writer', 'Unknown'),
                    'reasons': self._get_score_reasons(song, preferences)
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:num_results]
    
    def _score_song(self, song: pd.Series, preferences: Dict) -> float:
        """Score a single song based on preferences"""
        score = 0.0
        
        # Genre match
        if preferences.get('genre') and isinstance(preferences.get('genre'), str):
            if song['genre'].lower() == preferences['genre'].lower():
                score += self.WEIGHTS['genre_match']
        
        # Mood match
        if preferences.get('mood') and isinstance(preferences.get('mood'), str):
            if song['mood'].lower() == preferences['mood'].lower():
                score += self.WEIGHTS['mood_match']
        
        # Energy closeness
        if preferences.get('energy') is not None and isinstance(preferences.get('energy'), (int, float)):
            target_energy = preferences['energy']
            # Clamp to valid range
            target_energy = max(0.0, min(1.0, target_energy))
            energy_gap = abs(song['energy'] - target_energy)
            score += (1 - energy_gap) * self.WEIGHTS['energy_closeness']
        
        # Acoustic bonus
        if preferences.get('acousticness') and isinstance(preferences.get('acousticness'), (int, float)):
            if preferences['acousticness'] > 0.7 and song['acousticness'] > 0.7:
                score += self.WEIGHTS['acoustic_bonus']
        
        # Writer/Composer match
        if preferences.get('target_writers') and isinstance(preferences.get('target_writers'), list):
            song_writer = song.get('writer', 'Unknown')
            if song_writer in preferences['target_writers']:
                score += self.WEIGHTS['writer_match']
        
        # Tempo match
        if preferences.get('tempo') and isinstance(preferences.get('tempo'), (int, float)):
            target_tempo = preferences['tempo']
            tempo_gap = abs(song['tempo_bpm'] - target_tempo) / 100
            score += max(0, (1 - tempo_gap)) * self.WEIGHTS['tempo_match']
        
        # Danceability match
        if preferences.get('danceability') is not None and isinstance(preferences.get('danceability'), (int, float)):
            target_dance = preferences['danceability']
            dance_gap = abs(song['danceability'] - target_dance)
            score += (1 - dance_gap) * self.WEIGHTS['danceability_match']
        
        # Valence match
        if preferences.get('valence') is not None and isinstance(preferences.get('valence'), (int, float)):
            target_valence = preferences['valence']
            valence_gap = abs(song['valence'] - target_valence)
            score += (1 - valence_gap) * self.WEIGHTS['valence_match']
        
        return score
    
    def _get_score_reasons(self, song: pd.Series, preferences: Dict) -> List[str]:
        """Get human-readable reasons for the score"""
        reasons = []
        
        if preferences.get('genre'):
            if song['genre'].lower() == preferences['genre'].lower():
                reasons.append(f"Matches {song['genre']} genre")
        
        if preferences.get('mood'):
            if song['mood'].lower() == preferences['mood'].lower():
                reasons.append(f"Matches {song['mood']} mood")
        
        if preferences.get('target_writers'):
            song_writer = song.get('writer', 'Unknown')
            if song_writer in preferences['target_writers']:
                reasons.append(f"By favorite writer {song_writer}")
        
        if preferences.get('energy') is not None:
            energy_gap = abs(song['energy'] - preferences['energy'])
            if energy_gap < 0.2:
                reasons.append("Similar energy level")
        
        return reasons if reasons else ["General match"]
    
    def get_available_writers(self) -> List[str]:
        """Get list of all available writers/composers"""
        return sorted(self.writer_to_songs.keys())
    
    def get_writer_statistics(self) -> pd.DataFrame:
        """Get statistics about writers in the catalog"""
        writer_counts = []
        
        for writer, songs in self.writer_to_songs.items():
            writer_counts.append({
                'writer': writer,
                'count': len(songs),
                'songs': songs
            })
        
        df = pd.DataFrame(writer_counts)
        if not df.empty:
            df = df.sort_values('count', ascending=False)
        
        return df
    
    def get_confidence_score(self, song_title: str) -> float:
        """
        Calculate confidence score for a recommendation.
        
        Returns a value between 0 and 1 indicating how confident
        we are in the recommendation.
        """
        song = self.songs[self.songs['title'] == song_title]
        
        if song.empty:
            return 0.0
        
        song = song.iloc[0]
        
        # Factors that increase confidence
        confidence = 0.5  # Base confidence
        
        # Has complete data
        if pd.notna(song.get('genre')) and pd.notna(song.get('mood')):
            confidence += 0.1
        
        # Has writer information
        if song.get('writer') and song.get('writer') != 'Unknown':
            confidence += 0.2
        
        # Has all audio features
        features = ['energy', 'tempo_bpm', 'valence', 'danceability', 'acousticness']
        if all(pd.notna(song.get(f)) for f in features):
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def recommend_by_writer(self, writer: str, num_results: int = 10) -> List[Dict]:
        """Get recommendations specifically from a writer"""
        if writer not in self.writer_to_songs:
            return []
        
        writer_songs = self.songs[
            self.songs['title'].isin(self.writer_to_songs[writer])
        ]
        
        results = []
        for _, song in writer_songs.iterrows():
            results.append({
                'title': song['title'],
                'artist': song['artist'],
                'genre': song['genre'],
                'mood': song['mood'],
                'energy': song['energy'],
                'score': 1.0,
                'writer': song.get('writer', 'Unknown')
            })
        
        return results[:num_results]
    
    def get_similar_songs(self, song_title: str, num_results: int = 5) -> List[Dict]:
        """Find songs similar to a given song"""
        song = self.songs[self.songs['title'] == song_title]
        
        if song.empty:
            return []
        
        song = song.iloc[0]
        
        # Score all songs by similarity
        results = []
        for _, s in self.songs.iterrows():
            if s['title'] == song_title:
                continue
            
            similarity = 0.0
            
            # Same genre
            if s['genre'] == song['genre']:
                similarity += 0.3
            
            # Same mood
            if s['mood'] == song['mood']:
                similarity += 0.2
            
            # Similar energy
            energy_diff = abs(s['energy'] - song['energy'])
            similarity += (1 - energy_diff) * 0.3
            
            # Same writer
            if s.get('writer') == song.get('writer'):
                similarity += 0.2
            
            if similarity > 0:
                results.append({
                    'title': s['title'],
                    'artist': s['artist'],
                    'genre': s['genre'],
                    'similarity': similarity
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:num_results]