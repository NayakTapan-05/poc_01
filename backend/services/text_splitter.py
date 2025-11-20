"""
Text splitter for chunking documents.
Based on working-demo implementation.
"""
import logging
from typing import List, Dict

from config.default import settings

logger = logging.getLogger(__name__)


class TextSplitter:
    """Split documents into chunks with overlap."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize text splitter.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def split_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of document dicts with 'text' and 'brand' keys
            
        Returns:
            List of chunk dicts with 'text', 'brand', 'chunk_id', 'total_chunks' keys
        """
        all_chunks = []
        
        for doc in documents:
            text = doc['text']
            brand = doc['brand']
            
            chunks = self._split_text(text)
            
            for i, chunk_text in enumerate(chunks):
                all_chunks.append({
                    'text': chunk_text,
                    'brand': brand,
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                })
        
        logger.info(f"Split {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                for sep in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > self.chunk_size // 2:  # Only if in second half
                        end = start + last_sep + len(sep)
                        break
                else:
                    last_space = text[start:end].rfind(' ')
                    if last_space > self.chunk_size // 2:
                        end = start + last_space + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            
            if start >= end:
                start = end
        
        return chunks
