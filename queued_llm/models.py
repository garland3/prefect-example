"""SQLAlchemy ORM model for the jobs table."""

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase

from .schemas import JobStatus


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.queued, index=True)
    created_at = Column(String(64), nullable=False)
    completed_at = Column(String(64), nullable=True)
    request = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
