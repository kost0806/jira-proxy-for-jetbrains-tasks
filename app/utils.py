"""Utility functions for the Jira API Proxy"""

import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_username_from_auth_header(authorization: str) -> Optional[str]:
    """
    Extract username from Authorization header.

    Supports both Basic and Bearer authentication formats:
    - Basic: "Basic base64(username:password)"
    - Bearer: "Bearer token" (returns None as no username can be extracted)

    Args:
        authorization: The Authorization header value

    Returns:
        The extracted username, or None if extraction fails

    Example:
        >>> extract_username_from_auth_header("Basic dXNlcm5hbWU6cGFzc3dvcmQ=")
        'username'
    """
    if not authorization:
        logger.debug("No authorization header provided")
        return None

    try:
        # Handle Basic authentication
        if authorization.startswith("Basic "):
            # Extract base64 encoded credentials
            encoded_credentials = authorization.replace("Basic ", "").strip()

            # Decode base64
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")

            # Split username and password
            if ":" in decoded_credentials:
                username = decoded_credentials.split(":", 1)[0]
                logger.debug(f"Extracted username from Basic auth: {username}")
                return username
            else:
                logger.warning("Invalid Basic auth format: no colon separator found")
                return None

        # Handle Bearer authentication
        elif authorization.startswith("Bearer "):
            # Bearer tokens don't contain username information
            logger.debug("Bearer token provided, no username can be extracted")
            return None

        else:
            logger.warning(f"Unknown authorization format: {authorization[:20]}...")
            return None

    except Exception as e:
        logger.error(f"Failed to extract username from authorization header: {str(e)}")
        return None


def create_service_auth_header(username: str, api_token: str) -> str:
    """
    Create a Basic authentication header from username and API token.

    Args:
        username: The Jira username or email
        api_token: The Jira API token

    Returns:
        A formatted Authorization header value

    Example:
        >>> create_service_auth_header("user@example.com", "token123")
        'Basic dXNlckBleGFtcGxlLmNvbTp0b2tlbjEyMw=='
    """
    credentials = f"{username}:{api_token}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded_credentials}"
