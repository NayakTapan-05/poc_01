"""
Configuration module for the AI Content Generation PoC.
Centralizes all constants, paths, and model settings.
"""
import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REGISTRY_PATH = BASE_DIR / "models" / "registry.json"

# ChromaDB Vector Database Location
# All brand DNA data is stored in ChromaDB under this directory
# This directory MUST be writable for brand ingestion to work
# Location: ./data/chroma (relative to repo root)
CHROMA_DIR = DATA_DIR / "chroma"
UPLOAD_DIR = DATA_DIR / "uploaded_files"
OUTPUT_IMAGE_DIR = DATA_DIR / "outputs" / "images"
OUTPUT_VIDEO_DIR = DATA_DIR / "outputs" / "videos"
ASSETS_DIR = DATA_DIR / "assets"

# Model subdirectories
TEXT_MODELS_DIR = MODELS_DIR / "text"
IMAGE_MODELS_DIR = MODELS_DIR / "image"
VIDEO_MODELS_DIR = MODELS_DIR / "video"

# Ensure directories exist with proper permissions
import os
import stat

def ensure_writable_directory(path: Path):
    """Ensure a directory exists and is writable."""
    path.mkdir(parents=True, exist_ok=True)
    # Set full write permissions (777) to ensure ChromaDB and other services can write
    try:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except Exception as e:
        # Log but don't fail - permissions might be set by umask
        pass

# Ensure all data directories are writable - CRITICAL for brand ingestion
for d in [DATA_DIR, CHROMA_DIR, UPLOAD_DIR, OUTPUT_IMAGE_DIR, OUTPUT_VIDEO_DIR, ASSETS_DIR,
          TEXT_MODELS_DIR, IMAGE_MODELS_DIR, VIDEO_MODELS_DIR]:
    ensure_writable_directory(d)


def load_model_registry() -> Dict[str, Any]:
    """Load model registry from JSON file."""
    if not REGISTRY_PATH.exists():
        return {
            "chat": {},
            "image": {},
            "video": {},
            "embeddings": {}
        }
    
    with open(REGISTRY_PATH, 'r') as f:
        return json.load(f)


def get_model_by_id(category: str, model_id: str) -> Optional[Dict[str, Any]]:
    """Get a model by category and ID from registry."""
    registry = load_model_registry()
    category_models = registry.get(category, {})
    return category_models.get(model_id)


def get_default_model(category: str) -> Optional[Dict[str, Any]]:
    """Get the default model for a category."""
    registry = load_model_registry()
    category_models = registry.get(category, {})
    
    for model_id, model_info in category_models.items():
        if model_info.get("default", False):
            return model_info
    
    # If no default, return first model
    if category_models:
        return list(category_models.values())[0]
    
    return None


def list_models(category: str) -> list:
    """List all models in a category."""
    registry = load_model_registry()
    category_models = registry.get(category, {})
    return list(category_models.values())


# Load registry
MODEL_REGISTRY = load_model_registry()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    HF_TOKEN: str = ""  # Hardcoded for POC - enables FLUX and other HF API models
    
    DATABASE_URL: str = f"sqlite:///{str(BASE_DIR.absolute())}/data/metadata.db"
    
    STORAGE_BACKEND: str = "local"  # local or minio
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    
    # Model IDs from registry (can be overridden via env)
    EMBEDDING_MODEL_ID: str = "all-MiniLM-L6-v2"
    IMAGE_MODEL_ID: str = "sd-turbo"
    VIDEO_MODEL_ID: str = "svd"
    CHAT_MODEL_ID: str = "phi-3.5-mini"  # or "llama-3.1-8b"
    
    DEFAULT_IMAGE_STEPS: int = 4
    DEFAULT_IMAGE_SIZE: str = "512x512"
    DEFAULT_VIDEO_FRAMES: int = 96
    DEFAULT_VIDEO_FPS: int = 24
    DEFAULT_VIDEO_DURATION: int = 4
    
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    K_RETRIEVAL: int = 4
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Get model info from registry
def get_chat_model_info() -> Optional[Dict[str, Any]]:
    """Get chat model info from registry."""
    return get_model_by_id("chat", settings.CHAT_MODEL_ID) or get_default_model("chat")

def get_image_model_info() -> Optional[Dict[str, Any]]:
    """Get image model info from registry."""
    return get_model_by_id("image", settings.IMAGE_MODEL_ID) or get_default_model("image")

def get_video_model_info() -> Optional[Dict[str, Any]]:
    """Get video model info from registry."""
    return get_model_by_id("video", settings.VIDEO_MODEL_ID) or get_default_model("video")

def get_embedding_model_info() -> Optional[Dict[str, Any]]:
    """Get embedding model info from registry."""
    return get_model_by_id("embeddings", settings.EMBEDDING_MODEL_ID) or get_default_model("embeddings")

# Legacy compatibility - get model IDs
CHAT_MODEL = settings.CHAT_MODEL_ID
chat_model_info = get_chat_model_info()
CHAT_MODEL_PATH = str(BASE_DIR / chat_model_info["path"]) if chat_model_info and "path" in chat_model_info else str(TEXT_MODELS_DIR / "llama-3.1-8b-instruct-q4_k_m.gguf")

image_model_info = get_image_model_info()
IMAGE_MODEL = image_model_info.get("model_id", "stabilityai/sd-turbo") if image_model_info else "stabilityai/sd-turbo"

# HF API URL for flux-schnell (if using HF provider)
if image_model_info and image_model_info.get("provider") == "hf":
    HF_IMAGE_API_URL = f"https://router.huggingface.co/hf-inference/models/{IMAGE_MODEL}"
else:
    HF_IMAGE_API_URL = None
