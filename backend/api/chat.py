from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from backend.rag.rag_pipeline import ask_question

from backend.llm.llm_client import (
    generate_answer_stream,
)

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

    previous_messages = []

    if conversation:

        previous_messages = conversation.get(
            "messages",
            []
        )

    # --------------------------------------------------------
    # 4. Save user message
    # --------------------------------------------------------

    add_message(
        conversation_id,
        "user",
        question
    )

    # --------------------------------------------------------
    # 5. Run RAG pipeline
    # --------------------------------------------------------

    try:

        result = ask_question(
            question,
            conversation_messages=previous_messages
        )

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "The answer service is unavailable. "
                "Ensure Ollama is running and the "
                "configured model is installed."
            ),
        ) from exc

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
    # 7. Save assistant response + sources
    # --------------------------------------------------------

    add_message(
        conversation_id,
        "assistant",
        answer,
        sources
    )

    # --------------------------------------------------------
    # 8. Return response
    # --------------------------------------------------------

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources
    }


# ============================================================
# STREAMING CHAT ENDPOINT
# ============================================================

@router.post("/chat/stream")
def chat_stream(request: ChatRequest):

    # --------------------------------------------------------
    # 1. Validate question
    # --------------------------------------------------------

    question = request.question.strip()

    if not question:

        def empty_question():

            yield (
                "event: error\n"
                + "data: "
                + json.dumps(
                    {
                        "message":
                            "Question cannot be empty."
                    }
                )
                + "\n\n"
            )

        return StreamingResponse(
            empty_question(),
            media_type="text/event-stream"
        )

    # --------------------------------------------------------
    # 2. Get or create conversation
    # --------------------------------------------------------

    conversation_id = request.conversation_id

    if conversation_id:

        conversation = get_conversation(
            conversation_id
        )

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
    # 3. Get previous messages
    # --------------------------------------------------------

    previous_messages = []

    if conversation:

        previous_messages = conversation.get(
            "messages",
            []
        )

    # --------------------------------------------------------
    # 4. Save user message
    # --------------------------------------------------------

    add_message(
        conversation_id,
        "user",
        question
    )

    # --------------------------------------------------------
    # 5. Run RAG before streaming
    #
    # This keeps the existing RAG pipeline intact.
    # --------------------------------------------------------

    try:

        result = ask_question(
            question,
            conversation_messages=previous_messages
        )

    except Exception as exc:

        def service_error():

            yield (
                "event: error\n"
                + "data: "
                + json.dumps(
                    {
                        "message": (
                            "The answer service is unavailable. "
                            "Ensure Ollama is running and the "
                            "configured model is installed."
                        )
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

        return StreamingResponse(
            service_error(),
            media_type="text/event-stream"
        )

    # --------------------------------------------------------
    # 6. Extract result
    # --------------------------------------------------------

    answer = result.get(
        "answer",
        ""
    )

    sources = result.get(
        "sources",
        []
    )

    # --------------------------------------------------------
    # 7. Streaming generator
    # --------------------------------------------------------

    def generate():

        full_answer = ""

        try:

            # ------------------------------------------------
            # Send conversation ID
            # ------------------------------------------------

            yield (
                "event: conversation\n"
                + "data: "
                + json.dumps(
                    {
                        "conversation_id":
                            conversation_id
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

            # ------------------------------------------------
            # Stream generated response
            # ------------------------------------------------

            for token in generate_answer_stream(
                question,
                answer
            ):

                if not token:
                    continue

                full_answer += token

                yield (
                    "event: token\n"
                    + "data: "
                    + json.dumps(
                        {
                            "content": token
                        },
                        ensure_ascii=False
                    )
                    + "\n\n"
                )

            # ------------------------------------------------
            # Send sources
            # ------------------------------------------------

            yield (
                "event: sources\n"
                + "data: "
                + json.dumps(
                    {
                        "sources": sources
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

            # ------------------------------------------------
            # Save assistant response
            # ------------------------------------------------

            add_message(
                conversation_id,
                "assistant",
                full_answer,
                sources
            )

            # ------------------------------------------------
            # Done
            # ------------------------------------------------

            yield (
                "event: done\n"
                + "data: "
                + json.dumps(
                    {
                        "conversation_id":
                            conversation_id
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

        except Exception as exc:

            print(
                "STREAMING ERROR:",
                repr(exc)
            )

            yield (
                "event: error\n"
                + "data: "
                + json.dumps(
                    {
                        "message":
                            "Failed to stream AI response.",
                        "detail":
                            str(exc)
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

    # --------------------------------------------------------
    # 8. Return SSE response
    # --------------------------------------------------------

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no-cache"
        }
    )