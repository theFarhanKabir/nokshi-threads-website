import argparse
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from openai import APIError, OpenAI
from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_base import KnowledgeBase, Passage

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
MODEL = "openai/gpt-oss-120b"
SYSTEM_PROMPT = (
    "You are the Nokshi Threads legal information assistant. Answer the user's "
    "question directly using relevant retrieved passages as evidence. "
    "Combine relevant facts and explain them in clear, concise words. Treat "
    "research documents as references and Nokshi Threads documents as "
    "assignment-specific, not general facts. If evidence is insufficient, say "
    "so instead of guessing. Do not reveal private reasoning. For legal "
    "questions, provide information, not legal advice. Do not claim currentness "
    "unless the documents establish it. Output only the answer in plain text: "
    "no source lists, filenames, citations, tables, markdown formatting, "
    "prefaces, or extra commentary."
)
logger = logging.getLogger("nokshi.api")
load_dotenv(PROJECT_ROOT / ".env")


class ChatMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1500)


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    message: str = Field(min_length=1, max_length=1500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=6)


class ChatResponse(BaseModel):
    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.knowledge_base = KnowledgeBase(KNOWLEDGE_DIR)
    yield


app = FastAPI(title="Nokshi Threads API", lifespan=lifespan)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nokshi-threads-api"}


def _format_passages(passages: list[Passage]) -> str:
    if not passages:
        return "No relevant passages were found in the provided documents."
    return "\n\n".join(
        f"Source: {passage.group}/{passage.source}\n{passage.text}"
        for passage in passages
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    api_key = os.getenv("GROQ_APIKEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Chat is not configured. Set GROQ_APIKEY in the server .env file.",
        )

    knowledge_base: KnowledgeBase = request.app.state.knowledge_base
    passages = knowledge_base.search(payload.message)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *[
            {"role": item.role, "content": item.content}
            for item in payload.history
        ],
        {
            "role": "user",
            "content": (
                f"Question: {payload.message}\n\n"
                f"Retrieved document passages:\n{_format_passages(passages)}"
            ),
        },
    ]

    try:
        with OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        ) as client:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.2,
                max_completion_tokens=500,
            )
    except APIError as error:
        logger.warning("Groq request failed: %s", type(error).__name__)
        raise HTTPException(
            status_code=502,
            detail="The Groq request failed. Check the server configuration and try again.",
        ) from error

    if not response.choices or not response.choices[0].message.content:
        raise HTTPException(
            status_code=502,
            detail="Groq returned an empty response. Please try again.",
        )

    return ChatResponse(answer=response.choices[0].message.content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Nokshi Threads API.")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload the API when backend files change.",
    )
    args = parser.parse_args()

    options: dict[str, object] = {
        "app": "backend.main:app",
        "host": os.getenv("API_HOST", "127.0.0.1"),
        "port": int(os.getenv("API_PORT", "4001")),
        "reload": args.reload,
    }
    if args.reload:
        options["reload_dirs"] = [str(Path(__file__).resolve().parent)]

    uvicorn.run(**options)


if __name__ == "__main__":
    main()
