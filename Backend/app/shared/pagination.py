   
from __future__ import annotations

import base64
import uuid
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class CursorMeta(BaseModel):
                                                              
    total: int | None = Field(None, description="Total count (None if too expensive to compute)")
    has_next: bool
    next_cursor: str | None = Field(None, description="Pass as ?cursor= in next request")
    limit: int


class PaginatedResponse(BaseModel, Generic[T]):
       
    success: bool = True
    data: list[T]
    meta: CursorMeta


def encode_cursor(item_id: uuid.UUID) -> str:
                                                     
    return base64.urlsafe_b64encode(str(item_id).encode()).decode()


def decode_cursor(cursor: str) -> uuid.UUID:
       
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
        return uuid.UUID(decoded)
    except Exception as exc:
        raise ValueError(f"Invalid cursor: {cursor!r}") from exc


def make_pagination_meta(
    items: list,
    limit: int,
    total: int | None = None,
) -> CursorMeta:
       
    has_next = len(items) > limit
    next_cursor = None
    if has_next and items:
                                                                      
        last = items[limit - 1]
        if hasattr(last, "id"):
            next_cursor = encode_cursor(last.id)

    return CursorMeta(
        total=total,
        has_next=has_next,
        next_cursor=next_cursor,
        limit=limit,
    )