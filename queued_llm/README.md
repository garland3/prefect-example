# Queued LLM Chat Completions

FastAPI service that accepts OpenAI-style chat completion requests, queues each one as a Prefect flow run, and returns a job ID for polling.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | Submit a request. Returns `202` with `job_id`. |
| `GET` | `/v1/jobs/{job_id}` | Get status and result of a specific job. |
| `GET` | `/v1/jobs/{job_id}/status` | Lightweight status check. |
| `GET` | `/v1/jobs` | List all jobs. Optional `?status=completed` filter. |

## Quick Start (Local Mode)

In local mode, flows run in-process via `asyncio.create_task`. Good for development.

```bash
# Install dependencies
uv sync

# Start the API
uv run uvicorn queued_llm.app:app --reload --port 8000
```

## Production Mode (Prefect Workers)

For production, run flows via Prefect workers polling a work pool. This gives you:
- Distributed execution across multiple workers
- Flow run visibility in Prefect UI
- Retries, concurrency limits, and scheduling

### 1. Start Prefect Server

```bash
# Terminal 1: Start the Prefect server
uv run prefect server start
```

Prefect UI: http://localhost:4200

### 2. Create a Work Pool

```bash
# Create a process-based work pool
uv run prefect work-pool create llm-pool --type process
```

### 3. Start a Worker

```bash
# Terminal 2: Start a worker polling the pool
uv run prefect worker start --pool llm-pool
```

### 4. Deploy the Flow

```bash
# Deploy the flow to the work pool
uv run python queued_llm/deploy.py
```

### 5. Start the API

```bash
# Terminal 3: Start the FastAPI server
uv run uvicorn queued_llm.app:app --port 8000
```

Now requests will be queued to the work pool and executed by the worker.

## Example

```bash
# Submit (include auth header)
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer tok-alice-secret" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}' | jq .

# Poll
curl -s -H "Authorization: Bearer tok-alice-secret" \
  http://localhost:8000/v1/jobs/<job_id> | jq .

# List completed
curl -s -H "Authorization: Bearer tok-alice-secret" \
  'http://localhost:8000/v1/jobs?status=completed' | jq .
```

## How it works

1. `POST /v1/chat/completions` creates a job record in the DB and triggers a flow run.
2. The flow calls `llm_chat_completion`, a mock Prefect task that simulates 1-4s latency. Replace the task body with a real API call for production.
3. The caller polls `GET /v1/jobs/{job_id}` until `status` is `completed` or `failed`.

Job statuses: `queued` → `running` → `completed` | `failed`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./queued_llm/jobs.db` | DB connection string |
| `PREFECT_API_URL` | `http://localhost:4200/api` | Prefect server URL (for worker mode) |
| `USE_WORKER_MODE` | `false` | Set to `true` to submit to work pool instead of running locally |
| `WORK_POOL_NAME` | `llm-pool` | Work pool name for worker mode |

## Multi-tenant Auth

Two demo tokens are hardcoded:

| Token | Tenant |
|---|---|
| `tok-alice-secret` | `tenant-alice` |
| `tok-bob-secret` | `tenant-bob` |

Alice cannot see Bob's jobs and vice versa.
