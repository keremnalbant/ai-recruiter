from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from agents.base_agent import BaseAgent
from scrapers.github_scraper import GitHubScraper
from storage.models import GitHubContributor


class GitHubRequest(BaseModel):
    repository_name: str
    type: str = "contributors"  # can be "contributors", "maintainers", etc.
    limit: int = 50


class GitHubAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.scraper = GitHubScraper()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process GitHub-related requests."""
        request = GitHubRequest(**input_data)
        
        # Validate repository
        if not await self.scraper.validate_repository(request.repository_name):
            raise ValueError(f"Repository {request.repository_name} not found or not accessible")

        # Get contributors/maintainers based on type
        if request.type == "contributors":
            profiles = await self.scraper.get_contributors(
                request.repository_name, limit=request.limit
            )
        else:
            raise ValueError(f"Unsupported request type: {request.type}")

        # Extract social profiles and additional information
        enriched_profiles = []
        for profile in profiles:
            enriched_profile = {
                "github_username": profile.username,
                "github_url": f"https://github.com/{profile.username}",
                "name": profile.name,
                "email": profile.email,
                "contributions": profile.contributions,
                "social_urls": await self._extract_social_urls(profile)
            }
            enriched_profiles.append(enriched_profile)

        return {
            "repository": request.repository_name,
            "type": request.type,
            "total_profiles": len(enriched_profiles),
            "profiles": enriched_profiles
        }

    async def _extract_social_urls(self, profile: GitHubContributor) -> Dict[str, str]:
        """Extract social URLs from GitHub profile."""
        social_urls = {}
        
        # Extract LinkedIn URL if available
        if profile.linkedin_url:
            social_urls["linkedin"] = profile.linkedin_url

        # Additional social URL extraction can be added here
        # For example, Twitter, personal website, etc.

        return social_urls
