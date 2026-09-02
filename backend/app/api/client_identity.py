from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException


def require_browser_client_id(
    x_client_id: Annotated[str | None, Header()] = None,
) -> UUID:
    if not x_client_id:
        raise HTTPException(status_code=400, detail="Identificador do navegador ausente.")
    try:
        return UUID(x_client_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Identificador do navegador invalido.") from error
