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

## Setup

```bash
# From the prefect-example root
uv add fastmcp mcp litellm scipy numpy python-dotenv

# Set your API key
echo 'OPENROUTER_API_KEY=sk-or-v1-...' > .env
```

## Usage

### Full pipeline

```bash
uv run python doe_mcp/run_all.py
```

This will:
1. Discover MCP tools and generate Prefect tasks
2. Send tasks to the LLM to design a flow
3. Show the generated flow for review
4. Prompt for approval before running
5. Run Latin Hypercube DOE across the parameter space

### Individual steps

```bash
# Step 1: Generate tasks from MCP server
uv run python doe_mcp/task_generator.py

# Step 2: LLM designs the flow
uv run python doe_mcp/flow_designer.py

# Step 3: Run DOE (default 10 samples)
uv run python doe_mcp/doe_runner.py 20
```

## Configuration

Environment variables (set in `.env` or export directly):

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Required. Your OpenRouter API key |
| `LITELLM_MODEL` | `openai/gpt-oss-120b` | Model to use for flow design |
| `OPENROUTER_API_BASE` | `https://openrouter.ai/api/v1` | API base URL |

## Simulated Physics

The reactor simulation models yield as a function of three parameters:

- **temperature** (100–500 °C) — peaks around 350
- **pressure** (1–50 atm) — peaks around 25
- **catalyst_ratio** (0.01–1.0) — peaks around 0.4

Gaussian noise is added to each run. The DOE explores this space to find the optimum.
