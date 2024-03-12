from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.status import HTTP_403_FORBIDDEN
import os

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid authentication scheme."
        )
    api_key = os.getenv("API_KEY")
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid or expired token."
        )
    return credentials.credentials
