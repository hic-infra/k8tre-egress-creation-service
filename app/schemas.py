from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class Paths(BaseModel):
    paths: list[str] 

class JupyterHubUser(BaseModel):
    kind: str
    last_activity: datetime
    groups: list[str]
    name: str
    admin: bool
    token_id: str
    session_id: Optional[str] = None
    scopes: list[str]