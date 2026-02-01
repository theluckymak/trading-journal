"""
Chat service for support messages.
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.chat import ChatMessage
from app.models.user import User, UserRole


class ChatService:
    """Service for managing support chat messages."""
    
    @staticmethod
    def create_message(
        db: Session,
        user_id: int,
        message: str,
        conversation_user_id: int,
        is_admin: bool = False
    ) -> ChatMessage:
        """
        Create a new chat message.
        
        Args:
            db: Database session
            user_id: ID of the user sending the message
            message: Message content
            conversation_user_id: ID of the user whose conversation this belongs to
            is_admin: Whether the message is from an admin
            
        Returns:
            Created chat message
        """
        if not message or not message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        chat_message = ChatMessage(
            user_id=user_id,
            conversation_user_id=conversation_user_id,
            message=message.strip(),
            is_admin=is_admin
        )
        
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        # Eagerly load the user relationship to avoid lazy loading issues
        _ = chat_message.user
        
        return chat_message
    
    @staticmethod
    def get_messages(
        db: Session,
        user_id: int,
        is_admin: bool,
        conversation_user_id: int = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Get chat messages with user information.
        Admins can see all messages or filter by conversation_user_id.
        Users only see messages in their own conversation.
        
        Args:
            db: Database session
            user_id: ID of the requesting user
            is_admin: Whether the requesting user is an admin
            conversation_user_id: Filter messages for specific user's conversation (admin only)
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of chat messages
        """
        query = db.query(ChatMessage).options(joinedload(ChatMessage.user))
        
        if is_admin:
            # Admin can filter by specific conversation or see all
            if conversation_user_id:
                query = query.filter(ChatMessage.conversation_user_id == conversation_user_id)
        else:
            # Users only see their own conversation
            query = query.filter(ChatMessage.conversation_user_id == user_id)
        
        messages = query\
            .order_by(ChatMessage.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))
    
    @staticmethod
    def get_message_count(db: Session) -> int:
        """
        Get total count of chat messages.
        
        Args:
            db: Database session
            
        Returns:
            Total message count
        """
        return db.query(ChatMessage).count()
    
    @staticmethod
    def delete_message(
        db: Session,
        message_id: int,
        user_id: int,
        user_role: UserRole
    ) -> bool:
        """
        Delete a chat message (admins can delete any, users can delete own).
        
        Args:
            db: Database session
            message_id: ID of the message to delete
            user_id: ID of the user requesting deletion
            user_role: Role of the user
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException if message not found or unauthorized
        """
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Check permissions: admin can delete any, user can only delete own
        if user_role != UserRole.ADMIN and message.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this message"
            )
        
        db.delete(message)
        db.commit()
        
        return True
    
    @staticmethod
    def get_users_with_messages(db: Session) -> List[dict]:
        """
        Get list of users who have sent messages.
        
        Args:
            db: Database session
            
        Returns:
            List of users with their message counts
        """
        from sqlalchemy import func
        
        users = db.query(
            User.id,
            User.full_name,
            User.email,
            func.count(ChatMessage.id).label('message_count'),
            func.max(ChatMessage.created_at).label('last_message_at')
        ).join(
            ChatMessage, ChatMessage.conversation_user_id == User.id
        ).group_by(
            User.id
        ).order_by(
            func.max(ChatMessage.created_at).desc()
        ).all()
        
        return [
            {
                "id": user.id,
                "full_name": user.full_name or user.email,
                "email": user.email,
                "message_count": user.message_count,
                "last_message_at": user.last_message_at
            }
            for user in users
        ]
    
    @staticmethod
    def get_admin_stats(db: Session) -> dict:
        """
        Get admin statistics for the chat system.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with statistics
        """
        total_messages = db.query(ChatMessage).count()
        total_users = db.query(User).filter(User.is_active == True).count()
        admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).count()
        
        return {
            "total_messages": total_messages,
            "total_users": total_users,
            "admin_count": admin_count
        }
