"""FastAPI server that queues LLM chat completion requests as Prefect flow runs."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, get_session
from .flows import chat_completion_pipeline
from .models import Base, Job
from .schemas import ChatRequest, JobResponse, JobStatus

# ---------------------------------------------------------------------------
# Auth — token-to-tenant mapping
# ---------------------------------------------------------------------------
# In production, replace this with a real token store / JWT validation.

TOKENS: dict[str, str] = {
    "tok-alice-secret": "tenant-alice",
    "tok-bob-secret": "tenant-bob",
}

bearer_scheme = HTTPBearer()


async def get_tenant(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Validate bearer token and return the tenant ID."""
    tenant = TOKENS.get(creds.credentials)
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return tenant


# ---------------------------------------------------------------------------
# App lifecycle — create tables on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Queued LLM Chat Completions",
    description="Submit chat completions that run as queued Prefect flows. Poll for results.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Background job runner
# ---------------------------------------------------------------------------


async def _run_job(job_id: str) -> None:
    """Background coroutine that runs the Prefect flow and updates the DB."""
    from .database import async_session

    async with async_session() as session:
        job = await session.get(Job, job_id)
        if not job:
            return

        job.status = JobStatus.running
        await session.commit()

        try:
            req = job.request
            messages = req.get("messages", [])
            result = await chat_completion_pipeline(
                model=req.get("model", "mock-gpt"),
                messages=messages,
                temperature=req.get("temperature", 0.7),
            )
            job.result = result
            job.status = JobStatus.completed
        except Exception as exc:
            job.error = str(exc)
            job.status = JobStatus.failed

        job.completed_at = datetime.now(timezone.utc).isoformat()
        await session.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/v1/chat/completions", status_code=202)
async def create_completion(
    req: ChatRequest,
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Submit a chat completion request. Returns a job ID immediately."""
    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        tenant_id=tenant,
        status=JobStatus.queued,
        created_at=datetime.now(timezone.utc).isoformat(),
        request=req.model_dump(),
    )
    session.add(job)
    await session.commit()
    asyncio.create_task(_run_job(job_id))
    return {"job_id": job_id, "status": job.status}


@app.get("/v1/jobs/{job_id}")
async def get_job(
    job_id: str,
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    """Look up the full record for a specific job."""
    job = await session.get(Job, job_id)
    if not job or job.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@app.get("/v1/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Lightweight status-only lookup for a specific job."""
    job = await session.get(Job, job_id)
    if not job or job.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job.job_id, "status": job.status}


@app.get("/v1/jobs")
async def list_jobs(
    status: JobStatus | None = None,
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> list[JobResponse]:
    """List all jobs for the authenticated tenant, optionally filtered by status."""
    stmt = select(Job).where(Job.tenant_id == tenant)
    if status:
        stmt = stmt.where(Job.status == status)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [JobResponse.model_validate(r) for r in rows]
