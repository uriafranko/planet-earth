import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import TokenData, get_current_user, get_db
from app.core.logging import get_logger
from app.models.endpoint import Endpoint, EndpointRead
from app.models.schema import Schema
from app.tasks.endpoints import reindex_endpoint, reindex_schema_endpoints

logger = get_logger(__name__)

router = APIRouter(prefix="/management", tags=["management"])


@router.get(
    "/schemas/{schema_id}/endpoints",
    response_model=list[EndpointRead],
    summary="List endpoints for schema",
    description="Retrieve all endpoints associated with a specific schema.",
)
async def list_schema_endpoints(
    schema_id: uuid.UUID,
    include_deleted: bool = False,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all endpoints for a specific schema with pagination."""
    # Check if schema exists
    schema = db.get(Schema, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID {schema_id} not found.",
        )

    # Build query
    query = select(Endpoint).where(Endpoint.schema_id == schema_id)

    # Filter deleted endpoints if requested
    if not include_deleted:
        query = query.where(Endpoint.deleted_at.is_(None))

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    return db.exec(query).all()


@router.post(
    "/reindex",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Reindex vector store",
    description="Reindex all endpoints in the vector store. This is an asynchronous operation.",
)
async def reindex_vector_store(
    schema_id: uuid.UUID | None = None,
    _current_user: TokenData = Depends(get_current_user),
):
    """Reindex all endpoints in the vector store.

    This is useful after updating the embedding model or if the vector store
    gets corrupted. If schema_id is provided, only endpoints from that schema
    will be reindexed.
    """
    logger.info(
        "Starting vector store reindexing",
        extra={"schema_id": str(schema_id) if schema_id else "all"},
    )

    # Convert UUID to string for serialization
    schema_id_str = str(schema_id) if schema_id else None
    
    # Using Celery task for reindexing all endpoints
    task = reindex_schema_endpoints.delay(schema_id=schema_id_str)
    
    return {
        "message": f"Reindexing started in the background (task ID: {task.id})",
        "task_id": task.id,
    }


@router.post(
    "/endpoints/{endpoint_id}/reindex",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Reindex endpoint",
    description="Reindex a specific endpoint in the vector store. This is an asynchronous operation.",
)
async def reindex_endpoint_api(
    endpoint_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: TokenData = Depends(get_current_user),
):
    """Reindex a specific endpoint in the vector store.

    This is useful for updating the embedding of a specific endpoint after
    modifying its metadata or if its embedding is corrupted.
    """
    # Check if endpoint exists
    endpoint = db.get(Endpoint, endpoint_id)
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Endpoint with ID {endpoint_id} not found.",
        )

    logger.info(
        "Starting endpoint reindexing",
        extra={"endpoint_id": str(endpoint_id)},
    )

    # Start the Celery task to reindex the endpoint
    task = reindex_endpoint.delay(endpoint_id=str(endpoint_id))

    return {
        "message": f"Reindexing of endpoint {endpoint_id} started in the background (task ID: {task.id})",
        "task_id": task.id,
    }
