from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import httpx
from app.config import settings
from app.routers import jira_api
from app.middleware import LoggingMiddleware, SecurityHeadersMiddleware
from app.error_handlers import (
    jira_proxy_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    httpx_exception_handler,
    generic_exception_handler
)
from app.exceptions import JiraProxyException
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(JiraProxyException, jira_proxy_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(httpx.HTTPStatusError, httpx_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(jira_api.router)

# Import and include latest API router for JetBrains compatibility
from app.routers import latest_api
app.include_router(latest_api.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Jira API Proxy Server",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Jira API Proxy Server")
    logger.info(f"Jira Base URL: {settings.jira_base_url}")
    logger.info(f"Debug mode: {settings.debug}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Jira API Proxy Server")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.proxy_host,
        port=settings.proxy_port,
        reload=settings.debug
    )