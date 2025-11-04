import httpx
import base64
from typing import Optional, Dict, Any, List
from app.config import settings
from app.models.jira import (
    ServerInfo, Issue, SearchResult, TransitionResponse,
    CreateIssueRequest, UpdateIssueRequest, Project
)
from app.exceptions import (
    JiraConnectionError, JiraAuthenticationError, JiraNotFoundError,
    JiraPermissionError, JiraValidationError
)
from app.utils import create_service_auth_header
import logging

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.jira_base_url).rstrip('/')

    def _create_headers(self, acting_user: Optional[str] = None) -> Dict[str, str]:
        """
        Create headers for Jira API requests.

        Uses service account credentials for authentication.
        If acting_user is provided, adds X-Atlassian-User header for user impersonation
        (requires admin permissions on Jira Server/Data Center).

        Args:
            acting_user: Optional username to act as (for impersonation)

        Returns:
            Dictionary of HTTP headers
        """
        # Use service account credentials for authentication
        if settings.jira_service_username and settings.jira_service_api_token:
            auth_header = create_service_auth_header(
                settings.jira_service_username,
                settings.jira_service_api_token
            )
        else:
            logger.warning(
                "Service account credentials not configured. "
                "Please set JIRA_SERVICE_USERNAME and JIRA_SERVICE_API_TOKEN in .env"
            )
            # This will likely fail authentication, but we'll let Jira return the error
            auth_header = "Basic "

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Add impersonation header if acting user is provided
        # Note: This requires admin permissions on Jira Server/Data Center
        # Jira Cloud does not support this header
        if acting_user:
            headers["X-Atlassian-User"] = acting_user
            logger.debug(f"Added X-Atlassian-User header for impersonation: {acting_user}")

        return headers

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        authorization: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        acting_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Jira API.

        Uses service account credentials for authentication.
        If acting_user is provided, adds impersonation headers.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: Jira API endpoint
            authorization: Client authorization header (used only to extract acting user if needed)
            params: Query parameters
            json_data: JSON request body
            acting_user: Username to act as (for impersonation)

        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._create_headers(acting_user)

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

    async def get_server_info(self, authorization: str, acting_user: Optional[str] = None) -> ServerInfo:
        """Get Jira server information"""
        data = await self._make_request(
            "GET",
            "/rest/api/2/serverInfo",
            authorization,
            acting_user=acting_user
        )
        return ServerInfo(**data)

    async def search_issues(
        self,
        authorization: str,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: Optional[List[str]] = None,
        acting_user: Optional[str] = None
    ) -> SearchResult:
        """Search issues using JQL"""
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results
        }
        if fields:
            params["fields"] = ",".join(fields)

        # Use the new API v3 search/jql endpoint as the old ones are deprecated
        data = await self._make_request(
            "GET",
            "/rest/api/3/search/jql",
            authorization,
            params=params,
            acting_user=acting_user
        )

        # Convert the simplified response from search/jql to the full SearchResult format
        # The new endpoint returns a simplified format, so we need to transform it
        issues = data.get("issues", [])

        # If we have issues but they're simplified, we need to get full details
        if issues and isinstance(issues[0], dict) and "fields" not in issues[0]:
            # This is the simplified format, fetch full details for each issue
            full_issues = []
            for issue in issues:
                if "id" in issue:
                    try:
                        # Get the issue key from the basic info or construct it
                        issue_key = issue.get("key")
                        if not issue_key and "id" in issue:
                            # Try to get issue key from id - this is a workaround
                            issue_detail = await self._make_request(
                                "GET",
                                f"/rest/api/3/issue/{issue['id']}",
                                authorization,
                                acting_user=acting_user
                            )
                            full_issues.append(issue_detail)
                    except:
                        # If we can't get details, include what we have
                        full_issues.append(issue)

            result_data = {
                "expand": data.get("expand", ""),
                "startAt": start_at,
                "maxResults": max_results,
                "total": len(issues),  # We don't have total count in new API
                "issues": full_issues
            }
        else:
            # Already in the correct format or no issues
            result_data = {
                "expand": data.get("expand", ""),
                "startAt": start_at,
                "maxResults": max_results,
                "total": len(issues),
                "issues": issues
            }

        return SearchResult(**result_data)

    async def get_issue(
        self,
        authorization: str,
        issue_key: str,
        fields: Optional[List[str]] = None,
        acting_user: Optional[str] = None
    ) -> Issue:
        """Get specific issue by key"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        data = await self._make_request(
            "GET",
            f"/rest/api/2/issue/{issue_key}",
            authorization,
            params=params,
            acting_user=acting_user
        )
        return Issue(**data)

    async def get_issue_transitions(
        self,
        authorization: str,
        issue_key: str,
        acting_user: Optional[str] = None
    ) -> TransitionResponse:
        """Get available transitions for an issue"""
        data = await self._make_request(
            "GET",
            f"/rest/api/2/issue/{issue_key}/transitions",
            authorization,
            acting_user=acting_user
        )
        return TransitionResponse(**data)

    async def transition_issue(
        self,
        authorization: str,
        issue_key: str,
        transition_id: str,
        fields: Optional[Dict[str, Any]] = None,
        acting_user: Optional[str] = None
    ):
        """Transition an issue to a new status"""
        json_data = {
            "transition": {"id": transition_id}
        }
        if fields:
            json_data["fields"] = fields

        await self._make_request(
            "POST",
            f"/rest/api/2/issue/{issue_key}/transitions",
            authorization,
            json_data=json_data,
            acting_user=acting_user
        )

    async def create_issue(
        self,
        authorization: str,
        issue_data: CreateIssueRequest,
        acting_user: Optional[str] = None
    ) -> Issue:
        """Create a new issue"""
        data = await self._make_request(
            "POST",
            "/rest/api/2/issue",
            authorization,
            json_data=issue_data.dict(),
            acting_user=acting_user
        )
        return Issue(**data)

    async def update_issue(
        self,
        authorization: str,
        issue_key: str,
        update_data: UpdateIssueRequest,
        acting_user: Optional[str] = None
    ):
        """Update an existing issue"""
        await self._make_request(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            authorization,
            json_data=update_data.dict(exclude_none=True),
            acting_user=acting_user
        )

    async def get_projects(self, authorization: str, acting_user: Optional[str] = None) -> List[Project]:
        """Get all projects"""
        data = await self._make_request(
            "GET",
            "/rest/api/2/project",
            authorization,
            acting_user=acting_user
        )
        return [Project(**project) for project in data]

    async def get_project(
        self,
        authorization: str,
        project_key: str,
        acting_user: Optional[str] = None
    ) -> Project:
        """Get specific project by key"""
        data = await self._make_request(
            "GET",
            f"/rest/api/2/project/{project_key}",
            authorization,
            acting_user=acting_user
        )
        return Project(**data)


# Global client instance - no longer needs auth at startup
jira_client = JiraClient()