"""
Prefect Example: Server + Worker + Job Submission

This file demonstrates:
1. Defining tasks and flows
2. Deploying a flow to a work pool
3. Running the flow via the deployment

SETUP (run these in separate terminals):
  Terminal 1: prefect server start
  Terminal 2: prefect worker start --pool my-process-pool
  Terminal 3: python example_flow.py
"""

from prefect import flow, task


@task(log_prints=True)
def fetch_data(url: str) -> dict:
    """Simulate fetching data from an API."""
    print(f"Fetching data from {url}...")
    return {"url": url, "records": 42, "status": "ok"}


@task(log_prints=True)
def transform_data(data: dict) -> dict:
    """Simulate transforming fetched data."""
    print(f"Transforming {data['records']} records...")
    data["records_transformed"] = data["records"] * 2
    return data


@task(log_prints=True)
def save_results(data: dict):
    """Simulate saving results."""
    print(f"Saved {data['records_transformed']} transformed records. Done!")


@flow(name="etl-pipeline", log_prints=True)
def etl_pipeline(source_url: str = "https://api.example.com/data"):
    """A simple ETL pipeline flow."""
    print("Starting ETL pipeline...")
    raw = fetch_data(source_url)
    transformed = transform_data(raw)
    save_results(transformed)
    print("ETL pipeline complete!")
    return transformed


if __name__ == "__main__":
    # Run the flow directly (no server needed for this)
    print("=== Running flow directly ===")
    result = etl_pipeline()
    print(f"Result: {result}")
