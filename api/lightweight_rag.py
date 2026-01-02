"""
Lightweight RAG implementation for Vercel deployment.
Uses Google's Embedding API + numpy for vector similarity.
Pre-computed embeddings stored as JSON (no ChromaDB/PyTorch needed!)
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Google Generative AI for embeddings
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Alternative: Groq doesn't have embeddings, so we'll use a simple TF-IDF fallback
from collections import Counter
import re
import math


class LightweightRAG:
    """
    Lightweight RAG that works on Vercel's free tier.
    Uses Google Gemini embeddings or TF-IDF fallback.
    """
    
    def __init__(self, embeddings_file: str = None):
        self.embeddings_file = embeddings_file or "data/faq_embeddings.json"
        self.documents: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.use_gemini = False
        
        # Initialize Gemini if available
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if GEMINI_AVAILABLE and google_api_key:
            genai.configure(api_key=google_api_key)
            self.use_gemini = True
            self.embedding_model = "models/text-embedding-004"
            print("LightweightRAG: Using Google Gemini embeddings")
        else:
            print("LightweightRAG: Using TF-IDF fallback (no GOOGLE_API_KEY)")
        
        # Load pre-computed embeddings
        self._load_embeddings()
    
    def _load_embeddings(self):
        """Load pre-computed embeddings from JSON file."""
        embeddings_path = Path(self.embeddings_file)
        
        if embeddings_path.exists():
            try:
                with open(embeddings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.documents = data.get("documents", [])
                embeddings_list = data.get("embeddings", [])
                
                if embeddings_list:
                    self.embeddings = np.array(embeddings_list)
                    print(f"LightweightRAG: Loaded {len(self.documents)} documents with embeddings")
                else:
                    print(f"LightweightRAG: Loaded {len(self.documents)} documents (no embeddings)")
            except Exception as e:
                print(f"LightweightRAG: Error loading embeddings: {e}")
                self.documents = []
                self.embeddings = None
        else:
            print(f"LightweightRAG: No embeddings file found at {embeddings_path}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text using Gemini or TF-IDF fallback."""
        if self.use_gemini:
            try:
                result = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_query"
                )
                return result['embedding']
            except Exception as e:
                print(f"Gemini embedding error: {e}")
                return self._tfidf_embedding(text)
        else:
            return self._tfidf_embedding(text)
    
    def _tfidf_embedding(self, text: str, dim: int = 768) -> List[float]:
        """
        Simple TF-IDF inspired embedding fallback.
        Creates a consistent vector representation based on word frequencies.
        """
        # Tokenize and normalize
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = Counter(words)
        
        # Create a hash-based embedding
        embedding = [0.0] * dim
        for word, count in word_counts.items():
            # Use word hash to determine position
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
            positions = [(word_hash + i) % dim for i in range(5)]
            
            # TF component
            tf = 1 + math.log(count) if count > 0 else 0
            
            for pos in positions:
                embedding[pos] += tf * (1 if word_hash % 2 == 0 else -1)
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.documents:
            return []
        
        # Get query embedding
        query_embedding = np.array(self.get_embedding(query))
        
        # Calculate similarities
        if self.embeddings is not None:
            similarities = []
            for i, doc_embedding in enumerate(self.embeddings):
                sim = self.cosine_similarity(query_embedding, doc_embedding)
                similarities.append((i, sim))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k results
            results = []
            for idx, score in similarities[:top_k]:
                doc = self.documents[idx].copy()
                doc['score'] = float(score)
                results.append(doc)
            
            return results
        else:
            # No embeddings - use simple keyword matching
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fallback keyword-based search."""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        scores = []
        for i, doc in enumerate(self.documents):
            doc_text = doc.get('text', '').lower()
            doc_words = set(re.findall(r'\b\w+\b', doc_text))
            
            # Jaccard similarity
            intersection = len(query_words & doc_words)
            union = len(query_words | doc_words)
            score = intersection / union if union > 0 else 0
            
            scores.append((i, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            doc = self.documents[idx].copy()
            doc['score'] = score
            results.append(doc)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG statistics."""
        return {
            "total_documents": len(self.documents),
            "has_embeddings": self.embeddings is not None,
            "embedding_dim": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "embedding_type": "gemini" if self.use_gemini else "tfidf_fallback",
            "documents_loaded": len(self.documents) > 0
        }


# Singleton instance
_rag_instance: Optional[LightweightRAG] = None


def get_lightweight_rag() -> LightweightRAG:
    """Get or create the RAG instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = LightweightRAG()
    return _rag_instance
