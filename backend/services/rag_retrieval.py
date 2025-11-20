"""
RAG Retrieval Service - Clean interface for brand knowledge retrieval.
Provides top-K snippet retrieval with optional reranking.
"""
import logging
from typing import List, Dict, Optional
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGRetrieval:
    """
    RAG retrieval service with configurable top-K and optional reranking.
    Provides a clean interface for retrieving brand knowledge snippets.
    """
    
    def __init__(self, vector_store: VectorStore, top_k: int = 5):
        """
        Initialize RAG retrieval service.
        
        Args:
            vector_store: VectorStore instance
            top_k: Default number of results to retrieve
        """
        self.vector_store = vector_store
        self.top_k = top_k
        self._reranker = None
    
    def retrieve(
        self,
        brand_id: str,
        query: str,
        top_k: Optional[int] = None,
        use_reranking: bool = False
    ) -> List[Dict]:
        """
        Retrieve top-K brand snippets for a query.
        
        Args:
            brand_id: Brand identifier
            query: Query text
            top_k: Number of results (defaults to instance top_k)
            use_reranking: Whether to use cross-encoder reranking (optional)
            
        Returns:
            List of dicts with 'text', 'metadata', 'distance', 'score' keys
        """
        k = top_k or self.top_k
        
        # Retrieve from vector store
        results = self.vector_store.query(brand_id, query, k=k * 2 if use_reranking else k)
        
        if not results:
            logger.warning(f"No results found for brand '{brand_id}' with query: {query[:50]}")
            return []
        
        # Optional reranking
        if use_reranking and len(results) > k:
            results = self._rerank(query, results, top_k=k)
        
        # Format results with scores
        formatted = []
        for result in results[:k]:
            distance = result.get('distance', 1.0)
            score = max(0.0, 1.0 - distance)  # Convert distance to similarity score
            
            formatted.append({
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'distance': distance,
                'score': round(score, 4)
            })
        
        logger.info(f"Retrieved {len(formatted)} snippets for brand '{brand_id}'")
        return formatted
    
    def retrieve_multi_brand(
        self,
        brand_ids: List[str],
        query: str,
        top_k_per_brand: int = 3,
        total_top_k: int = 8
    ) -> List[Dict]:
        """
        Retrieve snippets across multiple brands.
        
        Args:
            brand_ids: List of brand identifiers
            query: Query text
            top_k_per_brand: Results per brand
            total_top_k: Total results to return
            
        Returns:
            List of results sorted by relevance, with brand metadata
        """
        all_results = []
        
        for brand_id in brand_ids:
            brand_results = self.vector_store.query(brand_id, query, k=top_k_per_brand)
            for result in brand_results:
                result['metadata'] = result.get('metadata', {})
                result['metadata']['brand'] = brand_id
                all_results.append(result)
        
        # Sort by distance (lower = more relevant)
        all_results.sort(key=lambda x: x.get('distance', 1.0))
        
        # Format and limit
        formatted = []
        for result in all_results[:total_top_k]:
            distance = result.get('distance', 1.0)
            score = max(0.0, 1.0 - distance)
            
            formatted.append({
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'distance': distance,
                'score': round(score, 4)
            })
        
        return formatted
    
    def _rerank(self, query: str, results: List[Dict], top_k: int) -> List[Dict]:
        """
        Rerank results using cross-encoder (optional, fallback if unavailable).
        
        Args:
            query: Query text
            results: Initial retrieval results
            top_k: Number of top results to return
            
        Returns:
            Reranked results
        """
        # Try to use cross-encoder reranker if available
        try:
            from sentence_transformers import CrossEncoder
            if self._reranker is None:
                # Use a small, fast cross-encoder model
                self._reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
            # Prepare pairs for reranking
            pairs = [[query, r['text']] for r in results]
            scores = self._reranker.predict(pairs)
            
            # Sort by score (higher = more relevant)
            scored_results = list(zip(results, scores))
            scored_results.sort(key=lambda x: x[1], reverse=True)
            
            return [r for r, _ in scored_results[:top_k]]
            
        except (ImportError, Exception) as e:
            logger.debug(f"Reranking not available, using vector search results: {e}")
            # Fallback: return top-K by distance
            results.sort(key=lambda x: x.get('distance', 1.0))
            return results[:top_k]

