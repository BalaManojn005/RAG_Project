from fastapi import APIRouter, HTTPException

from backend.history.history_manager import (
    get_all_conversations,
    get_conversation,
    delete_conversation,
)

router = APIRouter()


# ============================================================
# GET ALL CONVERSATIONS
# ============================================================

@router.get("/history")
def get_history():
    """
    Return all saved conversations.
    """

    conversations = get_all_conversations()

    return {
        "conversations": conversations
    }


# ============================================================
# GET SINGLE CONVERSATION
# ============================================================

@router.get("/history/{conversation_id}")
def get_history_conversation(
    conversation_id: str
):
    """
    Return one conversation with all messages.
    """

    conversation = get_conversation(
        conversation_id
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return conversation


# ============================================================
# DELETE CONVERSATION
# ============================================================

@router.delete("/history/{conversation_id}")
def remove_history_conversation(
    conversation_id: str
):
    """
    Delete one conversation.
    """

    deleted = delete_conversation(
        conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "message": "Conversation deleted successfully",
        "conversation_id": conversation_id
    }