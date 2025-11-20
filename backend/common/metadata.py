"""
Metadata management using SQLite.
Provides MediaItem dataclass and CRUD operations.
Mirrors GCP repo's Firestore patterns.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from config.default import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class MediaItemDB(Base):
    """SQLAlchemy model for media items."""
    __tablename__ = "media_items"
    
    id = Column(String, primary_key=True)
    status = Column(String, default="created")
    user_email = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    prompt = Column(String)
    original_prompt = Column(String)
    model = Column(String)
    mime_type = Column(String)
    generation_time = Column(Float)
    error_message = Column(String)
    mode = Column(String)
    
    file_path = Column(String)
    file_paths = Column(JSON)  # For multiple files
    
    aspect = Column(String)
    resolution = Column(String)
    duration = Column(Float)
    seed = Column(Integer)
    
    # New fields
    brand_id = Column(String)
    template_id = Column(String)
    template_values = Column(JSON)
    is_final = Column(Boolean, default=False)
    
    metadata_json = Column(JSON)


Base.metadata.create_all(bind=engine)


@dataclass
class MediaItem:
    """Represents a media item with metadata."""
    
    id: Optional[str] = None
    status: str = "created"
    user_email: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    prompt: Optional[str] = None
    original_prompt: Optional[str] = None
    model: Optional[str] = None
    mime_type: Optional[str] = None
    generation_time: Optional[float] = None
    error_message: Optional[str] = None
    mode: Optional[str] = None
    
    file_path: Optional[str] = None
    file_paths: List[str] = field(default_factory=list)
    
    aspect: Optional[str] = None
    resolution: Optional[str] = None
    duration: Optional[float] = None
    seed: Optional[int] = None
    
    # New fields
    brand_id: Optional[str] = None
    template_id: Optional[str] = None
    template_values: Optional[dict] = None
    is_final: bool = False
    
    metadata: dict = field(default_factory=dict)


def add_media_item(item: MediaItem) -> str:
    """
    Add or update a media item in the database.
    
    Args:
        item: MediaItem to store
        
    Returns:
        Item ID
    """
    db = SessionLocal()
    try:
        if not item.id:
            import uuid
            item.id = str(uuid.uuid4())
        
        if not item.timestamp:
            item.timestamp = datetime.utcnow()
        
        db_item = MediaItemDB(
            id=item.id,
            status=item.status,
            user_email=item.user_email,
            timestamp=item.timestamp,
            prompt=item.prompt,
            original_prompt=item.original_prompt,
            model=item.model,
            mime_type=item.mime_type,
            generation_time=item.generation_time,
            error_message=item.error_message,
            mode=item.mode,
            file_path=item.file_path,
            file_paths=item.file_paths,
            aspect=item.aspect,
            resolution=item.resolution,
            duration=item.duration,
            seed=item.seed,
            brand_id=item.brand_id,
            template_id=item.template_id,
            template_values=item.template_values,
            is_final=item.is_final,
            metadata_json=item.metadata
        )
        
        db.merge(db_item)
        db.commit()
        
        logger.info(f"Stored media item: {item.id}")
        return item.id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error storing media item: {e}")
        raise
    finally:
        db.close()


def get_media_item_by_id(item_id: str) -> Optional[MediaItem]:
    """Get a media item by ID."""
    db = SessionLocal()
    try:
        db_item = db.query(MediaItemDB).filter(MediaItemDB.id == item_id).first()
        if not db_item:
            return None
        
        return MediaItem(
            id=db_item.id,
            status=db_item.status,
            user_email=db_item.user_email,
            timestamp=db_item.timestamp,
            prompt=db_item.prompt,
            original_prompt=db_item.original_prompt,
            model=db_item.model,
            mime_type=db_item.mime_type,
            generation_time=db_item.generation_time,
            error_message=db_item.error_message,
            mode=db_item.mode,
            file_path=db_item.file_path,
            file_paths=db_item.file_paths or [],
            aspect=db_item.aspect,
            resolution=db_item.resolution,
            duration=db_item.duration,
            seed=db_item.seed,
            brand_id=db_item.brand_id,
            template_id=db_item.template_id,
            template_values=db_item.template_values,
            is_final=db_item.is_final if hasattr(db_item, 'is_final') else False,
            metadata=db_item.metadata_json or {}
        )
    finally:
        db.close()


def get_all_media_items(
    limit: int = 100,
    brand_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    is_final: Optional[bool] = True,
    offset: int = 0
) -> List[MediaItem]:
    """Get media items with filtering."""
    db = SessionLocal()
    try:
        query = db.query(MediaItemDB)
        
        if brand_id:
            query = query.filter(MediaItemDB.brand_id == brand_id)
        
        if asset_type:
            if asset_type == "image":
                query = query.filter(MediaItemDB.mime_type.like("image/%"))
            elif asset_type == "video":
                query = query.filter(MediaItemDB.mime_type.like("video/%"))
        
        if is_final is not None:
            query = query.filter(MediaItemDB.is_final == is_final)
        
        db_items = query.order_by(MediaItemDB.timestamp.desc()).offset(offset).limit(limit).all()
        return [
            MediaItem(
                id=item.id,
                status=item.status,
                user_email=item.user_email,
                timestamp=item.timestamp,
                prompt=item.prompt,
                original_prompt=item.original_prompt,
                model=item.model,
                mime_type=item.mime_type,
                file_path=item.file_path,
                file_paths=item.file_paths or [],
                brand_id=item.brand_id,
                template_id=item.template_id,
                template_values=item.template_values,
                is_final=item.is_final if hasattr(item, 'is_final') else False,
                metadata=item.metadata_json or {}
            )
            for item in db_items
        ]
    finally:
        db.close()


def create_asset_metadata(
    asset_type: str,
    brand_id: Optional[str],
    user_input: Optional[str],
    template_id: Optional[str],
    template_values: Optional[dict],
    master_prompt: str,
    negative_prompt: Optional[str],
    model_id: str,
    model_name: str,
    provider: str,
    params: dict,
    rag_snippets: Optional[List[str]] = None,
    file_path: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    file_size: Optional[int] = None
) -> dict:
    """
    Create comprehensive metadata JSON for an asset.
    
    Returns:
        Dict with all metadata fields
    """
    import os
    
    metadata = {
        "type": asset_type,
        "brand_id": brand_id,
        "prompt_info": {
            "user_input": user_input,
            "template_id": template_id,
            "template_values": template_values,
            "master_prompt": master_prompt,
            "negative_prompt": negative_prompt
        },
        "model_info": {
            "model_id": model_id,
            "model_name": model_name,
            "provider": provider,
            "params": params
        },
        "output_info": {
            "path": file_path,
            "width": width,
            "height": height,
            "file_size": file_size
        },
        "rag_snippets": rag_snippets or []
    }
    
    # Get file size if path provided
    if file_path and os.path.exists(file_path):
        metadata["output_info"]["file_size"] = os.path.getsize(file_path)
    
    return metadata
