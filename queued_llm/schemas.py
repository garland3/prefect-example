"""Pydantic schemas shared across the app."""

from enum import Enum

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "mock-gpt"
    messages: list[ChatMessage]
    temperature: float = 0.7


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobResponse(BaseModel):
    job_id: str
    tenant_id: str
    status: JobStatus
    created_at: str
    completed_at: str | None = None
    request: ChatRequest | dict | None = None
    result: dict | None = None
    error: str | None = None

    model_config = {"from_attributes": True}
