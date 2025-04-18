
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import TokenData, get_current_user
from app.core.config import settings
from app.core.logging import get_logger
from app.models.endpoint import EndpointSearchResult
from app.services.vector_search import search_vector_by_text

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
        # Prepare filters
        filters = {}
        if query.filter_schema_id:
            filters["schema_id"] = query.filter_schema_id
        if query.filter_method:
            filters["method"] = query.filter_method
        if not query.include_deprecated:
            filters["deleted_at"] = None

        # Log search request
        logger.info(
            "Using optimized single text search",
            extra={"query": query.q, "top_k": query.top_k, "filters": filters},
        )

        # Use the optimized single text search function
        return search_vector_by_text(
            query_text=f"{settings.EMBEDDING_INSTRUCTIONS} {query.q}",
            k=query.top_k,
            filters=filters,
            similarity_threshold=0.5,
        )

    except Exception as e:
        logger.exception("Error during semantic search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing search: {e!s}",
        ) from e
