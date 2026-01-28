"""Auto-generated Prefect tasks from MCP tool discovery."""

import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from prefect import task
import asyncio

SERVER_SCRIPT = str(Path(__file__).parent / "mcp_server.py")


async def _call_tool(name: str, arguments: dict) -> str:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_SCRIPT],
    )
    async with stdio_client(server_params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            return result.content[0].text

@task(name="set_parameters")
def set_parameters(temperature: float, pressure: float, catalyst_ratio: float) -> str:
    """Set experiment parameters.

Args:
    temperature: Reactor temperature in Celsius (100-500).
    pressure: Reactor pressure in atm (1-50).
    catalyst_ratio: Catalyst-to-substrate ratio (0.01-1.0)."""
    return asyncio.run(_call_tool("set_parameters", {"temperature": temperature, "pressure": pressure, "catalyst_ratio": catalyst_ratio}))


@task(name="run_simulation")
def run_simulation() -> str:
    """Run the reactor simulation with the currently set parameters. Returns yield percentage."""
    return asyncio.run(_call_tool("run_simulation", {}))


@task(name="analyze_results")
def analyze_results() -> str:
    """Analyze all simulation results collected so far. Returns statistics."""
    return asyncio.run(_call_tool("analyze_results", {}))


@task(name="log_experiment")
def log_experiment(note: str) -> str:
    """Log a free-text note about the experiment.

Args:
    note: A text note to record."""
    return asyncio.run(_call_tool("log_experiment", {"note": note}))

