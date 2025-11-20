"""
FastAPI main application with all endpoints.
Provides REST API for image generation, video generation, RAG chat, and brand management.
"""
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.default import settings
from services.image_gen import ImageGenerator
from services.video_gen import VideoGenerator
from services.vector_store import VectorStore
from services.doc_loader import load_document
from services.text_splitter import TextSplitter
from services.prompt_orchestrator import create_prompt_orchestrator
from services.chat_service import BrandChatService
from services.llm_client import LLMClient
from services.brand_ingest import BrandIngestService
from common.metadata import (
    MediaItem, add_media_item, get_media_item_by_id, get_all_media_items,
    create_asset_metadata
)
from common.error_handling import GenerationError
from common.storage import store_media
from common.chat_models import init_chat_db, ChatSession, ChatMessage, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Content Generation API", version="1.0.0")

# Initialize chat database
init_chat_db()

# Disable CORS for full-stack development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_generator = ImageGenerator()
video_generator = VideoGenerator()
vector_store = VectorStore()
text_splitter = TextSplitter()
brand_ingest_service = BrandIngestService(vector_store, text_splitter)

# Initialize LLM client and chat service
try:
    llm_client = LLMClient(model_id=settings.CHAT_MODEL_ID)
    logger.info(f"Initialized local LLM client with model: {settings.CHAT_MODEL_ID}")
except (FileNotFoundError, ImportError, ValueError) as e:
    logger.error(f"Local LLM not available: {e}")
    llm_client = None

# Initialize chat service with proper dependencies
if llm_client:
    try:
        from services.chat_store import ChatStore
        from services.chat_llm import ChatLLM
        from services.memory_engine import MemoryEngine
        from services.rag_retrieval import RAGRetrieval
        
        # Initialize chat dependencies
        chat_store = ChatStore()
        chat_llm = ChatLLM(model_id=settings.CHAT_MODEL_ID)
        rag_retrieval = RAGRetrieval(vector_store, top_k=5)
        memory_engine = MemoryEngine(chat_llm)
        
        # Initialize chat service with all dependencies
        chat_service = BrandChatService(
            vector_store=vector_store,
            llm_client=llm_client,
            chat_store=chat_store,
            chat_llm=chat_llm,
            memory_engine=memory_engine
        )
        logger.info("Chat service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chat service: {e}")
        chat_service = None
else:
    logger.warning("Chat service not available - LLM client not initialized")
    chat_service = None

# Initialize prompt orchestrator with LLM client if available
prompt_orchestrator = create_prompt_orchestrator(vector_store, llm_client=llm_client)

jobs = {}


class ImageGenerationRequest(BaseModel):
    prompt: str
    model_id: Optional[str] = None
    negative_prompt: Optional[str] = None
    steps: Optional[int] = 4
    width: Optional[int] = 512
    height: Optional[int] = 512
    size: Optional[str] = None  # Legacy: "512x512" format
    seed: Optional[int] = -1
    brand: Optional[str] = None
    brand_id: Optional[str] = None
    market: Optional[str] = None
    template_type: Optional[str] = None
    template_fields: Optional[dict] = None
    style_preset: Optional[str] = None
    lighting_preset: Optional[str] = None
    use_orchestrator: Optional[bool] = False


class VideoGenerationRequest(BaseModel):
    image_path: str
    model_id: Optional[str] = None
    prompt: Optional[str] = ""
    frames: Optional[int] = None
    fps: Optional[int] = None
    duration: Optional[int] = None
    resolution: Optional[str] = None
    brand: Optional[str] = None
    brand_id: Optional[str] = None
    market: Optional[str] = None
    template_type: Optional[str] = None
    template_fields: Optional[dict] = None
    style_preset: Optional[str] = None
    use_orchestrator: Optional[bool] = False


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    brand: Optional[str] = None
    messages: List[Dict[str, str]] = []
    # Legacy support: if 'query' is provided, convert to messages format
    query: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/api/image/generate")
