"""Main application for notification service"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.config import settings
from app.apis.containers import AppContainer
from app.apis.notification.consumer import start_consumer
from app.apis.routers import get_app_router

def create_app(container: AppContainer = AppContainer()) -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Notification Service",
        description="Notification Service",
        version="1.0.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    # Store container
    app.container = container

    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL] + settings.DEBUG_FRONT_URLS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app_router = get_app_router()
    app.include_router(
        app_router,
    )
    
    @app.get("/sanity-check")
    def sanity_check():
        """Health check endpoint"""
        return "Notification Service running!"
    
    @app.on_event("startup")
    async def startup_event():
        """Start the RabbitMQ consumer on application startup"""
        app.rabbitmq_consumer = await start_consumer(
            app.container.notification_container.notification_repository()
        )
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Stop the RabbitMQ consumer on application shutdown"""
        if hasattr(app, "rabbitmq_consumer"):
            await app.rabbitmq_consumer.stop()
    
    return app