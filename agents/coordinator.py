import asyncio
from typing import List, Optional

from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr

from agents.data_processor import DataProcessor
from config import settings
from scrapers.github_scraper import GitHubScraper
from scrapers.linkedin_scraper import LinkedInScraper
from storage.models import DeveloperProfile, LinkedInProfile


class CoordinatorAgent:
    def __init__(self):
        # Convert SecretStr to str and create a new SecretStr instance
        api_key = SecretStr(settings.ANTHROPIC_API_KEY.get_secret_value())
        self.llm = ChatAnthropic(
            anthropic_api_key=api_key, model_name="claude-3-sonnet"
        )
        self.github_scraper = GitHubScraper()
        self.linkedin_scraper = LinkedInScraper()
        self.data_processor = DataProcessor()

    async def execute_task(
        self, task_description: str, limit: int = 50
    ) -> List[DeveloperProfile]:
        """
        Execute the recruitment task.

        Args:
            task_description: Natural language description of the task
            limit: Maximum number of developers to find
        """
        # Get GitHub contributors
        github_profiles = await self.github_scraper.get_contributors(
            "langchain-ai/langchain", limit=limit
        )

        # Process profiles in parallel
        linkedin_tasks = []
        for github_profile in github_profiles:
            # First try to get LinkedIn from GitHub profile
            if github_profile.linkedin_url:
                linkedin_tasks.append(
                    self._get_linkedin_from_url(github_profile.linkedin_url)
                )
            else:
                # Fallback to search by name
                linkedin_tasks.append(
                    self.linkedin_scraper.find_profile(
                        github_profile.name or github_profile.username
                    )
                )

        linkedin_profiles = await asyncio.gather(*linkedin_tasks)

        # Combine and process the data
        return await self.data_processor.process_profiles(
            github_profiles, linkedin_profiles
        )

    async def _get_linkedin_from_url(self, url: str) -> Optional[LinkedInProfile]:
        """Get LinkedIn profile directly from URL."""
        try:
            return await self.linkedin_scraper.get_profile_from_url(url)
        except Exception:
            return None
