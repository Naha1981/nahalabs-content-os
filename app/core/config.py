from functools import lru_cache
from typing import Annotated
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False, extra='ignore')

    app_env: str = 'development'
    app_name: str = 'NahaLabs Content OS API'
    api_prefix: str = '/api/v1'
    log_level: str = 'INFO'

    database_url: str
    redis_url: str

    aws_region: str = 'af-south-1'
    aws_s3_bucket: str
    aws_s3_upload_expiry_seconds: int = 900
    aws_sqs_generation_queue_url: str | None = None
    aws_sqs_media_queue_url: str | None = None

    cognito_region: str
    cognito_user_pool_id: str
    cognito_app_client_id: str

    zernio_api_key: str | None = None
    kie_api_base_url: str = ''
    kie_api_key: str | None = None
    kie_submit_path: str = '/v1/generations'
    kie_status_path: str = '/v1/generations/{job_id}'
    kie_default_model: str = 'auto'
    generation_demo_mode: bool = True
    generation_max_cost_per_asset: float = 0.50
    higgsfield_api_base_url: str = ''
    higgsfield_api_key: str | None = None
    higgsfield_submit_path: str = '/v1/generations'
    higgsfield_status_path: str = '/v1/generations/{job_id}'
    higgsfield_demo_enabled: bool = False
    mpt_enabled: bool = False
    mpt_root: str = ''
    mpt_python: str = 'python'
    mpt_timeout_seconds: int = 1200
    zernio_api_base_url: str = 'https://zernio.com/api/v1'
    zernio_webhook_secret: str | None = None

    max_upload_bytes: int = 524_288_000
    allowed_video_mime_types: Annotated[list[str], NoDecode] = ['video/mp4', 'video/quicktime', 'video/webm']
    allowed_image_mime_types: Annotated[list[str], NoDecode] = ['image/jpeg', 'image/png', 'image/webp']

    @field_validator('allowed_video_mime_types', 'allowed_image_mime_types', mode='before')
    @classmethod
    def split_csv(cls, value):
        if isinstance(value, str):
            return [x.strip() for x in value.split(',') if x.strip()]
        return value

    @property
    def cognito_issuer(self) -> str:
        return f'https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}'


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
