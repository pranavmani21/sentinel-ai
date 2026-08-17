"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine

from sentinel_api.config import get_settings
from sentinel_api.database import create_engine, database_is_ready


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str
    service: str
    environment: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and dispose process-level resources."""

    engine = create_engine()
    app.state.database_engine = engine
    yield
    await engine.dispose()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Agentic incident investigation and response API.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
async def health() -> HealthResponse:
    """Return process liveness without checking downstream services."""

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )


@app.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
    tags=["operations"],
)
async def readiness(request: Request, response: Response) -> HealthResponse:
    """Return readiness based on database connectivity."""

    engine: AsyncEngine = request.app.state.database_engine
    ready = await database_is_ready(engine)
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ready" if ready else "not_ready",
        service=settings.app_name,
        environment=settings.app_env,
    )

