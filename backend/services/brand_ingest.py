"""
Brand Ingestion Service - Clean pipeline for ingesting brand knowledge.
Handles file loading, chunking, embedding, and vector store upsert.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional
from .doc_loader import load_document
from .text_splitter import TextSplitter
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class BrandIngestService:
    """
    Brand ingestion service that orchestrates the full pipeline:
    load → chunk → embed → upsert
    """
    
    def __init__(self, vector_store: VectorStore, text_splitter: TextSplitter = None):
        """
        Initialize brand ingestion service.
        
        Args:
            vector_store: VectorStore instance
            text_splitter: TextSplitter instance (creates default if None)
        """
        self.vector_store = vector_store
        self.text_splitter = text_splitter or TextSplitter()
    
    def ingest_file(
        self,
        file_path: str,
        brand: Optional[str] = None
    ) -> Dict:
        """
        Ingest a brand document file into the vector store.
        
        Args:
            file_path: Path to document file (CSV, XLSX, PDF, TXT)
            brand: Optional brand name (required for non-CSV/XLSX files)
            
        Returns:
            Dict with ingestion results:
            - brands: List of brand IDs ingested
            - total_chunks: Total number of chunks created
            - chunks_per_brand: Dict mapping brand to chunk count
        """
        logger.info(f"[ingest_file] Starting ingestion: file_path='{file_path}', brand='{brand}'")
        
        # Pre-flight validation
        if not self.vector_store:
            raise RuntimeError("Vector store is not initialized")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path_obj.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Check file is readable
        if not os.access(file_path_obj, os.R_OK):
            raise PermissionError(f"File is not readable: {file_path}")
        
        # Validate brand name for CSV/Excel files
        ext = file_path_obj.suffix.lower()
        if ext in ['.csv', '.xlsx', '.xls'] and (not brand or not brand.strip()):
            raise ValueError("Brand name is required for CSV/Excel files. Please provide a brand name.")
        
        logger.info(f"[ingest_file] Validation passed, proceeding with ingestion")
        
        # Load documents
        logger.info(f"[ingest_file] Step 1: Loading documents from file...")
        try:
            documents = load_document(file_path, brand=brand)
            if not documents:
                raise ValueError("No documents extracted from file")
            logger.info(f"[ingest_file] Step 1 complete: Loaded {len(documents)} documents")
        except Exception as e:
            logger.error(f"[ingest_file] Failed to load documents: {e}", exc_info=True)
            raise ValueError(f"Failed to load documents from file: {e}")
        
        # Split into chunks
        logger.info(f"[ingest_file] Step 2: Splitting documents into chunks...")
        try:
            chunks = self.text_splitter.split_documents(documents)
            if not chunks:
                raise ValueError("No chunks created from documents")
            logger.info(f"[ingest_file] Step 2 complete: Created {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"[ingest_file] Failed to create chunks: {e}", exc_info=True)
            raise ValueError(f"Failed to create chunks: {e}")
        
        # Group by brand
        logger.info(f"[ingest_file] Step 3: Grouping chunks by brand...")
        brands_dict = {}
        for chunk in chunks:
            chunk_brand = chunk.get('brand')
            if not chunk_brand:
                logger.warning(f"[ingest_file] Chunk missing brand field, skipping: {chunk.get('text', '')[:50]}")
                continue
            if chunk_brand not in brands_dict:
                brands_dict[chunk_brand] = []
            brands_dict[chunk_brand].append(chunk)
        
        if not brands_dict:
            raise ValueError("No brands found in documents. Ensure documents have a 'brand' field.")
        
        logger.info(f"[ingest_file] Step 3 complete: Found {len(brands_dict)} brand(s): {list(brands_dict.keys())}")
        
        # Store files by brand
        logger.info(f"[ingest_file] Step 4: Storing uploaded file copies...")
        try:
            self._store_uploaded_file(file_path, list(brands_dict.keys()))
            logger.info(f"[ingest_file] Step 4 complete: File copies stored")
        except Exception as e:
            logger.warning(f"[ingest_file] Failed to store file copies (non-critical): {e}")
        
        # Upsert to vector store
        logger.info(f"[ingest_file] Step 5: Upserting chunks to vector store...")
        chunks_per_brand = {}
        for brand_name, brand_chunks in brands_dict.items():
            logger.info(f"[ingest_file] Upserting {len(brand_chunks)} chunks for brand: {brand_name}")
            if brand_chunks:
                logger.info(f"[ingest_file] Sample chunk: {brand_chunks[0]['text'][:100]}")
            try:
                self.vector_store.add_documents(brand_name, brand_chunks)
                chunks_per_brand[brand_name] = len(brand_chunks)
                logger.info(f"[ingest_file] Successfully ingested brand: {brand_name} ({len(brand_chunks)} chunks)")
            except Exception as e:
                logger.error(f"[ingest_file] Failed to ingest brand '{brand_name}': {e}", exc_info=True)
                raise RuntimeError(f"Failed to ingest brand '{brand_name}': {e}")
        
        logger.info(f"[ingest_file] Step 5 complete: All brands ingested successfully")
        logger.info(f"[ingest_file] Ingestion complete: {len(chunks)} total chunks for {len(brands_dict)} brand(s)")
        
        return {
            "brands": list(brands_dict.keys()),
            "total_chunks": len(chunks),
            "chunks_per_brand": chunks_per_brand
        }
    
    def _store_uploaded_file(self, file_path: str, brands: List[str]):
        """
        Store uploaded file in brand-specific directories.

        Args:
            file_path: Path to uploaded file
            brands: List of brand IDs from the file
        """
        try:
            from config.default import UPLOAD_DIR
            from shutil import copy2
            import datetime

            file_path_obj = Path(file_path)

            # Store file in each brand's directory
            for brand in brands:
                # Create brand-specific directory with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                brand_dir = UPLOAD_DIR / brand / timestamp
                brand_dir.mkdir(parents=True, exist_ok=True)

                dest_path = brand_dir / file_path_obj.name
                copy2(file_path, dest_path)

                logger.info(f"Stored uploaded file for brand '{brand}' to: {dest_path}")

        except Exception as e:
            logger.warning(f"Could not store uploaded file copy: {e}")

