from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Order(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    item_name: str
    quantity: int
    notes: str | None = None
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)
    admin_action_at: datetime | None = Field(default=None)
