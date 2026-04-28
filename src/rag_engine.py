"""
RAG Engine - Retrieval-Augmented Generation for song context
Provides AI-powered insights about songs using vector storage
"""

import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import chromadb, fall back to simple implementation
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available, using simple fallback")


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for song context.
    
    Features:
    - Vector storage of song information
    - Semantic search for song context
    - Similarity-based retrieval
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the RAG engine"""
        self._song_docs = {}  # always initialized so fallback never raises AttributeError
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.Client(Settings(
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                ))
                
                # Try to get or create collection
                try:
                    self.collection = self.client.get_collection("song_context")
                except:
                    self.collection = self.client.create_collection(
                        "song_context",
                        metadata={"description": "Song context and information"}
                    )
                
                logger.info("RAG engine initialized with ChromaDB")
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {e}")
                self._use_fallback()
        else:
            self._use_fallback()
    
    def _use_fallback(self):
        """Use simple in-memory fallback"""
        self.collection = None
        self._song_docs = {}
        logger.info("RAG engine initialized with fallback mode")
    
    def add_song_context(self, title: str, artist: str, genre: str, 
                        mood: str, writer: str, description: str = ""):
        """
        Add song context to the knowledge base.
        
        Args:
            title: Song title
            artist: Artist name
            genre: Music genre
            mood: Song mood
            writer: Songwriter
            description: Additional context/description
        """
        if not description:
            description = self._generate_default_description(
                title, artist, genre, mood, writer
            )
        
        doc_id = f"{title}_{artist}".replace(" ", "_").lower()
        
        if self.collection is not None and CHROMADB_AVAILABLE:
            try:
                self.collection.add(
                    documents=[description],
                    ids=[doc_id],
                    metadatas=[{
                        "title": title,
                        "artist": artist,
                        "genre": genre,
                        "mood": mood,
                        "writer": writer
                    }]
                )
            except Exception as e:
                logger.warning(f"Failed to add to ChromaDB: {e}")
        
        # Also store in fallback
        self._song_docs[doc_id] = {
            "title": title,
            "artist": artist,
            "genre": genre,
            "mood": mood,
            "writer": writer,
            "description": description
        }
    
    def _generate_default_description(self, title: str, artist: str, 
                                       genre: str, mood: str, writer: str) -> str:
        """Generate a default description for a song"""
        return f"""
        Song: {title}
        Artist: {artist}
        Genre: {genre}
        Mood: {mood}
        Writer: {writer}
        
        This is a {mood.lower()} {genre.lower()} track by {artist}, 
        written by {writer}. The song fits into the {genre} genre 
        and has a {mood} emotional quality.
        """.strip()
    
    def get_song_context(self, query: str) -> str:
        """
        Get context information for a song.
        
        Args:
            query: Song title or search query
            
        Returns:
            Context information about the song
        """
        if self.collection is not None and CHROMADB_AVAILABLE:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=1
                )
                
                if results and results.get('documents'):
                    return results['documents'][0][0]
            except Exception as e:
                logger.warning(f"ChromaDB query failed: {e}")
        
        # Fallback to simple search
        return self._fallback_search(query)
    
    def _fallback_search(self, query: str) -> str:
        """Simple fallback search"""
        query_lower = query.lower()
        
        for doc_id, doc in self._song_docs.items():
            if query_lower in doc['title'].lower() or query_lower in doc['artist'].lower():
                return doc['description']
        
        # Return generic response if no match
        return f"""
        Information about '{query}':
        
        This song is in your music catalog. Use the recommendation system 
        to get more details about similar songs and artists.
        
        The RAG system can provide deeper context about songs when more 
        descriptive information is added to the knowledge base.
        """.strip()
    
    def find_similar_songs(self, query: str, n: int = 5) -> List[Dict]:
        """
        Find similar songs based on a query.
        
        Args:
            query: Search query
            n: Number of results to return
            
        Returns:
            List of similar songs with similarity scores
        """
        if self.collection is not None and CHROMADB_AVAILABLE:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n
                )
                
                similar = []
                if results and results.get('metadatas'):
                    for i, meta in enumerate(results['metadatas'][0]):
                        similar.append({
                            "title": meta.get("title", "Unknown"),
                            "artist": meta.get("artist", "Unknown"),
                            "genre": meta.get("genre", "Unknown"),
                            "similarity": 1.0 - (i * 0.1)  # Approximate similarity
                        })
                return similar
            except Exception as e:
                logger.warning(f"ChromaDB similar search failed: {e}")
        
        return []
    
    def get_document_count(self) -> int:
        """Get the number of documents in the knowledge base"""
        if self.collection is not None and CHROMADB_AVAILABLE:
            try:
                return self.collection.count()
            except:
                pass
        return len(self._song_docs)
    
    def bulk_add_songs(self, songs: List[Dict]):
        """
        Add multiple songs to the knowledge base.
        
        Args:
            songs: List of song dictionaries
        """
        for song in songs:
            self.add_song_context(
                title=song.get('title', ''),
                artist=song.get('artist', ''),
                genre=song.get('genre', ''),
                mood=song.get('mood', ''),
                writer=song.get('writer', 'Unknown'),
                description=song.get('description', '')
            )
        
        logger.info(f"Added {len(songs)} songs to RAG knowledge base")
    
    def search_by_genre(self, genre: str) -> List[Dict]:
        """Search songs by genre"""
        results = []
        
        for doc in self._song_docs.values():
            if doc['genre'].lower() == genre.lower():
                results.append(doc)
        
        return results
    
    def search_by_mood(self, mood: str) -> List[Dict]:
        """Search songs by mood"""
        results = []
        
        for doc in self._song_docs.values():
            if doc['mood'].lower() == mood.lower():
                results.append(doc)
        
        return results
    
    def search_by_writer(self, writer: str) -> List[Dict]:
        """Search songs by writer"""
        results = []
        
        for doc in self._song_docs.values():
            if writer.lower() in doc['writer'].lower():
                results.append(doc)
        
        return results
    
    def clear(self):
        """Clear all documents from the knowledge base"""
        if self.collection is not None and CHROMADB_AVAILABLE:
            try:
                self.client.delete_collection("song_context")
                self.collection = self.client.create_collection(
                    "song_context",
                    metadata={"description": "Song context and information"}
                )
            except Exception as e:
                logger.warning(f"Failed to clear collection: {e}")
        
        self._song_docs = {}
        logger.info("RAG knowledge base cleared")