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
    """
    Application settings with environment variable support.
    
    For local development: Create a .env file in backend/ directory
    For Azure deployment: Set environment variables in App Service Configuration
    
    Required for Azure:
    - DATA_DIR: Root path for data (default: /home/site/wwwroot/data in Azure)
    - HF_TOKEN: HuggingFace API token for FLUX image generation
    
    Optional for future model platform integration:
    - MODEL_API_URL: External model API endpoint
    - MODEL_API_KEY: External model API key
    """
    
    # Core paths - override for Azure deployment
    # In Azure, set DATA_DIR=/home/site/wwwroot/data
    DATA_DIR_OVERRIDE: str = ""  # If set, overrides default DATA_DIR
    DB_PATH: str = ""  # If set, overrides default database path
    
    # HuggingFace API token - enables FLUX and other HF API models
    HF_TOKEN: str = ""
    
    # Future model platform integration
    MODEL_API_URL: str = ""  # External model API endpoint (for future use)
    MODEL_API_KEY: str = ""  # External model API key (for future use)
    
    # Database URL (SQLite by default)
    DATABASE_URL: str = f"sqlite:///{str(BASE_DIR.absolute())}/data/metadata.db"
    
    # Storage backend configuration
    STORAGE_BACKEND: str = "local"  # local or minio
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    
    # Model IDs from registry (can be overridden via env)
    EMBEDDING_MODEL_ID: str = "all-MiniLM-L6-v2"
    IMAGE_MODEL_ID: str = "flux-schnell"  # Use HF API by default
    VIDEO_MODEL_ID: str = "composition"  # Use frame composition by default
    CHAT_MODEL_ID: str = "phi-3.5-mini"  # or "llama-3.1-8b"
    
    # Image generation defaults
    DEFAULT_IMAGE_STEPS: int = 4
    DEFAULT_IMAGE_SIZE: str = "512x512"
    
    # Video generation defaults
    DEFAULT_VIDEO_FRAMES: int = 96
    DEFAULT_VIDEO_FPS: int = 24
    DEFAULT_VIDEO_DURATION: int = 4
    
    # RAG/Chunking settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    K_RETRIEVAL: int = 4
    
    # API server settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS settings for frontend
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Override DATA_DIR if DATA_DIR_OVERRIDE is set (for Azure deployment)
if settings.DATA_DIR_OVERRIDE:
    DATA_DIR = Path(settings.DATA_DIR_OVERRIDE)
    CHROMA_DIR = DATA_DIR / "chroma"
    UPLOAD_DIR = DATA_DIR / "uploaded_files"
    OUTPUT_IMAGE_DIR = DATA_DIR / "outputs" / "images"
    OUTPUT_VIDEO_DIR = DATA_DIR / "outputs" / "videos"
    ASSETS_DIR = DATA_DIR / "assets"
    
    # Ensure overridden directories exist
    for d in [DATA_DIR, CHROMA_DIR, UPLOAD_DIR, OUTPUT_IMAGE_DIR, OUTPUT_VIDEO_DIR, ASSETS_DIR]:
        ensure_writable_directory(d)

# Override DATABASE_URL if DB_PATH is set
if settings.DB_PATH:
    settings.DATABASE_URL = f"sqlite:///{settings.DB_PATH}"

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
