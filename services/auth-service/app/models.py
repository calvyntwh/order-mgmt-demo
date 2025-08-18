
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, sa_column_kwargs={"unique": True})
    password_hash: str
    is_admin: bool = False
    created_at: str | None = None
    last_login: str | None = None
