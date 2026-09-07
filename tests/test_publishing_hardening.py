import hashlib, hmac
from app.api.v1.webhooks import verify_signature


def test_zernio_signature_valid():
    body = b'{"id":"evt_1","event":"post.published"}'
    secret = 'secret'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, signature, secret)


def test_zernio_signature_invalid():
    assert not verify_signature(b'{}', 'bad', 'secret')
