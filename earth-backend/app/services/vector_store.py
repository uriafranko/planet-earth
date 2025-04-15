"""Vector store service for storing and retrieving vector embeddings.

This module provides an abstract interface for vector stores and an implementation
for PostgreSQL with the pgvector extension.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_session_context
from app.models.endpoint import Endpoint

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Class for storing vector search results."""

    id: str
    score: float
    metadata: dict[str, Any]


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Add a vector to the store.

        Args:
            vector_id: Unique identifier for the vector
            embedding: Vector embedding
            metadata: Metadata to store with the vector
        """

    @abstractmethod
    def update(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Update a vector in the store.

        Args:
            vector_id: Unique identifier for the vector
            embedding: New vector embedding
            metadata: New metadata
        """

    @abstractmethod
    def delete(self, vector_id: str) -> None:
        """Delete a vector from the store.

        Args:
            vector_id: Unique identifier for the vector to delete
        """

    @abstractmethod
    def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Perform a similarity search.

        Args:
            query_embedding: Query vector
            k: Number of results to return
            filters: Optional filters to apply

        Returns:
            List of search results
        """

    @abstractmethod
    def get(self, vector_id: str) -> SearchResult | None:
        """Get a vector by ID.

        Args:
            vector_id: Unique identifier for the vector

        Returns:
            Search result or None if not found
        """

    @abstractmethod
    def count(self) -> int:
        """Get the number of vectors in the store.

        Returns:
            Count of vectors
        """


class PostgresVectorStore(VectorStore):
    """Vector store implementation using PostgreSQL with pgvector extension.

    This implementation stores vectors directly in the PostgreSQL database along with
    the endpoint data, eliminating the need for a separate vector database.
    """

    def __init__(
        self,
        embedding_dimension: int = 384,  # Default for all-MiniLM-L6-v2
    ):
        """Initialize the PostgreSQL vector store.

        Args:
            embedding_dimension: Dimension of the embeddings
        """
        self.embedding_dimension = embedding_dimension
        logger.info(f"Using PostgreSQL pgvector store with dimension {embedding_dimension}")

    def _update_vector(
        self,
        session: Session,
        vector_id: str,
        embedding: list[float],
    ) -> None:
        """Update the vector embedding for an endpoint.

        Args:
            session: SQLAlchemy session
            vector_id: UUID of the endpoint
            embedding: Vector embedding
        """
        # Store embedding as JSON string temporarily for migration
        embedding_json = json.dumps(embedding)

        # Convert embedding to vector format
        vector_str = ",".join(map(str, embedding))
        sql = text(
            """
            UPDATE endpoints
            SET
                embedding = :embedding_json,
                embedding_vector = :vector::vector
            WHERE id = :id
            """
        )

        session.execute(
            sql,
            {
                "id": vector_id,
                "embedding_json": embedding_json,
                "vector": f"[{vector_str}]",
            },
        )

    def add(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Add a vector to the store."""
        with get_session_context() as session:
            # Check if the endpoint exists
            endpoint = session.get(Endpoint, vector_id)
            if not endpoint:
                logger.warning(f"Endpoint with ID {vector_id} not found, cannot add vector")
                return

            # Update the vector
            self._update_vector(session, vector_id, embedding)
            session.commit()

    def update(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Update a vector in the store."""
        # Same implementation as add since we're using upsert semantics
        self.add(vector_id, embedding, metadata)

    def delete(self, vector_id: str) -> None:
        """Delete a vector from the store."""
        with get_session_context() as session:
            # We don't actually delete the endpoint, just null out the vector
            sql = text(
                """
                UPDATE endpoints
                SET
                    embedding = NULL,
                    embedding_vector = NULL
                WHERE id = :id
                """
            )
            session.execute(sql, {"id": vector_id})
            session.commit()

    def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Perform a similarity search.

        Uses cosine similarity with pgvector.
        """
        with get_session_context() as session:
            # Convert embedding to vector format
            vector_str = ",".join(map(str, query_embedding))

            # Start building the query
            sql = """
                SELECT
                    e.id,
                    e.schema_id,
                    e.path,
                    e.method,
                    e.operation_id,
                    e.summary,
                    e.description,
                    e.tags,
                    e.spec,
                    s.title as schema_title,
                    s.version as schema_version,
                    1 - (embedding_vector <=> :vector::vector) as similarity
                FROM 
                    endpoints e
                JOIN
                    schemas s ON e.schema_id = s.id
                WHERE
                    e.deleted_at IS NULL AND
                    e.embedding_vector IS NOT NULL
            """

            # Add filters if provided
            params = {"vector": f"[{vector_str}]"}
            if filters:
                conditions = []
                for key, value in filters.items():
                    if key == "schema_id" and value:
                        conditions.append("e.schema_id = :schema_id")
                        params["schema_id"] = value
                    # Add more filters as needed

                if conditions:
                    sql += " AND " + " AND ".join(conditions)

            # Add order by and limit
            sql += """
                ORDER BY similarity DESC
                LIMIT :limit
            """
            params["limit"] = k

            # Execute the query
            results = session.execute(text(sql), params).fetchall()

            # Format the results
            search_results = []
            for row in results:
                # Convert row to dict
                row_dict = {col: getattr(row, col) for col in row.keys()}

                # Extract metadata
                metadata = {
                    "schema_id": str(row.schema_id),
                    "path": row.path,
                    "method": row.method,
                    "operation_id": row.operation_id,
                    "summary": row.summary,
                    "description": row.description,
                    "tags": row.tags,
                    "schema_title": row.schema_title,
                    "schema_version": row.schema_version,
                    "spec": row.spec,
                }

                search_results.append(
                    SearchResult(
                        id=str(row.id),
                        score=float(row.similarity),
                        metadata=metadata,
                    )
                )

            return search_results

    def get(self, vector_id: str) -> SearchResult | None:
        """Get a vector by ID."""
        with get_session_context() as session:
            # Query the endpoint and its vector
            sql = """
                SELECT 
                    e.id,
                    e.schema_id,
                    e.path,
                    e.method,
                    e.operation_id,
                    e.summary,
                    e.description,
                    e.tags,
                    e.spec,
                    s.title as schema_title,
                    s.version as schema_version,
                    e.embedding_vector
                FROM 
                    endpoints e
                JOIN
                    schemas s ON e.schema_id = s.id
                WHERE
                    e.id = :id
            """

            result = session.execute(text(sql), {"id": vector_id}).first()

            if not result:
                return None

            # Convert row to dict
            row_dict = {col: getattr(result, col) for col in result.keys()}

            # Extract metadata
            metadata = {
                "schema_id": str(result.schema_id),
                "path": result.path,
                "method": result.method,
                "operation_id": result.operation_id,
                "summary": result.summary,
                "description": result.description,
                "tags": result.tags,
                "schema_title": result.schema_title,
                "schema_version": result.schema_version,
                "spec": result.spec,
            }

            return SearchResult(
                id=str(result.id),
                score=1.0,  # Perfect match for direct lookup
                metadata=metadata,
            )

    def count(self) -> int:
        """Get the number of vectors in the store."""
        with get_session_context() as session:
            count = session.execute(
                text("SELECT COUNT(*) FROM endpoints WHERE embedding_vector IS NOT NULL")
            ).scalar()
            return count or 0

    def batch_add(
        self,
        vector_ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add multiple vectors to the store in a single batch operation.

        This is much more efficient than adding vectors one by one.

        Args:
            vector_ids: List of unique identifiers
            embeddings: List of vector embeddings
            metadatas: List of metadata dictionaries
        """
        if not vector_ids or not embeddings or not metadatas:
            return

        if not (len(vector_ids) == len(embeddings) == len(metadatas)):
            error_msg = "Length of vector_ids, embeddings, and metadatas must be the same"
            raise ValueError(error_msg)

        with get_session_context() as session:
            # Process in chunks to avoid overwhelming the database
            chunk_size = 100
            for i in range(0, len(vector_ids), chunk_size):
                chunk_ids = vector_ids[i : i + chunk_size]
                chunk_embeddings = embeddings[i : i + chunk_size]

                # Update vectors in batch
                for j, vector_id in enumerate(chunk_ids):
                    embedding = chunk_embeddings[j]
                    self._update_vector(session, vector_id, embedding)

                # Commit after each chunk
                session.commit()

    def batch_delete(self, vector_ids: list[str]) -> None:
        """Delete multiple vectors from the store in a single batch operation.

        Args:
            vector_ids: List of unique identifiers to delete
        """
        if not vector_ids:
            return

        with get_session_context() as session:
            # We don't actually delete the endpoints, just null out the vectors
            placeholders = ", ".join(f"'{vid}'" for vid in vector_ids)
            sql = text(
                f"""
                UPDATE endpoints 
                SET 
                    embedding = NULL,
                    embedding_vector = NULL
                WHERE id IN ({placeholders})
                """
            )
            session.execute(sql)
            session.commit()


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """Get a singleton instance of the vector store.

    Returns:
        VectorStore instance based on PostgreSQL's pgvector extension
    """
    # We are now standardized on PostgreSQL vector store
    logger.info("Using PostgreSQL pgvector for vector storage")
    return PostgresVectorStore()
