import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import TokenData, get_current_user
from app.core.logging import get_logger
from app.models.endpoint import EndpointSearchResult
from app.services.embedder import get_embedder
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


class SearchQuery(BaseModel):
    """Model for semantic search requests."""

    q: str = Field(..., description="Search query text")
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of results to return",
    )
    filter_schema_id: str | None = Field(
        default=None,
        description="Optional filter by schema ID",
    )
    filter_method: str | None = Field(
        default=None,
        description="Optional filter by HTTP method",
    )
    include_deprecated: bool = Field(
        default=False,
        description="Whether to include deprecated endpoints",
    )


@router.post(
    "",
    response_model=list[EndpointSearchResult],
    summary="Semantic search",
    description="Search for API endpoints using natural language queries.",
)
async def search_endpoints(
    query: SearchQuery,
    _current_user: TokenData | None = Depends(get_current_user),
):
    """Perform semantic search over API endpoints.

    Embeds the query text and searches for similar endpoints in the vector store.
    """
    logger.info(
        "Performing semantic search",
        extra={"query": query.q, "top_k": query.top_k},
    )

    try:
        # Get embedder and vector store
        embedder = get_embedder()
        vector_store = get_vector_store()

        # Embed the query
        query_embedding = embedder.embed_query(query.q)

        # Prepare filters
        filters = {}
        if query.filter_schema_id:
            filters["schema_id"] = query.filter_schema_id
        if query.filter_method:
            filters["method"] = query.filter_method
        if not query.include_deprecated:
            filters["deleted_at"] = None

        # Perform vector search
        search_results = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=query.top_k,
            filters=filters,
        )

        # Format the results into the expected response model
        results = []
        for result in search_results:
            # Basic endpoint data from vector store metadata
            result_data = {
                "id": result.id,
                "schema_id": result.metadata.get("schema_id"),
                "path": result.metadata.get("path"),
                "method": result.metadata.get("method"),
                "score": result.score,
            }
            # Get additional metadata from the database
            try:
                # This would be a join query in a real implementation
                # For now, just use the metadata from the vector store
                result_data["schema_title"] = result.metadata.get(
                    "schema_title",
                    "Unknown",
                )
                result_data["schema_version"] = result.metadata.get(
                    "schema_version",
                    "Unknown",
                )
                result_data["operation_id"] = result.metadata.get("operation_id")
                result_data["summary"] = result.metadata.get("summary")
                result_data["description"] = result.metadata.get("description")
                result_data["tags"] = result.metadata.get("tags")
                spec = result.metadata.get("spec")
                if spec and isinstance(spec, str):
                    result_data["spec"] = json.loads(spec)
            except Exception:
                logger.exception("Error fetching endpoint details")

            results.append(EndpointSearchResult(**result_data))

        return results

    except Exception as e:
        logger.exception("Error during semantic search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing search: {e!s}",
        ) from e
