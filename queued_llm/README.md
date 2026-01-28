# Queued LLM Chat Completions

FastAPI service that accepts OpenAI-style chat completion requests, queues each one as a Prefect flow run, and returns a job ID for polling.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | Submit a request. Returns `202` with `job_id`. |
| `GET` | `/v1/jobs/{job_id}` | Get status and result of a specific job. |
| `GET` | `/v1/jobs` | List all jobs. Optional `?status=completed` filter. |

## Run

```bash
uv run uvicorn queued_llm.app:app --reload --port 8000
```

## Example

```bash
# Submit
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}' | jq .

# Poll
curl -s http://localhost:8000/v1/jobs/<job_id> | jq .

# List completed
curl -s 'http://localhost:8000/v1/jobs?status=completed' | jq .
```

## How it works

1. `POST /v1/chat/completions` creates a job record and kicks off a background `asyncio.create_task` that runs the Prefect flow.
2. The flow calls `llm_chat_completion`, a mock Prefect task that simulates 1-4s latency and returns a canned response. Replace the task body with a real API call for production use.
3. The caller polls `GET /v1/jobs/{job_id}` until `status` is `completed` or `failed`.

Job statuses: `queued` → `running` → `completed` | `failed`.
