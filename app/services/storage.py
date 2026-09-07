from __future__ import annotations
import uuid
from pathlib import Path
import boto3
from botocore.config import Config
from app.core.config import get_settings

class S3Storage:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.aws_s3_bucket
        self.client = boto3.client('s3', region_name=settings.aws_region, config=Config(signature_version='s3v4'))
        self.expiry = settings.aws_s3_upload_expiry_seconds

    def object_key(self, business_id: uuid.UUID, asset_id: uuid.UUID, filename: str) -> str:
        safe_name = Path(filename).name.replace('/', '_').replace('\\', '_')
        return f'private/businesses/{business_id}/assets/{asset_id}/{safe_name}'

    def presigned_put(self, key: str, mime_type: str) -> str:
        return self.client.generate_presigned_url('put_object', Params={'Bucket': self.bucket, 'Key': key, 'ContentType': mime_type}, ExpiresIn=self.expiry)

    def head(self, key: str) -> dict:
        return self.client.head_object(Bucket=self.bucket, Key=key)

    def presigned_get(self, key: str, expiry: int = 300) -> str:
        return self.client.generate_presigned_url('get_object', Params={'Bucket': self.bucket, 'Key': key}, ExpiresIn=expiry)

    def download(self, key: str, destination: str) -> str:
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, key, destination)
        return destination

    def upload_file(self, local_path: str, key: str, content_type: str) -> None:
        self.client.upload_file(local_path, self.bucket, key, ExtraArgs={'ContentType': content_type, 'ServerSideEncryption': 'AES256'})
