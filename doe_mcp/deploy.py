"""Deploy the generated evaluation pipeline flow to a Prefect work pool."""

import importlib.util
import sys
from pathlib import Path

from prefect import deploy

# Dynamically import the generated flow
flow_path = Path(__file__).parent / "generated_flow.py"
if not flow_path.exists():
    print(f"Error: {flow_path} not found. Run flow_designer.py first.")
    sys.exit(1)

spec = importlib.util.spec_from_file_location("generated_flow", flow_path)
mod = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(flow_path.parent))
spec.loader.exec_module(mod)

if __name__ == "__main__":
    deploy(
        mod.evaluation_pipeline.to_deployment(
            name="doe-evaluation-deployment",
            work_pool_name="doe-pool",
        ),
    )
    print("Deployed evaluation_pipeline to work pool 'doe-pool'")
