import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Base class for all SQLModel models with common fields."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": "now()"},
    )
    updated_at: datetime | None = Field(
        default=None,
        nullable=True,
    )
