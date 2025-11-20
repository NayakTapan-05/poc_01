"""
Local LLM Client using llama-cpp-python for offline inference.
Supports Phi-3 Mini, Llama 3.1 8B, and other GGUF models from registry.
"""
import os
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path
from config.default import settings, TEXT_MODELS_DIR, BASE_DIR, get_model_by_id, get_chat_model_info, list_models

logger = logging.getLogger(__name__)


def strip_deepseek_thinking(text: str) -> str:
    """Remove <think>...</think> reasoning blocks from DeepSeek output."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = text.strip()
    lines = [line for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


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
            
            response_text = strip_deepseek_thinking(response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"LLM inference error: {e}")
            raise


LLMClient = LocalLLMClient
