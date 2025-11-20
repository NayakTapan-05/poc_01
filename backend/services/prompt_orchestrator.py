"""
Prompt orchestrator for building enhanced prompts with brand context.
Uses LLM to generate master prompts from user input, brand DNA, and templates.
"""
from typing import Dict, Any, Optional, List
import logging
from .vector_store import VectorStore
from .rag_retrieval import RAGRetrieval
from .negative_prompt_library import negative_prompt_library

logger = logging.getLogger(__name__)


class PromptOrchestrator:
    """
    Orchestrate prompt building with brand context, templates, and LLM-based enhancement.
    Uses local LLM to generate structured master prompts.
    """
    
    TEMPLATES = {
        "product_hero": {
            "name": "Product Hero Image",
            "fields": ["brand", "scene", "tone"],
            "template": "{brand} product in {scene}, {tone} atmosphere"
        },
        "lifestyle": {
            "name": "Lifestyle Scene",
            "fields": ["brand", "scene", "tone", "audience"],
            "template": "{audience} enjoying {brand} in {scene}, {tone} mood"
        },
        "promo_short": {
            "name": "Promo Short",
            "fields": ["brand", "message", "mood"],
            "template": "{brand} promotional video showcasing {message}, {mood} style"
        },
        "social_clip": {
            "name": "Social Clip",
            "fields": ["brand", "message", "mood"],
            "template": "Social media content for {brand}: {message}, {mood} vibe"
        }
    }
    
    STYLE_PRESETS = {
        "cinematic": "cinematic lighting, film grain, shallow depth of field, dramatic composition, professional color grading",
        "minimal": "clean composition, minimalist aesthetic, simple background, elegant, uncluttered",
        "vibrant": "vibrant colors, high saturation, energetic, bold, eye-catching",
        "natural": "natural lighting, authentic, organic, realistic, candid",
        "luxury": "premium quality, sophisticated, elegant, high-end, refined",
        "modern": "contemporary, sleek, modern design, cutting-edge, innovative",
        "photorealistic": "photorealistic, highly detailed, professional photography",
        "illustration": "illustrated style, artistic, hand-drawn aesthetic",
        "3d": "3D rendered, CGI, polished 3D graphics",
        "flat": "flat design, vector art, clean lines, simple shapes"
    }
    
    LIGHTING_PRESETS = {
        "studio": "professional studio lighting, soft shadows, even illumination",
        "golden_hour": "golden hour lighting, warm tones, soft natural light",
        "dramatic": "dramatic lighting, strong contrast, moody atmosphere",
        "soft": "soft diffused lighting, gentle shadows, flattering",
        "natural": "natural daylight, realistic lighting, outdoor ambiance"
    }
    
    # Few-shot examples for LLM prompt generation
    FEW_SHOT_EXAMPLES = [
        {
            "role": "user",
            "content": (
                "User input: 'A product photo of moisturizer'\n"
                "Brand DNA: Dove - gentle care, real beauty, nourishing ingredients\n"
                "Template: Product Hero Image\n"
                "Style: Cinematic\n"
                "Generate a master prompt for image generation."
            )
        },
        {
            "role": "assistant",
            "content": (
                "Professional marketing campaign photography: A product photo of a moisturizer on a marble surface. "
                "Brand context: Dove - known for gentle care, real beauty philosophy, nourishing ingredients. "
                "Style: gentle, authentic, caring. Cinematic lighting, film grain, shallow depth of field, "
                "dramatic composition, professional color grading. High quality, detailed, professional, 8k, "
                "vibrant, well-lit, commercial style, product showcase"
            )
        },
        {
            "role": "user",
            "content": (
                "User input: 'A spa scene with natural elements'\n"
                "Brand DNA: Dove - authentic, caring, real beauty\n"
                "Template: Lifestyle Scene\n"
                "Style: Natural\n"
                "Generate a master prompt for image generation."
            )
        },
        {
            "role": "assistant",
            "content": (
                "Professional lifestyle photography: A spa scene with natural elements, featuring authentic moments "
                "of care and relaxation. Brand context: Dove - authentic, caring, real beauty philosophy. "
                "Style: gentle, authentic, caring. Natural lighting, authentic, organic, realistic, candid. "
                "High quality, detailed, professional, vibrant, well-lit, engaging atmosphere"
            )
        }
    ]
    
    def __init__(self, vector_store: VectorStore, llm_client=None):
        """
        Initialize prompt orchestrator.
        
        Args:
            vector_store: VectorStore instance
            llm_client: Optional LLM client for prompt generation (if None, uses template-based fallback)
        """
        self.vector_store = vector_store
        self.rag_retrieval = RAGRetrieval(vector_store, top_k=5)
        self.negative_library = negative_prompt_library
        self.llm_client = llm_client
    
    def build_master_prompt(
        self,
        user_prompt: str,
        brand: Optional[str] = None,
        market: Optional[str] = None,
        template_type: Optional[str] = None,
        template_fields: Optional[Dict[str, str]] = None,
        style_preset: Optional[str] = None,
        lighting_preset: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        continuity_context: Optional[str] = None,
        engine_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Build a master prompt using LLM (if available) or template-based enhancement.
        
        Args:
            user_prompt: User's original prompt
            brand: Brand name
            market: Optional market/region
            template_type: Template identifier
            template_fields: Values for template fields
            style_preset: Style preset name
            lighting_preset: Lighting preset name
            negative_prompt: Optional negative prompt (will be respected, not contradicted)
            continuity_context: Context from previous generations
            engine_type: "image" or "video"
            
        Returns:
            Dict with original_prompt, enhanced_prompt (master_prompt), negative_prompt, brand_context, rag_snippets, and metadata
        """
        original_prompt = user_prompt
        
        # Apply template if provided
        if template_type and template_type in self.TEMPLATES:
            template = self.TEMPLATES[template_type]
            if template_fields:
                try:
                    template_text = template["template"].format(**template_fields)
                    original_prompt = f"{template_text}. {user_prompt}"
                except KeyError as e:
                    logger.warning(f"Missing template field: {e}")
        
        # Retrieve brand snippets via RAG
        rag_snippets = []
        brand_context_text = None
        if brand:
            try:
                query = f"brand essence tone of voice key messages target audience style"
                if market:
                    query += f" {market}"
                
                rag_results = self.rag_retrieval.retrieve(brand, query, top_k=5)
                rag_snippets = [r['text'] for r in rag_results]
                
                if rag_snippets:
                    brand_context_text = "\n".join([
                        f"- {snippet[:200]}{'...' if len(snippet) > 200 else ''}"
                        for snippet in rag_snippets[:3]
                    ])
            except Exception as e:
                logger.warning(f"Error retrieving brand context: {e}")
        
        # Generate master prompt using LLM if available
        if self.llm_client and brand and rag_snippets:
            try:
                master_prompt = self._generate_master_prompt_with_llm(
                    user_prompt=original_prompt,
                    brand=brand,
                    brand_snippets=rag_snippets,
                    template_type=template_type,
                    template_fields=template_fields,
                    style_preset=style_preset,
                    lighting_preset=lighting_preset,
                    negative_prompt=negative_prompt,
                    engine_type=engine_type
                )
            except Exception as e:
                logger.warning(f"LLM prompt generation failed, falling back to template: {e}")
                master_prompt = self._generate_master_prompt_template(
                    user_prompt=original_prompt,
                    brand_snippets=rag_snippets,
                    style_preset=style_preset,
                    lighting_preset=lighting_preset,
                    continuity_context=continuity_context
                )
        else:
            # Fallback to template-based enhancement
            master_prompt = self._generate_master_prompt_template(
                user_prompt=original_prompt,
                brand_snippets=rag_snippets,
                style_preset=style_preset,
                lighting_preset=lighting_preset,
                continuity_context=continuity_context
            )
        
        # Generate/refine negative prompt
        final_negative_prompt = negative_prompt or self.negative_library.get_negative_prompt(
            engine_type=engine_type,
            include_brand_safety=True
        )
        
        if style_preset and style_preset in ["photorealistic", "illustration", "minimal", "cinematic"]:
            style_negatives = self.negative_library.get_style_negative_prompts()
            if style_preset in style_negatives:
                final_negative_prompt += ", " + style_negatives[style_preset]
        
        return {
            "original_prompt": original_prompt,
            "enhanced_prompt": master_prompt,
            "master_prompt": master_prompt,  # Alias
            "negative_prompt": final_negative_prompt,
            "brand_context": brand_context_text,
            "brand_dnai": {
                "brand": brand,
                "market": market,
                "raw_snippets": rag_snippets
            },
            "rag_snippets": rag_snippets,
            "metadata": {
                "brand": brand,
                "market": market,
                "template_type": template_type,
                "template_fields": template_fields,
                "style_preset": style_preset,
                "lighting_preset": lighting_preset,
                "engine_type": engine_type
            }
        }
    
    def _generate_master_prompt_with_llm(
        self,
        user_prompt: str,
        brand: str,
        brand_snippets: List[str],
        template_type: Optional[str],
        template_fields: Optional[Dict[str, str]],
        style_preset: Optional[str],
        lighting_preset: Optional[str],
        negative_prompt: Optional[str],
        engine_type: str
    ) -> str:
        """
        Generate master prompt using LLM.
        
        Args:
            user_prompt: User's prompt
            brand: Brand name
            brand_snippets: List of brand DNA snippets
            template_type: Template type
            template_fields: Template field values
            style_preset: Style preset
            lighting_preset: Lighting preset
            negative_prompt: Negative prompt constraints
            engine_type: "image" or "video"
            
        Returns:
            Generated master prompt string
        """
        # Build context
        brand_context = "\n".join([f"- {s[:200]}" for s in brand_snippets[:3]])
        
        template_info = ""
        if template_type and template_type in self.TEMPLATES:
            template = self.TEMPLATES[template_type]
            template_info = f"Template: {template['name']}"
            if template_fields:
                template_info += f" with fields: {template_fields}"
        
        style_info = ""
        if style_preset and style_preset in self.STYLE_PRESETS:
            style_info = f"Style: {self.STYLE_PRESETS[style_preset]}"
        
        lighting_info = ""
        if lighting_preset and lighting_preset in self.LIGHTING_PRESETS:
            lighting_info = f"Lighting: {self.LIGHTING_PRESETS[lighting_preset]}"
        
        negative_constraint = ""
        if negative_prompt:
            negative_constraint = f"\nIMPORTANT: Do NOT include anything from this negative prompt: {negative_prompt}"
        
        # Build LLM prompt
        system_prompt = (
            "You are a prompt engineer for AI image/video generation. "
            "Your task is to compose a single, well-formed master prompt that combines user intent, "
            "brand DNA, and style requirements into a clear, effective generation prompt. "
            "Output ONLY the final master prompt, nothing else."
        )
        
        user_message = (
            f"User input: '{user_prompt}'\n"
            f"Brand: {brand}\n"
            f"Brand DNA:\n{brand_context}\n"
        )
        
        if template_info:
            user_message += f"{template_info}\n"
        if style_info:
            user_message += f"{style_info}\n"
        if lighting_info:
            user_message += f"{lighting_info}\n"
        
        user_message += (
            f"Generate a master prompt for {engine_type} generation. "
            f"Make it specific, brand-aligned, and include quality descriptors. "
            f"{negative_constraint}"
        )
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add few-shot examples
        messages.extend(self.FEW_SHOT_EXAMPLES)
        
        # Add current request
        messages.append({"role": "user", "content": user_message})
        
        try:
            raw_response = self.llm_client.chat(messages).strip()
            
            # Clean up: remove any markdown formatting or extra text
            master_prompt = raw_response
            if master_prompt.startswith("```"):
                lines = master_prompt.split("\n")
                master_prompt = "\n".join(lines[1:-1]) if len(lines) > 2 else master_prompt
            
            # Remove common LLM artifacts
            master_prompt = master_prompt.strip()
            if master_prompt.startswith("Master Prompt:"):
                master_prompt = master_prompt.replace("Master Prompt:", "").strip()
            if master_prompt.startswith("Prompt:"):
                master_prompt = master_prompt.replace("Prompt:", "").strip()
            
            # Check if response looks like a format string or error
            if "," in master_prompt and len(master_prompt.split(",")) <= 3:
                if "master_prompt" in master_prompt.lower() or "negative_prompt" in master_prompt.lower() or "notes" in master_prompt.lower():
                    logger.warning(f"LLM returned format string instead of prompt: {master_prompt}")
                    raise ValueError("LLM returned invalid format")
            
            master_prompt = master_prompt.strip()
            
            if not master_prompt or len(master_prompt) < 10:
                logger.warning(f"LLM returned empty or too short prompt: {master_prompt}")
                raise ValueError("LLM returned invalid prompt")
            
            logger.info(f"Generated master prompt via LLM: {master_prompt[:100]}...")
            return master_prompt
            
        except Exception as e:
            logger.warning(f"LLM prompt generation failed, using template fallback: {e}")
            return self._generate_master_prompt_template(
                user_prompt=user_prompt,
                brand_snippets=brand_snippets,
                style_preset=style_preset,
                lighting_preset=lighting_preset
            )
    
    def _generate_master_prompt_template(
        self,
        user_prompt: str,
        brand_snippets: List[str],
        style_preset: Optional[str],
        lighting_preset: Optional[str],
        continuity_context: Optional[str] = None
    ) -> str:
        """
        Generate master prompt using template-based enhancement (fallback).
        
        Args:
            user_prompt: User's prompt
            brand_snippets: Brand DNA snippets
            style_preset: Style preset
            lighting_preset: Lighting preset
            continuity_context: Continuity context
            
        Returns:
            Enhanced prompt string
        """
        enhanced_parts = [user_prompt]
        
        if brand_snippets:
            brand_summary = " ".join([s[:100] for s in brand_snippets[:2]])
            enhanced_parts.append(f"Brand context: {brand_summary}")
        
        if style_preset and style_preset in self.STYLE_PRESETS:
            enhanced_parts.append(self.STYLE_PRESETS[style_preset])
        
        if lighting_preset and lighting_preset in self.LIGHTING_PRESETS:
            enhanced_parts.append(self.LIGHTING_PRESETS[lighting_preset])
        
        if continuity_context:
            enhanced_parts.append(f"Continuity: {continuity_context}")
        
        enhanced_parts.append("high quality, professional, detailed")
        
        return ", ".join(enhanced_parts)
    
    def get_brand_context(self, brand: str, market: Optional[str] = None) -> Optional[str]:
        """
        Get formatted brand context text (legacy method for compatibility).
        
        Args:
            brand: Brand name
            market: Optional market/region
            
        Returns:
            Formatted brand context string
        """
        try:
            query = f"brand essence tone of voice key messages target audience style"
            if market:
                query += f" {market}"
            
            results = self.rag_retrieval.retrieve(brand, query, top_k=5)
            
            if not results:
                return None
            
            context = f"Brand: {brand}\n"
            if market:
                context += f"Market: {market}\n"
            
            context += "\nBrand Knowledge:\n"
            for i, result in enumerate(results[:3], 1):
                snippet = result["text"][:200]
                context += f"{i}. {snippet}...\n"
            
            return context
            
        except Exception as e:
            logger.warning(f"Error getting brand context: {e}")
            return None
    
    def _extract_brand_dnai(self, brand: str, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract Brand DNAi structure from vector store (legacy method).
        
        Args:
            brand: Brand name
            market: Optional market/region
            
        Returns:
            Dict with brand DNA structure
        """
        try:
            query = f"brand essence tone of voice key messages target audience style"
            if market:
                query += f" {market}"
            
            results = self.rag_retrieval.retrieve(brand, query, top_k=5)
            
            if not results:
                return {}
            
            snippets = [r["text"] for r in results]
            
            return {
                "brand": brand,
                "market": market,
                "tone_of_voice": self._extract_tone(snippets),
                "key_messages": self._extract_messages(snippets),
                "target_audience": self._extract_audience(snippets),
                "brand_essence": self._extract_essence(snippets),
                "stylistic_keywords": self._extract_style_keywords(snippets),
                "raw_snippets": snippets
            }
            
        except Exception as e:
            logger.warning(f"Error extracting brand DNAi: {e}")
            return {}
    
    def _extract_tone(self, snippets: List[str]) -> str:
        """Extract tone of voice from snippets."""
        combined = " ".join(snippets[:3]).lower()
        
        tone_keywords = {
            "professional": ["professional", "expert", "reliable", "trustworthy"],
            "friendly": ["friendly", "warm", "approachable", "welcoming"],
            "innovative": ["innovative", "cutting-edge", "modern", "forward-thinking"],
            "luxury": ["luxury", "premium", "exclusive", "sophisticated"],
            "casual": ["casual", "relaxed", "easy", "simple"]
        }
        
        detected_tones = []
        for tone, keywords in tone_keywords.items():
            if any(kw in combined for kw in keywords):
                detected_tones.append(tone)
        
        return ", ".join(detected_tones[:2]) if detected_tones else "professional, authentic"
    
    def _extract_messages(self, snippets: List[str]) -> List[str]:
        """Extract key messages from snippets."""
        messages = []
        for snippet in snippets[:3]:
            sentences = snippet.split(".")
            for sentence in sentences:
                if 20 < len(sentence.strip()) < 200:
                    messages.append(sentence.strip())
                    if len(messages) >= 3:
                        break
            if len(messages) >= 3:
                break
        
        return messages[:3] if messages else ["Quality and innovation", "Customer-focused", "Trusted brand"]
    
    def _extract_audience(self, snippets: List[str]) -> str:
        """Extract target audience from snippets."""
        combined = " ".join(snippets[:2]).lower()
        
        if any(word in combined for word in ["consumer", "everyday", "family", "household"]):
            return "Everyday consumers and families"
        elif any(word in combined for word in ["professional", "business", "enterprise"]):
            return "Business professionals"
        elif any(word in combined for word in ["young", "millennial", "gen z"]):
            return "Young adults and millennials"
        else:
            return "Broad consumer audience"
    
    def _extract_essence(self, snippets: List[str]) -> str:
        """Extract brand essence from snippets."""
        if snippets:
            first_snippet = snippets[0]
            return first_snippet[:100] + "..." if len(first_snippet) > 100 else first_snippet
        return "A trusted brand delivering quality and value"
    
    def _extract_style_keywords(self, snippets: List[str]) -> List[str]:
        """Extract stylistic keywords from snippets."""
        combined = " ".join(snippets).lower()
        
        style_words = [
            "clean", "modern", "vibrant", "bold", "elegant", "minimalist",
            "colorful", "bright", "natural", "authentic", "dynamic", "fresh"
        ]
        
        found_keywords = [word for word in style_words if word in combined]
        
        return found_keywords[:5] if found_keywords else ["clean", "modern", "professional"]
    
    def get_available_templates(self, engine_type: str = "image") -> List[Dict[str, Any]]:
        """Get list of available templates."""
        templates = []
        for key, template in self.TEMPLATES.items():
            if engine_type == "image" and key in ["product_hero", "lifestyle"]:
                templates.append({
                    "id": key,
                    "name": template["name"],
                    "fields": template["fields"]
                })
            elif engine_type == "video" and key in ["promo_short", "social_clip"]:
                templates.append({
                    "id": key,
                    "name": template["name"],
                    "fields": template["fields"]
                })
        return templates
    
    def get_style_presets(self) -> List[Dict[str, str]]:
        """Get list of style presets."""
        return [{"id": k, "name": k.title(), "description": v} for k, v in self.STYLE_PRESETS.items()]
    
    def get_lighting_presets(self) -> List[Dict[str, str]]:
        """Get list of lighting presets."""
        return [{"id": k, "name": k.replace("_", " ").title(), "description": v} for k, v in self.LIGHTING_PRESETS.items()]


def create_prompt_orchestrator(vector_store: VectorStore, llm_client=None) -> PromptOrchestrator:
    """
    Factory function to create a prompt orchestrator.
    
    Args:
        vector_store: VectorStore instance
        llm_client: Optional LLM client for prompt generation
    """
    return PromptOrchestrator(vector_store, llm_client=llm_client)
