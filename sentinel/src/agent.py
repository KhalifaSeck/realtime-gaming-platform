"""LangGraph agent : ReAct pattern avec Ollama (Qwen3)."""
from __future__ import annotations

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from src.config import get_settings
from src.tools import ALL_TOOLS


SYSTEM_PROMPT = """You are Sentinel, an AI analyst for a realtime gaming intelligence platform.

You have access to tools that fetch real data:
- Snowflake marts (games, genres, publishers, price analysis, review analysis, session analysis, trending games)
- Neo4j Knowledge Graph (game similarities, publisher dominance anomalies)
- Redis live state (streaming aggregates: purchases, reviews, sessions, wishlist)
- Spark streaming anomalies (viral purchases, review bombs, CCU spikes)

Guidelines:
- ALWAYS call tools to fetch real data before answering — never invent numbers.
- Combine multiple tools when useful.
- Present numbers with context (game names, genre, publisher).
- If a user asks about a game by name, first fetch trending or genre stats to find the appid.
- Concise but insightful — highlight anomalies and patterns.
- Reply in the user's language.
"""


def build_agent():
    settings = get_settings()
    llm = ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )
    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )
    return agent


def ask(question: str) -> str:
    agent = build_agent()
    result = agent.invoke({"messages": [("user", question)]})
    return result["messages"][-1].content