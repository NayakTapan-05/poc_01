"""
Core flow tests for Brand DNAi Content Studio.
Tests brand ingestion, chat/RAG, image generation, and video generation.
Uses stubs/mocks where needed for external dependencies.
"""
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.default import settings, DATA_DIR, ASSETS_DIR


class TestBrandIngestion:
    """Tests for brand ingestion into ChromaDB."""
    
    def test_vector_store_initialization(self):
        """Test that VectorStore initializes correctly."""
        from services.vector_store import VectorStore
        
        vector_store = VectorStore()
        assert vector_store is not None
        assert vector_store.client is not None
        
    def test_vector_store_health_check(self):
        """Test VectorStore health check."""
        from services.vector_store import VectorStore
        
        vector_store = VectorStore()
        health = vector_store.health_check()
        
        assert health["status"] == "healthy"
        assert health["directory_exists"] is True
        assert health["chromadb_connected"] is True
        
    def test_brand_ingestion_pipeline(self):
        """Test full brand ingestion pipeline."""
        from services.vector_store import VectorStore
        from services.text_splitter import TextSplitter
        from services.brand_ingest import BrandIngestService
        
        vector_store = VectorStore()
        text_splitter = TextSplitter()
        brand_ingest = BrandIngestService(vector_store, text_splitter)
        
        # Create test file
        test_file = DATA_DIR / "test_brand_ingest.csv"
        test_file.write_text(
            "brand,description,tone\n"
            "TestBrandIngest,A test brand for ingestion,Professional and friendly\n"
        )
        
        try:
            result = brand_ingest.ingest_file(str(test_file), brand="TestBrandIngest")
            
            assert "brands" in result
            assert "TestBrandIngest" in result["brands"]
            assert result["total_chunks"] > 0
            
            # Verify brand was ingested
            brands = vector_store.get_all_brands()
            assert "TestBrandIngest" in brands
            
            # Test query
            results = vector_store.query("TestBrandIngest", "What is the brand tone?", k=2)
            assert len(results) > 0
            
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
            try:
                vector_store.clear_brand("TestBrandIngest")
            except:
                pass


class TestChatRAG:
    """Tests for Chat/RAG functionality."""
    
    def test_stub_llm_client(self):
        """Test that StubLLMClient provides contextual responses."""
        from services.llm_client import StubLLMClient
        
        client = StubLLMClient()
        
        # Test greeting
        messages = [{"role": "user", "content": "Hello!"}]
        response = client.chat(messages)
        assert response is not None
        assert len(response) > 0
        
        # Test help request
        messages = [{"role": "user", "content": "What can you help me with?"}]
        response = client.chat(messages)
        assert "help" in response.lower() or "assist" in response.lower() or "content" in response.lower()
        
        # Test image prompt request
        messages = [{"role": "user", "content": "Create an image of a product"}]
        response = client.chat(messages)
        assert response is not None
        
    def test_llm_client_factory(self):
        """Test create_llm_client factory function."""
        from services.llm_client import create_llm_client, StubLLMClient
        
        # Should fall back to stub when no model available
        client = create_llm_client(use_stub_if_unavailable=True)
        assert client is not None
        assert isinstance(client, StubLLMClient)
        
    def test_chat_service_initialization(self):
        """Test BrandChatService initializes correctly."""
        from services.vector_store import VectorStore
        from services.chat_service import BrandChatService
        from services.llm_client import create_llm_client
        
        vector_store = VectorStore()
        llm_client = create_llm_client(use_stub_if_unavailable=True)
        chat_service = BrandChatService(vector_store, llm_client)
        
        assert chat_service is not None
        assert chat_service.vector_store is not None
        
    def test_chat_session(self):
        """Test chat session creation and messaging."""
        from services.vector_store import VectorStore
        from services.chat_service import BrandChatService
        from services.llm_client import create_llm_client
        
        vector_store = VectorStore()
        llm_client = create_llm_client(use_stub_if_unavailable=True)
        chat_service = BrandChatService(vector_store, llm_client)
        
        # Test chat session
        result = chat_service.chat_session(
            session_id=None,
            brand=None,
            new_user_message="Hello, what can you help me with?"
        )
        
        assert "session_id" in result
        assert "answer" in result
        assert result["answer"] is not None
        assert len(result["answer"]) > 0


