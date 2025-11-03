"""Custom exceptions for Jira Proxy"""

from typing import Optional, Dict, Any


class JiraProxyException(Exception):
    """Base exception for Jira Proxy"""

    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class JiraConnectionError(JiraProxyException):
    """Raised when unable to connect to Jira"""

    def __init__(self, message: str = "Unable to connect to Jira server", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=503, details=details)


class JiraAuthenticationError(JiraProxyException):
    """Raised when Jira authentication fails"""

    def __init__(self, message: str = "Jira authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class JiraNotFoundError(JiraProxyException):
    """Raised when Jira resource is not found"""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class JiraPermissionError(JiraProxyException):
    """Raised when user doesn't have permission for Jira operation"""

    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class JiraValidationError(JiraProxyException):
    """Raised when Jira request validation fails"""

    def __init__(self, message: str = "Request validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)