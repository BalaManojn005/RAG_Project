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
        return {
            "error": "Question cannot be empty."
        }

    conversation_id = request.conversation_id

    # --------------------------------------------------------
    # Get or create conversation
    # --------------------------------------------------------

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
    # Previous messages
    # --------------------------------------------------------

    previous_messages = []

    if conversation:

        previous_messages = conversation.get(
            "messages",
            []
        )

    # --------------------------------------------------------
    # Save user message
    # --------------------------------------------------------

    add_message(
        conversation_id,
        "user",
        question,
    )

    # --------------------------------------------------------
    # Generate answer
    # --------------------------------------------------------

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
                "Ensure Ollama is running and the configured "
                "model is installed."
            ),
        ) from exc

    # --------------------------------------------------------
    # Extract result
    # --------------------------------------------------------

    answer = result.get(
        "answer",
        "I couldn't generate an answer.",
    )

    sources = result.get(
        "sources",
        []
    )

    # --------------------------------------------------------
    # Save assistant message
    # --------------------------------------------------------

    add_message(
        conversation_id,
        "assistant",
        answer,
        sources,
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

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

    # ========================================================
    # EMPTY QUESTION
    # ========================================================

    if not question:

        def empty_question():

            yield (
                "event: error\n"
                + "data: "
                + json.dumps(
                    {
                        "message": (
                            "Question cannot be empty."
                        )
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        return StreamingResponse(
            empty_question(),
            media_type="text/event-stream",
        )

    # ========================================================
    # GET OR CREATE CONVERSATION
    # ========================================================

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

    # ========================================================
    # PREVIOUS MESSAGES
    # ========================================================

    previous_messages = []

    if conversation:

        previous_messages = conversation.get(
            "messages",
            []
        )

    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    add_message(
        conversation_id,
        "user",
        question,
    )

    # ========================================================
    # RETRIEVAL ONLY
    #
    # IMPORTANT:
    # Do NOT call ask_question() here.
    #
    # ask_question() performs complete LLM generation.
    #
    # Streaming endpoint must:
    #
    # 1. Retrieve context
    # 2. Stream exactly one LLM generation
    # ========================================================

    try:

        prepared = prepare_streaming_question(
            question,
            conversation_messages=previous_messages,
        )

    except Exception as exc:

        # ----------------------------------------------------
        # IMPORTANT FIX
        #
        # Copy the exception message outside the generator.
        #
        # Python clears the "exc" exception variable after
        # leaving the except block.
        # ----------------------------------------------------

        error_detail = str(exc)

        def preparation_error():

            yield (
                "event: error\n"
                + "data: "
                + json.dumps(
                    {
                        "message": (
                            "Failed to prepare "
                            "the document context."
                        ),
                        "detail": error_detail,
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        return StreamingResponse(
            preparation_error(),
            media_type="text/event-stream",
        )

    # ========================================================
    # PREPARED DATA
    # ========================================================

    llm_question = prepared.get(
        "question",
        question,
    )

    context = prepared.get(
        "context",
        "",
    )

    sources = prepared.get(
        "sources",
        [],
    )

    # ========================================================
    # EMPTY CONTEXT
    #
    # Do not send empty context to the LLM.
    #
    # Otherwise the model could generate an answer using
    # its own knowledge.
    # ========================================================

    if not context.strip():

        fallback = (
            "I couldn't find that information "
            "in the document."
        )

        # ----------------------------------------------------
        # FIX:
        #
        # The old code incorrectly referenced:
        #
        # conversation_messages
        #
        # That variable does not exist inside this function.
        #
        # The correct variable is:
        #
        # previous_messages
        # ----------------------------------------------------

        if not sources and not previous_messages:

            fallback = (
                "Upload and index a document "
                "before asking a question."
            )

        # ----------------------------------------------------
        # Fallback streaming
        # ----------------------------------------------------

        def fallback_stream():

            # -----------------------------------------------
            # Conversation event
            # -----------------------------------------------

            yield (
                "event: conversation\n"
                + "data: "
                + json.dumps(
                    {
                        "conversation_id":
                            conversation_id
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

            # -----------------------------------------------
            # Token event
            # -----------------------------------------------

            yield (
                "event: token\n"
                + "data: "
                + json.dumps(
                    {
                        "content": fallback
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

            # -----------------------------------------------
            # Sources event
            # -----------------------------------------------

            yield (
                "event: sources\n"
                + "data: "
                + json.dumps(
                    {
                        "sources": sources
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

            # -----------------------------------------------
            # Save assistant response
            # -----------------------------------------------

            add_message(
                conversation_id,
                "assistant",
                fallback,
                sources,
            )

            # -----------------------------------------------
            # Done event
            # -----------------------------------------------

            yield (
                "event: done\n"
                + "data: "
                + json.dumps(
                    {
                        "conversation_id":
                            conversation_id
                    },
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

    # ========================================================
    # STREAM EXACTLY ONE LLM GENERATION
    # ========================================================

    def generate():

        full_answer = ""

        try:

            # ------------------------------------------------
            # Conversation event
            # ------------------------------------------------

            yield (
                "event: conversation\n"
                + "data: "
                + json.dumps(
                    {
                        "conversation_id":
                            conversation_id
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

            # ------------------------------------------------
            # Stream LLM tokens
            # ------------------------------------------------

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
                        {
                            "content": token
                        },
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )

            # ------------------------------------------------
            # Empty LLM response protection
            # ------------------------------------------------

            if not full_answer:

                full_answer = (
                    "I couldn't generate an answer."
                )

            # ------------------------------------------------
            # Sources event
            # ------------------------------------------------

            yield (
                "event: sources\n"
                + "data: "
                + json.dumps(
                    {
                        "sources": sources
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

            # ------------------------------------------------
            # Save assistant message
            # ------------------------------------------------

            add_message(
                conversation_id,
                "assistant",
                full_answer,
                sources,
            )

            # ------------------------------------------------
            # Done event
            # ------------------------------------------------

            yield (
                "event: done\n"
                + "data: "
                + json.dumps(
                    {
                        "conversation_id":
                            conversation_id
                    },
                    ensure_ascii=False,
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
                        "message": (
                            "Failed to stream "
                            "AI response."
                        ),
                        "detail": str(exc),
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

    # ========================================================
    # STREAMING RESPONSE
    # ========================================================

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no-cache",
        },
    )