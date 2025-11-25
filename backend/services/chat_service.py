"""
Brand Chat Service - Orchestrates chat with RAG, memory, and guardrails.
Uses chat_store, chat_llm, and memory_engine for clean separation.
"""
import logging
from typing import List, Dict, Optional, Literal
from .vector_store import VectorStore
from .rag_retrieval import RAGRetrieval
from .chat_store import ChatStore
from .chat_llm import ChatLLM
from .memory_engine import MemoryEngine
from .chat_prompts import (
    SYSTEM_PROMPT,
    TASK_PROMPTS,
    FEW_SHOT_EXAMPLES,
)

logger = logging.getLogger(__name__)

Intent = Literal["qa_brand", "creative_copy", "image_prompt", "video_prompt", "setup_or_onboarding", "small_talk"]


class BrandChatService:
    """
    Brand-aware chat service with RAG, multi-session memory, and guardrails.
    Orchestrates chat_store, chat_llm, memory_engine, and rag_retrieval.
    """
    
    # Guardrail: banned keywords (can be expanded)
    BANNED_KEYWORDS = [
        "hack", "exploit", "malware", "virus", "illegal", "harmful",
        "violence", "weapon", "drug", "porn", "explicit"
    ]
    
    def __init__(
        self,
        vector_store: VectorStore,
        llm_client=None,
        chat_store: Optional[ChatStore] = None,
        chat_llm: Optional[ChatLLM] = None,
        memory_engine: Optional[MemoryEngine] = None
    ):
        """
        Initialize brand chat service.
        
        Args:
            vector_store: VectorStore instance
            llm_client: Optional legacy LLMClient (for backward compatibility)
            chat_store: Optional ChatStore instance (creates default if None)
            chat_llm: Optional ChatLLM instance (creates default if None)
            memory_engine: Optional MemoryEngine instance (creates default if None)
        """
        self.vector_store = vector_store
        self.rag_retrieval = RAGRetrieval(vector_store, top_k=8)
        
        # Initialize chat components
        self.chat_store = chat_store or ChatStore()
        
        if chat_llm:
            self.chat_llm = chat_llm
        elif llm_client:
            # Create ChatLLM from legacy LLMClient
            from .chat_llm import ChatLLM
            self.chat_llm = ChatLLM(model_id=None)  # Will use default
            self.chat_llm._llm_client = llm_client  # Use legacy client
        else:
            self.chat_llm = ChatLLM()
        
        if memory_engine:
            self.memory_engine = memory_engine
        else:
            self.memory_engine = MemoryEngine(self.chat_llm)
    
    def check_guardrails(self, text: str) -> Optional[str]:
        """
        Check if user input violates guardrails.
        
        Args:
            text: User input text
            
        Returns:
            Refusal message if blocked, None if allowed
        """
        text_lower = text.lower()
        for keyword in self.BANNED_KEYWORDS:
            if keyword in text_lower:
                logger.warning(f"Blocked message containing banned keyword: {keyword}")
                return (
                    "I'm sorry, but I can't help with that request. "
                    "I'm designed to assist with brand-related questions, creative content, "
                    "and marketing tasks. How else can I help you today?"
                )
        return None
    
    def classify_intent(self, text: str) -> Intent:
        """Classify user intent using rules + LLM fallback."""
        lower = text.lower().strip()
        
        if any(k in lower for k in ["image", "visual", "banner", "hero image", "thumbnail", "key visual", "poster"]):
            return "image_prompt"
        
        if any(k in lower for k in ["video", "reel", "clip", "storyboard", "motion", "short form"]):
            return "video_prompt"
        
        if any(k in lower for k in ["post", "caption", "headline", "copy", "script", "email", "ad copy", "campaign idea", "tagline"]):
            return "creative_copy"
        
        if any(k in lower for k in ["who are you", "what can you do", "how to use", "help", "onboard", "getting started", "what is this"]):
            return "setup_or_onboarding"
        
        if any(k in lower for k in ["hi", "hello", "hey", "good morning", "good afternoon", "how are you"]):
            return "small_talk"
        
        # LLM fallback
        if self.chat_llm.is_available():
            try:
                classifier_messages = [
                    {
                        "role": "system",
                        "content": (
                            "Classify the user message into one of:\n"
                            "- qa_brand\n- creative_copy\n- image_prompt\n- video_prompt\n"
                            "- setup_or_onboarding\n- small_talk\n\n"
                            "Return ONLY the label, nothing else."
                        ),
                    },
                    {"role": "user", "content": text},
                ]
                label = self.chat_llm.chat(classifier_messages).strip().lower().replace(" ", "_")
                
                valid_intents = ["qa_brand", "creative_copy", "image_prompt", "video_prompt", "setup_or_onboarding", "small_talk"]
                if label in valid_intents:
                    return label
            except Exception as e:
                logger.warning(f"Intent classification error: {e}")
        
        return "qa_brand"
    
    def build_context(self, brand: Optional[str], query: str, intent: Intent) -> Dict:
        """Build Brand DNA context from RAG."""
        snippets = []
        sources = []
        
        if intent in ["qa_brand", "creative_copy", "image_prompt", "video_prompt"]:
            try:
                if brand:
                    results = self.rag_retrieval.retrieve(brand, query, top_k=8)
                else:
                    brands = self.vector_store.get_all_brands()
                    results = self.rag_retrieval.retrieve_multi_brand(
                        brands, query, top_k_per_brand=3, total_top_k=8
                    )
                
                for result in results:
                    text = result.get('text', '').strip()
                    if text:
                        snippets.append(text)
                        
                        source_brand = brand or result.get('metadata', {}).get('brand', 'Unknown')
                        score = result.get('score', 0.0)
                        
                        sources.append({
                            "brand": source_brand,
                            "snippet": text[:300] + ('...' if len(text) > 300 else ''),
                            "score": score
                        })
            
            except Exception as e:
                logger.error(f"Error building context: {e}")
        
        return {"snippets": snippets, "sources": sources}
    
    def build_llm_messages(
        self,
        session_summary: Optional[str],
        brand: Optional[str],
        intent: Intent,
        context_snippets: List[str],
        conversation_messages: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """Build LLM input messages with few-shot examples and context."""
        brand_label = brand or "the brand"
        
        context_text = (
            "\n".join(f"- {s[:200]}" for s in context_snippets[:5])
            if context_snippets else "No relevant Brand DNA snippets were found."
        )
        
        task_prompt_template = TASK_PROMPTS.get(intent, TASK_PROMPTS["qa_brand"])
        task_filled = task_prompt_template.format(brand_label=brand_label, context=context_text)
        
        base_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        
        base_messages.extend(FEW_SHOT_EXAMPLES)
        
        if session_summary:
            base_messages.append({
                "role": "system",
                "content": f"Conversation so far (summary, do NOT repeat verbatim):\n{session_summary}",
            })
        
        base_messages.append({"role": "system", "content": task_filled})
        
        # Get last 10-12 messages
        recent = [m for m in conversation_messages if m.get("role") in ["user", "assistant"]][-12:]
        
        return base_messages + recent
    
    def chat_session(
        self,
        session_id: Optional[str],
        brand: Optional[str],
        new_user_message: str,
        model_id: Optional[str] = None,
    ) -> Dict:
        """
        Session-aware chat with persistent memory and summaries.
        
        Args:
            session_id: Optional session ID (creates new if None)
            brand: Optional brand ID
            new_user_message: User's message
            
        Returns:
            Dict with session_id, answer, intent, brand, sources, debug info
        """
        # Check guardrails
        refusal = self.check_guardrails(new_user_message)
        if refusal:
            # Still create/update session, but return refusal
            if not session_id:
                session = self.chat_store.create_session(brand=brand)
                session_id = session["id"]
            
            self.chat_store.add_message(session_id, "user", new_user_message)
            self.chat_store.add_message(session_id, "assistant", refusal)
            
            return {
                "session_id": session_id,
                "answer": refusal,
                "intent": "small_talk",
                "brand": brand,
                "sources": [],
                "blocked": True
            }
        
        # Get or create session
        if session_id:
            session_data = self.chat_store.get_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
        else:
            session_data = self.chat_store.create_session(
                title=new_user_message[:80] + ("..." if len(new_user_message) > 80 else ""),
                brand=brand
            )
            session_id = session_data["id"]
        
        # Add user message
        self.chat_store.add_message(session_id, "user", new_user_message)
        
        # Get conversation history
        messages = self.chat_store.get_messages(session_id, limit=20)
        messages_list = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
            
        # Classify intent
        intent = self.classify_intent(new_user_message)
            
        # Build RAG context
        ctx = self.build_context(
            brand=brand or session_data.get("brand"),
            query=new_user_message,
            intent=intent
        )
            
        # Build LLM messages
        llm_messages = self.build_llm_messages(
            session_summary=session_data.get("summary"),
            brand=brand or session_data.get("brand"),
            intent=intent,
            context_snippets=ctx["snippets"],
            conversation_messages=messages_list
        )
            
        # Generate response
        # If model_id is provided, create a new ChatLLM instance with that model
        chat_llm_to_use = self.chat_llm
        if model_id and model_id != self.chat_llm.model_id:
            from .chat_llm import ChatLLM
            try:
                chat_llm_to_use = ChatLLM(model_id=model_id)
            except Exception as e:
                logger.warning(f"Failed to load model {model_id}, using default: {e}")
                chat_llm_to_use = self.chat_llm
        
        if not chat_llm_to_use.is_available():
            answer = "I'm sorry, but the chat model is not available. Please ensure a GGUF model is downloaded and placed in the models/text/ directory."
        else:
            try:
                answer = chat_llm_to_use.chat(llm_messages)
            except Exception as e:
                logger.error(f"LLM chat error: {e}")
                answer = f"I encountered an error while generating a response: {str(e)}"
        
        # Add assistant message
        self.chat_store.add_message(session_id, "assistant", answer)
        
        # Update summary if needed
        updated_messages = self.chat_store.get_messages(session_id)
        message_count = len(updated_messages)
        
        if self.memory_engine.should_summarize(message_count):
            logger.info(f"Generating summary for session {session_id}")
            summary = self.memory_engine.generate_summary([
                {"role": msg["role"], "content": msg["content"]}
                for msg in updated_messages
            ])
            if summary:
                self.chat_store.update_session(session_id, summary=summary)
        
        return {
            "session_id": session_id,
            "answer": answer,
            "intent": intent,
            "brand": brand or session_data.get("brand"),
            "sources": ctx["sources"],
            "debug": {
                "used_summary": session_data.get("summary") is not None,
                "snippet_count": len(ctx["snippets"])
            }
        }