async def generate_image(request: ImageGenerationRequest):
    """Generate an image from a text prompt."""
    try:
        logger.info(f"Generating image with prompt: {request.prompt[:100]}...")
        logger.info(f"Request details: model={request.model_id}, size={request.width}x{request.height}, steps={request.steps}")
        
        # Parse size if provided
        width = request.width or 512
        height = request.height or 512
        if request.size:
            parts = request.size.split("x")
            width = int(parts[0])
            height = int(parts[1]) if len(parts) > 1 else width
        
        brand_id = request.brand_id or request.brand or "default"
        
        if request.use_orchestrator and (request.brand or request.brand_id):
            result = image_generator.generate_with_orchestrator(
                prompt=request.prompt,
                brand=request.brand or request.brand_id,
                market=request.market,
                template_type=request.template_type,
                template_fields=request.template_fields,
                style_preset=request.style_preset,
                lighting_preset=request.lighting_preset,
                model_id=request.model_id,
                steps=request.steps,
                width=width,
                height=height,
                seed=request.seed
            )
            image_path = result["image_path"]
            
            # Get model info
            model_id = request.model_id or settings.IMAGE_MODEL_ID
            from config.default import get_model_by_id
            model_info = get_model_by_id("image", model_id) or {}
            
            # Create comprehensive metadata
            from common.metadata import create_asset_metadata
            metadata = create_asset_metadata(
                asset_type="image",
                brand_id=brand_id,
                user_input=request.prompt,
                template_id=request.template_type,
                template_values=request.template_fields,
                master_prompt=result["enhanced_prompt"],
                negative_prompt=result.get("negative_prompt"),
                model_id=model_id,
                model_name=model_info.get("name", model_id),
                provider=model_info.get("provider", "local"),
                params={"steps": request.steps, "width": width, "height": height, "seed": request.seed},
                rag_snippets=result.get("rag_snippets", []),
                file_path=image_path
            )
            
            item = MediaItem(
                status="complete",
                prompt=result["enhanced_prompt"],
                original_prompt=result["original_prompt"],
                model=model_id,
                mime_type="image/png",
                file_path=image_path,
                mode="text-to-image",
                brand_id=brand_id,
                template_id=request.template_type,
                template_values=request.template_fields,
                metadata=metadata
            )
            item_id = add_media_item(item)
            
            return {
                "success": True,
                "image_path": image_path,
                "item_id": item_id,
                "original_prompt": result["original_prompt"],
                "enhanced_prompt": result["enhanced_prompt"],
                "master_prompt": result["enhanced_prompt"],
                "negative_prompt": result.get("negative_prompt"),
                "brand_context": result.get("brand_context"),
                "rag_snippets": result.get("rag_snippets", [])
            }
        else:
            image_path = image_generator.generate(
                prompt=request.prompt,
                model_id=request.model_id,
                negative_prompt=request.negative_prompt,
                steps=request.steps,
                width=width,
                height=height,
                seed=request.seed,
                brand=brand_id
            )
            
            if not image_path:
                raise HTTPException(status_code=500, detail="Image generation failed")
            
            model_id = request.model_id or settings.IMAGE_MODEL_ID
            from config.default import get_model_by_id
            model_info = get_model_by_id("image", model_id) or {}
            
            # Create comprehensive metadata even without orchestrator
            from common.metadata import create_asset_metadata
            metadata = create_asset_metadata(
                asset_type="image",
                brand_id=brand_id,
                user_input=request.prompt,
                template_id=request.template_type,
                template_values=request.template_fields,
                master_prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                model_id=model_id,
                model_name=model_info.get("name", model_id),
                provider=model_info.get("provider", "local"),
                params={"steps": request.steps, "width": width, "height": height, "seed": request.seed},
                file_path=image_path
            )
            
            item = MediaItem(
                status="complete",
                prompt=request.prompt,
                original_prompt=request.prompt,
                model=model_id,
                mime_type="image/png",
                file_path=image_path,
                mode="text-to-image",
                brand_id=brand_id,
                metadata=metadata
            )
            item_id = add_media_item(item)
            
            return {
                "success": True,
                "image_path": image_path,
                "item_id": item_id,
                "master_prompt": request.prompt,
                "negative_prompt": request.negative_prompt
            }
        
    except FileNotFoundError as e:
        error_msg = str(e)
        logger.error(f"Model not found: {error_msg}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "model_not_installed",
                "message": error_msg,
                "instructions": "Download models using: python backend/scripts/download_models.py"
            }
        )
    except GenerationError as e:
        logger.error(f"Generation error: {e.message}")
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video/generate")
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a video from an image (async)."""
    try:
        import uuid
        job_id = str(uuid.uuid4())
        
        # Build enhanced prompt if orchestrator is enabled
        enhanced_prompt = request.prompt
        prompt_metadata = {}
        
        if request.use_orchestrator and request.brand:
            try:
                prompt_result = prompt_orchestrator.build_master_prompt(
                    user_prompt=request.prompt,
                    brand=request.brand,
                    market=request.market,
                    template_type=request.template_type,
                    template_fields=request.template_fields,
                    style_preset=request.style_preset,
                    engine_type="video"
                )
                enhanced_prompt = prompt_result["enhanced_prompt"]
                prompt_metadata = {
                    "original_prompt": prompt_result["original_prompt"],
                    "enhanced_prompt": enhanced_prompt,
                    "brand_context": prompt_result.get("brand_context")
                }
            except Exception as e:
                logger.warning(f"Failed to enhance prompt, using original: {e}")
        
        brand_id = request.brand_id or request.brand or "default"
        model_id = request.model_id or settings.VIDEO_MODEL_ID
        
        item = MediaItem(
            id=job_id,
            status="pending",
            prompt=request.prompt,
            model=model_id,
            mime_type="video/mp4",
            mode="image-to-video",
            brand_id=brand_id,
            template_id=request.template_type,
            template_values=request.template_fields
        )
        add_media_item(item)
        
        background_tasks.add_task(
            _process_video_generation,
            job_id=job_id,
            request=request,
            enhanced_prompt=enhanced_prompt,
            prompt_metadata=prompt_metadata
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            **prompt_metadata
        }
        
    except Exception as e:
        logger.error(f"Error creating video job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/video/job/{job_id}")
async def get_video_job_status(job_id: str):
    """Get status of a video generation job."""
    item = get_media_item_by_id(job_id)
    
    if not item:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job_id,
        "status": item.status
    }
    
    if item.status == "complete":
        response["video_path"] = item.file_path
    elif item.status == "failed":
        response["error"] = item.error_message
    
    return response


async def _process_video_generation(job_id: str, request: VideoGenerationRequest, enhanced_prompt: str = None, prompt_metadata: dict = None):
    """Background task for video generation."""
    try:
        logger.info(f"Processing video generation job: {job_id}")
        
        item = get_media_item_by_id(job_id)
        item.status = "processing"
        add_media_item(item)
        
        brand_id = request.brand_id or request.brand or "default"
        model_id = request.model_id or settings.VIDEO_MODEL_ID
        
        # Use enhanced prompt if available, otherwise fall back to original
        prompt_to_use = enhanced_prompt if enhanced_prompt else request.prompt
        
        video_path = video_generator.generate(
            image_path=request.image_path,
            model_id=model_id,
            prompt=prompt_to_use,
            frames=request.frames,
            fps=request.fps,
            duration=request.duration,
            resolution=request.resolution,
            brand=brand_id
        )
        
        if not video_path:
            raise GenerationError("Video generation failed", "generation_failed")
        
        # Get model info
        from config.default import get_model_by_id
        model_info = get_model_by_id("video", model_id) or {}
        
        # Create comprehensive metadata
        metadata = create_asset_metadata(
            asset_type="video",
            brand_id=brand_id,
            user_input=request.prompt,
            template_id=request.template_type,
            template_values=request.template_fields,
            master_prompt=prompt_metadata.get("enhanced_prompt", prompt_to_use) if prompt_metadata else prompt_to_use,
            negative_prompt=None,  # Videos typically don't use negative prompts
            model_id=model_id,
            model_name=model_info.get("name", model_id),
            provider=model_info.get("provider", "local"),
            params={
                "frames": request.frames,
                "fps": request.fps,
                "duration": request.duration,
                "resolution": request.resolution
            },
            rag_snippets=prompt_metadata.get("rag_snippets", []) if prompt_metadata else [],
            file_path=video_path
        )
        
        item.status = "complete"
        item.file_path = video_path
        item.model = model_id
        item.brand_id = brand_id
        item.template_id = request.template_type
        item.template_values = request.template_fields
        item.metadata = metadata
        add_media_item(item)
        
        logger.info(f"Video generation job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Video generation job {job_id} failed: {e}")
        
        item = get_media_item_by_id(job_id)
        item.status = "failed"
        item.error_message = str(e)
        add_media_item(item)




@app.get("/api/chat/sessions")
async def list_sessions():
    """List all chat sessions."""
    from services.chat_store import ChatStore
    try:
        chat_store = ChatStore()
        sessions = chat_store.list_sessions(limit=100)
        return sessions
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict()
    title: Optional[str] = None
    brand: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    model_config = ConfigDict()
    title: Optional[str] = None
    brand: Optional[str] = None
    archived: Optional[bool] = None


@app.post("/api/chat/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new chat session."""
    from services.chat_store import ChatStore
    chat_store = ChatStore()
    return chat_store.create_session(title=request.title, brand=request.brand)


