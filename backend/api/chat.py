from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.rag.rag_pipeline import ask_question

from backend.history.history_manager import (
    create_conversation,
    get_conversation,
    add_message,
)


router = APIRouter()


# ============================================================
# CHAT REQUEST
# ============================================================

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


# ============================================================
# CHAT ENDPOINT
# ============================================================

@router.post("/chat")
def chat(request: ChatRequest):

    # --------------------------------------------------------
    # 1. Validate question
    # --------------------------------------------------------

    question = request.question.strip()

    if not question:
        return {
            "error": "Question cannot be empty."
        }


    # --------------------------------------------------------
    # 2. Get or create conversation
    # --------------------------------------------------------

    conversation_id = request.conversation_id

    if conversation_id:

        conversation = get_conversation(
            conversation_id
        )

        # Invalid conversation ID
        # → create a new conversation

        if conversation is None:

            conversation = create_conversation(
                "New Chat"
            )

            conversation_id = conversation["id"]

    else:

        conversation = create_conversation(
            "New Chat"
        )

        conversation_id = conversation["id"]


    # --------------------------------------------------------
    # 3. Get previous conversation history
    # --------------------------------------------------------

    # IMPORTANT:
    # Get history BEFORE adding the current question.
    #
    # This prevents the current question from being
    # treated as previous conversation context.

    previous_messages = []

    if conversation:

        previous_messages = conversation.get(
            "messages",
            []
        )


    # --------------------------------------------------------
    # 4. Save current user message
    # --------------------------------------------------------

    add_message(
        conversation_id,
        "user",
        question
    )


    # --------------------------------------------------------
    # 5. Run context-aware RAG pipeline
    # --------------------------------------------------------

    result = ask_question(
        question,
        conversation_messages=previous_messages
    )


    # --------------------------------------------------------
    # 6. Extract answer and sources
    # --------------------------------------------------------

    answer = result.get(
        "answer",
        "I couldn't generate an answer."
    )

    sources = result.get(
        "sources",
        []
    )


    # --------------------------------------------------------
    # 7. Save ONLY answer text to history
    # --------------------------------------------------------

    add_message(
        conversation_id,
        "assistant",
        answer
    )


    # --------------------------------------------------------
    # 8. Return response to frontend
    # --------------------------------------------------------

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources
    }