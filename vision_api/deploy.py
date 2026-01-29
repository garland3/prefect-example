"""Deploy the detection pipeline flow to a Prefect work pool."""

from prefect import deploy

from flows import detection_pipeline

if __name__ == "__main__":
    deploy(
        detection_pipeline.to_deployment(
            name="detection-deployment",
            work_pool_name="vision-pool",
            job_variables={
                "env": {
                    "S3_ENDPOINT": "http://localhost:9000",
                    "S3_ACCESS_KEY": "minioadmin",
                    "S3_SECRET_KEY": "minioadmin",
                    "S3_BUCKET": "vision-jobs",
                }
            },
        ),
    )
    print("Deployed detection_pipeline to work pool 'vision-pool'")
