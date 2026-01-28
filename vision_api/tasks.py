"""Prefect tasks for YOLOv8 object detection."""

from io import BytesIO

from PIL import Image
from prefect import task
from ultralytics import YOLO


@task(name="run_yolov8_detection", retries=1)
def run_yolov8_detection(
    image_bytes: bytes,
    confidence_threshold: float = 0.25,
    model_size: str = "yolov8n",
) -> dict:
    """Run YOLOv8 inference on an image.

    Returns dict with 'detections' (list of bbox dicts) and 'annotated_image_bytes'.
    """
    model = YOLO(f"{model_size}.pt")

    img = Image.open(BytesIO(image_bytes)).convert("RGB")

    results = model(img, conf=confidence_threshold)
    result = results[0]

    detections = []
    for box in result.boxes:
        cls_id = int(box.cls[0])
        detections.append({
            "class_name": result.names[cls_id],
            "confidence": round(float(box.conf[0]), 4),
            "x1": round(float(box.xyxy[0][0]), 1),
            "y1": round(float(box.xyxy[0][1]), 1),
            "x2": round(float(box.xyxy[0][2]), 1),
            "y2": round(float(box.xyxy[0][3]), 1),
        })

    # Render annotated image
    annotated = result.plot()  # numpy BGR array
    annotated_img = Image.fromarray(annotated[..., ::-1])  # BGR -> RGB
    buf = BytesIO()
    annotated_img.save(buf, format="JPEG", quality=90)
    annotated_bytes = buf.getvalue()

    return {
        "detections": detections,
        "annotated_image_bytes": annotated_bytes,
    }
