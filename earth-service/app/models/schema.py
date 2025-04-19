from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.endpoint import Endpoint

class Schema(BaseModel, table=True):
    """Model for OpenAPI schemas.

    Based on the data model in the PRD:
    CREATE TABLE schemas (
      id UUID PRIMARY KEY,
      title TEXT,
      version TEXT,
      checksum TEXT UNIQUE,
      created_at TIMESTAMPTZ DEFAULT now()
    );
    """

    __tablename__ = "schemas"

    title: str = Field(index=True)
    version: str = Field(index=True)
    checksum: str = Field(unique=True, index=True)
    status: str | None = Field(index=True, nullable=True, default="idle")

    # Relationships
    endpoints: list["Endpoint"] = Relationship(
        back_populates="schema_obj",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class SchemaRead(BaseModel):
    """Schema read model (pydantic)."""

    title: str
    version: str
    checksum: str
    status: str


class SchemaCreate(SQLModel):
    """Schema create model (pydantic)."""

    title: str
    version: str
    checksum: str


class SchemaUpdate(SQLModel):
    """Schema update model (pydantic)."""

    title: str | None = None
    version: str | None = None


