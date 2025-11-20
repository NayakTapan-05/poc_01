"""
QA Chain for RAG-based question answering.
Based on working-demo implementation.
"""
import logging
from typing import Dict, List, Optional

from services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class QAChain:
    """QA chain that combines retrieval with simple answer generation."""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize QA chain.
        
        Args:
            vector_store: VectorStore instance for retrieval
        """
        self.vector_store = vector_store
        
        # Greeting patterns
        self.greetings = [
            'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon',
            'good evening', 'howdy', 'sup', 'what\'s up', 'yo'
        ]
        
        # Question patterns
        self.question_words = [
            'what', 'who', 'where', 'when', 'why', 'how', 'which', 'tell me',
            'explain', 'describe', 'what is', 'what are', 'can you', 'do you know'
        ]
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting."""
        query_lower = query.lower().strip()
        return any(query_lower.startswith(greeting) for greeting in self.greetings)
    
    def _is_question(self, query: str) -> bool:
        """Check if query is a question about brands."""
        query_lower = query.lower().strip()
        # Check for question words or question mark
        has_question_mark = '?' in query
        has_question_word = any(query_lower.startswith(qw) for qw in self.question_words)
        # Check for brand-related keywords
        has_brand_keywords = any(kw in query_lower for kw in ['brand', 'product', 'company', 'about'])
        
        return has_question_mark or has_question_word or has_brand_keywords
    
    def answer(self, brand: str, query: str) -> Dict:
        """
        Answer a question for a specific brand.
        
        Args:
            brand: Brand name
            query: User question
            
        Returns:
            Dict with 'answer' and 'sources' keys
        """
        try:
            query_lower = query.lower().strip()
            
            # Handle greetings
            if self._is_greeting(query):
                return {
                    'answer': f"Hello! I'm here to help you learn about {brand}. What would you like to know?",
                    'sources': []
                }
            
            # Handle non-questions
            if not self._is_question(query) and len(query.split()) < 5:
                return {
                    'answer': f"I can help you learn about {brand}. Try asking me a question like 'What is {brand}'s brand essence?' or 'Tell me about {brand}'.",
                    'sources': []
                }
            
            # Perform RAG search
            results = self.vector_store.query(brand, query, k=4)
            
            if not results:
                return {
                    'answer': f"I don't have specific information about '{query}' for {brand}. Try asking about the brand's essence, values, or key messages.",
                    'sources': []
                }
            
            # Build conversational answer
            if len(results) == 1:
                answer = f"Based on {brand}'s brand knowledge:\n\n{results[0]['text']}"
            else:
                answer = f"Here's what I found about {brand}:\n\n"
                for i, result in enumerate(results[:3], 1):
                    snippet = result['text'][:300] + ('...' if len(result['text']) > 300 else '')
                    answer += f"{i}. {snippet}\n\n"
            
            sources = [
                {
                    'text': r['text'],
                    'brand': brand,
                    'metadata': r['metadata'],
                    'relevance': max(0, 1.0 - r['distance'])  # Convert distance to relevance score
                }
                for r in results
            ]
            
            return {
                'answer': answer,
                'sources': sources
            }
            
        except Exception as e:
            logger.error(f"Error answering question for brand {brand}: {e}")
            return {
                'answer': f"Sorry, I encountered an error while searching for information about {brand}.",
                'sources': []
            }
    
    def answer_multi_brand(self, brands: List[str], query: str) -> Dict:
        """
        Answer a question across multiple brands.
        
        Args:
            brands: List of brand names
            query: User question
            
        Returns:
            Dict with 'answer' and 'sources' keys
        """
        try:
            query_lower = query.lower().strip()
            
            # Handle greetings
            if self._is_greeting(query):
                brand_list = ', '.join(brands[:3])
                if len(brands) > 3:
                    brand_list += f', and {len(brands) - 3} more'
                return {
                    'answer': f"Hello! I can help you learn about your brands: {brand_list}. What would you like to know?",
                    'sources': []
                }
            
            # Handle non-questions
            if not self._is_question(query) and len(query.split()) < 5:
                return {
                    'answer': f"I can help you learn about your brands. Try asking me a question like 'What is the brand essence?' or 'Tell me about the key messages.'",
                    'sources': []
                }
            
            # Perform RAG search across all brands
            all_results = []
            
            for brand in brands:
                results = self.vector_store.query(brand, query, k=2)
                for result in results:
                    result['metadata']['brand'] = brand
                    all_results.append(result)
            
            if not all_results:
                return {
                    'answer': f"I don't have specific information about '{query}' in the brand knowledge base. Try asking about brand essence, values, or key messages.",
                    'sources': []
                }
            
            # Sort by relevance (lower distance = more relevant)
            all_results.sort(key=lambda x: x['distance'])
            
            top_results = all_results[:4]
            
            # Build conversational answer
            if len(top_results) == 1:
                brand = top_results[0]['metadata'].get('brand', 'Unknown')
                answer = f"Based on {brand}'s brand knowledge:\n\n{top_results[0]['text']}"
            else:
                answer = "Here's what I found across your brands:\n\n"
                for i, result in enumerate(top_results, 1):
                    brand = result['metadata'].get('brand', 'Unknown')
                    snippet = result['text'][:250] + ('...' if len(result['text']) > 250 else '')
                    answer += f"**{brand}**: {snippet}\n\n"
            
            sources = [
                {
                    'text': r['text'],
                    'brand': r['metadata'].get('brand', 'Unknown'),
                    'metadata': r['metadata'],
                    'relevance': max(0, 1.0 - r['distance'])
                }
                for r in top_results
            ]
            
            return {
                'answer': answer,
                'sources': sources
            }
            
        except Exception as e:
            logger.error(f"Error answering multi-brand question: {e}")
            return {
                'answer': "Sorry, I encountered an error while searching for information.",
                'sources': []
            }
