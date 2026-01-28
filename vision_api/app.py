"""FastAPI service for queued YOLOv8 object detection with multi-tenant auth."""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, get_session
from .flows import detection_pipeline
from .models import Base, DetectionJob
from .schemas import JobResponse, JobStatus
from .storage import ensure_bucket, upload_bytes

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

TOKENS: dict[str, str] = {
    "tok-alice-secret": "tenant-alice",
    "tok-bob-secret": "tenant-bob",
}

bearer_scheme = HTTPBearer()


async def get_tenant(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    tenant = TOKENS.get(creds.credentials)
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")
    return tenant


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    ensure_bucket()
    yield
    await engine.dispose()


app = FastAPI(
    title="Queued Vision Detection API",
    description="Upload images for YOLOv8 detection. Results stored in DB, images in S3/MinIO.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Background job runner
# ---------------------------------------------------------------------------


async def _run_detection(job_id: str, image_bytes: bytes, confidence: float, model_size: str) -> None:
    from .database import async_session

    async with async_session() as session:
        job = await session.get(DetectionJob, job_id)
        if not job:
            return

        job.status = JobStatus.running
        await session.commit()

        try:
            # Run the Prefect flow (sync, so offload to thread)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: detection_pipeline(
                    image_bytes=image_bytes,
                    confidence_threshold=confidence,
                    model_size=model_size,
                ),
            )

            # Upload annotated image to S3
            annotated_key = f"{job.tenant_id}/{job_id}/annotated.jpg"
            annotated_url = upload_bytes(annotated_key, result["annotated_image_bytes"])

            job.detections = result["detections"]
            job.annotated_image_url = annotated_url
            job.status = JobStatus.completed
        except Exception as exc:
            job.error = str(exc)
            job.status = JobStatus.failed

        job.completed_at = datetime.now(timezone.utc).isoformat()
        await session.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/v1/detect", status_code=202)
async def create_detection(
    file: UploadFile = File(...),
    confidence: float = Form(0.25),
    model_size: str = Form("yolov8n"),
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Upload an image for object detection. Returns a job ID immediately."""
    image_bytes = await file.read()
    job_id = str(uuid.uuid4())

    # Upload original image to S3
    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
    original_key = f"{tenant}/{job_id}/original.{ext}"
    original_url = upload_bytes(original_key, image_bytes, content_type=file.content_type or "image/jpeg")

    job = DetectionJob(
        job_id=job_id,
        tenant_id=tenant,
        status=JobStatus.queued,
        created_at=datetime.now(timezone.utc).isoformat(),
        original_image_url=original_url,
    )
    session.add(job)
    await session.commit()

    asyncio.create_task(_run_detection(job_id, image_bytes, confidence, model_size))
    return {"job_id": job_id, "status": job.status}


@app.get("/v1/detections/{job_id}")
async def get_detection(
    job_id: str,
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> JobResponse:
    """Get full detection results for a job."""
    job = await session.get(DetectionJob, job_id)
    if not job or job.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@app.get("/v1/detections/{job_id}/status")
async def get_detection_status(
    job_id: str,
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Lightweight status-only check."""
    job = await session.get(DetectionJob, job_id)
    if not job or job.tenant_id != tenant:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job.job_id, "status": job.status}


@app.get("/v1/detections")
async def list_detections(
    status: JobStatus | None = None,
    tenant: str = Depends(get_tenant),
    session: AsyncSession = Depends(get_session),
) -> list[JobResponse]:
    """List all detection jobs for the authenticated tenant."""
    stmt = select(DetectionJob).where(DetectionJob.tenant_id == tenant)
    if status:
        stmt = stmt.where(DetectionJob.status == status)
    result = await session.execute(stmt)
    return [JobResponse.model_validate(r) for r in result.scalars().all()]
