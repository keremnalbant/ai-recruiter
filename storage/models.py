from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class GitHubActivityMetrics(BaseModel):
    total_commits: int = 0
    total_prs: int = 0
    total_issues: int = 0
    recent_commits: int = 0
    recent_prs: int = 0
    recent_issues: int = 0
    languages: Dict[str, int] = {}

class GitHubContributor(BaseModel):
    username: str
    contributions: int
    repos: List[str]
    email: Optional[str] = None
    name: Optional[str] = None
    linkedin_url: Optional[str] = None
    activity_metrics: Optional[GitHubActivityMetrics] = None
    is_maintainer: bool = False
    last_active: Optional[datetime] = None
    role: Optional[str] = None  # e.g., "Contributor", "Maintainer", "Owner"

class LinkedInProfile(BaseModel):
    profile_url: str  # Changed from HttpUrl to str for compatibility
    name: str
    current_position: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    volunteer: List[Dict[str, Any]] = Field(default_factory=list)


class DeveloperProfile(BaseModel):
    github_data: GitHubContributor
    linkedin_data: Optional[LinkedInProfile] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
