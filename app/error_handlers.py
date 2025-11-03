"""Error handlers for Jira Proxy"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import httpx
import logging
from app.exceptions import JiraProxyException

logger = logging.getLogger(__name__)


async def jira_proxy_exception_handler(request: Request, exc: JiraProxyException):
    """Handle custom Jira Proxy exceptions"""
    logger.error(f"JiraProxyException: {exc.message} - Details: {exc.details}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "type": exc.__class__.__name__
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions"""
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "HTTPException"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.error(f"ValidationError: {exc.errors()}")

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Request validation failed",
                "details": exc.errors(),
                "type": "ValidationError"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def httpx_exception_handler(request: Request, exc: httpx.HTTPStatusError):
    """Handle HTTPX HTTP errors (from Jira API calls)"""
    logger.error(f"Jira API Error: {exc.response.status_code} - {exc.response.text}")

    # Map Jira error codes to appropriate responses
    status_code = exc.response.status_code
    if status_code == 401:
        message = "Jira authentication failed"
    elif status_code == 403:
        message = "Permission denied for Jira operation"
    elif status_code == 404:
        message = "Jira resource not found"
    elif status_code == 429:
        message = "Jira API rate limit exceeded"
    elif 500 <= status_code < 600:
        message = "Jira server error"
    else:
        message = f"Jira API error: {exc.response.status_code}"

    try:
        error_details = exc.response.json()
    except:
        error_details = {"raw_response": exc.response.text}

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "details": error_details,
                "type": "JiraAPIError"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions"""
    logger.exception(f"Unhandled exception: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "InternalServerError"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )