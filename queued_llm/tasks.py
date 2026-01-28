"""Prefect tasks for queued LLM chat completion."""

import asyncio
import random
import time

from prefect import task


@task(name="llm_chat_completion", retries=2)
async def llm_chat_completion(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
) -> dict:
    """Mock LLM chat completion task.

    Simulates latency and returns a canned response based on the last user message.
    Replace the body of this function with a real API call to use in production.
    """
    # Simulate variable LLM latency (1-4 seconds)
    latency = 1.0 + random.random() * 3.0
    await asyncio.sleep(latency)

    # Simulate occasional failures (5% chance) for retry demo
    if random.random() < 0.05:
        raise RuntimeError("Simulated transient LLM API error")

    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
    completion_tokens = random.randint(20, 80)

    return {
        "id": f"mock-{int(time.time()*1000)}",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        f"[MOCK] This is a simulated response to: "
                        f"'{last_user_msg[:80]}'. "
                        f"Latency was {latency:.1f}s."
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
