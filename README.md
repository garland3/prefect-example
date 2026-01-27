# Prefect Example: Server + Worker + Job Submission

A minimal example showing how to run a self-hosted Prefect server, start a worker, deploy a flow, and submit a job.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## How It Works

Prefect has three main components:

1. **Server** — the API + UI that tracks flows, deployments, and runs
2. **Worker** — a long-running process that polls for scheduled work and executes it
3. **Flow** — your Python code decorated with `@flow` and `@task`

The workflow is: define a flow → deploy it to a work pool → a worker picks it up and runs it.

## Quick Start

### 1. Run the flow directly (no server needed)

```bash
uv run python example_flow.py
```

This runs the ETL pipeline locally in-process. Good for development and testing.

### 2. Run with the full server + worker setup

Open **three terminals**:

**Terminal 1 — Start the server:**

```bash
uv run prefect server start
```

The UI is at http://localhost:4200.

**Terminal 2 — Create a work pool and start a worker:**

```bash
export PREFECT_API_URL=http://localhost:4200/api
uv run prefect work-pool create my-process-pool --type process
uv run prefect worker start --pool my-process-pool
```

**Terminal 3 — Deploy and run:**

```bash
export PREFECT_API_URL=http://localhost:4200/api
uv run python deploy_flow.py
uv run prefect deployment run 'etl-pipeline/etl-deployment'
```

Check Terminal 2 — the worker picks up and executes the flow. Check the UI at http://localhost:4200 to see the run.

## Files

| File | Purpose |
|---|---|
| `example_flow.py` | Defines the ETL pipeline flow with three tasks |
| `deploy_flow.py` | Deploys the flow to the `my-process-pool` work pool |

## Key Concepts

- **`@task`** — a unit of work (a function). Tasks can be retried, cached, and observed independently.
- **`@flow`** — an orchestration function that calls tasks. Flows track state and can be deployed.
- **Work pool** — a named queue that workers poll for scheduled runs.
- **Worker** — a process that executes flow runs from a work pool.
- **Deployment** — a server-side record that associates a flow with a work pool and default parameters.
