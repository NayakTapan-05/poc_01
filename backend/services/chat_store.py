"""
Chat Store - Clean interface for chat session and message persistence.
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from common.chat_models import ChatSession, ChatMessage, SessionLocal

logger = logging.getLogger(__name__)


class ChatStore:
    """
    Chat store for managing sessions and messages.
    Provides clean CRUD operations for chat persistence.
    """
    
    def create_session(self, title: Optional[str] = None, brand: Optional[str] = None) -> Dict:
        """
        Create a new chat session.
        
        Args:
            title: Optional session title
            brand: Optional brand ID
            
        Returns:
            Dict with session data
        """
        db = SessionLocal()
        try:
            session = ChatSession(
                title=title or "Untitled conversation",
                brand=brand
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return {
                "id": session.id,
                "title": session.title,
                "brand": session.brand,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating session: {e}")
            raise
        finally:
            db.close()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session with message history.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with session and messages, or None if not found
        """
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                return None
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.index).all()
            
            return {
                "id": session.id,
                "title": session.title,
                "brand": session.brand,
                "summary": session.summary,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat() if msg.created_at else None
                    }
                    for msg in messages
                ]
            }
        finally:
            db.close()
    
    def list_sessions(self, limit: int = 100) -> List[Dict]:
        """
        List all chat sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dicts
        """
        db = SessionLocal()
        try:
            sessions = db.query(ChatSession).order_by(
                ChatSession.last_message_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": s.id,
                    "title": s.title or "Untitled conversation",
                    "brand": s.brand,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                    "last_message_at": s.last_message_at.isoformat() if s.last_message_at else None
                }
                for s in sessions
            ]
        finally:
            db.close()
    
    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        brand: Optional[str] = None,
        summary: Optional[str] = None,
        archived: Optional[bool] = None
    ) -> Optional[Dict]:
        """
        Update a chat session.
        
        Args:
            session_id: Session ID
            title: New title (if provided)
            brand: New brand (if provided)
            summary: New summary (if provided)
            archived: Archived status (if provided)
            
        Returns:
            Updated session dict, or None if not found
        """
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                return None
            
            if title is not None:
                session.title = title
            if brand is not None:
                session.brand = brand
            if summary is not None:
                session.summary = summary
            # Archived not implemented yet - requires database migration
            
            session.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(session)
            
            return {
                "id": session.id,
                "title": session.title,
                "brand": session.brand,
                "summary": session.summary,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating session: {e}")
            raise
        finally:
            db.close()
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False if not found
        """
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                return False
            
            db.delete(session)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting session: {e}")
            raise
        finally:
            db.close()
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        index: Optional[int] = None
    ) -> Dict:
        """
        Add a message to a session.
        
        Args:
            session_id: Session ID
            role: Message role ("user" or "assistant")
            content: Message content
            index: Optional message index (auto-incremented if not provided)
            
        Returns:
            Dict with message data
        """
        db = SessionLocal()
        try:
            # Get current message count if index not provided
            if index is None:
                existing_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).count()
                index = existing_count
            
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                index=index
            )
            db.add(message)
            
            # Update session
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.message_count = index + 1
                session.last_message_at = datetime.utcnow()
                session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(message)
            
            return {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "index": message.index,
                "created_at": message.created_at.isoformat() if message.created_at else None
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding message: {e}")
            raise
        finally:
            db.close()
    
    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session ID
            limit: Optional limit on number of messages (returns most recent)
            
        Returns:
            List of message dicts
        """
        db = SessionLocal()
        try:
            query = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.index)
            
            if limit:
                # Get last N messages
                total = query.count()
                offset = max(0, total - limit)
                messages = query.offset(offset).all()
            else:
                messages = query.all()
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        finally:
            db.close()

