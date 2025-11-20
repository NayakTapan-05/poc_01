"""
Test script for local LLM chat service.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.chat_service import ChatService
from services.vector_store import VectorStore
from services.llm_client import LocalLLMClient
from config.default import settings

def test_chat():
    """Test local chat service."""
    print("Testing local LLM chat service...")
    print(f"Chat model: {settings.CHAT_MODEL}\n")
    
    # Initialize vector store
    print("Loading vector store...")
    vs = VectorStore()
    
    # Check if we have brands
    brands = vs.get_all_brands()
    print(f"Available brands: {brands}\n")
    
    # Initialize LLM client
    try:
        print(f"Loading local LLM model: {settings.CHAT_MODEL}...")
        llm = LocalLLMClient(model_name=settings.CHAT_MODEL)
        print("✓ LLM loaded\n")
    except Exception as e:
        print(f"✗ Failed to load LLM: {e}")
        print("Please download models first: python backend/scripts/download_models.py")
        return
    
    # Initialize chat service
    chat = ChatService(vs, llm)
    
    # Test 1: Greeting
    print("=" * 50)
    print("Test 1: Greeting")
    print("=" * 50)
    messages = [{"role": "user", "content": "hi"}]
    result = chat.chat(messages, brand=None)
    print(f"Intent: {result['intent']}")
    print(f"Answer: {result['answer']}\n")
    
    # Test 2: Brand question (if brands available)
    if brands:
        brand = brands[0]
        print("=" * 50)
        print(f"Test 2: Brand question ({brand})")
        print("=" * 50)
        messages = [{"role": "user", "content": f"What is {brand}'s brand essence?"}]
        result = chat.chat(messages, brand=brand)
        print(f"Intent: {result['intent']}")
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Sources: {len(result['sources'])} snippets\n")
    
    # Test 3: Image intent
    print("=" * 50)
    print("Test 3: Image generation prompt")
    print("=" * 50)
    messages = [{"role": "user", "content": "generate a hero image for Dove"}]
    result = chat.chat(messages, brand="Dove" if "Dove" in brands else None)
    print(f"Intent: {result['intent']}")
    print(f"Answer: {result['answer']}\n")
    
    print("=" * 50)
    print("✓ All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_chat()

