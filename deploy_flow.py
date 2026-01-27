"""
Step 2: Deploy the flow to a work pool so a worker can pick it up.

Run AFTER the server is started:
  prefect server start

Usage:
  python deploy_flow.py
"""

from pathlib import Path
from example_flow import etl_pipeline

if __name__ == "__main__":
    # Deploy the flow from this local directory to the "my-process-pool" work pool
    etl_pipeline.from_source(
        source=str(Path(__file__).parent),
        entrypoint="example_flow.py:etl_pipeline",
    ).deploy(
        name="etl-deployment",
        work_pool_name="my-process-pool",
        parameters={"source_url": "https://api.example.com/production"},
    )
    print("Deployment created! Now run:")
    print("  prefect deployment run 'etl-pipeline/etl-deployment'")
