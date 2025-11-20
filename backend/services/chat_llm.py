"""
Chat LLM Service - Clean abstraction for LLM calls in chat.
Handles model selection and LLM invocation with proper chat templates.
"""
import logging
import os
from typing import List, Dict, Optional
from .llm_client import LLMClient
from config.default import settings, get_model_by_id

logger = logging.getLogger(__name__)


class GGUFChatModel:
    """
    Unified chat model wrapper for GGUF models.
    Handles model loading, chat template formatting, and generation.
    """
    
    def __init__(self, model_id: Optional[str] = None, context_length: int = 4096, gpu_layers_auto: bool = True):
        """
        Initialize GGUF chat model.
        
        Args:
            model_id: Model ID from registry (e.g., "phi-3.5-mini", "llama-3.1-8b")
            context_length: Context window size
            gpu_layers_auto: Auto-detect GPU layers if available
        """
        self.model_id = model_id or settings.CHAT_MODEL_ID
        self.context_length = context_length
        self._llm_client = None
        self._initialize_client(gpu_layers_auto)
    
    def _initialize_client(self, gpu_layers_auto: bool):
        """Initialize LLM client with proper configuration."""
        try:
            self._llm_client = LLMClient(model_id=self.model_id)
            logger.info(f"Initialized GGUFChatModel with model: {self.model_id}")
        except (FileNotFoundError, ImportError, ValueError) as e:
            logger.warning(f"Chat LLM not available: {e}")
            self._llm_client = None
    
    def is_available(self) -> bool:
        """Check if model is available."""
        return self._llm_client is not None
    
    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate chat response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Response text
            
        Raises:
            ValueError: If model is not available
        """
        if not self._llm_client:
            raise ValueError("LLM model not available. Please download a GGUF model.")
        
        try:
            response = self._llm_client.chat(messages, max_tokens=max_tokens, temperature=temperature)
            return response
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise


class ChatLLM:
    """
    Chat LLM service that handles model selection and LLM calls.
    Provides a clean interface for chat completion.
    Wraps GGUFChatModel for backward compatibility.
    """
    
    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize chat LLM service.
        
        Args:
            model_id: Optional model ID (uses default from settings if not provided)
        """
        self.model_id = model_id or settings.CHAT_MODEL_ID
        self._gguf_model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize GGUF chat model."""
        try:
            self._gguf_model = GGUFChatModel(model_id=self.model_id)
            logger.info(f"Initialized ChatLLM with model: {self.model_id}")
        except (FileNotFoundError, ImportError, ValueError) as e:
            logger.warning(f"Chat LLM not available: {e}")
            self._gguf_model = None
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self._gguf_model is not None and self._gguf_model.is_available()
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate (default 512)
            temperature: Sampling temperature (default 0.7)
            
        Returns:
            Assistant response text
            
        Raises:
            ValueError: If LLM is not available
        """
        if not self._gguf_model or not self._gguf_model.is_available():
            raise ValueError("LLM model not available. Please download a GGUF model.")
        
        try:
            response = self._gguf_model.generate(messages, max_tokens=max_tokens, temperature=temperature)
            return response
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise
    
    def select_model(self, prefer_heavy: bool = False) -> str:
        """
        Select appropriate chat model based on preferences and resources.
        
        Args:
            prefer_heavy: Whether to prefer heavier model (llama-3.1-8b) if available
            
        Returns:
            Model ID
        """
        if prefer_heavy:
            # Check if llama-3.1-8b is available
            llama_model = get_model_by_id("chat", "llama-3.1-8b")
            if llama_model:
                # Check if model file exists
                from config.default import TEXT_MODELS_DIR, BASE_DIR
                model_path = BASE_DIR / llama_model.get("path", "")
                if model_path.exists() or list(TEXT_MODELS_DIR.rglob("llama-3.1*.gguf")):
                    return "llama-3.1-8b"
        
        # Default to configured model
        return settings.CHAT_MODEL_ID


def generate_chat(model_id: str, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> str:
    """
    Generate chat response using specified model.
    
    Args:
        model_id: Model ID from registry
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        Response text
    """
    model = GGUFChatModel(model_id=model_id)
    return model.generate(messages, max_tokens=max_tokens, temperature=temperature)

