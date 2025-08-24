from typing import List
from fastapi import APIRouter
from models.schemas import (
    ConversationOut, 
    ConversationCreateRequest, 
    ConversationUpdateRequest,
    MessageOut,
    APIResponse
)
from services.conversation_service import conversation_service
from services.message_service import message_service

router = APIRouter(prefix="/chat/api", tags=["conversations"])

@router.post("/conversations", response_model=ConversationOut)
def create_conversation(request: ConversationCreateRequest):
    """Tạo conversation mới với title"""
    return conversation_service.create_conversation(request)

@router.get("/conversations", response_model=List[ConversationOut])
def get_conversations():
    """Lấy danh sách conversations với thông tin chi tiết"""
    return conversation_service.get_all_conversations()

@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation_detail(conversation_id: int):
    """Lấy chi tiết một conversation"""
    return conversation_service.get_conversation_detail(conversation_id)

@router.get("/messages/{conversation_id}", response_model=List[MessageOut])
def get_messages(conversation_id: int):
    """Lấy tin nhắn của một conversation"""
    return message_service.get_messages(conversation_id)

@router.put("/conversations/{conversation_id}/title", response_model=APIResponse)
def update_conversation_title(conversation_id: int, request: ConversationUpdateRequest):
    """Cập nhật title của conversation"""
    result = conversation_service.update_conversation_title(conversation_id, request.title)
    return APIResponse(message=result["message"], data=result)

@router.delete("/conversations/{conversation_id}", response_model=APIResponse)
def delete_conversation(conversation_id: int):
    """Xóa conversation và tất cả messages"""
    result = conversation_service.delete_conversation(conversation_id)
    return APIResponse(message=result["message"], data=result)