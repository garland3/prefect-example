"""Pydantic schemas for the vision detection API."""

from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Detection(BaseModel):
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class JobResponse(BaseModel):
    job_id: str
    tenant_id: str
    status: JobStatus
    created_at: str
    completed_at: str | None = None
    original_image_url: str | None = None
    annotated_image_url: str | None = None
    detections: list[Detection] | None = None
    error: str | None = None

    model_config = {"from_attributes": True}
