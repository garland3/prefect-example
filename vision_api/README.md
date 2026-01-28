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

## Setup

```bash
# Start MinIO
docker compose -f vision_api/docker-compose.yml up -d

# Run the API
uv run uvicorn vision_api.app:app --reload --port 8001
```

MinIO console: http://localhost:9001 (minioadmin / minioadmin)

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

## Model sizes

Passed via the `model_size` form field:

| Value | Parameters | Speed | Accuracy |
|---|---|---|---|
| `yolov8n` | 3.2M | Fastest | Good |
| `yolov8s` | 11.2M | Fast | Better |
| `yolov8m` | 25.9M | Medium | High |
| `yolov8l` | 43.7M | Slow | Higher |
| `yolov8x` | 68.2M | Slowest | Best |
