from app.schemas.publishing import ApprovalCreate, PublishCreate

def test_approval_is_scoped():
    x=ApprovalCreate(scope='batch', allowed_platforms=['instagram'], allowed_content_types=['video'])
    assert x.scope == 'batch'; assert x.allowed_platforms == ['instagram']

def test_publish_requires_asset_and_account_ids():
    import uuid
    x=PublishCreate(generated_asset_id=uuid.uuid4(), social_account_id=uuid.uuid4())
    assert x.scheduled_at is None
