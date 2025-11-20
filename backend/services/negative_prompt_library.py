"""
Negative prompt library for image and video generation.
Provides curated lists of negative prompts to improve generation quality.
"""
from typing import List, Dict


class NegativePromptLibrary:
    """Library of negative prompts for image/video generation."""
    
    COMMON_NEGATIVE = [
        "blurry",
        "low quality",
        "distorted",
        "deformed",
        "ugly",
        "bad anatomy",
        "poorly drawn",
        "extra limbs",
        "disfigured",
        "gross proportions",
        "malformed",
        "watermark",
        "signature",
        "text overlay",
        "username"
    ]
    
    IMAGE_SPECIFIC = [
        "jpeg artifacts",
        "duplicate",
        "morbid",
        "mutilated",
        "extra fingers",
        "mutated hands",
        "poorly drawn hands",
        "poorly drawn face",
        "mutation",
        "deformed hands",
        "bad hands",
        "missing fingers",
        "cropped",
        "worst quality",
        "low res"
    ]
    
    VIDEO_SPECIFIC = [
        "flickering",
        "jittery motion",
        "frame drops",
        "inconsistent lighting",
        "temporal artifacts",
        "motion blur",
        "choppy animation"
    ]
    
    BRAND_SAFETY = [
        "offensive",
        "inappropriate",
        "nsfw",
        "violent",
        "disturbing",
        "controversial"
    ]
    
    @staticmethod
    def get_negative_prompt(
        engine_type: str = "image",
        include_brand_safety: bool = True
    ) -> str:
        """
        Get a negative prompt for generation.
        
        Args:
            engine_type: "image" or "video"
            include_brand_safety: Whether to include brand safety terms
            
        Returns:
            Comma-separated negative prompt string
        """
        negatives = NegativePromptLibrary.COMMON_NEGATIVE.copy()
        
        if engine_type == "image":
            negatives.extend(NegativePromptLibrary.IMAGE_SPECIFIC)
        elif engine_type == "video":
            negatives.extend(NegativePromptLibrary.VIDEO_SPECIFIC)
        
        if include_brand_safety:
            negatives.extend(NegativePromptLibrary.BRAND_SAFETY)
        
        return ", ".join(negatives)
    
    @staticmethod
    def get_style_negative_prompts() -> Dict[str, str]:
        """Get style-specific negative prompts."""
        return {
            "photorealistic": "cartoon, anime, illustration, painting, drawing, art, sketch",
            "illustration": "photorealistic, photograph, photo, realistic",
            "minimal": "cluttered, busy, complex, detailed, ornate",
            "cinematic": "amateur, home video, low budget, poor lighting"
        }


negative_prompt_library = NegativePromptLibrary()
