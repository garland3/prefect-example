"""End-to-end orchestrator: generate tasks, design flow, approve, run DOE."""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def step(label: str, cmd: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}\n")
    subprocess.run(cmd, check=True)


def main() -> None:
    python = sys.executable

    # Step 1: Generate Prefect tasks from MCP server
    step("Step 1: Discovering MCP tools -> generating Prefect tasks",
         [python, str(HERE / "task_generator.py")])

    # Step 2: LLM designs the flow
    step("Step 2: LLM designing Prefect flow",
         [python, str(HERE / "flow_designer.py")])

    # Show generated flow for review
    flow_file = HERE / "generated_flow.py"
    print(f"\n--- Generated flow ({flow_file}) ---")
    print(flow_file.read_text())
    print("--- End of generated flow ---\n")

    # Step 3: Human approval gate
    answer = input("Approve this flow and run DOE? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        sys.exit(0)

    # Step 4: Run DOE
    n_samples = int(input("Number of DOE sample points [10]: ").strip() or "10")
    step(f"Step 3: Running Latin Hypercube DOE with {n_samples} points",
         [python, str(HERE / "doe_runner.py"), str(n_samples)])

    print("\nDone.")


if __name__ == "__main__":
    main()
