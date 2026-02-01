"""
Chat API routes for support system.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.user import User, UserRole
from app.models.chat import ChatMessage
from app.services.chat_service import ChatService
from app.middleware.auth import get_current_user


router = APIRouter(prefix="/api/chat", tags=["chat"])


# Schemas
class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_user_id: int = Field(default=None, description="User ID for the conversation (admin only)")


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""
    id: int
    user_id: int
    user_name: str
    message: str
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    """Schema for admin statistics."""
    total_messages: int
    total_users: int
    admin_count: int


# Helper function to check admin role
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for route access."""
    user_role_str = str(current_user.role.value) if hasattr(current_user.role, 'value') else str(current_user.role)
    if user_role_str.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Routes
@router.post("/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message.
    Regular users: message goes to their own conversation.
    Admins: must specify conversation_user_id to respond to a specific user.
    """
    # Check admin status - handle both enum and string comparison
    user_role_str = str(current_user.role.value) if hasattr(current_user.role, 'value') else str(current_user.role)
    is_admin = user_role_str.upper() == "ADMIN"
    
    print(f"[CHAT] User {current_user.id} role: {current_user.role} (str: {user_role_str}), is_admin: {is_admin}")
    
    # Determine which conversation this message belongs to
    if is_admin:
        if not message_data.conversation_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admins must specify conversation_user_id"
            )
        conversation_user_id = message_data.conversation_user_id
    else:
        # Regular users always message in their own conversation
        conversation_user_id = current_user.id
    
    message = ChatService.create_message(
        db=db,
        user_id=current_user.id,
        message=message_data.message,
        conversation_user_id=conversation_user_id,
        is_admin=is_admin
    )
    
    return ChatMessageResponse(
        id=message.id,
        user_id=message.user_id,
        user_name=message.user.full_name or message.user.email,
        message=message.message,
        is_admin=message.is_admin,
        created_at=message.created_at
    )


@router.get("/messages", response_model=List[ChatMessageResponse])
def get_messages(
    conversation_user_id: int = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat messages.
    Users see only their own conversation.
    Admins can specify conversation_user_id to see a specific user's conversation.
    Returns messages in chronological order (oldest first).
    """
    user_role_str = str(current_user.role.value) if hasattr(current_user.role, 'value') else str(current_user.role)
    is_admin = user_role_str.upper() == "ADMIN"
    
    # Non-admin users can only see their own conversation
    if not is_admin and conversation_user_id and conversation_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own messages"
        )
    
    messages = ChatService.get_messages(
        db=db,
        user_id=current_user.id,
        is_admin=is_admin,
        conversation_user_id=conversation_user_id,
        limit=limit,
        offset=offset
    )
    
    return [
        ChatMessageResponse(
            id=msg.id,
            user_id=msg.user_id,
            user_name=msg.user.full_name or msg.user.email,
            message=msg.message,
            is_admin=msg.is_admin,
            created_at=msg.created_at
        )
        for msg in messages
    ]


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chat message.
    Admins can delete any message, users can only delete their own.
    """
    ChatService.delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
    
    return None


@router.get("/admin/users", response_model=List[dict])
def get_users_with_messages(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of users with messages (admin only).
    """
    users = ChatService.get_users_with_messages(db=db)
    return users


@router.get("/admin/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get admin statistics (admin only).
    """
    stats = ChatService.get_admin_stats(db=db)
    return AdminStatsResponse(**stats)
