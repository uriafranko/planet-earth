"""Tasks for processing OpenAPI schemas.

This module defines Celery tasks for ingesting and processing OpenAPI specifications.
"""

import datetime
import json
import uuid

from sqlmodel import Session, select

from app.core.logging import get_logger
from app.db.session import get_session_context
from app.models.endpoint import Endpoint
from app.models.schema import Schema
from app.services.embedder import embed_endpoint
from app.services.parser import OpenAPIParser
from app.tasks.celery_app import celery_app


class SchemaNotFoundError(ValueError):
    """Exception raised when a schema cannot be found in the database."""

    def __init__(self, schema_id: str) -> None:
        """Initialize the exception with the schema ID.

        Args:
            schema_id: The ID of the schema that was not found.
        """
        self.schema_id = schema_id
        self.message = f"Schema with ID {schema_id} not found"
        super().__init__(self.message)


logger = get_logger(__name__)


def enqueue_schema_processing(
    schema_id: str,
    file_content: bytes,
    file_name: str,
) -> str:
    """Enqueue a schema for processing in the background.

    Args:
        schema_id: UUID of the schema to process
        file_content: Raw content of the uploaded OpenAPI spec
        file_name: Name of the uploaded file

    Returns:
        Task ID for tracking
    """
    task = process_schema.delay(
        schema_id=schema_id,
        file_content=file_content,
        file_name=file_name,
    )
    logger.info(
        "Enqueued schema processing task",
        extra={"schema_id": schema_id, "task_id": task.id},
    )
    return task.id


def _validate_schema_exists(session: Session, schema_id: str) -> Schema:
    """Validate that a schema exists and return it.

    Args:
        session: Database session
        schema_id: UUID of the schema to validate

    Returns:
        Schema object if found

    Raises:
        SchemaNotFoundError: If schema with the given ID is not found
    """
    schema = session.get(Schema, uuid.UUID(schema_id))
    if not schema:
        raise SchemaNotFoundError(schema_id)
    return schema


@celery_app.task(name="process_schema")
def process_schema(schema_id: str, file_content: bytes, file_name: str) -> dict:
    """Process an OpenAPI schema: parse, extract endpoints, and store them.

    This is the main worker function that:
    1. Parses the OpenAPI spec
    2. Extracts metadata and endpoints
    3. Updates the schema record with parsed metadata
    4. Creates endpoint records in the database
    5. Embeds endpoint texts and stores them in the vector database

    Args:
        self: The Celery task instance
        schema_id: UUID of the schema to process
        file_content: Raw content of the uploaded OpenAPI spec
        file_name: Name of the uploaded file

    Returns:
        Dictionary with processing results
    """
    logger.info(f"Processing schema {schema_id}")

    try:
        # Initialize the parser
        parser = OpenAPIParser()

        # Parse the OpenAPI spec
        parsed_spec = parser.parse(file_content)

        # Extract schema metadata
        title, version = parser.extract_schema_metadata(parsed_spec)

        # Extract endpoints from the spec
        endpoints = parser.extract_endpoints(parsed_spec)

        logger.info(f"Extracted {len(endpoints)} endpoints from OpenAPI spec")

        # Update schema and create endpoints in the database
        with get_session_context() as session:
            # Get and validate the schema record
            schema = _validate_schema_exists(session, schema_id)

            # Update schema metadata
            schema.title = title
            schema.version = version
            schema.status = "processing"  # Mark as processing
            session.add(schema)
            session.commit()

            # Process the endpoints
            process_endpoints(session, schema, endpoints)

            schema.status = "processed"  # Mark as successfully processed
            session.add(schema)
            session.commit()

            logger.info(
                f"Successfully processed schema {schema_id}",
                extra={
                    "schema_id": schema_id,
                    "title": title,
                    "version": version,
                    "endpoints_count": len(endpoints),
                },
            )

            return {
                "status": "success",
                "schema_id": schema_id,
                "title": title,
                "version": version,
                "endpoints_count": len(endpoints),
            }
    except Exception as e:
        logger.exception("Error processing schema {schema_id}")

        # Update schema status to indicate failure
        with get_session_context() as session:
            try:
                schema = _validate_schema_exists(session, schema_id)
                schema.status = "error"
                session.add(schema)
                session.commit()
            except Exception:
                logger.exception("Error updating schema status")

        return {
            "status": "error",
            "schema_id": schema_id,
            "error": str(e),
        }


