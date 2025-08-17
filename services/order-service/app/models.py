from typing import Optional
from sqlmodel import SQLModel, Field


class Order(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    item_name: str
    quantity: int
    notes: Optional[str] = None
    status: str = "PENDING"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    admin_action_at: Optional[str] = None
