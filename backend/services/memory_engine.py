"""
Memory Engine - Handles conversation summarization and memory management.
"""
import logging
from typing import List, Dict, Optional
from .chat_llm import ChatLLM

logger = logging.getLogger(__name__)


class MemoryEngine:
    """
    Memory engine for generating and updating conversation summaries.
    Uses LLM to create compact memory summaries.
    """
    
    def __init__(self, chat_llm: ChatLLM):
        """
        Initialize memory engine.
        
        Args:
            chat_llm: ChatLLM instance for summarization
        """
        self.chat_llm = chat_llm
        self.summary_interval = 8  # Generate summary every N messages
    
    def should_summarize(self, message_count: int) -> bool:
        """
        Check if conversation should be summarized.
        
        Args:
            message_count: Current message count
            
        Returns:
            True if summary should be generated
        """
        return message_count > 0 and message_count % self.summary_interval == 0
    
    def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate conversation summary from messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Summary text (bullet points)
        """
        if not self.chat_llm.is_available():
            logger.warning("LLM not available for summarization")
            return ""
        
        try:
            # Get recent messages (last 12)
            recent_messages = [
                m for m in messages 
                if m.get("role") in ["user", "assistant"]
            ][-12:]
            
            if not recent_messages:
                return ""
            
            summary_prompt = [
                {
                    "role": "system",
                    "content": (
                        "Summarize this conversation in 4-6 concise bullet points. "
                        "Focus on: brand discussed, key questions asked, decisions made, "
                        "preferences expressed, and any constraints mentioned. "
                        "Keep each bullet point to one line. "
                        "Output ONLY the bullet points, nothing else."
                    )
                }
            ]
            
            summary_prompt.extend(recent_messages)
            
            summary = self.chat_llm.chat(summary_prompt)
            
            # Clean up summary
            summary = summary.strip()
            if summary.startswith("-"):
                # Already formatted
                pass
            elif "\n" not in summary:
                # Single line, try to split by periods
                summary = summary.replace(". ", ".\n- ").replace("• ", "\n- ")
                if not summary.startswith("-"):
                    summary = "- " + summary
            
            logger.info(f"Generated summary: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""
    
    def update_summary(
        self,
        current_summary: Optional[str],
        new_messages: List[Dict[str, str]]
    ) -> str:
        """
        Update existing summary with new messages.
        
        Args:
            current_summary: Existing summary (if any)
            new_messages: New messages to incorporate
            
        Returns:
            Updated summary
        """
        if not new_messages:
            return current_summary or ""
        
        if not current_summary:
            # Generate fresh summary
            return self.generate_summary(new_messages)
        
        # Update existing summary
        if not self.chat_llm.is_available():
            return current_summary
        
        try:
            update_prompt = [
                {
                    "role": "system",
                    "content": (
                        "Update this conversation summary with new messages. "
                        "Keep it to 4-6 bullet points total. "
                        "Focus on the most important recent information. "
                        "Output ONLY the updated bullet points, nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": f"Current summary:\n{current_summary}\n\nNew messages:\n{self._format_messages(new_messages)}"
                }
            ]
            
            updated_summary = self.chat_llm.chat(update_prompt)
            return updated_summary.strip()
            
        except Exception as e:
            logger.error(f"Error updating summary: {e}")
            return current_summary
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for summary update."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

