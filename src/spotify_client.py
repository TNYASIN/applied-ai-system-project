"""
Spotify Client - OAuth authentication and API integration
"""

import os
import json
import base64
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List


class SpotifyClient:
    """Client for Spotify Web API integration"""
    
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.token_expiry = None
        
    @classmethod
    def demo_mode(cls) -> 'SpotifyClient':
        """Create a demo mode client with mock data"""
        client = cls.__new__(cls)
        client.client_id = "demo"
        client.client_secret = "demo"
        client.redirect_uri = "http://localhost:8501"
        client.access_token = "demo_token"
        client.token_expiry = datetime.now() + timedelta(hours=1)
        client._demo_data = True
        return client
    
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL"""
        scopes = [
            "user-read-private",
            "user-read-email", 
            "user-top-read",
            "user-library-read",
            "user-read-recently-played"
        ]
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "show_dialog": "true"
        }
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query}"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expiry = datetime.now() + timedelta(
            seconds=token_data["expires_in"]
        )
        
        return token_data
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh an expired access token"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expiry = datetime.now() + timedelta(
            seconds=token_data["expires_in"]
        )
        
        return token_data
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated API request"""
        if self._demo_data:
            return self._get_demo_response(endpoint)
            
        if not self.access_token:
            raise ValueError("Not authenticated. Call exchange_code_for_token first.")
        
        if self.token_expiry and datetime.now() >= self.token_expiry:
            raise ValueError("Token expired. Please re-authenticate.")
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        
        url = f"{self.API_BASE}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        
        return response.json()
    
    def _get_demo_response(self, endpoint: str) -> Dict:
        """Get demo response for testing"""
        if "me" in endpoint:
            return {
                "id": "demo_user",
                "display_name": "Demo User",
                "email": "demo@example.com",
                "images": []
            }
        elif "top" in endpoint:
            return self._get_demo_top_tracks()
        elif "recently-played" in endpoint:
            return self._get_demo_recent()
        elif "search" in endpoint:
            return self._get_demo_search()
        return {}
    
    def _get_demo_top_tracks(self) -> Dict:
        """Generate demo top tracks"""
        return {
            "items": [
                {
                    "track": {
                        "id": "1",
                        "name": "Come Here",
                        "artists": [{"name": "Alexi Laiho"}],
                        "album": {"name": "The Unwanted"},
                        "duration_ms": 180000
                    }
                },
                {
                    "track": {
                        "id": "2", 
                        "name": "These Days",
                        "artists": [{"name": "Foo Fighters"}],
                        "album": {"name": "In Your Honor"},
                        "duration_ms": 240000
                    }
                },
                {
                    "track": {
                        "id": "3",
                        "name": "Keep the Rain", 
                        "artists": [{"name": "Iron & Wine"}],
                        "album": {"name": "Our Endless Numbered Days"},
                        "duration_ms": 200000
                    }
                }
            ]
        }
    
    def _get_demo_recent(self) -> Dict:
        """Generate demo recently played"""
        return self._get_demo_top_tracks()
    
    def _get_demo_search(self) -> Dict:
        """Generate demo search results"""
        return {
            "tracks": {
                "items": [
                    {
                        "id": "10",
                        "name": "Poison",
                        "artists": [{"name": "Prince"}],
                        "album": {"name": "Lovesexy"},
                        "duration_ms": 300000
                    }
                ]
            }
        }
    
    def get_current_user(self) -> Dict:
        """Get current user profile"""
        return self._make_request("GET", "/me")
    
    def get_top_tracks(self, time_range: str = "medium_term", limit: int = 50) -> List[Dict]:
        """Get user's top tracks"""
        params = f"?time_range={time_range}&limit={limit}"
        return self._make_request("GET", f"/me/top/tracks{params}")["items"]
    
    def get_recently_played(self, limit: int = 50) -> List[Dict]:
        """Get recently played tracks"""
        params = f"?limit={limit}"
        return self._make_request("GET", f"/me/player/recently-played{params}")["items"]
    
    def search_tracks(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for tracks"""
        params = f"?q={query}&type=track&limit={limit}"
        return self._make_request("GET", f"/search{params}")["tracks"]["items"]
    
    def get_track_features(self, track_id: str) -> Dict:
        """Get audio features for a track"""
        return self._make_request("GET", f"/audio-features/{track_id}")
    
    def get_track(self, track_id: str) -> Dict:
        """Get track details"""
        return self._make_request("GET", f"/tracks/{track_id}")
    
    def get_artists(self, artist_ids: List[str]) -> List[Dict]:
        """Get multiple artist details"""
        ids = ",".join(artist_ids)
        return self._make_request("GET", f"/artists?ids={ids}")["artists"]
    
    def get_related_artists(self, artist_id: str) -> List[Dict]:
        """Get artists related to the given artist"""
        return self._make_request("GET", f"/artists/{artist_id}/related-artists")["artists"]
    
    def create_playlist(self, name: str, description: str = "") -> Dict:
        """Create a new playlist"""
        user = self.get_current_user()
        
        data = {
            "name": name,
            "description": description,
            "public": False
        }
        
        return self._make_request(
            "POST", 
            f"/users/{user['id']}/playlists",
            json=data
        )
    
    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> Dict:
        """Add tracks to a playlist"""
        data = {"uris": track_uris}
        
        return self._make_request(
            "POST",
            f"/playlists/{playlist_id}/tracks",
            json=data
        )
    
    def is_demo(self) -> bool:
        """Check if running in demo mode"""
        return getattr(self, '_demo_data', False)