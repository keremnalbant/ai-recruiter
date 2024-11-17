from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GitHubContributor(BaseModel):
    username: str
    contributions: int
    repos: List[str]
    email: Optional[str] = None
    name: Optional[str] = None
    linkedin_url: Optional[str] = None


class LinkedInProfile(BaseModel):
    profile_url: str
    name: str
    current_position: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None


class DeveloperProfile(BaseModel):
    github_data: GitHubContributor
    linkedin_data: Optional[LinkedInProfile] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