class TestImageGeneration:
    """Tests for image generation."""
    
    def test_image_generator_initialization(self):
        """Test ImageGenerator initializes correctly."""
        from services.image_gen import ImageGenerator
        
        generator = ImageGenerator()
        assert generator is not None
        
    @pytest.mark.skipif(not settings.HF_TOKEN, reason="HF_TOKEN not available")
    def test_image_generation_hf_api(self):
        """Test image generation with HuggingFace API."""
        from services.image_gen import ImageGenerator
        
        generator = ImageGenerator()
        
        image_path = generator.generate(
            prompt="A simple test image of a blue square",
            model_id="flux-schnell",
            brand="TestImageGen"
        )
        
        assert image_path is not None
        assert Path(image_path).exists()
        
        # Cleanup
        try:
            Path(image_path).unlink()
        except:
            pass
            
    def test_image_generator_model_selection(self):
        """Test that image generator selects appropriate model."""
        from services.image_gen import ImageGenerator
        from config.default import get_model_by_id
        
        generator = ImageGenerator()
        
        # Check flux-schnell model exists in registry
        flux_model = get_model_by_id("image", "flux-schnell")
        assert flux_model is not None
        assert flux_model["provider"] == "hf"


class TestVideoGeneration:
    """Tests for video generation."""
    
    def test_video_generator_initialization(self):
        """Test VideoGenerator initializes correctly."""
        from services.video_gen import VideoGenerator
        
        generator = VideoGenerator()
        assert generator is not None
        
    def test_video_generator_availability(self):
        """Test video generator availability check."""
        from services.video_gen import VideoGenerator, IMAGEIO_AVAILABLE
        
        generator = VideoGenerator()
        assert generator.is_available() == IMAGEIO_AVAILABLE
        
    @pytest.mark.skipif(not settings.HF_TOKEN, reason="HF_TOKEN not available for image generation")
    def test_video_generation_frame_composition(self):
        """Test video generation with frame composition."""
        from services.image_gen import ImageGenerator
        from services.video_gen import VideoGenerator, IMAGEIO_AVAILABLE
        
        if not IMAGEIO_AVAILABLE:
            pytest.skip("imageio not available")
        
        # First generate an image
        image_generator = ImageGenerator()
        image_path = image_generator.generate(
            prompt="A simple test image",
            model_id="flux-schnell",
            brand="TestVideoGen"
        )
        
        try:
            # Then generate video from image
            video_generator = VideoGenerator()
            video_path = video_generator.generate(
                image_path=image_path,
                model_id="composition",
                frames=12,
                fps=6,
                brand="TestVideoGen"
            )
            
            assert video_path is not None
            assert Path(video_path).exists()
            
        finally:
            # Cleanup
            try:
                if image_path:
                    Path(image_path).unlink()
            except:
                pass


class TestConfiguration:
    """Tests for configuration module."""
    
    def test_settings_loaded(self):
        """Test that settings are loaded correctly."""
        from config.default import settings
        
        assert settings is not None
        assert hasattr(settings, 'HF_TOKEN')
        assert hasattr(settings, 'CHAT_MODEL_ID')
        assert hasattr(settings, 'IMAGE_MODEL_ID')
        
    def test_directories_exist(self):
        """Test that required directories exist."""
        from config.default import DATA_DIR, CHROMA_DIR, ASSETS_DIR
        
        assert DATA_DIR.exists()
        assert CHROMA_DIR.exists()
        assert ASSETS_DIR.exists()
        
    def test_model_registry_loaded(self):
        """Test that model registry is loaded."""
        from config.default import load_model_registry, get_model_by_id
        
        registry = load_model_registry()
        assert registry is not None
        assert "chat" in registry
        assert "image" in registry
        assert "video" in registry
        
        # Test get_model_by_id
        flux_model = get_model_by_id("image", "flux-schnell")
        assert flux_model is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
