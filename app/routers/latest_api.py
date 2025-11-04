from fastapi import APIRouter, HTTPException, Query, Path, Body, Header
from typing import Optional
from app.services.jira_client import jira_client
from app.models.jira import CreateIssueRequest, UpdateIssueRequest
import logging

logger = logging.getLogger(__name__)

# Router for /rest/api/latest endpoints (JetBrains IDE compatibility)
router = APIRouter(prefix="/rest/api/latest")


@router.get("/serverInfo")
async def get_server_info(authorization: Optional[str] = Header(None)):
    """Get Jira server information - Required for JetBrains IDE compatibility (latest API)

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        return await jira_client.get_server_info()
    except Exception as e:
        logger.debug(f"Failed to get server info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get server information")


@router.get("/search")
async def search_issues(
    jql: str = Query(..., description="JQL query string"),
    startAt: int = Query(0, description="Starting index"),
    maxResults: int = Query(50, description="Maximum number of results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return"),
    authorization: Optional[str] = Header(None)
):
    """Search issues using JQL

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        field_list = fields.split(",") if fields else None
        return await jira_client.search_issues(jql, startAt, maxResults, field_list)
    except Exception as e:
        logger.debug(f"Failed to search issues: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search issues")


@router.get("/search/jql")
async def search_issues_jql(
    jql: str = Query(..., description="JQL query string"),
    startAt: int = Query(0, description="Starting index"),
    maxResults: int = Query(160, description="Maximum number of results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return"),
    authorization: Optional[str] = Header(None)
):
    """Search issues using JQL - JetBrains IDE specific endpoint

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        field_list = fields.split(",") if fields else None
        return await jira_client.search_issues(jql, startAt, maxResults, field_list)
    except Exception as e:
        logger.debug(f"Failed to search issues via JQL endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search issues")


@router.get("/issue/{issue_key}")
async def get_issue(
    issue_key: str = Path(..., description="Issue key (e.g., PROJ-123)"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return"),
    authorization: Optional[str] = Header(None)
):
    """Get specific issue by key

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        field_list = fields.split(",") if fields else None
        return await jira_client.get_issue(issue_key, field_list)
    except Exception as e:
        logger.debug(f"Failed to get issue {issue_key}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")


@router.put("/issue/{issue_key}")
async def update_issue(
    issue_key: str = Path(..., description="Issue key (e.g., PROJ-123)"),
    update_data: UpdateIssueRequest = Body(...),
    authorization: Optional[str] = Header(None)
):
    """Update an existing issue

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        await jira_client.update_issue(issue_key, update_data)
        return {"message": f"Issue {issue_key} updated successfully"}
    except Exception as e:
        logger.debug(f"Failed to update issue {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update issue {issue_key}")


@router.get("/issue/{issue_key}/transitions")
async def get_issue_transitions(
    issue_key: str = Path(..., description="Issue key (e.g., PROJ-123)"),
    authorization: Optional[str] = Header(None)
):
    """Get available transitions for an issue

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        return await jira_client.get_issue_transitions(issue_key)
    except Exception as e:
        logger.debug(f"Failed to get transitions for issue {issue_key}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")


@router.post("/issue/{issue_key}/transitions")
async def transition_issue(
    issue_key: str = Path(..., description="Issue key (e.g., PROJ-123)"),
    transition_data: dict = Body(..., description="Transition data with id and optional fields"),
    authorization: Optional[str] = Header(None)
):
    """Transition an issue to a new status

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        transition_id = transition_data.get("transition", {}).get("id")
        if not transition_id:
            raise HTTPException(status_code=400, detail="Transition ID is required")

        fields = transition_data.get("fields")
        await jira_client.transition_issue(issue_key, transition_id, fields)
        return {"message": f"Issue {issue_key} transitioned successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"Failed to transition issue {issue_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to transition issue {issue_key}")


@router.post("/issue")
async def create_issue(
    issue_data: CreateIssueRequest,
    authorization: Optional[str] = Header(None)
):
    """Create a new issue

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        return await jira_client.create_issue(issue_data)
    except Exception as e:
        logger.debug(f"Failed to create issue: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create issue")


@router.get("/project")
async def get_projects(authorization: Optional[str] = Header(None)):
    """Get all projects

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        return await jira_client.get_projects()
    except Exception as e:
        logger.debug(f"Failed to get projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get projects")


@router.get("/project/{project_key}")
async def get_project(
    project_key: str = Path(..., description="Project key (e.g., PROJ)"),
    authorization: Optional[str] = Header(None)
):
    """Get specific project by key

    Note: Authorization header is ignored. All requests use service account credentials from .env
    """
    try:
        return await jira_client.get_project(project_key)
    except Exception as e:
        logger.debug(f"Failed to get project {project_key}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Project {project_key} not found")


# Health check endpoint for the proxy
@router.get("/health")
async def health_check():
    """Health check endpoint - does not require authorization"""
    return {"status": "healthy", "message": "Proxy server is running. Authentication is handled per-request."}