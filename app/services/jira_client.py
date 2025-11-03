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
import logging

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.jira_base_url).rstrip('/')

    def _create_headers(self, authorization: str) -> Dict[str, str]:
        """Create headers with the provided authorization"""
        return {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        authorization: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Jira API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._create_headers(authorization)

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

    async def get_server_info(self, authorization: str) -> ServerInfo:
        """Get Jira server information"""
        data = await self._make_request("GET", "/rest/api/2/serverInfo", authorization)
        return ServerInfo(**data)

    async def search_issues(
        self,
        authorization: str,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: Optional[List[str]] = None
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
        data = await self._make_request("GET", "/rest/api/3/search/jql", authorization, params=params)

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
                            issue_detail = await self._make_request("GET", f"/rest/api/3/issue/{issue['id']}", authorization)
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

    async def get_issue(self, authorization: str, issue_key: str, fields: Optional[List[str]] = None) -> Issue:
        """Get specific issue by key"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        data = await self._make_request("GET", f"/rest/api/2/issue/{issue_key}", authorization, params=params)
        return Issue(**data)

    async def get_issue_transitions(self, authorization: str, issue_key: str) -> TransitionResponse:
        """Get available transitions for an issue"""
        data = await self._make_request("GET", f"/rest/api/2/issue/{issue_key}/transitions", authorization)
        return TransitionResponse(**data)

    async def transition_issue(self, authorization: str, issue_key: str, transition_id: str, fields: Optional[Dict[str, Any]] = None):
        """Transition an issue to a new status"""
        json_data = {
            "transition": {"id": transition_id}
        }
        if fields:
            json_data["fields"] = fields

        await self._make_request("POST", f"/rest/api/2/issue/{issue_key}/transitions", authorization, json_data=json_data)

    async def create_issue(self, authorization: str, issue_data: CreateIssueRequest) -> Issue:
        """Create a new issue"""
        data = await self._make_request("POST", "/rest/api/2/issue", authorization, json_data=issue_data.dict())
        return Issue(**data)

    async def update_issue(self, authorization: str, issue_key: str, update_data: UpdateIssueRequest):
        """Update an existing issue"""
        await self._make_request("PUT", f"/rest/api/2/issue/{issue_key}", authorization, json_data=update_data.dict(exclude_none=True))

    async def get_projects(self, authorization: str) -> List[Project]:
        """Get all projects"""
        data = await self._make_request("GET", "/rest/api/2/project", authorization)
        return [Project(**project) for project in data]

    async def get_project(self, authorization: str, project_key: str) -> Project:
        """Get specific project by key"""
        data = await self._make_request("GET", f"/rest/api/2/project/{project_key}", authorization)
        return Project(**data)


# Global client instance - no longer needs auth at startup
jira_client = JiraClient()