def process_endpoints(
    session: Session,
    schema: Schema,
    endpoints: list[dict],
) -> None:
    """Process endpoints extracted from an OpenAPI spec.

    This function:
    1. Creates or updates endpoint records in the database
    2. Generates text representations for embedding
    3. Embeds the texts and stores them in the vector database

    Args:
        session: Database session
        schema: Schema object
        endpoints: List of endpoint dictionaries
        parser: OpenAPIParser instance for generating embedding texts
    """
    # Fetch existing endpoints for this schema to avoid duplicates
    existing_endpoints = session.exec(
        select(Endpoint).where(
            Endpoint.schema_id == schema.id,
            Endpoint.deleted_at == None,  # noqa: E711
        )
    ).all()

    # Create a lookup of existing endpoints by path+method
    existing_lookup = {
        f"{endpoint.path}:{endpoint.method}": endpoint for endpoint in existing_endpoints
    }

    # Track processed paths to handle deletions later
    processed_paths = set()

    # Process each endpoint
    for endpoint_data in endpoints:
        path_method_key = f"{endpoint_data['path']}:{endpoint_data['method']}"
        processed_paths.add(path_method_key)

        # Check if this endpoint already exists
        if path_method_key in existing_lookup:
            # Update existing endpoint
            endpoint = existing_lookup[path_method_key]
            update_existing_endpoint(session, endpoint, endpoint_data, schema.title)
        else:
            # Create new endpoint
            create_new_endpoint(session, schema, endpoint_data, schema.title)

    # Handle endpoints that were deleted from the schema
    handle_deleted_endpoints(session, existing_lookup, processed_paths)


def update_existing_endpoint(
    session: Session,
    endpoint: Endpoint,
    endpoint_data: dict,
    schema_title: str,
) -> None:
    """Update an existing endpoint with new data and embedding."""
    # Check if the endpoint has actually changed
    if endpoint.hash != endpoint_data["hash"]:
        # Update endpoint record
        endpoint.operation_id = endpoint_data["operation_id"]
        endpoint.summary = endpoint_data["summary"]
        endpoint.description = endpoint_data["description"]
        endpoint.tags = json.dumps(endpoint_data["tags"])
        endpoint.spec = endpoint_data["spec"]
        endpoint.hash = endpoint_data["hash"]
        endpoint.embedding_vector = embed_endpoint(
            schema_title,
            endpoint_data["summary"],
            endpoint_data["description"],
            endpoint_data["tags"],
            endpoint_data["path"],
        )

        session.add(endpoint)
        session.commit()

        logger.info(
            f"Updated endpoint: {endpoint.path} {endpoint.method}",
            extra={"endpoint_id": str(endpoint.id)},
        )


def create_new_endpoint(
    session: Session,
    schema: Schema,
    endpoint_data: dict,
    schema_title: str,
) -> None:
    """Create a new endpoint with data and embedding."""
    # Create new endpoint record
    endpoint = Endpoint(
        id=uuid.uuid4(),
        schema_id=schema.id,
        path=endpoint_data["path"],
        method=endpoint_data["method"],
        operation_id=endpoint_data["operation_id"],
        summary=endpoint_data["summary"],
        description=endpoint_data["description"],
        tags=json.dumps(endpoint_data["tags"]),
        spec=endpoint_data["spec"],
        hash=endpoint_data["hash"],
        created_at=datetime.datetime.now(tz=datetime.UTC),
        embedding_vector=embed_endpoint(
            schema_title,
            endpoint_data["summary"],
            endpoint_data["description"],
            endpoint_data["tags"],
            endpoint_data["path"],
        ),
    )

    session.add(endpoint)
    session.commit()

    logger.info(
        f"Created endpoint: {endpoint.path} {endpoint.method}",
        extra={"endpoint_id": str(endpoint.id)},
    )


def handle_deleted_endpoints(
    session: Session,
    existing_lookup: dict[str, Endpoint],
    processed_paths: set[str],
) -> None:
    """Mark endpoints as deleted if they're not in the new spec."""
    for path_method, endpoint in existing_lookup.items():
        if path_method not in processed_paths:
            # Mark as deleted
            endpoint.deleted_at = datetime.datetime.now(tz=datetime.UTC)
            session.add(endpoint)

            logger.info(
                f"Marked endpoint as deleted: {endpoint.path} {endpoint.method}",
                extra={"endpoint_id": str(endpoint.id)},
            )

    session.commit()
