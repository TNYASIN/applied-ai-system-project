"""
Data Manager - Handles song catalog and writer/composer data
"""

import pandas as pd
import os
from typing import List, Dict


class DataManager:
    """Manages song catalog and writer/composer data"""
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            # Use data from original project
            data_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                '..',
                'ai110-module3show-musicrecommendersimulation-starter',
                'data'
            )
        
        self.data_path = data_path
        self.songs = self._load_songs()
        self.writers = self._load_writers()
    
    def _load_songs(self) -> pd.DataFrame:
        """Load song catalog"""
        # Try to load from original project first
        songs_file = os.path.join(self.data_path, 'songs.csv')
        
        if os.path.exists(songs_file):
            df = pd.read_csv(songs_file)
            # Add writer column if missing (for backward compatibility)
            if 'writer' not in df.columns:
                df['writer'] = self._generate_writers(df)
        else:
            # Create sample data
            df = self._create_sample_data()
        
        return df
    
    def _generate_writers(self, df: pd.DataFrame) -> pd.Series:
        """Generate writer credits for songs - different from artists (like Spotify credits)"""
        # Map songs to their actual songwriters/composers (different from performing artists)
        # This follows real-world Spotify credits pattern
        song_to_writer = {
            'Sunrise City': 'Sarah Mitchell',
            'Midnight Coding': 'James Chen',
            'Storm Runner': 'Marcus Webb',
            'Library Rain': 'Elena Rodriguez',
            'Gym Hero': 'David Kim',
            'Spacewalk Thoughts': 'Nina Petrov',
            'Coffee Shop Stories': 'Thomas Blue',
            'Night Drive Loop': 'Sarah Mitchell',
            'Focus Flow': 'James Chen',
            'Rooftop Lights': 'Olivia Hart',
            'Come Here': 'Daniel Lanois',
            'Strangers': 'Mark Feehily',
            '9+1#': 'Jung Jae-chul',
            'Hardly Ever Smile': 'Annie Clark',
            'Poison': 'Bob Dylan',
            'Keep the Rain': 'Sufjan Stevens',
            'Dil Dhadakne Do': 'A.R. Rahman',
            '있지': 'Kim Yoon-ji',
            'These Days': 'Jackson Browne'
        }
        
        writers = []
        for title in df['title']:
            writers.append(song_to_writer.get(title, 'Unknown'))
        
        return pd.Series(writers)
    
    def _create_sample_data(self) -> pd.DataFrame:
        """Create sample song data with writer credits (different from artists)"""
        songs = [
            # Pop
            {"title": "Come Here", "artist": "Alexi Laiho", "genre": "Pop", "mood": "Happy", 
             "energy": 0.65, "tempo_bpm": 120, "valence": 0.7, "danceability": 0.6, 
             "acousticness": 0.3, "writer": "Daniel Lanois"},
            {"title": "These Days", "artist": "Foo Fighters", "genre": "Pop", "mood": "Energetic",
             "energy": 0.8, "tempo_bpm": 140, "valence": 0.6, "danceability": 0.5, 
             "acousticness": 0.2, "writer": "Jackson Browne"},
            {"title": "Keep the Rain", "artist": "Iron & Wine", "genre": "Pop", "mood": "Calm",
             "energy": 0.3, "tempo_bpm": 90, "valence": 0.4, "danceability": 0.4, 
             "acousticness": 0.8, "writer": "Sufjan Stevens"},
            
            # Rock
            {"title": "Poison", "artist": "Prince", "genre": "Rock", "mood": "Intense",
             "energy": 0.9, "tempo_bpm": 160, "valence": 0.8, "danceability": 0.7, 
             "acousticness": 0.1, "writer": "Prince"},
            {"title": "9+1#", "artist": "Radiohead", "genre": "Rock", "mood": "Intense",
             "energy": 0.85, "tempo_bpm": 150, "valence": 0.5, "danceability": 0.6, 
             "acousticness": 0.2, "writer": "Thom Yorke"},
            {"title": "Storm Runner", "artist": "Green Day", "genre": "Rock", "mood": "Energetic",
             "energy": 0.95, "tempo_bpm": 180, "valence": 0.7, "danceability": 0.8, 
             "acousticness": 0.1, "writer": "Billie Joe Armstrong"},
            
            # Hip-Hop
            {"title": "있지", "artist": "BTS", "genre": "Hip-Hop", "mood": "Energetic",
             "energy": 0.8, "tempo_bpm": 140, "valence": 0.8, "danceability": 0.9, 
             "acousticness": 0.2, "writer": "Bang Si-hyuk"},
            {"title": "Midnight Coding", "artist": "Lo-Fi Collective", "genre": "Hip-Hop", "mood": "Chill",
             "energy": 0.35, "tempo_bpm": 80, "valence": 0.5, "danceability": 0.5, 
             "acousticness": 0.7, "writer": "James Chen"},
            {"title": "Library Rain", "artist": "Chill Beats", "genre": "Hip-Hop", "mood": "Calm",
             "energy": 0.3, "tempo_bpm": 75, "valence": 0.4, "danceability": 0.4, 
             "acousticness": 0.8, "writer": "Elena Rodriguez"},
            
            # Electronic
            {"title": "Electric Dreams", "artist": "Synthwave Master", "genre": "Electronic", "mood": "Intense",
             "energy": 0.9, "tempo_bpm": 128, "valence": 0.7, "danceability": 0.9, 
             "acousticness": 0.0, "writer": "Giorgio Moroder"},
            {"title": "Neon Nights", "artist": "Cyber Punk", "genre": "Electronic", "mood": "Energetic",
             "energy": 0.85, "tempo_bpm": 135, "valence": 0.8, "danceability": 0.95, 
             "acousticness": 0.0, "writer": "Kraftwerk"},
            
            # R&B
            {"title": "Smooth Groove", "artist": "Sade", "genre": "R&B", "mood": "Calm",
             "energy": 0.4, "tempo_bpm": 100, "valence": 0.6, "danceability": 0.5, 
             "acousticness": 0.5, "writer": "Sade Adu"},
            {"title": "Velvet Touch", "artist": "D'Angelo", "genre": "R&B", "mood": "Chill",
             "energy": 0.35, "tempo_bpm": 95, "valence": 0.5, "danceability": 0.6, 
             "acousticness": 0.4, "writer": "D'Angelo"},
            
            # Folk
            {"title": "Mountain Song", "artist": "Mumford & Sons", "genre": "Folk", "mood": "Sad",
             "energy": 0.45, "tempo_bpm": 110, "valence": 0.3, "danceability": 0.4, 
             "acousticness": 0.9, "writer": "Marcus Mumford"},
            {"title": "River Flow", "artist": "Bon Iver", "genre": "Folk", "mood": "Calm",
             "energy": 0.3, "tempo_bpm": 85, "valence": 0.4, "danceability": 0.3, 
             "acousticness": 0.95, "writer": "Justin Vernon"},
            
            # Jazz
            {"title": "Blue Note", "artist": "Miles Davis", "genre": "Jazz", "mood": "Calm",
             "energy": 0.4, "tempo_bpm": 120, "valence": 0.5, "danceability": 0.4, 
             "acousticness": 0.8, "writer": "Miles Davis"},
            {"title": "Swing Time", "artist": "Duke Ellington", "genre": "Jazz", "mood": "Happy",
             "energy": 0.7, "tempo_bpm": 150, "valence": 0.8, "danceability": 0.8, 
             "acousticness": 0.7, "writer": "Duke Ellington"},
            
            # Classical
            {"title": "Moonlight Sonata", "artist": "Beethoven", "genre": "Classical", "mood": "Sad",
             "energy": 0.3, "tempo_bpm": 60, "valence": 0.3, "danceability": 0.2, 
             "acousticness": 1.0, "writer": "Ludwig van Beethoven"},
            {"title": "Four Seasons", "artist": "Vivaldi", "genre": "Classical", "mood": "Happy",
             "energy": 0.6, "tempo_bpm": 130, "valence": 0.7, "danceability": 0.5, 
             "acousticness": 1.0, "writer": "Antonio Vivaldi"},
            
            # Country
            {"title": "Country Roads", "artist": "John Denver", "genre": "Country", "mood": "Happy",
             "energy": 0.55, "tempo_bpm": 100, "valence": 0.7, "danceability": 0.6, 
             "acousticness": 0.8, "writer": "Bill Danoff"},
            {"title": "Take Me Home", "artist": "Patsy Cline", "genre": "Country", "mood": "Sad",
             "energy": 0.4, "tempo_bpm": 90, "valence": 0.4, "danceability": 0.5, 
             "acousticness": 0.7, "writer": "Harlan Howard"},
            
            # Indie
            {"title": "Arctic Lights", "artist": "Arcade Fire", "genre": "Indie", "mood": "Intense",
             "energy": 0.75, "tempo_bpm": 125, "valence": 0.5, "danceability": 0.6, 
             "acousticness": 0.5, "writer": "Win Butler"},
            {"title": "Neon Bible", "artist": "Arcade Fire", "genre": "Indie", "mood": "Intense",
             "energy": 0.8, "tempo_bpm": 140, "valence": 0.4, "danceability": 0.5, 
             "acousticness": 0.4, "writer": "Win Butler"},
            
            # Metal
            {"title": "Heavy Metal", "artist": "Metallica", "genre": "Metal", "mood": "Intense",
             "energy": 0.95, "tempo_bpm": 170, "valence": 0.6, "danceability": 0.7, 
             "acousticness": 0.0, "writer": "James Hetfield"},
            {"title": "Thunder Strike", "artist": "Iron Maiden", "genre": "Metal", "mood": "Energetic",
             "energy": 0.9, "tempo_bpm": 160, "valence": 0.7, "danceability": 0.6, 
             "acousticness": 0.1, "writer": "Steve Harris"},
        ]
        
        return pd.DataFrame(songs)
    
    def _load_writers(self) -> pd.DataFrame:
        """Load writer/composer data"""
        writer_data = []
        
        for writer in self.songs['writer'].unique():
            if writer and writer != 'Unknown':
                writer_songs = self.songs[self.songs['writer'] == writer]
                writer_data.append({
                    'writer': writer,
                    'song_count': len(writer_songs),
                    'genres': ', '.join(writer_songs['genre'].unique()),
                    'songs': list(writer_songs['title'])
                })
        
        return pd.DataFrame(writer_data)
    
    def get_songs(self) -> pd.DataFrame:
        """Get all songs"""
        return self.songs
    
    def get_writers(self) -> pd.DataFrame:
        """Get all writers/composers"""
        return self.writers
    
    def get_song_by_title(self, title: str) -> pd.Series:
        """Get a specific song by title"""
        matches = self.songs[self.songs['title'] == title]
        if not matches.empty:
            return matches.iloc[0]
        return None
    
    def get_songs_by_writer(self, writer: str) -> pd.DataFrame:
        """Get all songs by a specific writer"""
        return self.songs[self.songs['writer'] == writer]
    
    def get_songs_by_genre(self, genre: str) -> pd.DataFrame:
        """Get all songs in a genre"""
        return self.songs[self.songs['genre'] == genre]
    
    def get_genres(self) -> List[str]:
        """Get all unique genres"""
        return sorted(self.songs['genre'].unique())
    
    def get_moods(self) -> List[str]:
        """Get all unique moods"""
        return sorted(self.songs['mood'].unique())