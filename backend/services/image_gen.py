"""
Image generation service supporting local diffusers models and HF API.
Supports: sd-turbo, sd-1.5, sdxl-turbo (local), flux-schnell (HF API, optional).
"""
import requests
from pathlib import Path
from datetime import datetime
import logging
import time
from typing import Optional, Dict, Any
from PIL import Image
import io

from config.default import (
    settings, HF_IMAGE_API_URL, get_model_by_id, get_image_model_info,
    ASSETS_DIR
)
from common.error_handling import GenerationError
from common.storage import store_asset

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Image generator supporting local diffusers and HF API."""
    
    def __init__(self):
        """Initialize the image generator."""
        self.max_retries = 3
        self.retry_delay = 10
        self._local_models = {}  # Cache for loaded models
        logger.info("Image generator initialized")

        # Preload default model in background (non-blocking)
        # This prevents blocking the server startup if model loading fails
        try:
            import threading
            default_model = get_image_model_info()
            if default_model and default_model.get("provider") == "local":
                def preload_model():
                    try:
                        logger.info(f"Preloading default model in background: {default_model['id']}")
                        self._load_local_model(default_model["id"])
                        logger.info(f"✅ Successfully preloaded default model: {default_model['id']}")
                    except Exception as preload_error:
                        logger.warning(f"Could not preload default model {default_model['id']}: {preload_error}")
                        logger.info("Model will be loaded on first use")
                
                # Start preloading in background thread
                threading.Thread(target=preload_model, daemon=True).start()
        except Exception as e:
            logger.warning(f"Could not start model preloading: {e}")
    
    def _load_local_model(self, model_id: str):
        """Load a local diffusers model."""
        if model_id in self._local_models:
            logger.info(f"Using cached model: {model_id}")
            return self._local_models[model_id]
        
        try:
            from diffusers import DiffusionPipeline
            import torch

            model_info = get_model_by_id("image", model_id)
            if not model_info:
                raise ValueError(f"Model {model_id} not found in registry")

            model_name = model_info.get("model_id")
            logger.info(f"Loading local model: {model_name}")

            # Use CPU by default, GPU if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32

            # Set safety checker to None to avoid issues
            safety_checker = None

            try:
                if "turbo" in model_id.lower() or "sdxl-turbo" in model_id.lower():
                    pipe = DiffusionPipeline.from_pretrained(
                        model_name,
                        torch_dtype=dtype,
                        safety_checker=safety_checker
                    )
                else:
                    from diffusers import StableDiffusionPipeline
                    pipe = StableDiffusionPipeline.from_pretrained(
                        model_name,
                        torch_dtype=dtype,
                        safety_checker=safety_checker
                    )

                pipe = pipe.to(device)
                if device == "cpu":
                    pipe.enable_attention_slicing()

                self._local_models[model_id] = pipe
                logger.info(f"✅ Loaded model {model_id} on {device}")
                return pipe

            except Exception as load_error:
                logger.error(f"Model loading failed: {load_error}")
                # Try with minimal config
                try:
                    pipe = DiffusionPipeline.from_pretrained(
                        model_name,
                        torch_dtype=torch.float32,
                        safety_checker=None,
                        requires_safety_checker=False
                    )
                    pipe = pipe.to("cpu")
                    pipe.enable_attention_slicing()
                    self._local_models[model_id] = pipe
                    logger.info(f"✅ Loaded model {model_id} with fallback config")
                    return pipe
                except Exception as fallback_error:
                    logger.error(f"Fallback loading also failed: {fallback_error}")
                    raise load_error
            
        except ImportError:
            raise ImportError(
                "diffusers and torch are required for local image generation. "
                "Install with: pip install diffusers torch"
            )
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            logger.error(f"Model info: {model_info}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise GenerationError(f"Failed to load model {model_id}: {str(e)}", "model_load_error")

    def _preload_model(self, model_id: str):
        """Preload a model in the background."""
        try:
            logger.info(f"Preloading model: {model_id}")
            self._load_local_model(model_id)
            logger.info(f"✅ Successfully preloaded model: {model_id}")
        except Exception as e:
            logger.warning(f"Failed to preload model {model_id}: {e}")
    
    def _generate_local(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        model_id: str,
        width: int = 512,
        height: int = 512,
        steps: int = 4,
        seed: Optional[int] = None
    ) -> Image.Image:
        """Generate image using local diffusers model."""
        try:
            pipe = self._load_local_model(model_id)
        except Exception as load_error:
            logger.error(f"Failed to load model {model_id}: {load_error}")
            raise GenerationError(f"Failed to load model {model_id}: {load_error}", "model_load_error")
        
        generator = None
        if seed is not None and seed >= 0:
            import torch
            generator = torch.Generator().manual_seed(seed)
        
        logger.info(f"Generating image with {model_id} (local) - {width}x{height}, {steps} steps")
        
        try:
            # Use smaller batch size and enable memory efficient attention
            import torch
            if hasattr(pipe, 'enable_attention_slicing'):
                pipe.enable_attention_slicing()
            if hasattr(pipe, 'enable_model_cpu_offload'):
                try:
                    pipe.enable_model_cpu_offload()
                except:
                    pass  # Not all models support this
            
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                generator=generator,
                guidance_scale=1.0 if "turbo" in model_id.lower() else 7.5
            )
            
            if not result or not hasattr(result, 'images') or not result.images:
                raise GenerationError("Model returned empty result", "empty_result")
            
            return result.images[0]
        except BrokenPipeError as e:
            logger.error(f"Broken pipe error during generation: {e}")
            # Clear the model cache to force reload
            if model_id in self._local_models:
                del self._local_models[model_id]
            raise GenerationError(f"Broken pipe error - model connection lost. Try again or use HF API model.", "broken_pipe")
        except RuntimeError as e:
            logger.error(f"Runtime error during generation: {e}")
            if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
                raise GenerationError(f"Memory error: {e}. Try using HF API model or reducing image size.", "memory_error")
            raise GenerationError(f"Runtime error: {e}", "runtime_error")
        except Exception as e:
            logger.error(f"Local generation error: {e}", exc_info=True)
            raise GenerationError(f"Image generation failed: {e}", "generation_failed")
    
    def _generate_hf_api(
        self,
        prompt: str,
        model_id: str
    ) -> bytes:
        """Generate image using HuggingFace API."""
        model_info = get_model_by_id("image", model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found in registry")
        
        if not settings.HF_TOKEN:
            raise GenerationError(
                f"HF_TOKEN required for {model_id}. Set it in .env or environment.",
                "missing_token"
            )
        
        api_url = f"https://router.huggingface.co/hf-inference/models/{model_info['model_id']}"
        headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"HF API generation attempt {attempt + 1}/{self.max_retries}")
                
                payload = {
                    "inputs": prompt,
                    "options": {"wait_for_model": True}
                }
                
                response = requests.post(api_url, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 503:
                    logger.warning(f"Model loading... waiting {self.retry_delay}s")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                        raise GenerationError("Model still loading after max retries", "model_loading")
                
                if response.status_code == 429:
                    logger.warning(f"Rate limited... waiting 20s")
                    if attempt < self.max_retries - 1:
                        time.sleep(20)
                        continue
                        raise GenerationError("Rate limited after max retries", "rate_limit")
                
                response.raise_for_status()
                
                if "application/json" in response.headers.get("Content-Type", ""):
                    error_data = response.json()
                    raise GenerationError(f"API error: {error_data.get('error')}", "api_error")
                
                return response.content
                
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise GenerationError("Request timeout after max retries", "timeout")
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise GenerationError(f"HF API error: {e}", "api_error")
        
        raise GenerationError("HF API generation failed after max retries", "max_retries")
    
    def generate(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        steps: int = 4,
        width: int = 512,
        height: int = 512,
        seed: int = -1,
        brand: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description
            model_id: Model ID from registry (defaults to settings default)
            negative_prompt: Negative prompt
            steps: Inference steps
            width: Image width
            height: Image height
            seed: Random seed (-1 for random)
            brand: Brand name (for storage organization)
            **kwargs: Additional parameters

        Returns:
            Path to generated image file
        """
        logger.info(f"ImageGenerator.generate called with model_id={model_id}, prompt='{prompt[:50]}...'")
        if not model_id:
            model_info = get_image_model_info()
            # Prefer HF API model if token is available (more reliable)
            if settings.HF_TOKEN:
                flux_model = get_model_by_id("image", "flux-schnell")
                if flux_model:
                    model_id = "flux-schnell"
                    logger.info(f"Using FLUX model (HF API) as default")
                else:
                    model_id = model_info["id"] if model_info else "sd-turbo"
                    logger.info(f"Using default model: {model_id}")
            else:
                model_id = model_info["id"] if model_info else "sd-turbo"
                logger.info(f"Using default model: {model_id}")
        
        model_info = get_model_by_id("image", model_id)
        if not model_info:
            raise ValueError(f"Image model {model_id} not found in registry")
        
        provider = model_info.get("provider", "local")
        
        # Parse size if provided as string
        if isinstance(width, str) and "x" in str(width):
            parts = str(width).split("x")
            width = int(parts[0])
            height = int(parts[1]) if len(parts) > 1 else width
        
        # Generate image
        if provider == "local":
            try:
                image = self._generate_local(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    model_id=model_id,
                    width=width,
                    height=height,
                    steps=steps,
                    seed=seed if seed >= 0 else None
                )
            except (BrokenPipeError, OSError, RuntimeError) as e:
                logger.error(f"Local model generation failed with error: {e}")
                # Fallback to HF API if available
                if settings.HF_TOKEN:
                    logger.info(f"Falling back to HF API for model: {model_id}")
                    try:
                        image_bytes = self._generate_hf_api(prompt, model_id)
                        # Use module-level Image import (already imported at top)
                        image = Image.open(io.BytesIO(image_bytes))
                    except Exception as hf_error:
                        logger.error(f"HF API fallback also failed: {hf_error}")
                        raise GenerationError(
                            f"Image generation failed. Local model error: {e}. HF API error: {hf_error}",
                            "generation_failed"
                        )
                else:
                    raise GenerationError(
                        f"Local model generation failed: {e}. Set HF_TOKEN for API fallback.",
                        "generation_failed"
                    )
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            image_content = img_bytes.read()
        else:  # HF API
            image_content = self._generate_hf_api(prompt, model_id)
            # Image is already imported at module level
        
        # Store using new structure
        brand_id = brand or "default"
        file_path, metadata_path = store_asset(
            content=image_content,
            asset_type="image",
            brand_id=brand_id,
            mime_type="image/png"
        )
        
        logger.info(f"✅ Image saved to: {file_path}")
        return file_path
    
    def generate_with_orchestrator(
        self,
        prompt: str,
        brand: str = None,
        market: str = None,
        template_type: str = None,
        template_fields: dict = None,
        style_preset: str = None,
        lighting_preset: str = None,
        model_id: str = None,
        steps: int = 4,
        width: int = 512,
        height: int = 512,
        seed: int = -1,
        **kwargs
    ) -> dict:
        """
        Generate an image using the prompt orchestrator.
            
        Returns:
            Dict with image_path and prompt metadata
        """
        from services.prompt_orchestrator import create_prompt_orchestrator
        from services.vector_store import VectorStore
        
        vector_store = VectorStore()
        orchestrator = create_prompt_orchestrator(vector_store)
        
        prompt_result = orchestrator.build_master_prompt(
            user_prompt=prompt,
            brand=brand,
            market=market,
            template_type=template_type,
            template_fields=template_fields,
            style_preset=style_preset,
            lighting_preset=lighting_preset,
            engine_type="image"
        )
        
        enhanced_prompt = prompt_result["enhanced_prompt"]
        negative_prompt = prompt_result.get("negative_prompt")
        
        # Extract RAG snippets
        rag_snippets = []
        if prompt_result.get("brand_dnai") and prompt_result["brand_dnai"].get("raw_snippets"):
            rag_snippets = prompt_result["brand_dnai"]["raw_snippets"]
        
        image_path = self.generate(
            prompt=enhanced_prompt,
            model_id=model_id,
            negative_prompt=negative_prompt,
            steps=steps,
            width=width,
            height=height,
            seed=seed,
            brand=brand
        )
        
        return {
            "image_path": image_path,
            "original_prompt": prompt_result["original_prompt"],
            "enhanced_prompt": enhanced_prompt,
            "negative_prompt": negative_prompt,
            "brand_context": prompt_result.get("brand_context"),
            "rag_snippets": rag_snippets,
            "metadata": prompt_result.get("metadata", {})
        }
