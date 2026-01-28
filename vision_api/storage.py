"""S3-compatible object storage via boto3 (MinIO or AWS S3)."""

import os
from io import BytesIO

import boto3
from botocore.config import Config

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.environ.get("S3_BUCKET", "vision-jobs")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")


def _client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket() -> None:
    s3 = _client()
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except Exception:
        s3.create_bucket(Bucket=S3_BUCKET)


def upload_bytes(key: str, data: bytes, content_type: str = "image/jpeg") -> str:
    """Upload bytes to S3 and return the object URL."""
    s3 = _client()
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"{S3_ENDPOINT}/{S3_BUCKET}/{key}"


def download_bytes(key: str) -> bytes:
    s3 = _client()
    resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return resp["Body"].read()
