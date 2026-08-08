from fastapi import APIRouter
from pydantic import BaseModel

from backend.rag.rag_pipeline import ask_question

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(request: ChatRequest):

    answer = ask_question(request.question)

    return {
        "answer": answer
    }