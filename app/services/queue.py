import json
import boto3
from app.core.config import get_settings


class JobQueue:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = boto3.client('sqs', region_name=settings.aws_region)
        self.generation_queue = settings.aws_sqs_generation_queue_url
        self.media_queue = settings.aws_sqs_media_queue_url

    def enqueue_generation(self, payload: dict) -> None:
        if not self.generation_queue:
            return
        self.client.send_message(QueueUrl=self.generation_queue, MessageBody=json.dumps(payload, default=str))

    def enqueue_media(self, payload: dict) -> None:
        if not self.media_queue:
            return
        self.client.send_message(QueueUrl=self.media_queue, MessageBody=json.dumps(payload, default=str))
