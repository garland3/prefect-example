"""Prefect flow wrapping the LLM chat completion task."""

from prefect import flow

from .tasks import llm_chat_completion


@flow(name="chat_completion_pipeline")
async def chat_completion_pipeline(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
) -> dict:
    result = await llm_chat_completion(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return result
