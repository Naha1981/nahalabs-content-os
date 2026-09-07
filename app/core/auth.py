from functools import lru_cache
import time
import jwt
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import get_settings

bearer = HTTPBearer(auto_error=True)


@lru_cache
def _jwks_url() -> str:
    return f"{get_settings().cognito_issuer}/.well-known/jwks.json"


class CognitoVerifier:
    def __init__(self) -> None:
        self._keys: dict | None = None
        self._loaded_at = 0.0

    async def _get_keys(self) -> dict:
        if self._keys and time.time() - self._loaded_at < 3600:
            return self._keys
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(_jwks_url())
            response.raise_for_status()
            self._keys = response.json()
            self._loaded_at = time.time()
            return self._keys

    async def verify(self, token: str) -> dict:
        settings = get_settings()
        try:
            header = jwt.get_unverified_header(token)
            keys = await self._get_keys()
            key = next((k for k in keys['keys'] if k['kid'] == header.get('kid')), None)
            if not key:
                self._keys = None
                keys = await self._get_keys()
                key = next((k for k in keys['keys'] if k['kid'] == header.get('kid')), None)
            if not key:
                raise ValueError('Unknown signing key')
            claims = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                issuer=settings.cognito_issuer,
                options={'verify_aud': False},
            )
            if claims.get('token_use') != 'access':
                raise ValueError('Expected Cognito access token')
            if claims.get('client_id') != settings.cognito_app_client_id:
                raise ValueError('Invalid client')
            return claims
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication token') from exc


verifier = CognitoVerifier()


async def get_current_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    return await verifier.verify(credentials.credentials)
