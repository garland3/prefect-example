"""FastMCP stdio server with 4 simulated experiment tools."""

import json
import math
import os
import random
from pathlib import Path

from fastmcp import FastMCP

STATE_FILE = Path(__file__).parent / ".experiment_state.json"

mcp = FastMCP("DOE Experiment Server")


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"parameters": {}, "results": [], "logs": []}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


@mcp.tool()
def set_parameters(temperature: float, pressure: float, catalyst_ratio: float) -> str:
    """Set experiment parameters.

    Args:
        temperature: Reactor temperature in Celsius (100-500).
        pressure: Reactor pressure in atm (1-50).
        catalyst_ratio: Catalyst-to-substrate ratio (0.01-1.0).
    """
    state = _load_state()
    state["parameters"] = {
        "temperature": temperature,
        "pressure": pressure,
        "catalyst_ratio": catalyst_ratio,
    }
    _save_state(state)
    return json.dumps({"status": "ok", "parameters": state["parameters"]})


@mcp.tool()
def run_simulation() -> str:
    """Run the reactor simulation with the currently set parameters. Returns yield percentage."""
    state = _load_state()
    p = state.get("parameters")
    if not p:
        return json.dumps({"error": "No parameters set. Call set_parameters first."})

    t, pr, cr = p["temperature"], p["pressure"], p["catalyst_ratio"]

    # Simulated physics: yield peaks around t=350, pr=25, cr=0.4
    yield_val = (
        100
        * math.exp(-((t - 350) ** 2) / 20000)
        * math.exp(-((pr - 25) ** 2) / 500)
        * math.exp(-((cr - 0.4) ** 2) / 0.08)
    )
    noise = random.gauss(0, 1.5)
    yield_val = max(0.0, min(100.0, yield_val + noise))

    result = {"yield_pct": round(yield_val, 4), "parameters": p}
    state["results"].append(result)
    _save_state(state)
    return json.dumps(result)


@mcp.tool()
def analyze_results() -> str:
    """Analyze all simulation results collected so far. Returns statistics."""
    state = _load_state()
    results = state.get("results", [])
    if not results:
        return json.dumps({"error": "No results to analyze."})

    yields = [r["yield_pct"] for r in results]
    best = max(results, key=lambda r: r["yield_pct"])
    stats = {
        "n_experiments": len(yields),
        "mean_yield": round(sum(yields) / len(yields), 4),
        "max_yield": round(max(yields), 4),
        "min_yield": round(min(yields), 4),
        "best_parameters": best["parameters"],
    }
    return json.dumps(stats)


@mcp.tool()
def log_experiment(note: str) -> str:
    """Log a free-text note about the experiment.

    Args:
        note: A text note to record.
    """
    state = _load_state()
    state["logs"].append(note)
    _save_state(state)
    return json.dumps({"status": "logged", "total_logs": len(state["logs"])})


if __name__ == "__main__":
    mcp.run(transport="stdio")
