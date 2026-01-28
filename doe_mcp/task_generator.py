"""Connect to MCP server via stdio, discover tools, and generate Prefect tasks."""

import asyncio
import json
import sys
import textwrap
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = str(Path(__file__).parent / "mcp_server.py")
OUTPUT_FILE = Path(__file__).parent / "generated_tasks.py"


async def discover_and_generate() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[SERVER_SCRIPT],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tools = tools_result.tools

    lines = [
        '"""Auto-generated Prefect tasks from MCP tool discovery."""',
        "",
        "import json",
        "import sys",
        "from pathlib import Path",
        "",
        "from mcp import ClientSession, StdioServerParameters",
        "from mcp.client.stdio import stdio_client",
        "from prefect import task",
        "import asyncio",
        "",
        f'SERVER_SCRIPT = str(Path(__file__).parent / "mcp_server.py")',
        "",
        "",
        "async def _call_tool(name: str, arguments: dict) -> str:",
        "    server_params = StdioServerParameters(",
        "        command=sys.executable,",
        '        args=[SERVER_SCRIPT],',
        "    )",
        "    async with stdio_client(server_params) as (r, w):",
        "        async with ClientSession(r, w) as session:",
        "            await session.initialize()",
        "            result = await session.call_tool(name, arguments)",
        "            return result.content[0].text",
        "",
    ]

    for tool in tools:
        name = tool.name
        desc = tool.description or ""
        schema = tool.inputSchema or {}
        props = schema.get("properties", {})
        required = set(schema.get("required", []))

        # Build function signature
        params = []
        for pname, pinfo in props.items():
            ptype = {"string": "str", "number": "float", "integer": "int", "boolean": "bool"}.get(
                pinfo.get("type", "string"), "str"
            )
            if pname in required:
                params.append(f"{pname}: {ptype}")
            else:
                default = pinfo.get("default", "None")
                params.append(f"{pname}: {ptype} = {default!r}")

        sig = ", ".join(params)
        args_dict = ", ".join(f'"{p}": {p}' for p in props)

        lines.append(f'@task(name="{name}")')
        lines.append(f"def {name}({sig}) -> str:")
        lines.append(f'    """{desc}"""')
        lines.append(f"    return asyncio.run(_call_tool(\"{name}\", {{{args_dict}}}))")
        lines.append("")
        lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines))
    print(f"Generated {len(tools)} tasks -> {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(discover_and_generate())
