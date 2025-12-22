"""
ChromaDB-based RAG Retriever
Fast, local, persistent vector database for knowledge retrieval
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class ChromaDBRetriever:
    """
    Local RAG with ChromaDB and sentence transformers.
    
    Performance:
    - Embedding: ~50-100ms
    - Search: ~10-50ms
    - Total: ~60-150ms
    """
    
    def __init__(self, persist_directory: str = "./data/vectordb"):
        """Initialize ChromaDB and embedding model"""
        
        # Create directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding model (384 dimensions, fast!)
        logger.info("loading_embedding_model", model="all-MiniLM-L6-v2")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        doc_count = self.collection.count()
        logger.info("chromadb_initialized", 
                   collection_size=doc_count,
                   persist_directory=persist_directory)
        
        # Initialize with sample data if empty
        if doc_count == 0:
            self._add_sample_knowledge()
    
    def _add_sample_knowledge(self):
        """Add sample knowledge base"""
        sample_docs = [
            "Python is a high-level interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            
            "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It uses statistical techniques to give computers the ability to learn from data.",
            
            "TinyLlama is a compact language model with 1.1 billion parameters, optimized for fast inference on consumer hardware. It can generate text at approximately 50 tokens per second on CPU.",
            
            "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic API documentation and is built on Starlette and Pydantic.",
            
            "Async programming in Python uses asyncio to handle concurrent operations efficiently. It allows multiple tasks to run concurrently without using multiple threads, making it ideal for I/O-bound operations.",
            
            "Retrieval Augmented Generation (RAG) combines large language models with information retrieval to provide more accurate and contextual responses by grounding the model's outputs in retrieved documents.",
            
            "Vector databases store high-dimensional vectors representing data semantics, enabling fast similarity search. They are essential for RAG systems, recommendation engines, and semantic search applications.",
            
            "Guardrails in AI systems are safety mechanisms that check inputs and outputs for harmful content, PII, toxicity, and prompt injection attempts. They help ensure AI systems behave responsibly and safely.",
            
            "ChromaDB is an open-source embedding database that makes it easy to build LLM applications by providing a simple API for storing and querying embeddings with metadata.",
            
            "Voice assistants use speech recognition to convert spoken language into text, process it with AI models, and convert responses back to speech using text-to-speech systems."
        ]
        
        sample_metadata = [
            {"category": "programming", "language": "python", "topic": "basics"},
            {"category": "ai", "topic": "machine-learning", "level": "intro"},
            {"category": "ai", "model": "tinyllama", "topic": "llm"},
            {"category": "framework", "language": "python", "topic": "api"},
            {"category": "programming", "language": "python", "topic": "async"},
            {"category": "ai", "topic": "rag", "concept": "retrieval"},
            {"category": "database", "topic": "vectors", "concept": "search"},
            {"category": "ai", "topic": "safety", "concept": "guardrails"},
            {"category": "database", "name": "chromadb", "topic": "vectors"},
            {"category": "ai", "topic": "voice", "concept": "assistant"}
        ]
        
        self.add_documents(sample_docs, sample_metadata)
        logger.info("sample_knowledge_added", count=len(sample_docs))
    
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None):
        """
        Add documents to knowledge base.
        
        Args:
            documents: List of text documents
            metadatas: Optional list of metadata dicts
        """
        if not documents:
            return
        
        # Generate embeddings
        logger.info("generating_embeddings", count=len(documents))
        embeddings = self.embedder.encode(documents).tolist()
        
        # Generate IDs
        existing_count = self.collection.count()
        ids = [f"doc_{existing_count + i}" for i in range(len(documents))]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas or [{}] * len(documents)
        )
        
        logger.info("documents_added", 
                   count=len(documents),
                   total_docs=self.collection.count())
    
    def search(self, query: str, top_k: int = 3, score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search knowledge base.
        
        Args:
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of results with text, score, and metadata
        """
        # Encode query
        query_embedding = self.embedder.encode([query]).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        # Format results
        formatted = []
        for i in range(len(results['documents'][0])):
            # Convert distance to similarity score (1 - normalized distance)
            score = 1 - results['distances'][0][i]
            
            if score >= score_threshold:
                formatted.append({
                    'text': results['documents'][0][i],
                    'score': float(score),
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'id': results['ids'][0][i]
                })
        
        logger.debug("search_complete", 
                    query=query[:50],
                    results_found=len(formatted))
        
        return formatted
    
    def clear(self):
        """Clear all documents"""
        self.client.delete_collection("knowledge_base")
        self.collection = self.client.create_collection("knowledge_base")
        logger.info("knowledge_base_cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name
        }


# Global singleton instance
_rag_instance = None

def get_rag_retriever() -> ChromaDBRetriever:
    """Get or create RAG retriever singleton"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = ChromaDBRetriever()
    return _rag_instance
