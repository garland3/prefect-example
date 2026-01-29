# Queued Vision Detection API

Multi-tenant FastAPI service for YOLOv8 object detection. Images are stored in MinIO (S3-compatible), detection results (bounding boxes) in SQLite/Postgres.

## Architecture

```
POST /v1/detect (image upload)
    → save original to MinIO
    → queue Prefect flow
    → return job_id (202)

Background:
    → YOLOv8 inference (Prefect task)
    → save annotated image to MinIO
    → save bbox JSON to DB
    → mark job completed

GET /v1/detections/{job_id}        full results + image URLs
GET /v1/detections/{job_id}/status lightweight status check
GET /v1/detections?status=completed list jobs
```

## Quick Start (Local Mode)

In local mode, flows run in-process. Good for development.

```bash
# Start MinIO for image storage
docker compose -f vision_api/docker-compose.yml up -d

# Run the API (flows execute locally)
uv run uvicorn vision_api.app:app --reload --port 8001
```

MinIO console: http://localhost:9001 (minioadmin / minioadmin)

## Production Mode (Prefect Workers)

For production, run flows via Prefect workers. This gives you:
- Distributed execution across multiple GPU workers
- Flow run visibility in Prefect UI
- Retries, concurrency limits, and scheduling

### 1. Start Infrastructure

```bash
# Terminal 1: MinIO
docker compose -f vision_api/docker-compose.yml up -d

# Terminal 2: Prefect server
uv run prefect server start
```

Prefect UI: http://localhost:4200

### 2. Create a Work Pool

```bash
# Create a process-based work pool for vision tasks
uv run prefect work-pool create vision-pool --type process
```

### 3. Start Workers

Start one or more workers (e.g., on GPU machines):

```bash
# Terminal 3: Start a worker
uv run prefect worker start --pool vision-pool
```

For multiple workers on different machines:
```bash
# Machine 1
PREFECT_API_URL=http://prefect-server:4200/api uv run prefect worker start --pool vision-pool

# Machine 2
PREFECT_API_URL=http://prefect-server:4200/api uv run prefect worker start --pool vision-pool
```

### 4. Deploy the Flow

```bash
uv run python vision_api/deploy.py
```

### 5. Start the API

```bash
# Terminal 4: FastAPI server
USE_WORKER_MODE=true uv run uvicorn vision_api.app:app --port 8001
```

## Usage

```bash
# Submit an image
curl -X POST http://localhost:8001/v1/detect \
  -H "Authorization: Bearer tok-alice-secret" \
  -F "file=@photo.jpg" \
  -F "confidence=0.3" \
  -F "model_size=yolov8n"

# Check status
curl -H "Authorization: Bearer tok-alice-secret" \
  http://localhost:8001/v1/detections/<job_id>/status

# Get full results (detections + image URLs)
curl -H "Authorization: Bearer tok-alice-secret" \
  http://localhost:8001/v1/detections/<job_id>

# List completed jobs
curl -H "Authorization: Bearer tok-alice-secret" \
  'http://localhost:8001/v1/detections?status=completed'
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./vision_api/detections.db` | DB connection string |
| `S3_ENDPOINT` | `http://localhost:9000` | MinIO/S3 endpoint |
| `S3_ACCESS_KEY` | `minioadmin` | S3 access key |
| `S3_SECRET_KEY` | `minioadmin` | S3 secret key |
| `S3_BUCKET` | `vision-jobs` | Bucket for images |
| `PREFECT_API_URL` | `http://localhost:4200/api` | Prefect server URL |
| `USE_WORKER_MODE` | `false` | Set `true` to submit to work pool |
| `WORK_POOL_NAME` | `vision-pool` | Work pool name |

## Model sizes

Passed via the `model_size` form field:

| Value | Parameters | Speed | Accuracy |
|---|---|---|---|
| `yolov8n` | 3.2M | Fastest | Good |
| `yolov8s` | 11.2M | Fast | Better |
| `yolov8m` | 25.9M | Medium | High |
| `yolov8l` | 43.7M | Slow | Higher |
| `yolov8x` | 68.2M | Slowest | Best |

## Multi-tenant Auth

| Token | Tenant |
|---|---|
| `tok-alice-secret` | `tenant-alice` |
| `tok-bob-secret` | `tenant-bob` |
