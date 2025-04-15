"""Model for API endpoints extracted from OpenAPI specifications."""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, text
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import BaseModel
from app.models.schema import Schema


class Endpoint(BaseModel, table=True):
    """Model for API endpoints extracted from OpenAPI specifications.

    Based on the data model in the PRD, with added vector embedding support:

    CREATE TABLE endpoints (
      id UUID PRIMARY KEY,
      schema_id UUID REFERENCES schemas(id) ON DELETE CASCADE,
      path TEXT,
      method TEXT,
      operation_id TEXT,
      hash TEXT,
      embedding_vector vector(384),
      created_at TIMESTAMPTZ DEFAULT now(),
      deleted_at TIMESTAMPTZ
    );
    CREATE UNIQUE INDEX ux_schema_path_method ON endpoints(schema_id, path, method);
    CREATE INDEX endpoints_embedding_vector_idx ON endpoints USING ivfflat (embedding_vector vector_cosine_ops);
    """

    __tablename__ = "endpoints"  # type: ignore

    # Add the unique constraint for schema_id, path, and method
    __table_args__ = (
        UniqueConstraint("schema_id", "path", "method", name="ux_schema_path_method"),
    )

    # Vector embedding stored as a PostgreSQL vector
    # This is stored as a string temporarily during migration
    embedding_vector: Any = Field(default=None, sa_column=Column(Vector(384)))

    # This is the actual vector column that will be used after migration
    # Note: SQLModel doesn't support pgvector directly, so we'll access it through raw SQL

    schema_id: uuid.UUID = Field(foreign_key="schemas.id", index=True)
    path: str = Field(index=True)
    method: str = Field(index=True)
    operation_id: str | None = Field(default=None, index=True)
    hash: str = Field(index=True)  # Hash for content-based comparison
    deleted_at: datetime | None = Field(default=None, nullable=True)

    # Relationship back to the schema
    schema: Schema = Relationship(back_populates="endpoints")


    # Additional fields not in the base schema but useful for the application
    summary: str | None = Field(default=None)
    description: str | None = Field(default=None)
    tags: str | None = Field(default=None)  # Stored as JSON string
    spec: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    @property
    def vector_data(self) -> dict[str, Any]:
        """Get metadata for vector search."""
        return {
            "schema_id": str(self.schema_id),
            "path": self.path,
            "method": self.method,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "spec": self.spec,
        }

    @staticmethod
    def cosine_similarity(embedding: list[float]):
        """SQL expression for cosine similarity search."""
        vector_str = ",".join(map(str, embedding))
        return text(f"embedding_vector <=> '[{vector_str}]'::vector")


class EndpointRead(BaseModel):
    """Endpoint read model (pydantic)."""

    schema_id: uuid.UUID
    path: str
    method: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: str | None = None
    deleted_at: datetime | None = None


class EndpointCreate(SQLModel):
    """Endpoint create model (pydantic)."""

    schema_id: str
    path: str
    method: str
    operation_id: str | None = None
    hash: str
    summary: str | None = None
    description: str | None = None
    tags: str | None = None


class EndpointUpdate(SQLModel):
    """Endpoint update model (pydantic)."""

    operation_id: str | None = None
    hash: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: str | None = None
    deleted_at: datetime | None = None


class EndpointSearchResult(SQLModel):
    """Model for endpoint search results including vector similarity score."""

    id: str
    schema_id: str
    path: str
    method: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: str | None = None
    score: float  # Similarity score from vector search
    spec: dict[str, Any] | None = None

