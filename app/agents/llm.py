from __future__ import annotations

import logging
from contextlib import suppress

from openai import APIError, AuthenticationError, AsyncOpenAI, OpenAIError

from app.config import get_settings


logger = logging.getLogger("mak.llm")

SYSTEM_PROMPT = """You are the Summarizer agent in a knowledge-management RAG system.
Answer only from the supplied context. Use compact citations in square brackets, e.g. [D1-C3].
If the context does not support the answer, say what is missing instead of guessing."""


def has_llm() -> bool:
    return bool(get_settings().openai_api_key)


async def generate_answer(question: str, context_blocks: list[str]) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        return extractive_answer(question, context_blocks)

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    context = "\n\n".join(context_blocks)
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question:\n{question}\n\nContext:\n{context}"},
            ],
        )
        return response.choices[0].message.content or "I could not produce an answer from the supplied context."
    except AuthenticationError:
        logger.warning("OpenAI authentication failed. Falling back to deterministic extractive answer.")
    except (APIError, OpenAIError) as exc:
        logger.warning("OpenAI answer generation failed: %s. Falling back to deterministic extractive answer.", exc)
    finally:
        with suppress(Exception):
            await client.close()
    return extractive_answer(question, context_blocks)


def extractive_answer(question: str, context_blocks: list[str]) -> str:
    if not context_blocks:
        return "I do not have enough cited context to answer that yet."

    selected = []
    for block in context_blocks[:3]:
        citation, _, content = block.partition("\n")
        sentences = [part.strip() for part in content.strip().split(". ") if part.strip()]
        sentence = next(
            (part for part in sentences if "Filtered possible prompt-injection" not in part),
            "",
        )
        if sentence:
            selected.append(f"{sentence.rstrip('.')} {citation.strip()}.")

    if not selected:
        return "I found related sources, but not enough clear evidence to answer confidently."
    return " ".join(selected)
