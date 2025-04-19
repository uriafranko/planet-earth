import hashlib
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlmodel import Session, col, select

from app.api.deps import TokenData, get_current_user, get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schema import Schema, SchemaRead
from app.tasks.schemas import enqueue_schema_processing

logger = get_logger(__name__)

router = APIRouter(prefix="/schemas", tags=["schemas"])


@router.post(
    "",
    response_model=SchemaRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload an OpenAPI schema",
    description="Upload a YAML or JSON OpenAPI 3.x specification file for processing.",
)
async def upload_schema(
    file: Annotated[UploadFile, File()] = ...,
    db: Session = Depends(get_db),
    _current_user: TokenData | None = Depends(get_current_user),
):
    """Upload an OpenAPI schema file (YAML or JSON) for processing.

    The file will be validated, its checksum calculated, and queued for async processing.
    Returns immediately with a 202 Accepted response and the schema ID for tracking.
    """
    # Check file size limit (in bytes)
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file_size = 0

    # Read the file and calculate checksum
    contents = await file.read()
    file_size = len(contents)

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # Calculate file checksum for uniqueness/comparison
    checksum = hashlib.sha256(contents).hexdigest()

    # Check if schema with this checksum already exists
    existing_schema = db.exec(select(Schema).where(Schema.checksum == checksum)).first()

    if existing_schema:
        # Return 409 Conflict for duplicate uploads
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Schema with checksum {checksum} already exists (ID: {existing_schema.id}).",
        )

    # Create a new schema record with temporary title/version
    # These will be updated after parsing in the worker
    new_schema = Schema(
        title=file.filename or "Untitled Schema",
        version="0.0.0",  # Placeholder until parsed
        checksum=checksum,
    )

    db.add(new_schema)
    db.commit()
    db.refresh(new_schema)

    # Enqueue the schema for processing in the background
    enqueue_schema_processing(
        schema_id=str(new_schema.id),
        file_content=contents,
    )

    logger.info(
        "Schema uploaded and queued for processing",
        extra={"schema_id": str(new_schema.id), "checksum": checksum},
    )

    return new_schema


@router.get(
    "",
    response_model=list[SchemaRead],
    summary="List all schemas",
    description="Retrieve a list of all uploaded schemas with their metadata.",
)
async def list_schemas(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all schemas with pagination."""
    return db.exec(
        select(Schema).offset(offset).limit(limit).order_by(col(Schema.created_at).desc()),
    ).all()


@router.get(
    "/{schema_id}",
    response_model=SchemaRead,
    summary="Get schema details",
    description="Retrieve details about a specific schema by its ID.",
)
async def get_schema(
    schema_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """Get details for a specific schema by ID."""
    schema = db.get(Schema, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID {schema_id} not found.",
        )
    return schema


@router.delete(
    "/{schema_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete schema",
    description="Delete a schema and all its associated endpoints.",
)
async def delete_schema(
    schema_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[TokenData | None, Depends(get_current_user)],
):
    """Delete a schema and all its associated endpoints (cascading delete)."""
    schema = db.get(Schema, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID {schema_id} not found.",
        )

    # Note: due to CASCADE DELETE in the DB, this will also delete all endpoints
    db.delete(schema)
    db.commit()

    logger.info("Schema deleted", extra={"schema_id": str(schema_id)})
