"""
Smoke tests for Brand DNAi Content Studio.
Tests basic functionality of all major features.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.vector_store import VectorStore
from services.text_splitter import TextSplitter
from services.prompt_orchestrator import create_prompt_orchestrator
from services.negative_prompt_library import negative_prompt_library


def test_ingestion_and_rag():
    """Test document ingestion and RAG retrieval."""
    vector_store = VectorStore()
    text_splitter = TextSplitter()
    
    sample_docs = [
        {
            "text": "Nike is a leading sports brand known for innovation and performance.",
            "brand": "Nike",
            "metadata": {"source": "test"}
        },
        {
            "text": "Nike targets athletes and active individuals with cutting-edge products.",
            "brand": "Nike",
            "metadata": {"source": "test"}
        }
    ]
    
    chunks = []
    for doc in sample_docs:
        doc_chunks = text_splitter.split_text(doc["text"])
        for chunk in doc_chunks:
            chunks.append({
                "text": chunk,
                "brand": doc["brand"],
                "metadata": doc["metadata"]
            })
    
    vector_store.add_documents("Nike", chunks)
    
    results = vector_store.query("Nike", "What is Nike known for?", k=2)
    
    assert len(results) > 0, "Should retrieve at least one result"
    assert "Nike" in results[0]["text"] or "nike" in results[0]["text"].lower()
    
    print("✅ Ingestion/RAG test passed")


def test_prompt_pipeline():
    """Test prompt orchestrator builds enhanced prompts with brand context."""
    vector_store = VectorStore()
    orchestrator = create_prompt_orchestrator(vector_store)
    
    sample_docs = [
        {
            "text": "Nike embodies innovation, performance, and athletic excellence.",
            "brand": "Nike",
            "metadata": {"source": "test"}
        }
    ]
    
    vector_store.add_documents("Nike", sample_docs)
    
    result = orchestrator.build_master_prompt(
        user_prompt="A professional athlete running",
        brand="Nike",
        style_preset="cinematic",
        lighting_preset="golden_hour",
        engine_type="image"
    )
    
    assert result["original_prompt"], "Should have original prompt"
    assert result["enhanced_prompt"], "Should have enhanced prompt"
    assert result["negative_prompt"], "Should have negative prompt"
    assert len(result["enhanced_prompt"]) > len(result["original_prompt"]), "Enhanced should be longer"
    assert "cinematic" in result["enhanced_prompt"].lower(), "Should include style preset"
    
    print("✅ Prompt pipeline test passed")


def test_negative_prompts():
    """Test negative prompt library."""
    image_negative = negative_prompt_library.get_negative_prompt("image")
    video_negative = negative_prompt_library.get_negative_prompt("video")
    
    assert image_negative, "Should return image negative prompt"
    assert video_negative, "Should return video negative prompt"
    assert "blurry" in image_negative, "Should include common negatives"
    assert "flickering" in video_negative, "Should include video-specific negatives"
    
    print("✅ Negative prompt test passed")


def test_chat_rag():
    """Test RAG-based chat returns answer and sources."""
    from services.qa_chain import QAChain
    
    vector_store = VectorStore()
    qa_chain = QAChain(vector_store)
    
    sample_docs = [
        {
            "text": "Apple is known for innovative technology and premium design.",
            "brand": "Apple",
            "metadata": {"source": "test"}
        }
    ]
    
    vector_store.add_documents("Apple", sample_docs)
    
    result = qa_chain.answer("Apple", "What is Apple known for?")
    
    assert result["answer"], "Should return an answer"
    assert result["sources"], "Should return sources"
    assert len(result["sources"]) > 0, "Should have at least one source"
    
    print("✅ Chat RAG test passed")


def test_templates_and_presets():
    """Test that templates and presets are available."""
    vector_store = VectorStore()
    orchestrator = create_prompt_orchestrator(vector_store)
    
    templates = orchestrator.get_available_templates("image")
    style_presets = orchestrator.get_style_presets()
    lighting_presets = orchestrator.get_lighting_presets()
    
    assert len(templates) > 0, "Should have image templates"
    assert len(style_presets) > 0, "Should have style presets"
    assert len(lighting_presets) > 0, "Should have lighting presets"
    
    print("✅ Templates and presets test passed")


if __name__ == "__main__":
    print("Running smoke tests...\n")
    
    try:
        test_ingestion_and_rag()
        test_prompt_pipeline()
        test_negative_prompts()
        test_chat_rag()
        test_templates_and_presets()
        
        print("\n✅ All smoke tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
