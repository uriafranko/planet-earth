from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_session_context

logger = get_logger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Model for JWT token payload data."""

    username: str | None = None


async def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.
    Usage:
    ```
    @app.get("/items/")
    def read_items(db: Session = Depends(get_db)):
        # use db session
    ```
    """
    with get_session_context() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenData | None:
    """Validate JWT token if auth is enabled, otherwise pass through.

    Usage:
    ```
    @app.get("/protected/")
    def protected_route(current_user: TokenData = Depends(get_current_user)):
        # Only accessible with valid token if auth is enabled
    ```
    """
    # If auth is disabled, return default user
    if not settings.ENABLE_AUTH:
        return TokenData(username="default")

    # Auth is enabled but no credentials provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode and validate the token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.exception("JWT validation failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    return token_data
