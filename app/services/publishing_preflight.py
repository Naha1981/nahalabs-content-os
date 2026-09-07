from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from app.adapters.zernio import ZernioAdapter
from app.models import GeneratedAsset, MediaAsset, PublishingJob, SocialAccount
from app.services.storage import S3Storage


def _value(obj: Any, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _normalize(result: Any) -> dict:
    data = _value(result, 'data', result)
    return {
        'valid': bool(_value(data, 'valid', False)),
        'message': _value(data, 'message'),
        'errors': list(_value(data, 'errors', []) or []),
        'warnings': list(_value(data, 'warnings', []) or []),
    }

async def run_preflight(job: PublishingJob, asset: GeneratedAsset, media: MediaAsset, account: SocialAccount, adapter: ZernioAdapter, storage: S3Storage) -> dict:
    payload = job.payload or {}
    caption = payload.get('caption') or ''
    custom_content = payload.get('custom_content', {}).get(job.platform) if isinstance(payload.get('custom_content'), dict) else None
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory(prefix='nahalabs-preflight-') as td:
        local = str(Path(td) / Path(media.storage_key).name)
        storage.download(media.storage_key, local)
        media_url = await __import__('asyncio').to_thread(adapter.upload_media, local)
        result = await __import__('asyncio').to_thread(
            adapter.validate_post,
            content=caption,
            platform=job.platform,
            account_id=account.external_account_id,
            media_url=media_url,
            media_type='image' if media.mime_type.startswith('image/') else 'video',
            custom_content=custom_content,
        )
    normalized = _normalize(result)
    normalized['checked_at'] = datetime.now(timezone.utc).isoformat()
    return normalized
