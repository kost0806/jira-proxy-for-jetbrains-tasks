from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ServerInfo(BaseModel):
    baseUrl: str
    displayUrl: Optional[str] = None
    displayUrlServicedeskHelpCenter: Optional[str] = None
    displayUrlCSMHelpSeeker: Optional[str] = None
    displayUrlConfluence: Optional[str] = None
    version: str
    versionNumbers: List[int]
    deploymentType: str
    buildNumber: int
    buildDate: str
    databaseBuildNumber: Optional[int] = None  # Not present in Jira Cloud
    serverTime: Optional[str] = None
    scmInfo: str
    serverTitle: str
    defaultLocale: Optional[Dict[str, str]] = None
    serverTimeZone: Optional[str] = None


class User(BaseModel):
    accountId: Optional[str] = None
    accountType: Optional[str] = None
    name: Optional[str] = None
    key: Optional[str] = None
    emailAddress: Optional[str] = None
    displayName: str
    active: bool = True
    timeZone: Optional[str] = None
    locale: Optional[str] = None


class Priority(BaseModel):
    id: str
    name: str
    iconUrl: Optional[str] = None


class IssueType(BaseModel):
    id: str
    name: str
    subtask: bool = False
    iconUrl: Optional[str] = None
    description: Optional[str] = None


class Status(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    iconUrl: Optional[str] = None
    statusCategory: Optional[Dict[str, Any]] = None


class Project(BaseModel):
    id: str
    key: str
    name: str
    description: Optional[str] = None
    lead: Optional[User] = None
    projectTypeKey: Optional[str] = None
    avatarUrls: Optional[Dict[str, str]] = None


class Fields(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[User] = None
    reporter: Optional[User] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    resolution: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    project: Optional[Project] = None
    issuetype: Optional[IssueType] = None


class Issue(BaseModel):
    id: str
    key: str
    self: str
    fields: Fields
    expand: Optional[str] = None


class SearchResult(BaseModel):
    expand: Optional[str] = None
    startAt: int
    maxResults: int
    total: int
    issues: List[Issue]


class Transition(BaseModel):
    id: str
    name: str
    to: Status
    fields: Optional[Dict[str, Any]] = None


class TransitionResponse(BaseModel):
    transitions: List[Transition]


class CreateIssueRequest(BaseModel):
    fields: Dict[str, Any]


class UpdateIssueRequest(BaseModel):
    fields: Optional[Dict[str, Any]] = None
    transition: Optional[Dict[str, str]] = None


class ErrorResponse(BaseModel):
    errorMessages: List[str]
    errors: Optional[Dict[str, str]] = None