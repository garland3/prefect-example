"""SQLAlchemy ORM models for vision detection jobs."""

from sqlalchemy import JSON, Column, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase

from .schemas import JobStatus


class Base(DeclarativeBase):
    pass


class DetectionJob(Base):
    __tablename__ = "detection_jobs"

    job_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.queued, index=True)
    created_at = Column(String(64), nullable=False)
    completed_at = Column(String(64), nullable=True)
    original_image_url = Column(Text, nullable=True)
    annotated_image_url = Column(Text, nullable=True)
    detections = Column(JSON, nullable=True)  # list of {class_name, confidence, x1, y1, x2, y2}
    error = Column(Text, nullable=True)
