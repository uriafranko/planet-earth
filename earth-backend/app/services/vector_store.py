"""Vector store service for storing and retrieving vector embeddings.

This module provides an abstract interface for vector stores and implementations
for different backends (Chroma, Qdrant).
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings
from app.core.logging import get_logger

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


class ChromaVectorStore(VectorStore):
    """Vector store implementation using Chroma."""

    def __init__(
        self,
        collection_name: str,
        persist_directory: str,
        embedding_dimension: int = 384,  # Default for all-MiniLM-L6-v2
    ):
        """Initialize the Chroma vector store.

        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist the database
            embedding_dimension: Dimension of the embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_dimension = embedding_dimension

        # Create the persist directory if it doesn't exist
        if not Path(persist_directory).exists():
            Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client
        if settings.CHROMA_MODE == "http":
            # HTTP client mode (for client/server setup)
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                ),
            )
        else:
            # Persistent client mode (local)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                ),
            )

        # Get or create the collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Using existing Chroma collection: {collection_name}")
        except ValueError:
            # Collection doesn't exist, create it
            logger.info(f"Creating new Chroma collection: {collection_name}")
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"dimension": embedding_dimension},
            )

    def add(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Add a vector to the store."""
        self.collection.add(
            ids=[vector_id],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def update(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Update a vector in the store."""
        # Chroma's upsert method will add or update
        self.collection.upsert(
            ids=[vector_id],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def delete(self, vector_id: str) -> None:
        """Delete a vector from the store."""
        self.collection.delete(ids=[vector_id])

    def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Perform a similarity search."""
        # Convert filters to Chroma where clause if provided
        where = filters if filters else None

        # Perform the search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["metadatas", "distances"],
        )

        # Format the results
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, id_val in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0

                # Convert distance to similarity score (1.0 is perfect match)
                score = 1.0 - min(distance, 1.0)

                search_results.append(
                    SearchResult(
                        id=id_val,
                        score=score,
                        metadata=metadata,
                    ),
                )

        return search_results

    def get(self, vector_id: str) -> SearchResult | None:
        """Get a vector by ID."""
        try:
            result = self.collection.get(
                ids=[vector_id],
                include=["metadatas", "embeddings"],
            )

            if not result["ids"]:
                return None

            return SearchResult(
                id=result["ids"][0],
                score=1.0,  # Perfect match for direct lookup
                metadata=result["metadatas"][0] if result["metadatas"] else {},
            )
        except Exception:
            logger.exception(f"Error getting vector with ID {vector_id}")
            return None

    def count(self) -> int:
        """Get the number of vectors in the store."""
        return self.collection.count()


class QdrantVectorStore(VectorStore):
    """Vector store implementation using Qdrant.

    Optimized for performance with connection pooling, batch operations,
    and efficient filtering.
    """

    def __init__(
        self,
        collection_name: str = settings.QDRANT_COLLECTION_NAME,
        embedding_dimension: int = 384,  # Default for all-MiniLM-L6-v2
        distance: str = "Cosine",  # Cosine, Euclid, or Dot
    ):
        """Initialize the Qdrant vector store.

        Args:
            collection_name: Name of the collection to use
            embedding_dimension: Dimension of the embeddings
            distance: Distance metric to use (Cosine, Euclid, or Dot)
        """
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension

        # Map string distance to Qdrant Distance enum
        distance_map = {
            "cosine": Distance.COSINE,
            "euclid": Distance.EUCLID,
            "dot": Distance.DOT,
        }
        self.distance = distance_map.get(distance.lower(), Distance.COSINE)
        if settings.QDRANT_URL:
            self.client = QdrantClient(
                url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None
            )
        else:  # noqa: PLR5501
            # Initialize Qdrant client with connection pooling for better performance
            if settings.QDRANT_PREFER_GRPC:
                # Use gRPC for better performance when available
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_GRPC_PORT,
                    api_key=settings.QDRANT_API_KEY or None,
                    https=settings.QDRANT_HTTPS,
                    prefer_grpc=True,
                    timeout=10.0,  # Increased timeout for reliability
                )
                logger.info("Using Qdrant with gRPC transport")
            else:
                # Use HTTP otherwise
                self.client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY or None,
                    https=settings.QDRANT_HTTPS,
                    timeout=10.0,  # Increased timeout for reliability
                )
                logger.info("Using Qdrant with HTTP transport")

        # Get or create the collection
        try:
            _ = self.client.get_collection(collection_name=collection_name)
            logger.info(f"Using existing Qdrant collection: {collection_name}")
        except (ValueError, UnexpectedResponse):
            # Collection doesn't exist, create it
            logger.info(f"Creating new Qdrant collection: {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_dimension,
                    distance=self.distance,
                ),
                # Add optimized index parameters
                optimizers_config=qdrant_models.OptimizersConfigDiff(
                    indexing_threshold=20000,  # Larger for batch indexing
                    memmap_threshold=100000,  # Use memory mapping for large collections
                ),
                # Add vector sparse index for faster search
                hnsw_config=qdrant_models.HnswConfigDiff(
                    m=16,  # Number of bidirectional links (higher = better recall, more memory)
                    ef_construct=128,  # Size of the dynamic list for nearest neighbors (higher = better recall)
                    full_scan_threshold=10000,  # Threshold for full scan vs index
                    on_disk=True,  # Store index on disk for larger datasets
                ),
            )

    def add(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Add a vector to the store."""
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qdrant_models.PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload=metadata,
                )
            ],
        )

    def update(self, vector_id: str, embedding: list[float], metadata: dict[str, Any]) -> None:
        """Update a vector in the store."""
        # Qdrant's upsert method will add or update
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qdrant_models.PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload=metadata,
                )
            ],
        )

    def delete(self, vector_id: str) -> None:
        """Delete a vector from the store."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qdrant_models.PointIdsList(
                points=[vector_id],
            ),
        )

    def _convert_filters(self, filters: dict[str, Any] | None) -> qdrant_models.Filter | None:  # noqa: C901
        """Convert dictionary filters to Qdrant filter format.

        Args:
            filters: Dictionary of filters

        Returns:
            Qdrant filter object or None if no filters
        """
        if not filters:
            return None

        # Build filter conditions
        conditions = []
        for key, value in filters.items():
            if not value:
                continue
            if isinstance(value, list):
                # Handle list values (any match)
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchAny(any=value),
                    )
                )
            elif isinstance(value, dict):
                # Handle range queries with operators
                range_operators = {}
                for op, val in value.items():
                    if op == "gt":
                        range_operators["gt"] = val
                    elif op == "gte":
                        range_operators["gte"] = val
                    elif op == "lt":
                        range_operators["lt"] = val
                    elif op == "lte":
                        range_operators["lte"] = val

                if range_operators:
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            range=qdrant_models.Range(**range_operators),
                        )
                    )
            else:
                # Handle exact match
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value),
                    )
                )

        if conditions:
            return qdrant_models.Filter(
                must=conditions,
            )

        return None

    def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Perform a similarity search.

        Optimized to use Qdrant's efficient search capabilities with proper filtering.
        """
        # Convert filters to Qdrant format if provided
        qdrant_filter = self._convert_filters(filters)

        # Perform the search with optimized parameters
        search_params = qdrant_models.SearchParams(
            hnsw_ef=128,  # Controls recall vs performance tradeoff (higher = better recall)
            exact=False,  # Set to True for exact search (slower but more accurate)
        )

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=k,
            query_filter=qdrant_filter,
            with_payload=True,
            search_params=search_params,
        )

        # Format the results
        return [
            SearchResult(
                id=str(result.id),
                score=float(result.score),
                metadata=result.payload or {},
            )
            for result in results
        ]

    def get(self, vector_id: str) -> SearchResult | None:
        """Get a vector by ID."""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
                with_payload=True,
                with_vectors=True,
            )

            if not result:
                return None

            point = result[0]
            return SearchResult(
                id=str(point.id),
                score=1.0,  # Perfect match for direct lookup
                metadata=point.payload or {},
            )
        except Exception:
            logger.exception(f"Error getting vector with ID {vector_id}")
            return None

    def count(self) -> int:
        """Get the number of vectors in the store."""
        collection_info = self.client.get_collection(collection_name=self.collection_name)
        return collection_info.vectors_count

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

        # Create point structs
        points = [
            qdrant_models.PointStruct(
                id=vector_id,
                vector=embedding,
                payload=metadata,
            )
            for vector_id, embedding, metadata in zip(
                vector_ids, embeddings, metadatas, strict=False
            )
        ]

        # Use batch upsert for better performance
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,  # Wait for operation to complete
        )

    def batch_delete(self, vector_ids: list[str]) -> None:
        """Delete multiple vectors from the store in a single batch operation.

        Args:
            vector_ids: List of unique identifiers to delete
        """
        if not vector_ids:
            return

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qdrant_models.PointIdsList(
                points=vector_ids,
            ),
            wait=True,  # Wait for operation to complete
        )


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """Get a singleton instance of the vector store.

    Returns:
        VectorStore instance
    """
    # Determine which vector store to use based on configuration
    vector_store_type = os.environ.get("VECTOR_STORE_TYPE", "qdrant").lower()

    if vector_store_type == "qdrant":
        try:
            return QdrantVectorStore()
        except Exception:
            logger.exception("Failed to initialize Qdrant vector store")
            logger.warning("Falling back to Chroma vector store")
            return ChromaVectorStore()
    elif vector_store_type == "chroma":
        return ChromaVectorStore()
    else:
        logger.warning(f"Unknown vector store type: {vector_store_type}, using Qdrant")
        return QdrantVectorStore()
