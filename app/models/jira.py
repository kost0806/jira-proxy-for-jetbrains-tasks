from pydantic import BaseModel
from typing import Optional, Dict, Any


class CreateIssueRequest(BaseModel):
    fields: Dict[str, Any]


class UpdateIssueRequest(BaseModel):
    fields: Optional[Dict[str, Any]] = None
    transition: Optional[Dict[str, str]] = None