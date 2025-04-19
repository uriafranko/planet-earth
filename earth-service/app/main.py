from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi_mcp import FastApiMCP
from sqlmodel import SQLModel
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # noqa: ALL
from app.api.v1 import audit, documents, management, schemas, search
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import engine, install_extension
from app.models.documents import DocumentSearchResult
from app.models.endpoint import EndpointSearchResult
from app.services.embedder import get_embedder
from app.services.vector_search import search_endpoints_by_text, search_documents_by_text

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting up...")
    install_extension()
    SQLModel.metadata.create_all(engine)
    get_embedder()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,  # We'll define a custom docs url that handles auth conditionally
    redoc_url=None,
    lifespan=lifespan,
)


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include API routers
app.include_router(schemas.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(management.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI that can be extended for auth if needed."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get("/api/health", include_in_schema=False)
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        """Serve the React app's index.html for all paths."""
        try:
            response = await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            raise
        return response


# Serve React app static files from app/ui at root URL
app.mount("/ui/", SPAStaticFiles(directory="app/ui", html=True), name="ui")

def custom_openapi():
    """Custom OpenAPI schema generation function."""
    if app.openapi_schema: # type: ignore
        return app.openapi_schema # type: ignore

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="OpenAPI Ingestion & Local Vector-Search Service",
        routes=app.routes,  # type: ignore
    )

    # You can customize the OpenAPI schema here if needed
    # For example, add security schemes for JWT auth when enabled
    if settings.ENABLE_AUTH:
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
        }
        # Apply security globally or to specific operations
        openapi_schema["security"] = [{"bearerAuth": []}]

    app.openapi_schema = openapi_schema  # type: ignore
    return app.openapi_schema # type: ignore


app.openapi = custom_openapi

# app.mount("/mcp/", mcp_app.sse_app())



# Explicit operation_id (tool will be named "find_api_spec")
@app.get(
    "/find_api_spec",
    operation_id="find_api_spec",
    description="Find any API endpoint documentation by service name and description.",
    tags=["API Search"],
)
async def find_api_spec(
    api_description: Annotated[str, Query(description="A brief description of the API endpoint goal to search for")]
    ) -> list[EndpointSearchResult]:
    """
    Find any API endpoint documentation by description.
    Search query for API endpoint documentation - e.g. "Search Slack messages" or "Create a github repository".
    This will return a list of API endpoints that match the description.
    """
    return search_endpoints_by_text(
            query_text=f"{api_description}",
            k=5,
            similarity_threshold=0.4,
    )
    
# Explicit operation_id (tool will be named "find_api_spec")
@app.get(
    "/find_docs",
    operation_id="find_docs",
    description="Find internal technical documentations any thing",
    tags=["API Search"],
)
async def find_docs(
    doc_description: Annotated[str, Query(description="A brief description of the document goal to search for")]
    ) -> list[DocumentSearchResult]:
    """
    Find any internal technical documentations by description.
    Search query for internal technical documentations - e.g. "Search Slack messages" or "Create a github repository".
    This will return a list of internal technical documentations that match the description.
    The search is performed using a vector search algorithm.
    """
    return search_documents_by_text(
            query_text=f"{doc_description}",
            k=5,
            similarity_threshold=0.4,
    )
# Only include specific operations
mcp = FastApiMCP(
    app,
    include_operations=["find_api_spec"]
)

mcp.mount()
