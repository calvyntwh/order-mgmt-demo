from __future__ import annotations

from pydantic import BaseModel, Field


class OrderForm(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., ge=1, le=100)
    notes: str | None = Field(default=None, max_length=1000)
