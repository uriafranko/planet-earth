import time
from typing import Any
from uuid import UUID

from sqlmodel import col, desc, select, text

from app.core.logging import get_logger
from app.db.session import get_session_context
from app.models.audit import Audit, AuditResult
from app.models.documents import Document, DocumentChunk, DocumentSearchResult
from app.models.endpoint import Endpoint, EndpointSearchResult
from app.services.embedder import get_embedder

logger = get_logger(__name__)



def get_embedding_dimension() -> int:
    embedder = get_embedder()
    return embedder.get_dimension()


def search_endpoints_by_text(
    query_text: str,
    k: int = 10,
    filters: dict[str, Any] | None = None,
    similarity_threshold: float = 0.0,
    use_hnsw: bool = True,  # pgvector automatically chooses the best index
) -> list[EndpointSearchResult]:
    embedder = get_embedder()
    embedding = embedder.embed_query(query_text)
    logger.debug(f"Embedding query text: {query_text}")

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

        logger.debug(f"Executing vector search with provided embedding and filters: {filters}")

        query = query.order_by(desc("similarity"))
        if k:
            query = query.limit(k)

        start_time = time.time()
        results = session.exec(query).all()
        elapsed = time.time() - start_time

        logger.debug(f"Vector search completed in {elapsed:.3f}s, found {len(results)} results")
        endpoint_results = [
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

        # --- AUDIT LOGGING ---
        try:
            audit = Audit(
                query=query_text,
                total_result_count=len(endpoint_results),
            )
            session.add(audit)
            session.flush()  # To get audit.id

            for result in endpoint_results:
                audit_result = AuditResult(
                    audit_id=audit.id,
                    schema_id=UUID(result.schema_id),
                    endpoint_id=UUID(result.id),
                    result_count=1,  # Each EndpointSearchResult is one result
                )
                session.add(audit_result)

            session.commit()
            logger.info(f"Audit log saved for query: {query_text} ({len(endpoint_results)} results)")
        except Exception:
            logger.exception("Failed to save audit log")
            session.rollback()
        return endpoint_results



def search_documents_by_text(
    query_text: str,
    k: int = 10,
    filters: dict[str, Any] | None = None,
    similarity_threshold: float = 0.0,
    return_full_document: bool = True,
    use_hnsw: bool = True,  # pgvector automatically chooses the best index
) -> list[DocumentSearchResult]:
    embedder = get_embedder()
    embedding = embedder.embed_query(query_text)
    logger.debug(f"Embedding query text: {query_text}")

    with get_session_context() as session:
        similarity_expr = (1 - DocumentChunk.embedding.cosine_distance(embedding)).label("similarity")

        query = (
            select(DocumentChunk, similarity_expr)
            .where(
                DocumentChunk.embedding.is_not(None),
            )
        )
        if return_full_document:
            query = query.join(Document)
            query = query.where(DocumentChunk.document_id == Document.id)

        # # similarity threshold condition
        if similarity_threshold > 0:
            query = query.where(
                similarity_expr >= similarity_threshold
            )

        # Apply filters dynamically

        if filters and (created_at := filters.get("created_at")):
            query = query.where(DocumentChunk.created_at == created_at)

        logger.debug(f"Executing vector search with provided embedding and filters: {filters}")

        query = query.order_by(desc(text("similarity")))
        if k:
            query = query.limit(k)
        start_time = time.time()
        results = session.exec(query).all()
        elapsed = time.time() - start_time
        logger.debug(f"Vector search completed in {elapsed:.3f}s, found {len(results)} results")
        document_results = [
            DocumentSearchResult(
                chunk_id=str(document_chunk.id),
                document_id=str(document_chunk.document_id),
                title=document_chunk.document.title if document_chunk.document else "Unknown",
                chunk_text=document_chunk.text,
                document_text=document_chunk.document.text if document_chunk.document else "",
                score=similarity,
                created_at=document_chunk.created_at,
            )
            for document_chunk, similarity in results
        ]

        return document_results

