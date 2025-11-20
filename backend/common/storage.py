"""
Storage abstraction layer.
Provides local filesystem storage with optional MinIO support.
Organizes assets by brand and date: data/assets/<brand>/<YYYY-MM>/
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Union, Optional, Dict, Any
import logging

from config.default import settings, OUTPUT_IMAGE_DIR, OUTPUT_VIDEO_DIR, UPLOAD_DIR, ASSETS_DIR

logger = logging.getLogger(__name__)


def store_asset(
    content: Union[bytes, str],
    asset_type: str,
    brand_id: Optional[str] = None,
    filename: Optional[str] = None,
    mime_type: str = "application/octet-stream",
    metadata: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    """
    Store asset to data/assets/<brand>/<YYYY-MM>/ with metadata JSON.
    
    Args:
        content: File content as bytes or string
        asset_type: Type of asset (image, video)
        brand_id: Brand identifier (defaults to "default" if not provided)
        filename: Optional filename (auto-generated if not provided)
        mime_type: MIME type of the content
        metadata: Optional metadata dict to save as JSON
        
    Returns:
        Tuple of (file_path, metadata_path)
    """
    brand_id = brand_id or "default"
    date_str = datetime.now().strftime("%Y-%m")
    
    # Create directory: data/assets/<brand>/<YYYY-MM>/
    target_dir = ASSETS_DIR / brand_id / date_str
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
        ext = _get_extension_from_mime(mime_type)
        filename = f"{asset_type}_{timestamp}{ext}"
    
    file_path = target_dir / filename
    
    # Write content
    if isinstance(content, bytes):
        with open(file_path, 'wb') as f:
            f.write(content)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Write metadata JSON
    metadata_path = target_dir / f"{file_path.stem}_metadata.json"
    if metadata:
        metadata["file_path"] = str(file_path)
        metadata["filename"] = filename
        metadata["created_at"] = datetime.now().isoformat()
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Stored asset to: {file_path}")
    return str(file_path), str(metadata_path)


def store_media(
    content: Union[bytes, str],
    media_type: str,
    folder: str = "",
    filename: str = "",
    mime_type: str = "application/octet-stream"
) -> str:
    """
    Store media to local filesystem (legacy function for backward compatibility).
    
    Args:
        content: File content as bytes or string
        media_type: Type of media (image, video, document)
        folder: Optional subfolder
        filename: Optional filename (auto-generated if not provided)
        mime_type: MIME type of the content
        
    Returns:
        Local file path
    """
    if media_type == "image":
        base_dir = OUTPUT_IMAGE_DIR
    elif media_type == "video":
        base_dir = OUTPUT_VIDEO_DIR
    elif media_type == "document":
        base_dir = UPLOAD_DIR
    else:
        base_dir = Path(settings.STORAGE_BACKEND) / media_type
        base_dir.mkdir(parents=True, exist_ok=True)
    
    if folder:
        target_dir = base_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_dir = base_dir
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
        ext = _get_extension_from_mime(mime_type)
        filename = f"{media_type}_{timestamp}{ext}"
    
    file_path = target_dir / filename
    
    if isinstance(content, bytes):
        with open(file_path, 'wb') as f:
            f.write(content)
    else:
        with open(file_path, 'w') as f:
            f.write(content)
    
    logger.info(f"Stored media to: {file_path}")
    return str(file_path)


def _get_extension_from_mime(mime_type: str) -> str:
    """Get file extension from MIME type."""
    mime_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "video/mp4": ".mp4",
        "video/mpeg": ".mpeg",
        "text/plain": ".txt",
        "text/csv": ".csv",
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }
    return mime_map.get(mime_type, ".bin")


store_to_gcs = store_media
