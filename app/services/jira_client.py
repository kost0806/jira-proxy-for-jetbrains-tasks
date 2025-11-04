import httpx
import base64
from typing import Optional, Dict, Any, List
from app.config import settings
from app.models.jira import CreateIssueRequest, UpdateIssueRequest
from app.exceptions import (
    JiraConnectionError, JiraAuthenticationError, JiraNotFoundError,
    JiraPermissionError, JiraValidationError
)
import logging

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.jira_base_url).rstrip('/')

    def _create_headers(self) -> Dict[str, str]:
        """
        Create headers for Jira API requests using service account credentials.

        Returns:
            Dictionary of HTTP headers

        Raises:
            ValueError: If service account credentials are not configured
        """
        # Always use service account credentials
        if not settings.jira_service_username or not settings.jira_service_api_token:
            raise ValueError(
                "Service account credentials not configured. "
                "Please set JIRA_SERVICE_USERNAME and JIRA_SERVICE_API_TOKEN in .env"
            )

        # Create service account authorization
        credentials = f"{settings.jira_service_username}:{settings.jira_service_api_token}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        auth_header = f"Basic {encoded_credentials}"

        return {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Jira API using service account credentials.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: Jira API endpoint
            params: Query parameters
            json_data: JSON request body

        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._create_headers()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.ConnectError as e:
                logger.error(f"Connection error to Jira: {str(e)}")
                raise JiraConnectionError(f"Unable to connect to Jira at {self.base_url}")
            except httpx.TimeoutException as e:
                logger.error(f"Timeout error: {str(e)}")
                raise JiraConnectionError("Request to Jira timed out")
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                logger.error(f"HTTP error {status_code}: {e.response.text}")

                if status_code == 401:
                    raise JiraAuthenticationError("Invalid Jira credentials")
                elif status_code == 403:
                    raise JiraPermissionError("Insufficient permissions for Jira operation")
                elif status_code == 404:
                    raise JiraNotFoundError("Jira resource not found")
                elif status_code == 400:
                    raise JiraValidationError("Invalid request to Jira API")
                else:
                    # Re-raise the original exception for other status codes
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise JiraConnectionError(f"Unexpected error communicating with Jira: {str(e)}")

    async def get_server_info(self) -> Dict[str, Any]:
        """Get Jira server information"""
        return await self._make_request("GET", "/rest/api/2/serverInfo")

    async def search_issues(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search issues using JQL"""
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results
        }
        if fields:
            params["fields"] = ",".join(fields)

        # Use the standard API v2 search endpoint
        return await self._make_request("GET", "/rest/api/2/search", params=params)

    async def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get specific issue by key"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        return await self._make_request("GET", f"/rest/api/2/issue/{issue_key}", params=params)

    async def get_issue_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for an issue"""
        return await self._make_request("GET", f"/rest/api/2/issue/{issue_key}/transitions")

    async def transition_issue(self, issue_key: str, transition_id: str, fields: Optional[Dict[str, Any]] = None):
        """Transition an issue to a new status"""
        json_data = {
            "transition": {"id": transition_id}
        }
        if fields:
            json_data["fields"] = fields

        await self._make_request("POST", f"/rest/api/2/issue/{issue_key}/transitions", json_data=json_data)

    async def create_issue(self, issue_data: CreateIssueRequest) -> Dict[str, Any]:
        """Create a new issue"""
        return await self._make_request("POST", "/rest/api/2/issue", json_data=issue_data.dict())

    async def update_issue(self, issue_key: str, update_data: UpdateIssueRequest):
        """Update an existing issue"""
        await self._make_request("PUT", f"/rest/api/2/issue/{issue_key}", json_data=update_data.dict(exclude_none=True))

    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        return await self._make_request("GET", "/rest/api/2/project")

    async def get_project(self, project_key: str) -> Dict[str, Any]:
        """Get specific project by key"""
        return await self._make_request("GET", f"/rest/api/2/project/{project_key}")


# Global client instance - no longer needs auth at startup
jira_client = JiraClient()