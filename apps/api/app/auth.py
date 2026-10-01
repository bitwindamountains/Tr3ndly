import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from tr3ndly.config import Settings, get_settings


async def require_operator(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Require `Authorization: Bearer <OPERATOR_TOKEN>` whenever a token is configured.

    Without a token (development only; production refuses to start) the API is open.
    """
    if settings.operator_token is None:
        return
    expected = settings.operator_token.get_secret_value()
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(
        supplied.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
