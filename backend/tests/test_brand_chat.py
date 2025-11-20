"""
Test script for Brand Chat Service with DeepSeek.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.chat_service import BrandChatService
from services.vector_store import VectorStore
from services.llm_client import LocalLLMClient
from config.default import settings


def test_brand_chat():
    """Test brand chat service."""
    print("=" * 60)
    print("Brand Chat Service Test")
    print("=" * 60)
    
    print(f"\nLoading vector store...")
    vs = VectorStore()
    
    brands = vs.get_all_brands()
    print(f"Available brands: {brands}\n")
    
    print(f"Loading local LLM: {settings.CHAT_MODEL}...")
    llm = LocalLLMClient(model_name=settings.CHAT_MODEL)
    print(f"✓ LLM loaded\n")
    
    chat = BrandChatService(vs, llm)
    
    # Test 1: Small talk
    print("=" * 60)
    print("Test 1: Small Talk")
    print("=" * 60)
    result = chat.chat_session(
        session_id=None,
        brand=None,
        new_user_message="Hi, how are you?"
    )
    print(f"Intent: {result['intent']}")
    print(f"Answer: {result['answer'][:150]}...")
    print(f"Session ID: {result['session_id']}\n")
    session_1 = result['session_id']
    
    # Test 2: Brand Q&A (same session)
    if brands:
        brand = brands[0]
        print("=" * 60)
        print(f"Test 2: Brand Q&A ({brand})")
        print("=" * 60)
        result = chat.chat_session(
            session_id=session_1,
            brand=brand,
            new_user_message=f"What is {brand}'s brand essence?"
        )
        print(f"Intent: {result['intent']}")
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Sources: {len(result['sources'])} items")
        print(f"Debug: {result.get('debug', {})}\n")
    
    # Test 3: Creative copy
    print("=" * 60)
    print("Test 3: Creative Copy")
    print("=" * 60)
    result = chat.chat_session(
        session_id=None,
        brand=brands[0] if brands else None,
        new_user_message="Write a launch headline for our new body wash"
    )
    print(f"Intent: {result['intent']}")
    print(f"Answer: {result['answer'][:200]}...")
    print(f"Session ID: {result['session_id']}\n")
    
    # Test 4: Image prompt
    print("=" * 60)
    print("Test 4: Image Prompt")
    print("=" * 60)
    result = chat.chat_session(
        session_id=None,
        brand=brands[0] if brands else None,
        new_user_message="Create a hero image for the campaign"
    )
    print(f"Intent: {result['intent']}")
    print(f"Answer: {result['answer'][:200]}...")
    print(f"Session ID: {result['session_id']}\n")
    
    print("=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_brand_chat()

