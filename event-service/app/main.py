from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.config import settings
from app.apis.containers import AppContainer
from app.apis.routers import get_app_router


def create_app(container: AppContainer = AppContainer()) -> FastAPI:
    app = FastAPI(
        title="Event Service",
        description="Event Service",
        version="1.0.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL] + settings.DEBUG_FRONT_URLS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app_router = get_app_router()

    @app_router.get("/sanity-check")
    def sanity_check():
        return "FastAPI running!"

    app.include_router(app_router)
    return app
