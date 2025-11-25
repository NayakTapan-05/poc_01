"""
LLM Client module with support for local GGUF models and stub/mock for development.
Provides a clean interface that can be configured via environment variables.
"""
import os
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path
from config.default import settings, TEXT_MODELS_DIR, BASE_DIR, get_model_by_id, get_chat_model_info, list_models

logger = logging.getLogger(__name__)


def strip_thinking_blocks(text: str) -> str:
    """Remove <think>...</think> reasoning blocks from model output."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = text.strip()
    lines = [line for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


class StubLLMClient:
    """
    Stub LLM client for development/testing when no local model is available.
    Returns contextual responses based on the input to allow testing of the full pipeline.
    """
    
    def __init__(self):
        """Initialize stub LLM client."""
        self.model_id = "stub"
        self.model_name = "Stub LLM (Development Mode)"
        logger.warning("Using StubLLMClient - no local GGUF model available")
        logger.warning("For production, download a model: python backend/scripts/download_models.py")
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate a stub response based on the input messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate (ignored in stub)
            temperature: Sampling temperature (ignored in stub)
            
        Returns:
            Stub response text
        """
        user_messages = [m for m in messages if m.get("role") == "user"]
        last_user_message = user_messages[-1].get("content", "") if user_messages else ""
        
        lower_msg = last_user_message.lower()
        
        if any(k in lower_msg for k in ["image", "visual", "banner", "hero", "thumbnail"]):
            return self._generate_image_prompt_response(last_user_message)
        elif any(k in lower_msg for k in ["video", "reel", "clip", "motion"]):
            return self._generate_video_prompt_response(last_user_message)
        elif any(k in lower_msg for k in ["post", "caption", "headline", "copy", "script", "email", "tagline"]):
            return self._generate_creative_copy_response(last_user_message)
        elif any(k in lower_msg for k in ["who are you", "what can you do", "help", "how to"]):
            return self._generate_help_response()
        elif any(k in lower_msg for k in ["hi", "hello", "hey", "good morning"]):
            return self._generate_greeting_response()
        else:
            return self._generate_qa_response(last_user_message, messages)
    
    def _generate_image_prompt_response(self, query: str) -> str:
        return (
            "Based on your request, here's an enhanced image prompt:\n\n"
            f"**Original request:** {query[:100]}...\n\n"
            "**Enhanced prompt:** A professional, high-quality marketing image featuring "
            "vibrant colors, clean composition, and brand-aligned visual elements. "
            "The image should convey trust, quality, and modern aesthetics.\n\n"
            "*Note: This is a stub response. Connect a real LLM model for production use.*"
        )
    
    def _generate_video_prompt_response(self, query: str) -> str:
        return (
            "Based on your request, here's a video concept:\n\n"
            f"**Original request:** {query[:100]}...\n\n"
            "**Video concept:** A dynamic 4-second video with smooth zoom and pan effects, "
            "transitioning from product focus to lifestyle context. "
            "The motion should feel premium and engaging.\n\n"
            "*Note: This is a stub response. Connect a real LLM model for production use.*"
        )
    
    def _generate_creative_copy_response(self, query: str) -> str:
        return (
            "Here's a creative copy suggestion:\n\n"
            f"**Brief:** {query[:100]}...\n\n"
            "**Headline:** Discover the Difference\n"
            "**Body:** Experience quality that speaks for itself. "
            "Our commitment to excellence shines through in every detail.\n"
            "**CTA:** Learn More\n\n"
            "*Note: This is a stub response. Connect a real LLM model for production use.*"
        )
    
    def _generate_help_response(self) -> str:
        return (
            "I'm UCA.ai, your AI-powered content assistant. I can help you with:\n\n"
            "1. **Brand-aware image generation** - Create visuals aligned with your brand DNA\n"
            "2. **Video creation** - Generate dynamic videos from images\n"
            "3. **Creative copywriting** - Headlines, captions, and marketing copy\n"
            "4. **Brand Q&A** - Answer questions about ingested brand guidelines\n\n"
            "To get started, try asking me to create an image or write some copy!\n\n"
            "*Note: This is a stub response. Connect a real LLM model for production use.*"
        )
    
    def _generate_greeting_response(self) -> str:
        return (
            "Hello! I'm UCA.ai, your AI content assistant. "
            "I'm here to help you create brand-aligned content including images, videos, and copy. "
            "What would you like to create today?\n\n"
            "*Note: This is a stub response. Connect a real LLM model for production use.*"
        )
    
    def _generate_qa_response(self, query: str, messages: List[Dict[str, str]]) -> str:
        system_messages = [m for m in messages if m.get("role") == "system"]
        has_brand_context = any("Brand DNA" in m.get("content", "") or "context" in m.get("content", "").lower() 
                                for m in system_messages)
        
        if has_brand_context:
            return (
                f"Based on the brand context provided, here's my response to: '{query[:50]}...'\n\n"
                "The brand emphasizes quality, trust, and customer-centric values. "
                "Key messaging should focus on these core attributes while maintaining "
                "a professional yet approachable tone.\n\n"
                "*Note: This is a stub response. Connect a real LLM model for production use.*"
            )
        else:
            return (
                f"Regarding your question: '{query[:50]}...'\n\n"
                "I'd be happy to help! For more accurate brand-specific responses, "
                "please ensure brand DNA documents have been ingested into the system.\n\n"
                "*Note: This is a stub response. Connect a real LLM model for production use.*"
            )


