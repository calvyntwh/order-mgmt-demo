from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel  # type: ignore


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Order(SQLModel, table=True):
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True)
    item_name: str
    quantity: int
    notes: str | None = None
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)
    admin_action_at: datetime | None = Field(default=None)


class OrderCreate(SQLModel):
    """Pydantic/SQLModel input model for creating orders.

    This centralizes validation so other modules can import the schema.
    """

    item_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., ge=1, le=100)
    notes: str | None = Field(default=None, max_length=1000)
