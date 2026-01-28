"""Use an LLM (via litellm) to design a Prefect flow from the generated tasks."""

import os
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion

load_dotenv(Path(__file__).parent.parent / ".env")

TASKS_FILE = Path(__file__).parent / "generated_tasks.py"
OUTPUT_FILE = Path(__file__).parent / "generated_flow.py"

SYSTEM_PROMPT = """\
You are a Prefect flow designer. Given auto-generated Prefect task functions,
write a single Python file that defines an `evaluation_pipeline` flow.

The flow must:
1. Accept parameters: temperature (float), pressure (float), catalyst_ratio (float).
2. Call set_parameters with those values.
3. Call run_simulation to get the yield.
4. Call log_experiment with a summary note.
5. Return the parsed result dict from run_simulation.

Import tasks from generated_tasks (relative import or same-directory import).
Use `from prefect import flow` and `import json`.
Output ONLY valid Python code, no markdown fences.
"""


def design_flow() -> None:
    if not TASKS_FILE.exists():
        raise FileNotFoundError(
            f"{TASKS_FILE} not found. Run task_generator.py first."
        )

    tasks_source = TASKS_FILE.read_text()
    model = os.environ.get("LITELLM_MODEL", "openai/gpt-oss-120b")
    api_base = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    api_key = os.environ.get("OPENROUTER_API_KEY")

    response = completion(
        model=model,
        api_base=api_base,
        api_key=api_key,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here are the generated tasks:\n\n"
                    f"```python\n{tasks_source}\n```\n\n"
                    "Write the evaluation_pipeline flow."
                ),
            },
        ],
    )

    code = response.choices[0].message.content.strip()
    # Strip markdown fences if the LLM included them anyway
    if code.startswith("```"):
        code = "\n".join(code.split("\n")[1:])
    if code.endswith("```"):
        code = "\n".join(code.split("\n")[:-1])

    OUTPUT_FILE.write_text(code + "\n")
    print(f"Flow written -> {OUTPUT_FILE}")


if __name__ == "__main__":
    design_flow()
