"""
Video generation service supporting SVD (Stable Video Diffusion) and frame composition.
Supports: svd (local diffusers), frame-composition (local fallback).
"""
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image
import numpy as np
from typing import Optional, Dict, Any
import io

from config.default import (
    settings, get_model_by_id, get_video_model_info,
    ASSETS_DIR
)
from common.error_handling import GenerationError
from common.storage import store_asset

logger = logging.getLogger(__name__)

try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    logger.warning("imageio not available - video generation will be limited")


class VideoGenerator:
    """
    Video generator supporting SVD (Stable Video Diffusion) and frame composition.
    """
    
    def __init__(self):
        """Initialize video generator."""
        self._svd_model = None
    
    def _load_svd_model(self):
        """Load Stable Video Diffusion model."""
        if self._svd_model is not None:
            return self._svd_model
        
        try:
            from diffusers import StableVideoDiffusionPipeline
            import torch
            
            model_info = get_model_by_id("video", "svd")
            if not model_info:
                raise ValueError("SVD model not found in registry")
            
            model_name = model_info.get("model_id", "stabilityai/stable-video-diffusion-img2vid-xt-1-1")
            logger.info(f"Loading SVD model: {model_name}")
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32
            
            pipe = StableVideoDiffusionPipeline.from_pretrained(
                model_name,
                torch_dtype=dtype
            )
            pipe = pipe.to(device)
            
            if device == "cpu":
                pipe.enable_attention_slicing()
            
            self._svd_model = pipe
            logger.info(f"Loaded SVD model on {device}")
            return pipe
            
        except ImportError:
            raise ImportError(
                "diffusers and torch are required for SVD. "
                "Install with: pip install diffusers torch"
            )
        except Exception as e:
            logger.error(f"Error loading SVD model: {e}")
            raise GenerationError(f"Failed to load SVD model: {e}", "model_load_error")
    
    def _generate_svd(
        self,
        image_path: str,
        motion_bucket_id: int = 127,
        num_frames: int = 25,
        num_inference_steps: int = 25
    ) -> list:
        """
        Generate video using Stable Video Diffusion.
        
        Args:
            image_path: Path to input image
            motion_bucket_id: Motion bucket ID (1-255, higher = more motion)
            num_frames: Number of frames to generate
            num_inference_steps: Number of inference steps
            
        Returns:
            List of PIL Images (frames)
        """
        pipe = self._load_svd_model()
        
        # Load and preprocess image
        image = Image.open(image_path).convert("RGB")
        
        # Resize to SVD's expected size (1024x576 or similar)
        width, height = image.size
        target_height = 576
        target_width = int(width * target_height / height)
        target_width = (target_width // 64) * 64  # Round to multiple of 64
        
        if image.size != (target_width, target_height):
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        logger.info(f"Generating {num_frames} frames with SVD")
        
        try:
            frames = pipe(
                image,
                motion_bucket_id=motion_bucket_id,
                num_inference_steps=num_inference_steps,
                num_frames=num_frames,
                decode_chunk_size=8
            ).frames[0]
            
            return frames
        except Exception as e:
            logger.error(f"SVD generation error: {e}")
            raise GenerationError(f"SVD generation failed: {e}", "generation_failed")
    
    def _generate_frame_composition(
        self,
        image_path: str,
        prompt: str = "",
        frames: int = 96,
        fps: int = 24
    ) -> list:
        """
        Generate video using frame composition (fallback method).
        
        Args:
            image_path: Path to input image
            prompt: Optional prompt (not used in composition)
            frames: Number of frames
            fps: Frames per second
        
        Returns:
            List of PIL Images (frames)
        """
        if not IMAGEIO_AVAILABLE:
            raise GenerationError("imageio not available - cannot generate video", "dependency_missing")
        
        image_path_obj = Path(image_path)
        if not image_path_obj.exists():
            raise GenerationError(f"Image not found: {image_path}", "file_not_found")
        
            base_image = Image.open(image_path)
            if base_image.mode != 'RGB':
                base_image = base_image.convert('RGB')
            
            width, height = base_image.size
        frames_list = []
        
        # Create frames with zoom, pan, fade effects
        for i in range(frames):
            progress = i / frames
                
            if i < frames // 4:
                # Fade in
                alpha = i / (frames // 4)
                frame = self._apply_fade(base_image, alpha)
            elif i < frames // 2:
                # Zoom
                zoom_progress = (i - frames // 4) / (frames // 4)
                scale = 1.0 + (zoom_progress * 0.3)
                frame = self._apply_zoom(base_image, scale)
            elif i < 3 * frames // 4:
                # Pan
                pan_progress = (i - frames // 2) / (frames // 4)
                offset_x = int(width * 0.1 * pan_progress)
                frame = self._apply_pan(base_image, offset_x, 0)
            else:
                # Fade out
                fade_progress = (i - 3 * frames // 4) / (frames // 4)
                alpha = 1.0 - fade_progress
                frame = self._apply_fade(base_image, alpha)
                
            frames_list.append(frame)
            
        return frames_list
    
    def _apply_fade(self, image: Image.Image, alpha: float) -> Image.Image:
        """Apply fade effect."""
        img = image.copy()
        alpha = max(0, min(1, alpha))
        if alpha < 1.0:
            dark = Image.new('RGB', img.size, (0, 0, 0))
            img = Image.blend(dark, img, alpha)
        return img
    
    def _apply_zoom(self, image: Image.Image, scale: float) -> Image.Image:
        """Apply zoom effect."""
        width, height = image.size
        new_size = (int(width * scale), int(height * scale))
        zoomed = image.resize(new_size, Image.Resampling.LANCZOS)
        output = Image.new('RGB', (width, height), (0, 0, 0))
        offset_x = (width - new_size[0]) // 2
        offset_y = (height - new_size[1]) // 2
        output.paste(zoomed, (offset_x, offset_y))
        return output
    
    def _apply_pan(self, image: Image.Image, offset_x: int, offset_y: int) -> Image.Image:
        """Apply pan effect."""
        width, height = image.size
        output = Image.new('RGB', (width, height), (0, 0, 0))
        output.paste(image, (offset_x, offset_y))
        return output
    
    def generate(
        self,
        image_path: str,
        model_id: Optional[str] = None,
        prompt: str = "",
        frames: int = None,
        fps: int = None,
        duration: int = None,
        resolution: str = None,
        brand: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate video from input image.
        
        Args:
            image_path: Path to input image
            model_id: Model ID from registry (defaults to settings default)
            prompt: Motion prompt (for SVD)
            frames: Number of frames
            fps: Frames per second
            duration: Video duration in seconds
            resolution: Video resolution (e.g., "512x512")
            brand: Brand name (for storage organization)
            **kwargs: Additional parameters
            
        Returns:
            Path to generated video file
        """
        if not model_id:
            model_info = get_video_model_info()
            model_id = model_info["id"] if model_info else "frame-composition"
        
        model_info = get_model_by_id("video", model_id)
        if not model_info:
            raise ValueError(f"Video model {model_id} not found in registry")
        
        # Set defaults
        if model_id == "svd":
            num_frames = frames or 25
            fps = fps or 6  # SVD typically generates at 6 fps
            duration = duration or (num_frames / fps)
        else:  # frame-composition
            fps = fps or settings.DEFAULT_VIDEO_FPS
            duration = duration or settings.DEFAULT_VIDEO_DURATION
            num_frames = frames or (fps * duration)
        
        # Generate frames
        if model_id == "svd":
            try:
                frames_list = self._generate_svd(
                    image_path=image_path,
                    num_frames=num_frames,
                    num_inference_steps=25
                )
            except (ImportError, GenerationError) as e:
                logger.warning(f"SVD generation failed, falling back to frame-composition: {e}")
                frames_list = self._generate_frame_composition(
                    image_path=image_path,
                    prompt=prompt,
                    frames=num_frames,
                    fps=fps
                )
        else:  # frame-composition
            frames_list = self._generate_frame_composition(
                image_path=image_path,
                prompt=prompt,
                frames=num_frames,
                fps=fps
            )
        
        if not frames_list:
            raise GenerationError("Failed to generate video frames", "frame_generation_failed")
        
        # Save video using store_asset with brand organization
        brand_id = brand or "default"
        video_bytes = self._frames_to_mp4_bytes(frames_list, fps)
        
        if not video_bytes:
            raise GenerationError("Failed to create video", "video_creation_failed")
        
        # Store using new structure
        file_path, metadata_path = store_asset(
            content=video_bytes,
            asset_type="video",
            brand_id=brand_id,
            mime_type="video/mp4"
        )
        
        logger.info(f"✅ Video saved to: {file_path}")
        return file_path
    
    def _frames_to_mp4_bytes(self, frames: list, fps: int) -> Optional[bytes]:
        """Convert frames to MP4 video bytes."""
        if not IMAGEIO_AVAILABLE:
            raise GenerationError("imageio not available - cannot save video", "dependency_missing")
        
        try:
            # Convert PIL images to numpy arrays
            frame_arrays = []
            for frame in frames:
                if isinstance(frame, Image.Image):
                    frame_array = np.array(frame)
                else:
                    frame_array = frame
                frame_arrays.append(frame_array)
            
            # Use imageio to write MP4 to bytes
            buffer = io.BytesIO()
            writer = imageio.get_writer(
                buffer,
                format='mp4',
                fps=fps,
                codec='libx264',
                pixelformat='yuv420p'
            )
            
            for frame_array in frame_arrays:
                writer.append_data(frame_array)
            
            writer.close()
            buffer.seek(0)
            video_bytes = buffer.read()
            
            size_mb = len(video_bytes) / (1024 * 1024)
            logger.info(f"✅ MP4 created successfully: {size_mb:.2f} MB")
            return video_bytes
                
        except Exception as e:
            logger.error(f"❌ Failed to create MP4: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if video generation is available."""
        return IMAGEIO_AVAILABLE
