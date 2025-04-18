"""Audit log models for search queries and their results."""

import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseModel
from app.models.endpoint import Endpoint
from app.models.schema import Schema

if TYPE_CHECKING:
    from app.models.endpoint import Endpoint
    from app.models.schema import Schema

class Audit(BaseModel, table=True):
    """
    Audit log for a search query.

    Stores:
    - The search query string
    - Timestamp of the search
    - Total number of results returned
    - Related AuditResult records for each schema/endpoint that returned results
    """

    __tablename__ = "audits"  # type: ignore

    query: str = Field(index=True, description="The search query string")
    total_result_count: int = Field(default=0, description="Total number of results returned by the query")

    # Relationship to AuditResult
    results: list["AuditResult"] = Relationship(back_populates="audit")


class AuditResult(BaseModel, table=True):
    """
    Stores the result of a search for a specific schema and endpoint.

    - Links to the parent Audit record
    - References the schema and endpoint that returned results
    - Stores the number of results for this schema/endpoint
    """

    __tablename__ = "audit_results"  # type: ignore

    audit_id: uuid.UUID = Field(
        sa_column=__import__("sqlalchemy").Column(
            __import__("sqlalchemy").ForeignKey("audits.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    schema_id: uuid.UUID = Field(
        sa_column=__import__("sqlalchemy").Column(
            __import__("sqlalchemy").ForeignKey("schemas.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    endpoint_id: uuid.UUID = Field(
        sa_column=__import__("sqlalchemy").Column(
            __import__("sqlalchemy").ForeignKey("endpoints.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    result_count: int = Field(default=0, description="Number of results returned by this schema/endpoint")

    # Relationships
    audit: "Audit" = Relationship(back_populates="results")
    schema_obj: "Schema" = Relationship()
    endpoint: "Endpoint" = Relationship()
