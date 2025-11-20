"""
Download GGUF models for local LLM inference.
Uses huggingface_hub for authenticated downloads.
Downloads models from models/registry.json.
"""
import os
import json
from pathlib import Path

# Get the project root (3 levels up from this script)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "text"
REGISTRY_PATH = PROJECT_ROOT / "models" / "registry.json"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Load models from registry.json
MODELS = {}
if REGISTRY_PATH.exists():
    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)
    
    # Extract chat models from registry
    if "chat" in registry:
        for model_id, model_info in registry["chat"].items():
            if model_info.get("provider") == "local" and "repo_id" in model_info:
                MODELS[model_id] = {
                    "repo_id": model_info["repo_id"],
                    "filename": model_info.get("filename", ""),
                    "name": model_info.get("name", model_id),
                    "path": model_info.get("path", ""),  # Include path for nested directories
                }
else:
    # Fallback to default models if registry doesn't exist
MODELS = {
        "phi-3.5-mini": {
            "repo_id": "bartowski/Phi-3.5-mini-instruct-GGUF",
            "filename": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
            "name": "Phi-3.5 Mini",
            "path": "models/text/phi-3.5-mini-instruct/Phi-3.5-mini-instruct-Q4_K_M.gguf"
    },
        "llama-3.1-8b": {
            "repo_id": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
            "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "name": "Llama 3.1 8B",
            "path": "models/text/llama-3.1-8b-instruct/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    },
}

def download_model(repo_id: str, filename: str, filepath: Path):
    """Download a model using huggingface_hub."""
    try:
        from huggingface_hub import hf_hub_download, list_repo_files
        
        # Try exact filename first
        try:
            print(f"Downloading {filename} from {repo_id}...")
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(filepath.parent),
            )
            
            # Move to final location if needed
            if downloaded_path != str(filepath):
                import shutil
                if Path(downloaded_path).exists():
                    shutil.move(downloaded_path, filepath)
            
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                print(f"✓ Downloaded {filename} ({size_mb:.1f} MB)")
                return True
        except Exception as e1:
            print(f"  Exact filename not found, searching for alternatives...")
            
            # Try to find any Q4 GGUF file
            try:
                files = list_repo_files(repo_id)
                gguf_files = [f for f in files if '.gguf' in f.lower() and 'q4' in f.lower()]
                if gguf_files:
                    alt_filename = gguf_files[0]
                    print(f"  Found alternative: {alt_filename}")
                    downloaded_path = hf_hub_download(
                        repo_id=repo_id,
                        filename=alt_filename,
                        local_dir=str(filepath.parent),
                    )
                    # Rename to expected filename
                    import shutil
                    if Path(downloaded_path).exists():
                        shutil.move(downloaded_path, filepath)
                    if filepath.exists():
                        size_mb = filepath.stat().st_size / (1024 * 1024)
                        print(f"✓ Downloaded {alt_filename} as {filename} ({size_mb:.1f} MB)")
                        return True
            except Exception as e2:
                print(f"  Could not find alternatives: {e2}")
                raise e1
        
        return False
        
    except ImportError:
        print("huggingface_hub not installed.")
        print("Please install it using Poetry:")
        print("  cd backend && poetry add huggingface_hub")
        print("Or with pip:")
        print("  pip install huggingface_hub")
        print("\nThen run this script again.")
        return False
    except Exception as e:
        print(f"✗ Error downloading {filename}: {e}")
        print(f"  You can manually download from: https://huggingface.co/{repo_id}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GGUF Model Downloader")
    print("=" * 60)
    print(f"\nModels directory: {MODELS_DIR}")
    print(f"Available models: {list(MODELS.keys())}\n")
    
    downloaded = []
    for model_id, model_info in MODELS.items():
        model_name = model_info.get("name", model_id)
        
        # Determine target path (nested directory if path specified, else flat)
        if "path" in model_info and model_info["path"]:
            # Extract directory from path (e.g., "models/text/phi-3.5-mini-instruct/...")
            path_parts = Path(model_info["path"]).parts
            if len(path_parts) >= 2:
                model_dir = path_parts[-2]  # e.g., "phi-3.5-mini-instruct"
                target_dir = MODELS_DIR / model_dir
                target_dir.mkdir(parents=True, exist_ok=True)
                filepath = target_dir / model_info["filename"]
            else:
                filepath = MODELS_DIR / model_info["filename"]
        else:
        filepath = MODELS_DIR / model_info["filename"]
        
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✓ {model_name} ({model_id}) already exists ({size_mb:.1f} MB)")
            downloaded.append(model_id)
        else:
            print(f"\n📥 Downloading {model_name} ({model_id})...")
            print(f"   Repository: {model_info['repo_id']}")
            print(f"   Filename: {model_info['filename']}")
            print(f"   Target: {filepath}")
            if download_model(model_info["repo_id"], model_info["filename"], filepath):
                downloaded.append(model_id)
    
    print("\n" + "=" * 60)
    if downloaded:
        print(f"✅ Successfully downloaded: {', '.join(downloaded)}")
        print(f"\nModels are ready! Restart the backend to use them.")
    else:
        print("⚠️  No models downloaded.")
        print("\nYou can manually download models from:")
        for model_id, model_info in MODELS.items():
            print(f"  • {model_info.get('name', model_id)}: https://huggingface.co/{model_info['repo_id']}")
    print("=" * 60)

