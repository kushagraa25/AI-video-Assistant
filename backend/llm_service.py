"""Mistral LLM client used by the summarizer and the RAG chat."""

import os

from langchain_mistralai import ChatMistralAI


def get_llm(temperature: float = 0.3) -> ChatMistralAI:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is not set in the .env file.")

    return ChatMistralAI(
        model=os.getenv("MISTRAL_MODEL", "open-mistral-nemo"),
        api_key=api_key,
        temperature=temperature,
    )
