"""
Vector store module using ChromaDB for persistent vector storage.
Based on working-demo implementation with brand-scoped collections.
"""
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging
import hashlib
import json
from datetime import datetime

from config.default import settings, CHROMA_DIR

# Try to import Settings - may not be available in all ChromaDB versions
try:
    from chromadb.config import Settings
    HAS_SETTINGS = True
except ImportError:
    HAS_SETTINGS = False
    Settings = None

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB-based vector store with brand-scoped collections.
    
    Database Location:
    - ChromaDB data is stored in: ./data/chroma (relative to repo root)
    - This directory MUST be writable for brand ingestion to work
    - ChromaDB creates SQLite files (chroma.sqlite3, etc.) in this directory
    - All files are automatically set to writable permissions (666) on initialization
    
    If you see "readonly database" errors:
    1. Check that ./data/chroma exists and is writable
    2. Check file permissions: ls -la data/chroma
    3. Ensure the directory is not on a read-only filesystem
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory for persistent storage
        """
        if persist_directory is None:
            persist_directory = str(CHROMA_DIR)
        
        self.persist_directory = Path(persist_directory)
        
        # Ensure directory exists and is writable - CRITICAL for brand ingestion
        import os
        import stat
        try:
            # Create directory with full permissions
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created ChromaDB directory: {self.persist_directory}")
            
            # Make directory fully writable (777) - ensures ChromaDB can create SQLite files
            os.chmod(self.persist_directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            logger.info(f"Set ChromaDB directory permissions to 777: {self.persist_directory}")
            
            # Verify write access by creating a test file
            test_file = self.persist_directory / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                logger.info(f"Verified ChromaDB directory is writable: {self.persist_directory}")
            except Exception as test_error:
                logger.error(f"ChromaDB directory is NOT writable: {test_error}")
                raise RuntimeError(
                    f"ChromaDB directory is not writable: {self.persist_directory}. "
                    f"This will cause 'readonly database' errors. Error: {test_error}"
                )
            
            # Also ensure any existing database files are writable
            for db_file in self.persist_directory.rglob("*"):
                if db_file.is_file() and not db_file.name.startswith('.'):
                    try:
                        # Set full read/write permissions (666 for files)
                        os.chmod(db_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                        logger.debug(f"Set write permissions for {db_file}")
                    except Exception as e:
                        logger.warning(f"Could not set permissions for {db_file}: {e}")
        except Exception as e:
            logger.error(f"Error setting directory permissions: {e}", exc_info=True)
            raise RuntimeError(
                f"Failed to setup writable ChromaDB directory at {self.persist_directory}: {e}. "
                f"Brand ingestion will fail with 'readonly database' errors."
            )
        
        # Initialize ChromaDB client with explicit write permissions
        # ChromaDB 0.4.x uses PersistentClient - CRITICAL: must point to writable directory
        try:
            # Use PersistentClient which handles persistence automatically
            # The path MUST be writable or ChromaDB will create SQLite files in readonly mode
            if HAS_SETTINGS:
                self.client = chromadb.PersistentClient(
                    path=str(self.persist_directory.absolute()),  # Use absolute path for clarity
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            else:
                # Fallback for ChromaDB versions without Settings
                self.client = chromadb.PersistentClient(path=str(self.persist_directory.absolute()))
            
            logger.info(f"Initialized ChromaDB PersistentClient at {self.persist_directory.absolute()}")
            
            # Test write access by trying to list collections (this also verifies connection)
            try:
                collections = self.client.list_collections()
                logger.info(f"ChromaDB connection successful. Found {len(collections)} collections")
                
                # Additional test: try to create a test collection to verify write access
                test_collection_name = "__write_test__"
                try:
                    # Try to get or create a test collection
                    test_col = self.client.get_or_create_collection(name=test_collection_name)
                    # Try to add a test document
                    test_col.add(
                        documents=["test"],
                        ids=["test_id"],
                        embeddings=[[0.1] * 384]  # Dummy embedding
                    )
                    # Delete the test collection
                    self.client.delete_collection(name=test_collection_name)
                    logger.info("ChromaDB write test successful - database is writable")
                except Exception as write_test_error:
                    logger.warning(f"ChromaDB write test failed (may be OK if collections exist): {write_test_error}")
            except Exception as test_error:
                logger.error(f"ChromaDB connection test failed: {test_error}", exc_info=True)
                raise RuntimeError(
                    f"ChromaDB connection failed. This will cause brand ingestion to fail. "
                    f"Error: {test_error}. Directory: {self.persist_directory.absolute()}"
                )
                
        except Exception as e:
            logger.error(f"Error initializing ChromaDB PersistentClient: {e}", exc_info=True)
            # Try to fix permissions and retry
            try:
                import os
                import stat
                logger.info("Attempting to fix permissions and retry ChromaDB initialization...")
                # Fix permissions again
                os.chmod(self.persist_directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                for db_file in self.persist_directory.rglob("*"):
                    if db_file.is_file():
                        os.chmod(db_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                
                # Retry initialization
                if HAS_SETTINGS:
                    self.client = chromadb.PersistentClient(
                        path=str(self.persist_directory.absolute()),
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True
                        )
                    )
                else:
                    self.client = chromadb.PersistentClient(path=str(self.persist_directory.absolute()))
                
                logger.info(f"Retried and initialized ChromaDB PersistentClient at {self.persist_directory.absolute()}")
            except Exception as e2:
                logger.error(f"Failed to initialize ChromaDB after permission fix: {e2}", exc_info=True)
                raise RuntimeError(
                    f"Failed to initialize ChromaDB with write access: {e2}. "
                    f"Directory: {self.persist_directory.absolute()}. "
                    f"Please ensure the directory exists and is writable. "
                    f"This error will cause brand ingestion to fail with 'readonly database' errors."
                )
        
        # Initialize embedding model
        embedding_model_id = getattr(settings, 'EMBEDDING_MODEL_ID', getattr(settings, 'EMBEDDING_MODEL', 'all-MiniLM-L6-v2'))
        logger.info(f"Loading embedding model: {embedding_model_id}")
        self.embedding_model = SentenceTransformer(embedding_model_id)
        
        # Metadata file for tracking collections
        self.metadata_file = self.persist_directory / "metadata.json"
        self.metadata = self._load_metadata()
        
        # Verify write access - CRITICAL: ensures brand ingestion won't fail with readonly errors
        self._verify_write_access()
        
        # Ensure any SQLite files ChromaDB creates are writable
        self._ensure_chromadb_files_writable()
    
    def _verify_write_access(self):
        """Verify that the ChromaDB directory and files are writable."""
        import os
        import stat
        try:
            # Test directory write access
            test_file = self.persist_directory / ".write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                logger.info("Verified ChromaDB directory is writable")
            except Exception as e:
                logger.error(f"ChromaDB directory is not writable: {e}")
                raise RuntimeError(
                    f"ChromaDB directory is not writable: {self.persist_directory}. "
                    f"This will cause brand ingestion to fail with 'readonly database' errors. Error: {e}"
                )
            
            # Verify metadata file is writable
            if self.metadata_file.exists():
                try:
                    os.chmod(self.metadata_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                except Exception as e:
                    logger.warning(f"Could not set metadata file permissions: {e}")
        except Exception as e:
            logger.error(f"Error verifying write access: {e}", exc_info=True)
            raise
    
    def _ensure_chromadb_files_writable(self):
        """
        Ensure all ChromaDB SQLite files are writable.
        ChromaDB creates SQLite files internally, and they must be writable for brand ingestion.
        """
        import os
        import stat
        import time
        
        try:
            # ChromaDB creates files like chroma.sqlite3, chroma.sqlite3-wal, etc.
            # Ensure all SQLite files in the directory are writable
            sqlite_patterns = ['*.sqlite', '*.sqlite3', '*.db', '*-wal', '*-shm']
            files_fixed = 0
            
            for pattern in sqlite_patterns:
                for db_file in self.persist_directory.glob(pattern):
                    if db_file.is_file():
                        try:
                            # Set full read/write permissions (666 for files)
                            os.chmod(db_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                            files_fixed += 1
                            logger.debug(f"Ensured write permissions for ChromaDB file: {db_file.name}")
                        except Exception as e:
                            logger.warning(f"Could not set permissions for {db_file}: {e}")
            
            if files_fixed > 0:
                logger.info(f"Ensured write permissions for {files_fixed} ChromaDB database files")
            
            # Also check for any files ChromaDB might create in subdirectories
            for db_file in self.persist_directory.rglob("*.sqlite*"):
                if db_file.is_file():
                    try:
                        os.chmod(db_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                    except Exception as e:
                        logger.warning(f"Could not set permissions for {db_file}: {e}")
                        
        except Exception as e:
            logger.warning(f"Error ensuring ChromaDB files are writable: {e}")
            # Don't fail initialization, but log the warning
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the vector store.
        
        Returns:
            Dict with health status and diagnostic information
        """
        health = {
            "status": "healthy",
            "directory": str(self.persist_directory),
            "directory_exists": self.persist_directory.exists(),
            "directory_writable": False,
            "chromadb_connected": False,
            "collections_count": 0,
            "metadata_file_exists": self.metadata_file.exists(),
            "metadata_file_writable": False,
            "errors": []
        }
        
        try:
            # Check directory writability
            import os
            import stat
            test_file = self.persist_directory / ".health_check"
            try:
                test_file.write_text("health_check")
                test_file.unlink()
                health["directory_writable"] = True
            except Exception as e:
                health["status"] = "unhealthy"
                health["errors"].append(f"Directory not writable: {e}")
            
            # Check ChromaDB connection
            try:
                collections = self.client.list_collections()
                health["chromadb_connected"] = True
                health["collections_count"] = len(collections)
            except Exception as e:
                health["status"] = "unhealthy"
                health["errors"].append(f"ChromaDB connection failed: {e}")
            
            # Check metadata file
            if self.metadata_file.exists():
                try:
                    os.chmod(self.metadata_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                    health["metadata_file_writable"] = True
                except Exception as e:
                    health["errors"].append(f"Metadata file not writable: {e}")
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["errors"].append(f"Health check failed: {e}")
        
        return health
    
    def _load_metadata(self) -> dict:
        """Load metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                return {}
        return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            # Ensure directory exists and is writable
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            import os
            import stat
            if self.metadata_file.exists():
                os.chmod(self.metadata_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            # Ensure file is writable after creation
            if self.metadata_file.exists():
                os.chmod(self.metadata_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        except PermissionError as e:
            logger.error(f"Permission error saving metadata: {e}. File: {self.metadata_file}")
            raise
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            # Don't raise - metadata is not critical for functionality


    def reload_metadata(self):
        """Reload metadata from file (useful after external changes)."""
        self._load_metadata()
        logger.info(f"Reloaded metadata for {len(self.metadata)} brands")
    
    def _get_collection_name(self, brand: str) -> str:
        """
        Get sanitized collection name for a brand.
        
        Args:
            brand: Brand name
            
        Returns:
            Sanitized collection name
        """
        # Sanitize brand name for collection naming
        sanitized = brand.lower().replace(' ', '_').replace('-', '_')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
        
        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = 'brand_' + sanitized
        
        # Truncate if too long
        if len(sanitized) > 63:
            sanitized = sanitized[:63]
        
        # Ensure minimum length
        if len(sanitized) < 3:
            sanitized = sanitized + '_collection'
        
        return sanitized
    
    def add_documents(self, brand: str, documents: List[Dict[str, str]]):
        """
        Add documents to the vector store for a specific brand.
        
        Args:
            brand: Brand name
            documents: List of document dicts with 'text' key
        """
        if not documents:
            logger.warning(f"No documents to add for brand: {brand}")
            return
        
        if not brand or not brand.strip():
            raise ValueError("Brand name is required and cannot be empty")
        
        # Verify write access before proceeding
        try:
            self._verify_write_access()
        except Exception as e:
            logger.error(f"Write access verification failed: {e}")
            raise RuntimeError(f"Cannot write to ChromaDB: {e}")
        
        collection_name = self._get_collection_name(brand)
        logger.info(f"[add_documents] Starting: brand='{brand}', collection='{collection_name}', documents={len(documents)}")
        
        try:
            # Get or create collection
            # Use get/create pattern to avoid ChromaDB 0.3.23 _client bug
            logger.info(f"[add_documents] Attempting to get or create collection '{collection_name}'")
            try:
                collection = self.client.get_collection(name=collection_name)
                logger.info(f"[add_documents] Found existing collection '{collection_name}'")
            except Exception as e:
                logger.info(f"[add_documents] Collection not found, creating new one: {e}")
                try:
                    collection = self.client.create_collection(
                        name=collection_name,
                        metadata={"brand": brand}
                    )
                    logger.info(f"[add_documents] Successfully created collection '{collection_name}'")
                except Exception as create_error:
                    logger.error(f"[add_documents] Failed to create collection: {create_error}", exc_info=True)
                    raise RuntimeError(f"Failed to create ChromaDB collection '{collection_name}': {create_error}")
            
            # Prepare documents
            texts = [doc['text'] for doc in documents]
            logger.info(f"[add_documents] Prepared {len(texts)} document texts")
            
            # Generate embeddings
            logger.info(f"[add_documents] Generating embeddings for {len(texts)} documents...")
            try:
                embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
                logger.info(f"[add_documents] Generated embeddings: shape={embeddings.shape}")
            except Exception as embed_error:
                logger.error(f"[add_documents] Failed to generate embeddings: {embed_error}", exc_info=True)
                raise RuntimeError(f"Failed to generate embeddings: {embed_error}")
            
            ids = []
            metadatas = []
            logger.info(f"[add_documents] Preparing metadata for {len(documents)} documents")
            for i, doc in enumerate(documents):
                text_hash = hashlib.md5(doc['text'].encode()).hexdigest()
                doc_id = f"{brand}_{text_hash}_{i}"
                ids.append(doc_id)
                
                metadata = {
                    'brand': brand,
                    'chunk_id': doc.get('chunk_id', 0),
                    'total_chunks': doc.get('total_chunks', 1),
                }
                metadatas.append(metadata)
            
            logger.info(f"[add_documents] Prepared {len(ids)} document IDs and metadata entries")
            
            # Add to collection
            logger.info(f"[add_documents] Adding {len(texts)} documents to collection '{collection_name}'")
            try:
                collection.add(
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"[add_documents] Successfully added {len(texts)} documents to collection '{collection_name}'")
            except Exception as add_error:
                logger.error(f"Error adding documents to ChromaDB: {add_error}", exc_info=True)
                error_str = str(add_error).lower()
                
                # Check if it's a permission/readonly error
                if "readonly" in error_str or "permission" in error_str or "read-only" in error_str:
                    # Try to fix permissions and retry
                    import os
                    import stat
                    try:
                        logger.info("Detected readonly error, fixing permissions...")
                        
                        # Fix directory permissions
                        os.chmod(self.persist_directory, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                        
                        # Fix all database files (including SQLite files ChromaDB creates)
                        files_fixed = 0
                        for db_file in self.persist_directory.rglob("*"):
                            if db_file.is_file():
                                try:
                                    # Set full read/write permissions (666 for files)
                                    os.chmod(db_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
                                    files_fixed += 1
                                    logger.debug(f"Fixed permissions for {db_file}")
                                except Exception as perm_error:
                                    logger.warning(f"Could not fix permissions for {db_file}: {perm_error}")
                        
                        if files_fixed > 0:
                            logger.info(f"Fixed permissions for {files_fixed} database files")
                        
                        # Reinitialize client to ensure fresh connection
                        try:
                            if HAS_SETTINGS:
                                self.client = chromadb.PersistentClient(
                                    path=str(self.persist_directory),
                                    settings=Settings(
                                        anonymized_telemetry=False,
                                        allow_reset=True
                                    )
                                )
                            else:
                                self.client = chromadb.PersistentClient(path=str(self.persist_directory))
                            # Get collection again
                            collection = self.client.get_collection(name=collection_name)
                        except Exception as reinit_error:
                            logger.warning(f"Could not reinitialize client: {reinit_error}")
                        
                        logger.info("Retrying document addition after permission fix...")
                        collection.add(
                            embeddings=embeddings.tolist(),
                            documents=texts,
                            metadatas=metadatas,
                            ids=ids
                        )
                        logger.info(f"Successfully added documents after permission fix")
                    except Exception as retry_error:
                        logger.error(f"Retry also failed: {retry_error}", exc_info=True)
                        raise RuntimeError(
                            f"ChromaDB write error (readonly database): {add_error}. "
                            f"Tried to fix permissions but failed: {retry_error}. "
                            f"Please check directory permissions: {self.persist_directory}"
                        )
                else:
                    # Re-raise non-permission errors
                    raise

            # Force persistence for ChromaDB 0.4.x
            # Note: PersistentClient automatically persists, but we can try explicit persist if available
            try:
                if hasattr(self.client, 'persist'):
                    self.client.persist()
                    logger.info(f"Explicitly persisted collection {collection_name}")
                else:
                    # PersistentClient auto-persists, just log
                    logger.info(f"Collection {collection_name} persisted automatically (PersistentClient)")
            except Exception as e:
                # Persist might not be available or needed for PersistentClient
                logger.debug(f"Persist method not available or not needed: {e}")

            # Verify collection exists after persistence
            logger.info(f"[add_documents] Verifying collection persistence...")
            try:
                verify_collection = self.client.get_collection(name=collection_name)
                verify_count = verify_collection.count()
                logger.info(f"[add_documents] Verified collection '{collection_name}' has {verify_count} documents")
            except Exception as e:
                logger.warning(f"[add_documents] Could not verify collection count: {e}")
            
            # Update metadata
            logger.info(f"[add_documents] Updating metadata for brand '{brand}'")
            if brand not in self.metadata:
                self.metadata[brand] = {
                    'collection_name': collection_name,
                    'created_at': datetime.now().isoformat(),
                }
            
            # Get count safely (handle different ChromaDB versions)
            try:
                doc_count = collection.count()
                logger.info(f"[add_documents] Collection count: {doc_count}")
            except Exception as e:
                logger.warning(f"[add_documents] Could not get collection count: {e}, using estimated count")
                # Try alternative method
                try:
                    results = collection.get(limit=1)
                    doc_count = len(results.get('ids', [])) if results else 0
                except:
                    doc_count = len(documents)  # Fallback to input count
            
            self.metadata[brand].update({
                'last_ingested_at': datetime.now().isoformat(),
                'total_documents': doc_count,
            })
            
            try:
                self._save_metadata()
                logger.info(f"[add_documents] Saved metadata successfully")
            except Exception as meta_error:
                logger.error(f"[add_documents] Failed to save metadata: {meta_error}")
                # Don't fail the whole operation if metadata save fails
            
            logger.info(f"[add_documents] Completed: Added {len(documents)} documents to collection '{collection_name}' for brand '{brand}'")
        
        except Exception as e:
            logger.error(f"[add_documents] Error adding documents for brand '{brand}': {e}", exc_info=True)
            raise
    
    def query(self, brand: str, query_text: str, k: int = None) -> List[Dict]:
        """
        Query the vector store for a specific brand.
        
        Args:
            brand: Brand name
            query_text: Query text
            k: Number of results to return
            
        Returns:
            List of result dicts with 'text', 'metadata', and 'distance' keys
        """
        if k is None:
            k = settings.K_RETRIEVAL
        
        # Check if brand exists in metadata first
        if brand not in self.metadata:
            logger.error(f"Brand '{brand}' not found in metadata")
            return []

        collection_name = self._get_collection_name(brand)
        
        try:
            # Get collection
            collection = self.client.get_collection(name=collection_name)
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query_text])[0]
            
            # Query
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            logger.info(f"Retrieved {len(formatted_results)} results for brand '{brand}'")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error querying brand {brand}: {e}")
            return []
    
    def get_all_brands(self) -> List[str]:
        """Get list of all brands in the vector store."""
        return list(self.metadata.keys())

    def get_unique_brand_keys(self) -> List[str]:
        """Get list of unique brand keys (grouping by brand name)."""
        # Since each brand in metadata represents a unique brand key
        # (each brand key gets its own collection), return unique brand names
        brand_keys = set()
        for brand_name in self.metadata.keys():
            # Extract the base brand key (before any processing)
            # For now, just return the brand names as they are unique
            brand_keys.add(brand_name)
        return sorted(list(brand_keys))
    
    def get_brand_stats(self, brand: str) -> Dict:
        """Get statistics for a specific brand."""
        if brand not in self.metadata:
            return {}
        
        collection_name = self._get_collection_name(brand)
        
        try:
            collection = self.client.get_collection(name=collection_name)
            # Get count safely (handle different ChromaDB versions)
            try:
                count = collection.count()
            except Exception as e:
                logger.warning(f"Could not get collection count: {e}, using alternative method")
                # Try alternative method
                try:
                    results = collection.get(limit=10000)  # Get all to count
                    count = len(results.get('ids', [])) if results else 0
                except:
                    count = 0
            
            # Calculate chunks (same as documents/vectors for this implementation)
            chunks = count
            vectors = count  # In ChromaDB, each document is a vector
            
            stats = {
                'brand': brand,
                'collection_name': collection_name,
                'total_documents': count,
                'chunks': chunks,
                'vectors': vectors,
                'docs': count,  # Alias for compatibility
                'created_at': self.metadata[brand].get('created_at', 'Unknown'),
                'last_ingested_at': self.metadata[brand].get('last_ingested_at', 'Unknown'),
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting stats for brand {brand}: {e}")
            return {}
    
    def get_all_stats(self) -> List[Dict]:
        """Get statistics for all brands."""
        stats = []
        for brand in self.get_all_brands():
            brand_stats = self.get_brand_stats(brand)
            if brand_stats:
                stats.append(brand_stats)
        return stats
    
    def clear_brand(self, brand: str):
        """Clear all data for a specific brand."""
        collection_name = self._get_collection_name(brand)
        
        try:
            self.client.delete_collection(name=collection_name)
            if brand in self.metadata:
                del self.metadata[brand]
                self._save_metadata()
            logger.info(f"Cleared data for brand: {brand}")
        except Exception as e:
            logger.error(f"Error clearing brand {brand}: {e}")
    
    def clear_all(self):
        """Clear all data from the vector store."""
        try:
            collections = self.client.list_collections()
            for collection in collections:
                # Handle both collection objects and collection names
                collection_name = collection.name if hasattr(collection, 'name') else str(collection)
                self.client.delete_collection(name=collection_name)
            
            self.metadata = {}
            self._save_metadata()
            
            logger.info("Cleared all data from vector store")
        except Exception as e:
            logger.error(f"Error clearing all data: {e}")
