"""Platform service entry point."""

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.exceptions import (
    ArtworkDeadlinePassedError,
    CampaignNotActiveError,
    InsufficientCapacityError,
    InvalidStateTransitionError,
)
from platform_api.auth.router import router as auth_router
from platform_api.catalog.router import router as catalog_router
from platform_api.campaigns.router import router as campaigns_router
from platform_api.commerce.router import router as commerce_router, webhook_router
from platform_api.jobs.router import router as jobs_router

app = FastAPI(
    title="WIC API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CampaignNotActiveError)
async def campaign_not_active_handler(
    _request: Request, exc: CampaignNotActiveError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message or "Campaign is not active"},
    )


@app.exception_handler(InsufficientCapacityError)
async def insufficient_capacity_handler(
    _request: Request, exc: InsufficientCapacityError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message or "Campaign has reached maximum capacity"},
    )


@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_transition_handler(
    _request: Request, exc: InvalidStateTransitionError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message or "Invalid state transition"},
    )


@app.exception_handler(ArtworkDeadlinePassedError)
async def artwork_deadline_passed_handler(
    _request: Request, exc: ArtworkDeadlinePassedError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message or "Artwork upload deadline has passed"},
    )


app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(campaigns_router)
app.include_router(commerce_router)
app.include_router(webhook_router)
app.include_router(jobs_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check for load balancers and monitoring."""
    return {"status": "ok"}
