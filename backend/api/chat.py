from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from backend.rag.rag_pipeline import (
    ask_question,
    prepare_streaming_question,
)

from backend.llm.llm_client import generate_answer_stream

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
    question = request.question.strip()

    if not question:
        return {"error": "Question cannot be empty."}

    conversation_id = request.conversation_id

    if conversation_id:
        conversation = get_conversation(conversation_id)

        if conversation is None:
            conversation = create_conversation("New Chat")
            conversation_id = conversation["id"]
    else:
        conversation = create_conversation("New Chat")
        conversation_id = conversation["id"]

    previous_messages = []

    if conversation:
        previous_messages = conversation.get("messages", [])

    add_message(
        conversation_id,
        "user",
        question,
    )

    try:
        result = ask_question(
            question,
            conversation_messages=previous_messages,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The answer service is unavailable. "
                "Ensure Ollama is running and the configured model is installed."
            ),
        ) from exc

    answer = result.get(
        "answer",
        "I couldn't generate an answer.",
    )

    sources = result.get("sources", [])

    add_message(
        conversation_id,
        "assistant",
        answer,
        sources,
    )

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "sources": sources,
    }


# ============================================================
# TRUE STREAMING CHAT ENDPOINT
# ============================================================

@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    question = request.question.strip()

    if not question:
        def empty_question():
            yield (
                "event: error\n"
                f"data: {json.dumps({'message': 'Question cannot be empty.'})}\n\n"
            )

        return StreamingResponse(
            empty_question(),
            media_type="text/event-stream",
        )

    # --------------------------------------------------------
    # Get or create conversation
    # --------------------------------------------------------

    conversation_id = request.conversation_id

    if conversation_id:
        conversation = get_conversation(conversation_id)

        if conversation is None:
            conversation = create_conversation("New Chat")
            conversation_id = conversation["id"]
    else:
        conversation = create_conversation("New Chat")
        conversation_id = conversation["id"]

    previous_messages = []

    if conversation:
        previous_messages = conversation.get("messages", [])

    # Save the user message before generation.
    add_message(
        conversation_id,
        "user",
        question,
    )

    # --------------------------------------------------------
    # Retrieval only
    # IMPORTANT: Do NOT call ask_question() here.
    # ask_question() performs a complete LLM generation.
    # --------------------------------------------------------

    try:
        prepared = prepare_streaming_question(
            question,
            conversation_messages=previous_messages,
        )
    except Exception as exc:
        def preparation_error():
            yield (
                "event: error\n"
                + "data: "
                + json.dumps(
                    {
                        "message": "Failed to prepare the document context.",
                        "detail": str(exc),
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        return StreamingResponse(
            preparation_error(),
            media_type="text/event-stream",
        )

    llm_question = prepared.get("question", question)
    context = prepared.get("context", "")
    sources = prepared.get("sources", [])

    # Empty context means retrieval could not provide an answer.
    # Do not send an empty context to the LLM because that would
    # unnecessarily allow a model-generated guess.
    if not context.strip():
        fallback = (
            "I couldn't find that information in the document."
        )

        if not sources:
            fallback = (
                "Upload and index a document before asking a question."
                if not conversation_messages and not prepared.get("context")
                else fallback
            )

        def fallback_stream():
            yield (
                "event: conversation\n"
                + "data: "
                + json.dumps(
                    {"conversation_id": conversation_id},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            yield (
                "event: token\n"
                + "data: "
                + json.dumps(
                    {"content": fallback},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            yield (
                "event: sources\n"
                + "data: "
                + json.dumps(
                    {"sources": sources},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            add_message(
                conversation_id,
                "assistant",
                fallback,
                sources,
            )
            yield (
                "event: done\n"
                + "data: "
                + json.dumps(
                    {"conversation_id": conversation_id},
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        return StreamingResponse(
            fallback_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no-cache",
            },
        )

    # --------------------------------------------------------
    # Stream exactly ONE LLM generation
    # --------------------------------------------------------

    def generate():
        full_answer = ""

        try:
            yield (
                "event: conversation\n"
                + "data: "
                + json.dumps(
                    {"conversation_id": conversation_id},
                    ensure_ascii=False,
                )
                + "\n\n"
            )

            for token in generate_answer_stream(
                llm_question,
                context,
            ):
                if not token:
                    continue

                full_answer += token

                yield (
                    "event: token\n"
                    + "data: "
                    + json.dumps(
                        {"content": token},
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )

            if not full_answer:
                full_answer = "I couldn't generate an answer."

            yield (
                "event: sources\n"
                + "data: "
                + json.dumps(
                    {"sources": sources},
                    ensure_ascii=False,
                )
                + "\n\n"
            )

            add_message(
                conversation_id,
                "assistant",
                full_answer,
                sources,
            )

            yield (
                "event: done\n"
                + "data: "
                + json.dumps(
                    {"conversation_id": conversation_id},
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        except Exception as exc:
            print("STREAMING ERROR:", repr(exc))

            yield (
                "event: error\n"
                + "data: "
                + json.dumps(
                    {
                        "message": "Failed to stream AI response.",
                        "detail": str(exc),
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no-cache",
        },
    )
