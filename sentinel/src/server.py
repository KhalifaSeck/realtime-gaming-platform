"""
FastAPI server exposant l'agent Sentinel via HTTP.

Usage :
    cd sentinel
    uvicorn src.server:app --host 0.0.0.0 --port 8888
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from src.agent import ask


app = FastAPI(title="Sentinel AI", description="LangGraph agent over rtgaming platform", version="0.1.0")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(payload: AskRequest) -> AskResponse:
    answer = ask(payload.question)
    return AskResponse(question=payload.question, answer=answer)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8888, reload=True)