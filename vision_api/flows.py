"""Prefect flow for the detection pipeline."""

from prefect import flow

from .tasks import run_yolov8_detection


@flow(name="detection_pipeline")
def detection_pipeline(
    image_bytes: bytes,
    confidence_threshold: float = 0.25,
    model_size: str = "yolov8n",
) -> dict:
    return run_yolov8_detection(
        image_bytes=image_bytes,
        confidence_threshold=confidence_threshold,
        model_size=model_size,
    )
