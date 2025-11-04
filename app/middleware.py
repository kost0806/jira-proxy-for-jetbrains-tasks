"""Middleware for Jira Proxy"""

import time
import uuid
import json
from typing import Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with body content"""

    SENSITIVE_FIELDS = {
        "password", "passwd", "secret", "token", "key", "authorization",
        "auth", "credential", "credentials", "api_key", "apikey"
    }

    MAX_BODY_SIZE = 2000  # Maximum body size to log

    def _filter_sensitive_data(self, data: dict) -> dict:
        """Filter sensitive data from request/response bodies"""
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                filtered[key] = "***FILTERED***"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            elif isinstance(value, list):
                filtered[key] = [self._filter_sensitive_data(item) if isinstance(item, dict) else item for item in value]
            else:
                filtered[key] = value
        return filtered

    def _format_body_for_logging(self, body: bytes) -> Optional[str]:
        """Format body content for logging"""
        if not body:
            return None

        try:
            # Try to parse as JSON
            body_json = json.loads(body)
            filtered_body = self._filter_sensitive_data(body_json)
            formatted = json.dumps(filtered_body, indent=2, ensure_ascii=False)

            # Truncate if too long
            if len(formatted) > self.MAX_BODY_SIZE:
                formatted = formatted[:self.MAX_BODY_SIZE] + "\n...(truncated)"

            return formatted
        except json.JSONDecodeError:
            # If not JSON, return as string (truncated if too long)
            try:
                body_str = body.decode('utf-8', errors='ignore')
                if len(body_str) > self.MAX_BODY_SIZE:
                    body_str = body_str[:self.MAX_BODY_SIZE] + "...(truncated)"
                return body_str
            except:
                return f"<binary data: {len(body)} bytes>"

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Skip logging for health check endpoints
        is_health_check = request.url.path.endswith("/health")

        # Log basic request info
        start_time = time.time()

        if not is_health_check:
            client_host = request.client.host if request.client else 'unknown'
            query_params = str(request.query_params) if request.query_params else ""

            log_msg = f"Request {request_id}: {request.method} {request.url.path} from {client_host}"
            if query_params:
                log_msg += f"\nQuery: {query_params}"

            # Try to get request body for logging
            try:
                if request.method in ("POST", "PUT", "PATCH"):
                    body = await request.body()
                    if body:
                        formatted_body = self._format_body_for_logging(body)
                        if formatted_body:
                            log_msg += f"\nRequest Body:\n{formatted_body}"
            except Exception as e:
                logger.debug(f"Failed to read request body: {e}")

            logger.debug(log_msg)

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response (skip for health check)
            if not is_health_check:
                log_msg = f"Response {request_id}: {response.status_code} in {process_time:.3f}s"

                # Try to get response body for logging
                try:
                    if (hasattr(response, 'body') and
                        response.headers.get('content-type', '').startswith('application/json')):

                        if hasattr(response, 'body') and response.body:
                            formatted_body = self._format_body_for_logging(response.body)
                            if formatted_body:
                                log_msg += f"\nResponse Body:\n{formatted_body}"
                except Exception as e:
                    logger.debug(f"Failed to read response body: {e}")

                logger.debug(log_msg)

            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error {request_id}: {str(e)} "
                f"in {process_time:.3f}s"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response