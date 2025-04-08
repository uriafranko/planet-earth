"""Tasks for managing API endpoints.

This module defines Celery tasks for operations on API endpoints,
such as reindexing in the vector database.
"""

import datetime
import json
import uuid

from sqlmodel import select

from app.core.logging import get_logger
from app.db.session import get_session_context
from app.models.endpoint import Endpoint
from app.models.schema import Schema
from app.services.embedder import get_embedder
from app.services.vector_store import get_vector_store
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, name="reindex_endpoint")
def reindex_endpoint(self, endpoint_id: str) -> dict:
    """Reindex a specific endpoint in the vector store.

    This function:
    1. Retrieves the endpoint from the database
    2. Generates a new text representation for embedding
    3. Embeds the text and updates the vector store

    Args:
        self: The Celery task instance
        endpoint_id: UUID of the endpoint to reindex

    Returns:
        Dictionary with reindexing results

    Raises:
        ValueError: If endpoint with the given ID is not found
    """
    logger.info(f"Reindexing endpoint {endpoint_id}")

    try:
        # Initialize services
        embedder = get_embedder()
        vector_store = get_vector_store()

        with get_session_context() as session:
            # Get the endpoint
            endpoint = session.get(Endpoint, uuid.UUID(endpoint_id))
            if not endpoint:
                error_message = f"Endpoint with ID {endpoint_id} not found"
                logger.error(error_message)
                raise ValueError(error_message)

            # Get the schema
            schema = session.get(Schema, endpoint.schema_id)
            if not schema:
                error_message = f"Schema with ID {endpoint.schema_id} not found"
                logger.error(error_message)
                raise ValueError(error_message)

            # Create endpoint data dictionary for embedding
            endpoint_data = {
                "path": endpoint.path,
                "method": endpoint.method,
                "operation_id": endpoint.operation_id,
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": json.loads(endpoint.tags) if endpoint.tags else [],
                "hash": endpoint.hash,
                "spec": endpoint.spec,
            }

            # Generate embedding
            text = f"{schema.title} {endpoint_data['path']} {endpoint_data['summary'] or endpoint_data['description']} {', '.join(endpoint_data['tags'])}"
            embedding = embedder.embed_text(text)

            # Update vector store
            vector_store.update(
                vector_id=str(endpoint.id),
                embedding=embedding,
                metadata={
                    "schema_id": str(endpoint.schema_id),
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "operation_id": endpoint.operation_id,
                    "summary": endpoint.summary,
                    "description": endpoint.description,
                    "tags": endpoint.tags,
                    "schema_title": schema.title,
                    "schema_version": schema.version,
                    "spec": endpoint.spec,
                },
            )

            # Update endpoint's updated_at timestamp
            endpoint.updated_at = datetime.datetime.now(tz=datetime.UTC)
            session.add(endpoint)
            session.commit()

            logger.info(
                f"Successfully reindexed endpoint: {endpoint.path} {endpoint.method}",
                extra={"endpoint_id": endpoint_id},
            )

            return {
                "status": "success",
                "endpoint_id": endpoint_id,
                "path": endpoint.path,
                "method": endpoint.method,
            }

    except Exception as e:
        logger.exception("Error reindexing endpoint")
        return {
            "status": "error",
            "endpoint_id": endpoint_id,
            "error": str(e),
        }


@celery_app.task(bind=True, name="reindex_endpoints_batch")
def reindex_endpoints_batch(self, endpoint_ids: list[str]) -> dict:
    """Reindex multiple endpoints in the vector store.

    Args:
        self: The Celery task instance
        endpoint_ids: List of endpoint UUIDs to reindex

    Returns:
        Dictionary with batch reindexing results
    """
    logger.info(f"Reindexing batch of {len(endpoint_ids)} endpoints")

    results = {
        "total": len(endpoint_ids),
        "success": 0,
        "errors": 0,
        "endpoints": [],
    }

    for endpoint_id in endpoint_ids:
        try:
            result = reindex_endpoint.apply(args=[endpoint_id]).get()

            if result["status"] == "success":
                results["success"] += 1
            else:
                results["errors"] += 1

            results["endpoints"].append(result)

        except Exception as e:
            results["errors"] += 1
            results["endpoints"].append(
                {
                    "status": "error",
                    "endpoint_id": endpoint_id,
                    "error": str(e),
                }
            )

    logger.info(
        f"Batch reindexing completed: {results['success']} successful, {results['errors']} errors"
    )

    return results


@celery_app.task(bind=True, name="reindex_schema_endpoints")
def reindex_schema_endpoints(self, schema_id: str = None) -> dict:
    """Reindex all endpoints for a specific schema or all schemas.

    Args:
        self: The Celery task instance
        schema_id: Optional schema UUID to limit reindexing to

    Returns:
        Dictionary with schema reindexing results
    """
    logger.info(
        f"Starting reindex of all endpoints for schema: {schema_id if schema_id else 'ALL'}"
    )

    try:
        with get_session_context() as session:
            # Build query to find endpoints
            query = select(Endpoint)

            # Filter by schema if provided
            if schema_id:
                query = query.where(Endpoint.schema_id == uuid.UUID(schema_id))

            # Only include non-deleted endpoints
            query = query.where(Endpoint.deleted_at == None)  # noqa: E711

            # Execute query
            endpoints = session.exec(query).all()

            if not endpoints:
                logger.warning(
                    f"No endpoints found to reindex for schema: {schema_id if schema_id else 'ALL'}"
                )
                return {
                    "status": "success",
                    "message": "No endpoints found to reindex",
                    "count": 0,
                }

            logger.info(f"Found {len(endpoints)} endpoints to reindex")

            # Process in batches of 50 endpoints
            batch_size = 50
            batches = [
                [str(endpoints[i].id) for i in range(j, min(j + batch_size, len(endpoints)))]
                for j in range(0, len(endpoints), batch_size)
            ]

            batch_results = []
            for batch in batches:
                result = reindex_endpoints_batch.apply_async(args=[batch])
                batch_results.append(result.id)

            return {
                "status": "success",
                "message": f"Reindexing {len(endpoints)} endpoints in {len(batches)} batches",
                "count": len(endpoints),
                "batch_tasks": batch_results,
            }

    except Exception as e:
        logger.exception("Error starting schema reindexing")
        return {
            "status": "error",
            "schema_id": schema_id,
            "error": str(e),
        }
