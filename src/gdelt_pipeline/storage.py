# Upload files to the Hugging Face bucket (it speaks the S3 language)
import boto3
from botocore.config import Config

from . import config


def client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config.HF_NAMESPACE}.s3.hf.co",
        aws_access_key_id=config.HF_S3_KEY_ID,
        aws_secret_access_key=config.HF_S3_SECRET,
        config=Config(
            region_name="us-east-1",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 10, "mode": "adaptive"},
            # the gateway can't parse the checksums newer boto3 sends by default
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


def upload(local_path, key):
    client().upload_file(str(local_path), config.HF_BUCKET, key)