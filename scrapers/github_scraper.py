from typing import List

import aiohttp

from config import settings
from storage.models import GitHubContributor


class GitHubScraper:
    def __init__(self):
        self.headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}

    async def get_contributors(
        self, repo: str, limit: int = 50
    ) -> List[GitHubContributor]:
        """Get contributors for a GitHub repository."""

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"https://api.github.com/repos/{repo}/contributors?per_page={limit}"
            ) as response:
                if response.status == 200:
                    contributors_data = await response.json()

                    contributors = []
                    for data in contributors_data[:limit]:
                        # Get additional user details
                        async with session.get(data["url"]) as user_response:
                            if user_response.status == 200:
                                user_data = await user_response.json()

                                contributor = GitHubContributor(
                                    username=data["login"],
                                    contributions=data["contributions"],
                                    repos=[repo],
                                    email=user_data.get("email"),
                                    name=user_data.get("name"),
                                    linkedin_url=user_data.get("blog"),
                                )
                                contributors.append(contributor)

                    return contributors
                else:
                    raise Exception(f"GitHub API error: {response.status}")
