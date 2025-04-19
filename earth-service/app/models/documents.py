import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlmodel import Column, Field, Relationship, SQLModel
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.models.base import BaseModel


class Document(BaseModel, table=True):
    __tablename__ = "documents" # type: ignore[assignment]

    title: str
    original_filename: str | None = None
    file_type: str  # "plain", "pdf", "docx"
    text: str | None = None
    chunks: list["DocumentChunk"] = Relationship(
        back_populates="document",
        sa_relationship=relationship(
            "DocumentChunk",
            back_populates="document",
            cascade="all, delete-orphan"
        )
    )

class DocumentChunk(BaseModel, table=True):
    __tablename__ = "document_chunks" # type: ignore[assignment]

    document_id: uuid.UUID = Field(
        sa_column=__import__("sqlalchemy").Column(
            __import__("sqlalchemy").ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    chunk_index: int
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    document: Document | None = Relationship(back_populates="chunks")
    embedding: Any = Field(default=None, sa_column=Column(Vector(settings.EMBEDDING_DIMENSION)))


class DocumentSearchRequest(SQLModel):
    query: str
    top_k: int = 10
    created_at: str | None = None  # ISO format string

class DocumentSearchResult(SQLModel):
    document_id: str
    chunk_id: str
    title: str
    chunk_text: str
    document_text: str | None
    score: float
    created_at: datetime