@app.get("/api/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session with message history."""
    from services.chat_store import ChatStore
    chat_store = ChatStore()
    session = chat_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with multi-session support."""
    if not chat_service:
        raise HTTPException(
            status_code=500,
            detail="Local LLM model not found. Please download a GGUF model."
        )
    
    try:
        user_messages = [m for m in request.messages if m.get("role") == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        last_user_message = user_messages[-1].get("content", "")
        
        result = chat_service.chat_session(
            session_id=request.session_id,
            brand=request.brand,
            new_user_message=last_user_message
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        error_msg = str(e)
        logger.error(f"Model not found: {error_msg}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "model_not_installed",
                "message": error_msg,
                "instructions": "Download models using: python backend/scripts/download_models.py"
            }
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class SendMessageRequest(BaseModel):
    model_config = ConfigDict()
    content: str
    brand: Optional[str] = None
    model_id: Optional[str] = None


@app.post("/api/chat/sessions/{session_id}/messages")
async def send_message(session_id: str, request: SendMessageRequest):
    """Send a message in a session."""
    if not chat_service:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "model_not_installed",
                "message": "Local LLM model not found. Please download a GGUF model.",
                "instructions": "Run: python backend/scripts/download_models.py"
            }
        )
    
    try:
        actual_session_id = None if session_id == "new" else session_id
        
        result = chat_service.chat_session(
            session_id=actual_session_id,
            brand=request.brand,
            new_user_message=request.content,
            model_id=request.model_id
        )
        
        return result
        
    except FileNotFoundError as e:
        error_msg = str(e)
        logger.error(f"Model not found: {error_msg}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "model_not_installed",
                "message": error_msg,
                "instructions": "Download models using: python backend/scripts/download_models.py"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class PromptEnhanceRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    
    user_input: str
    brand_id: Optional[str] = None
    template_id: Optional[str] = None
    template_values: Optional[dict] = None
    negative_prompt: Optional[str] = None
    engine_type: str = "image"


@app.post("/api/prompt/enhance")
async def enhance_prompt(request: PromptEnhanceRequest):
    """Enhance prompt using LLM with brand context and templates."""
    try:
        result = prompt_orchestrator.build_master_prompt(
            user_prompt=request.user_input,
            brand=request.brand_id,
            template_type=request.template_id,
            template_fields=request.template_values,
            negative_prompt=request.negative_prompt,
            engine_type=request.engine_type
        )
        
        return {
            "master_prompt": result.get("enhanced_prompt", result.get("master_prompt", "")),
            "negative_prompt": result.get("negative_prompt", ""),
            "rag_snippets": result.get("rag_snippets", []),
            "metadata": result.get("metadata", {})
        }
    except Exception as e:
        logger.error(f"Prompt enhancement error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/chat/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """Update a chat session (rename, archive, etc.)."""
    from services.chat_store import ChatStore
    chat_store = ChatStore()
    updated = chat_store.update_session(
        session_id,
        title=request.title,
        brand=request.brand
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@app.delete("/api/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    from services.chat_store import ChatStore
    chat_store = ChatStore()
    deleted = chat_store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "message": "Session deleted"}


@app.get("/api/brands")
async def get_brands():
    """Get all unique brands in the knowledge base."""
    try:
        # Reload metadata to get latest brands
        vector_store.reload_metadata()

        # Get unique brand keys (grouping by brand name)
        unique_brand_keys = vector_store.get_unique_brand_keys()

        # Create brand options for dropdown
        brand_options = []
        for brand_key in unique_brand_keys:
            brand_options.append({
                "brand": brand_key,
                "collection_name": vector_store._get_collection_name(brand_key),
                "total_documents": 1,  # Placeholder, will be updated with actual stats
                "chunks": 1,
                "vectors": 1,
                "docs": 1
            })

        return {"brands": brand_options}
    except Exception as e:
        logger.error(f"Error getting brands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/brands/upload")
async def upload_brand_document(
    file: UploadFile = File(...),
    brand: Optional[str] = Form(None)
):
    """Upload a brand document."""
    try:
        # Save uploaded file
        from config.default import UPLOAD_DIR
        file_path = UPLOAD_DIR / file.filename
        
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Uploaded file: {file_path}")
        
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/brands/ingest")
async def ingest_brand_document(
    file_path: str = Form(...),
    brand: Optional[str] = Form(None)
):
    """Ingest a brand document into the vector store."""
    try:
        logger.info(f"[ingest_endpoint] Request received: file_path='{file_path}', brand='{brand}'")
        
        # Pre-flight validation
        if not file_path or not file_path.strip():
            logger.error("[ingest_endpoint] Validation failed: file_path is empty")
            raise HTTPException(status_code=400, detail="File path is required and cannot be empty")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"[ingest_endpoint] Validation failed: File not found: {file_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        if not file_path_obj.is_file():
            logger.error(f"[ingest_endpoint] Validation failed: Path is not a file: {file_path}")
            raise HTTPException(status_code=400, detail=f"Path is not a file: {file_path}")
        
        # Check file format
        ext = file_path_obj.suffix.lower()
        supported_formats = ['.csv', '.xlsx', '.xls', '.txt', '.pdf', '.docx']
        if ext not in supported_formats:
            logger.error(f"[ingest_endpoint] Validation failed: Unsupported file format: {ext}")
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {ext}. Supported formats: {', '.join(supported_formats)}"
            )
        
        # Validate brand name for CSV/Excel files
        if ext in ['.csv', '.xlsx', '.xls']:
            if not brand or not brand.strip():
                logger.error(f"[ingest_endpoint] Validation failed: Brand name required for {ext} files")
                raise HTTPException(
                    status_code=400,
                    detail=f"Brand name is required for {ext} files. Please provide a brand name."
                )
        
        logger.info(f"[ingest_endpoint] Validation passed, starting ingestion...")
        
        # Use brand ingestion service
        try:
            result = brand_ingest_service.ingest_file(file_path, brand=brand)
            logger.info(f"[ingest_endpoint] Ingestion successful: {result}")
        except ValueError as ve:
            logger.error(f"[ingest_endpoint] Validation error during ingestion: {ve}", exc_info=True)
            raise HTTPException(status_code=400, detail=f"Validation error: {str(ve)}")
        except FileNotFoundError as fe:
            logger.error(f"[ingest_endpoint] File not found: {fe}", exc_info=True)
            raise HTTPException(status_code=404, detail=f"File not found: {str(fe)}")
        except PermissionError as pe:
            logger.error(f"[ingest_endpoint] Permission error: {pe}", exc_info=True)
            raise HTTPException(status_code=403, detail=f"Permission error: {str(pe)}")
        except RuntimeError as re:
            logger.error(f"[ingest_endpoint] Runtime error: {re}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Runtime error: {str(re)}")
        
        # Get updated stats
        try:
            stats = vector_store.get_all_stats()
            logger.info(f"[ingest_endpoint] Ingestion complete. Total brands in store: {len(stats)}")
        except Exception as stats_error:
            logger.warning(f"[ingest_endpoint] Could not get updated stats: {stats_error}")
            stats = []
        
        return {
            "success": True,
            "brands": result["brands"],
            "total_chunks": result["total_chunks"],
            "chunks_per_brand": result["chunks_per_brand"],
            "message": f"Successfully ingested {result['total_chunks']} chunks for {len(result['brands'])} brand(s)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ingest_endpoint] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Ingestion failed: {str(e)}. Check server logs for details."
        )


@app.get("/api/brands/health")
async def get_brands_health():
    """Quick health check for ChromaDB and vector store."""
    try:
        health = vector_store.health_check()
        status_code = 200 if health["status"] == "healthy" else 503
        return health
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/brands/diagnose")
async def diagnose_brands():
    """Comprehensive diagnostic endpoint for ChromaDB setup."""
    try:
        import chromadb
        import os
        import stat
        from config.default import CHROMA_DIR
        
        diagnostics = {
            "chromadb_version": getattr(chromadb, "__version__", "unknown"),
            "directory_path": str(CHROMA_DIR),
            "directory_exists": CHROMA_DIR.exists(),
            "directory_writable": False,
            "directory_permissions": None,
            "chromadb_connected": False,
            "collections_count": 0,
            "collections": [],
            "health_check": None,
            "errors": []
        }
        
        # Check directory
        if CHROMA_DIR.exists():
            try:
                # Get permissions
                stat_info = os.stat(CHROMA_DIR)
                diagnostics["directory_permissions"] = oct(stat_info.st_mode)[-3:]
                
                # Test write access
                test_file = CHROMA_DIR / ".diagnostic_test"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    diagnostics["directory_writable"] = True
                except Exception as e:
                    diagnostics["errors"].append(f"Directory not writable: {e}")
                    diagnostics["directory_writable"] = False
            except Exception as e:
                diagnostics["errors"].append(f"Error checking directory: {e}")
        else:
            diagnostics["errors"].append("ChromaDB directory does not exist")
        
        # Check ChromaDB connection
        try:
            collections = vector_store.client.list_collections()
            diagnostics["chromadb_connected"] = True
            diagnostics["collections_count"] = len(collections)
            diagnostics["collections"] = [
                {
                    "name": col.name if hasattr(col, 'name') else str(col),
                    "metadata": col.metadata if hasattr(col, 'metadata') else {}
                }
                for col in collections
            ]
        except Exception as e:
            diagnostics["errors"].append(f"ChromaDB connection failed: {e}")
            diagnostics["chromadb_connected"] = False
        
        # Run health check
        try:
            diagnostics["health_check"] = vector_store.health_check()
        except Exception as e:
            diagnostics["errors"].append(f"Health check failed: {e}")
        
        # Overall status
        if diagnostics["errors"]:
            diagnostics["status"] = "unhealthy"
        elif diagnostics["chromadb_connected"] and diagnostics["directory_writable"]:
            diagnostics["status"] = "healthy"
        else:
            diagnostics["status"] = "degraded"
        
        return diagnostics
        
    except Exception as e:
        logger.error(f"Diagnostic error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Diagnostic failed: {str(e)}")


@app.get("/api/media")
async def get_media_library(
    brand_id: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    is_final: Optional[bool] = True
):
    """Get media items with filtering."""
    try:
        items = get_all_media_items(
            brand_id=brand_id,
            asset_type=type,
            limit=limit,
            offset=offset,
            is_final=is_final
        )
        return {
            "items": [
                {
                    "id": item.id,
                    "status": item.status,
                    "prompt": item.prompt,
                    "original_prompt": item.original_prompt,
                    "model": item.model,
                    "mime_type": item.mime_type,
                    "file_path": item.file_path,
                    "brand_id": item.brand_id,
                    "template_id": item.template_id,
                    "template_values": item.template_values,
                    "is_final": item.is_final,
                    "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                    "metadata": item.metadata
                }
                for item in items
            ]
        }
    except Exception as e:
        logger.error(f"Error getting media: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/media/{item_id}")
async def get_media_item(item_id: str):
    """Get a specific media item."""
    item = get_media_item_by_id(item_id)
    
    if not item:
        raise HTTPException(status_code=404, detail="Media item not found")
    
    return {
        "id": item.id,
        "status": item.status,
        "prompt": item.prompt,
        "original_prompt": item.original_prompt,
        "model": item.model,
        "mime_type": item.mime_type,
        "file_path": item.file_path,
        "brand_id": item.brand_id,
        "template_id": item.template_id,
        "template_values": item.template_values,
        "is_final": item.is_final,
        "timestamp": item.timestamp.isoformat() if item.timestamp else None,
        "metadata": item.metadata
    }


@app.post("/api/assets/{asset_id}/finalize")
async def finalize_asset(asset_id: str):
    """Mark an asset as final/approved."""
    try:
        item = get_media_item_by_id(asset_id)
        if not item:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        item.is_final = True
        add_media_item(item)
        
        return {"success": True, "message": "Asset finalized"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/media/{item_id}/download")
async def download_media_item(item_id: str):
    """Download a media file."""
    item = get_media_item_by_id(item_id)
    
    if not item or not item.file_path:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    file_path = Path(item.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=str(file_path),
        media_type=item.mime_type,
        filename=file_path.name
    )


class PromptPreviewRequest(BaseModel):
    model_config = ConfigDict()
    prompt: str
    brand: str
    modality: Optional[str] = "image"
    market: Optional[str] = None
    template_type: Optional[str] = None
    template_fields: Optional[dict] = None
    style_preset: Optional[str] = None
    lighting_preset: Optional[str] = None


@app.post("/api/prompt/preview")
async def preview_prompt(request: PromptPreviewRequest):
    """Preview enhanced prompt without generating image/video."""
    try:
        if not request.brand:
            raise HTTPException(status_code=400, detail="Brand is required for prompt preview")
        
        # Map modality to engine_type
        engine_type = "image" if request.modality in ["image", "video"] else "chat"
        
        prompt_result = prompt_orchestrator.build_master_prompt(
            user_prompt=request.prompt,
            brand=request.brand,
            market=request.market,
            template_type=request.template_type,
            template_fields=request.template_fields,
            style_preset=request.style_preset,
            lighting_preset=request.lighting_preset,
            engine_type=engine_type
        )
        
        # Extract brand snippets for easier frontend consumption
        brand_snippets = []
        if prompt_result.get("brand_dnai") and prompt_result["brand_dnai"].get("raw_snippets"):
            brand_snippets = prompt_result["brand_dnai"]["raw_snippets"]
        
        return {
            "original_prompt": prompt_result["original_prompt"],
            "enhanced_prompt": prompt_result["enhanced_prompt"],
            "master_prompt": prompt_result["enhanced_prompt"],  # Alias for compatibility
            "negative_prompt": prompt_result["negative_prompt"],
            "brand_context": prompt_result["brand_context"],
            "brand_snippets": brand_snippets,
            "brand_dnai": prompt_result["brand_dnai"],
            "metadata": prompt_result["metadata"]
        }
    except Exception as e:
        logger.error(f"Prompt preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompt/templates")
async def get_templates(engine_type: str = "image"):
    """Get available prompt templates."""
    try:
        templates = prompt_orchestrator.get_available_templates(engine_type)
        return {"templates": templates}
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompt/presets")
async def get_presets():
    """Get available style and lighting presets."""
    try:
        return {
            "style_presets": prompt_orchestrator.get_style_presets(),
            "lighting_presets": prompt_orchestrator.get_lighting_presets()
        }
    except Exception as e:
        logger.error(f"Error getting presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/brands/{brand}/snippet")
async def get_brand_snippet(brand: str):
    """Get a sample snippet from brand knowledge."""
    try:
        # Reload metadata to ensure we have latest brands
        vector_store.reload_metadata()
        results = vector_store.query(brand, "brand essence", k=1)
        if not results:
            raise HTTPException(status_code=404, detail=f"Brand '{brand}' not found")
        
        return {
            "brand": brand,
            "snippet": results[0]["text"][:500]
        }
    except Exception as e:
        logger.error(f"Error getting brand snippet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/clear-vector-store")
async def clear_vector_store():
    """Clear all data from vector store."""
    try:
        vector_store.clear_all()
        return {"success": True, "message": "Vector store cleared"}
    except Exception as e:
        logger.error(f"Error clearing vector store: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/registry")
async def get_model_registry():
    """Get model registry."""
    try:
        from config.default import load_model_registry
        registry = load_model_registry()
        return {"registry": registry}
    except Exception as e:
        logger.error(f"Error getting registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models")
async def get_models(type: Optional[str] = Query(None, alias="type")):
    """
    Get list of models, optionally filtered by type.
    
    Args:
        model_type: Optional filter by type (chat, image, video, embeddings)
    
    Returns:
        List of models with id, name, description, and default params
    """
    try:
        from config.default import load_model_registry, get_model_by_id
        from config.default import settings
        
        registry = load_model_registry()
        models_list = []
        
        # Check if HF_TOKEN is available
        has_hf_token = bool(getattr(settings, 'HF_TOKEN', None))
        
        # Filter by type if provided
        if type:
            category_models = registry.get(type, {})
        else:
            # Return all models
            category_models = {}
            for category in ["chat", "image", "video", "embeddings"]:
                category_models.update(registry.get(category, {}))
        
        for model_id, model_info in category_models.items():
            # Skip HF models if token not available
            if model_info.get("requires_token") and not has_hf_token:
                continue
            
            # Format model info
            formatted_model = {
                "id": model_info.get("id", model_id),
                "name": model_info.get("name", model_id),
                "description": model_info.get("description", ""),
                "type": model_info.get("type", ""),
                "provider": model_info.get("provider", "local"),
                "default": model_info.get("default", False),
            }
            
            # Add default params if available
            if "default_params" in model_info:
                formatted_model["default_params"] = model_info["default_params"]
            
            # Add requires_token flag if present
            if model_info.get("requires_token"):
                formatted_model["requires_token"] = True
                formatted_model["optional"] = model_info.get("optional", False)
            
            models_list.append(formatted_model)
        
        return {"models": models_list}
        
    except Exception as e:
        logger.error(f"Error getting models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/clear-outputs")
async def clear_outputs():
    """Clear all generated outputs."""
    try:
        from config.default import OUTPUT_IMAGE_DIR, OUTPUT_VIDEO_DIR, ASSETS_DIR
        import shutil
        
        if Path(OUTPUT_IMAGE_DIR).exists():
            shutil.rmtree(OUTPUT_IMAGE_DIR)
            Path(OUTPUT_IMAGE_DIR).mkdir(parents=True, exist_ok=True)
        
        if Path(OUTPUT_VIDEO_DIR).exists():
            shutil.rmtree(OUTPUT_VIDEO_DIR)
            Path(OUTPUT_VIDEO_DIR).mkdir(parents=True, exist_ok=True)
        
        if Path(ASSETS_DIR).exists():
            shutil.rmtree(ASSETS_DIR)
            Path(ASSETS_DIR).mkdir(parents=True, exist_ok=True)
        
        return {"success": True, "message": "Outputs cleared"}
    except Exception as e:
        logger.error(f"Error clearing outputs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
