# DOE + MCP + Prefect

Proof-of-concept that auto-maps MCP tools to Prefect tasks, uses an LLM to design the flow, gates on human approval, and runs a Latin Hypercube DOE across the parameter space.

## Architecture

```
mcp_server.py          FastMCP stdio server (4 simulated reactor tools)
        │
task_generator.py      Connects via stdio, discovers tools, writes generated_tasks.py
        │
flow_designer.py       Sends tasks to LLM (OpenRouter), writes generated_flow.py
        │
doe_runner.py          Latin Hypercube sampling, calls the flow at each point
        │
run_all.py             Orchestrator: generate → design → approve → run
```

## Quick Start (Local Mode)

In local mode, flows run in-process. Good for development and small DOE runs.

```bash
# Install dependencies
uv add fastmcp mcp litellm scipy numpy python-dotenv

# Set your API key
echo 'OPENROUTER_API_KEY=sk-or-v1-...' > .env

# Run the full pipeline
uv run python doe_mcp/run_all.py
```

## Production Mode (Prefect Workers)

For large DOE runs, execute flows via Prefect workers for parallelism.

### 1. Start Prefect Server

```bash
# Terminal 1
uv run prefect server start
```

Prefect UI: http://localhost:4200

### 2. Create a Work Pool

```bash
uv run prefect work-pool create doe-pool --type process

# Optional: set concurrency limit for parallel DOE points
uv run prefect work-pool update doe-pool --concurrency-limit 4
```

### 3. Start Workers

```bash
# Terminal 2 (start multiple for parallelism)
uv run prefect worker start --pool doe-pool
```

### 4. Generate and Deploy

```bash
# Generate tasks from MCP server
uv run python doe_mcp/task_generator.py

# LLM designs the flow
uv run python doe_mcp/flow_designer.py

# Deploy the generated flow
uv run python doe_mcp/deploy.py
```

### 5. Run DOE with Worker Mode

```bash
# Run DOE, submitting each point to the work pool
USE_WORKER_MODE=true uv run python doe_mcp/doe_runner.py 20
```

Each DOE sample point becomes a separate flow run, executed in parallel by available workers.

## Individual Steps

```bash
# Step 1: Generate tasks from MCP server
uv run python doe_mcp/task_generator.py

# Step 2: LLM designs the flow
uv run python doe_mcp/flow_designer.py

# Step 3: Run DOE (default 10 samples)
uv run python doe_mcp/doe_runner.py 20
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Required. Your OpenRouter API key |
| `LITELLM_MODEL` | `openai/gpt-oss-120b` | Model to use for flow design |
| `OPENROUTER_API_BASE` | `https://openrouter.ai/api/v1` | API base URL |
| `PREFECT_API_URL` | `http://localhost:4200/api` | Prefect server URL |
| `USE_WORKER_MODE` | `false` | Set `true` to submit to work pool |
| `WORK_POOL_NAME` | `doe-pool` | Work pool name |

## Simulated Physics

The reactor simulation models yield as a function of three parameters:

- **temperature** (100–500 °C) — peaks around 350
- **pressure** (1–50 atm) — peaks around 25
- **catalyst_ratio** (0.01–1.0) — peaks around 0.4

Gaussian noise is added to each run. The DOE explores this space to find the optimum.