class LocalLLMClient:
    """Local LLM client using llama-cpp-python for GGUF models."""
    
    def __init__(self, model_id: Optional[str] = None):
        """Initialize local LLM client.
        
        Args:
            model_id: Model ID from registry (e.g., "phi-3-mini", "llama-3.1-8b")
                     If None, uses default from settings.
        """
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python is required. Install with: pip install llama-cpp-python"
            )
        
        # Get model info from registry
        if model_id:
            model_info = get_model_by_id("chat", model_id)
        else:
            model_info = get_chat_model_info()
        
        if not model_info:
            raise ValueError(f"Chat model not found in registry. Available models: {list_models('chat')}")
        
        self.model_id = model_info["id"]
        self.model_name = model_info.get("name", self.model_id)
        
        # Find model file
        model_path = None
        
        # Try path from registry (supports nested directories)
        if "path" in model_info:
            registry_path = BASE_DIR / model_info["path"]
            if registry_path.exists():
                model_path = registry_path
            else:
                # Try nested directory structure: models/text/{model_dir}/{filename}
                path_parts = Path(model_info["path"]).parts
                if len(path_parts) >= 3:
                    # Extract model directory and filename
                    model_dir = path_parts[-2]  # e.g., "phi-3.5-mini-instruct"
                    filename = path_parts[-1]   # e.g., "Phi-3.5-mini-instruct-Q4_K_M.gguf"
                    nested_path = TEXT_MODELS_DIR / model_dir / filename
                    if nested_path.exists():
                        model_path = nested_path
                
                # Try relative to TEXT_MODELS_DIR (flat structure)
                if not model_path:
                    alt_path = TEXT_MODELS_DIR / Path(model_info["path"]).name
                    if alt_path.exists():
                        model_path = alt_path
        
        # Try filename from registry in nested directory
        if not model_path and "filename" in model_info:
            # Try nested: models/text/{model_dir}/{filename}
            if "path" in model_info:
                path_parts = Path(model_info["path"]).parts
                if len(path_parts) >= 2:
                    model_dir = path_parts[-2]
                    nested_path = TEXT_MODELS_DIR / model_dir / model_info["filename"]
                    if nested_path.exists():
                        model_path = nested_path
            
            # Try flat structure
            if not model_path:
                candidate_path = TEXT_MODELS_DIR / model_info["filename"]
            if candidate_path.exists():
                model_path = candidate_path
        
        # Fallback: search recursively for matching GGUF file
        if not model_path:
            model_name_lower = self.model_id.lower()
            for gguf_file in TEXT_MODELS_DIR.rglob("*.gguf"):
                file_name_lower = gguf_file.name.lower()
                if (model_name_lower in file_name_lower or 
                    ("phi" in model_name_lower and "phi" in file_name_lower) or
                    ("llama" in model_name_lower and "llama" in file_name_lower)):
                    model_path = gguf_file
                    logger.warning(f"Found matching model file: {gguf_file}")
                break
        
        # Last resort: use any GGUF file
        if not model_path:
            gguf_files = list(TEXT_MODELS_DIR.rglob("*.gguf"))
            if gguf_files:
                model_path = gguf_files[0]
                logger.warning(f"Using first available model: {model_path}")
            else:
                expected_path = BASE_DIR / model_info.get('path', 'models/text/...')
                error_msg = (
                    f"No GGUF model file found for model '{self.model_id}'. "
                    f"Expected path: {expected_path}. "
                    f"Please download models: python backend/scripts/download_models.py"
                )
                # Raise a custom exception that can be caught and formatted as JSON
                raise FileNotFoundError(error_msg)
        
        logger.info(f"Loading local LLM model: {self.model_name} from {model_path}")
        
        n_gpu_layers = int(os.getenv("LLM_GPU_LAYERS", "20"))
        n_threads = int(os.getenv("LLM_THREADS", "4"))
        
        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
            use_mlock=True,
        )
        logger.info(f"Local LLM model loaded: {self.model_name}")
    
    def _format_messages_for_model(self, messages: List[Dict[str, str]]) -> str:
        """
        Format messages according to the model's chat template.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Formatted prompt string
        """
        # Llama 3.1 8B Instruct format
        if "llama-3.1" in self.model_id.lower() or "llama" in self.model_id.lower():
            prompt_parts = ["<|begin_of_text|>"]
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    prompt_parts.append(f"<|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>")
                elif role == "user":
                    prompt_parts.append(f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>")
                elif role == "assistant":
                    prompt_parts.append(f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>")
            
            prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
            return "".join(prompt_parts)
        
        # Phi-3.5 Mini Instruct format
        elif "phi-3.5" in self.model_id.lower() or "phi" in self.model_id.lower():
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    prompt_parts.append(f"<|system|>\n{content}<|end|>")
                elif role == "user":
                    prompt_parts.append(f"<|user|>\n{content}<|end|>")
                elif role == "assistant":
                    prompt_parts.append(f"<|assistant|>\n{content}<|end|>")
            
            prompt_parts.append("<|assistant|>\n")
            return "".join(prompt_parts)
        
        # Default: use llama-cpp-python's built-in chat format
        else:
            # Return messages as-is for llama-cpp-python to handle
            return messages
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generate chat completion using local model.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Assistant response text
        """
        try:
            # For models with custom templates, format the prompt
            if "llama-3.1" in self.model_id.lower() or "phi-3.5" in self.model_id.lower() or "phi" in self.model_id.lower():
                formatted_prompt = self._format_messages_for_model(messages)
                
                # Use create_completion for custom formatted prompts
                result = self.llm(
                    formatted_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["</s>", "\n\n\n", "<|im_end|>", "<|end|>", "<|eot_id|>", "</think>"],
                )
                
                # Handle both dict and string responses
                if isinstance(result, dict):
                    response_text = result.get("choices", [{}])[0].get("text", "").strip()
                else:
                    response_text = str(result).strip()
            else:
                # Use create_chat_completion for standard format
                result = self.llm.create_chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop=["</s>", "\n\n\n", "<|im_end|>", "</think>"],
                )
            
            response_text = result["choices"][0]["message"]["content"].strip()
            
            response_text = strip_thinking_blocks(response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"LLM inference error: {e}")
            raise


def create_llm_client(model_id: Optional[str] = None, use_stub_if_unavailable: bool = True):
    """
    Factory function to create an LLM client.
    
    Args:
        model_id: Model ID from registry
        use_stub_if_unavailable: If True, return StubLLMClient when no model is available
        
    Returns:
        LLM client instance (LocalLLMClient or StubLLMClient)
    """
    try:
        return LocalLLMClient(model_id)
    except (FileNotFoundError, ImportError, ValueError) as e:
        if use_stub_if_unavailable:
            logger.warning(f"Local LLM not available ({e}), using stub client")
            return StubLLMClient()
        raise


LLMClient = LocalLLMClient
