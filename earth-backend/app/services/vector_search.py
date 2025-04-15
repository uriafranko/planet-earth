import time
from typing import Any

from sqlalchemy import func
from sqlmodel import col, desc, select

from app.core.logging import get_logger
from app.db.session import get_session_context
from app.models.endpoint import Endpoint, EndpointSearchResult
from app.services.embedder import get_embedder

logger = get_logger(__name__)

def search_vector_by_text(
    query_text: str,
    k: int = 10,
    filters: dict[str, Any] | None = None,
    similarity_threshold: float = 0.0,
    use_hnsw: bool = True,
) -> list[EndpointSearchResult]:
    embedder = get_embedder()
    embedding = embedder.embed_query(query_text)
    logger.debug(f"Embedding query text: {query_text}")
    return search_vector_by_embedding(
        embedding=embedding,
        k=k,
        filters=filters,
        similarity_threshold=similarity_threshold,
        use_hnsw=use_hnsw,
    )


def search_vector_by_embedding(
    embedding: list[float],
    k: int = 10,
    filters: dict[str, Any] | None = None,
    similarity_threshold: float = 0.0,
    use_hnsw: bool = True,  # pgvector automatically chooses the best index
) -> list[EndpointSearchResult]:
    with get_session_context() as session:
        similarity_expr = (1 - Endpoint.embedding_vector.cosine_distance(embedding)).label("similarity")
        query = (
            select(
                Endpoint,
                similarity_expr,
            )
            .where(
                col(Endpoint.deleted_at).is_(None),
                Endpoint.embedding_vector.is_not(None),
            )
        )

        # # similarity threshold condition
        if similarity_threshold > 0:
            query = query.where(
                similarity_expr >= similarity_threshold
            )

        # Apply filters dynamically

        if filters:
            if schema_id := filters.get("schema_id"):
                query = query.where(Endpoint.schema_id == schema_id)
            if method := filters.get("method"):
                query = query.where(Endpoint.method == method)
            if tags := filters.get("tags"):
                query = query.where(col(Endpoint.tags).contains(tags))

        # query = query.order_by(col("similarity").desc()).limit(k)
        logger.debug(f"Executing vector search with provided embedding and filters: {filters}")

        query = query.order_by(desc("similarity"))
        if k:
            query = query.limit(k)

        start_time = time.time()
        results = session.exec(query).all()
        elapsed = time.time() - start_time

        logger.debug(f"Vector search completed in {elapsed:.3f}s, found {len(results)} results")

        return [
            EndpointSearchResult(
                id=str(endpoint.id),
                schema_id=str(endpoint.schema_id),
                path=endpoint.path,
                method=endpoint.method,
                operation_id=endpoint.operation_id,
                summary=endpoint.summary,
                description=endpoint.description,
                tags=endpoint.tags,
                score=similarity,
                spec=endpoint.spec if endpoint.spec else None,
            )
            for endpoint, similarity in results
        ]


def count_indexed_vectors() -> int:
    with get_session_context() as session:
        count_query = select(func.count()).where(Endpoint.embedding_vector != None)
        count = session.exec(count_query).one()
        return count or 0


def get_embedding_dimension() -> int:
    embedder = get_embedder()
    return embedder.get_dimension()
