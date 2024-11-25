from typing import Any, Dict, List, Optional

import aiohttp
from datetime import datetime, timedelta

from config import settings
from storage.models import GitHubContributor


class GitHubScraper:
    def __init__(self):
        self.headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}

    async def validate_repository(self, repo: str) -> bool:
        """Check if a GitHub repository exists and is accessible."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"https://api.github.com/repos/{repo}"
            ) as response:
                return response.status == 200

    async def get_activity_metrics(self, repo: str, username: str) -> Dict[str, Any]:
        """Get detailed activity metrics for a user in a repository."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Get commit activity
            async with session.get(
                f"https://api.github.com/repos/{repo}/commits",
                params={"author": username, "per_page": 100}
            ) as response:
                commits = await response.json() if response.status == 200 else []

            # Get PR activity
            async with session.get(
                f"https://api.github.com/repos/{repo}/pulls",
                params={"creator": username, "state": "all", "per_page": 100}
            ) as response:
                prs = await response.json() if response.status == 200 else []

            # Get issue activity
            async with session.get(
                f"https://api.github.com/repos/{repo}/issues",
                params={"creator": username, "state": "all", "per_page": 100}
            ) as response:
                issues = await response.json() if response.status == 200 else []

            # Calculate metrics
            recent_date = datetime.now() - timedelta(days=90)
            metrics = {
                "total_commits": len(commits),
                "total_prs": len(prs),
                "total_issues": len(issues),
                "recent_commits": sum(1 for c in commits if datetime.fromisoformat(c["commit"]["author"]["date"].rstrip('Z')) > recent_date),
                "recent_prs": sum(1 for pr in prs if datetime.fromisoformat(pr["created_at"].rstrip('Z')) > recent_date),
                "recent_issues": sum(1 for i in issues if datetime.fromisoformat(i["created_at"].rstrip('Z')) > recent_date),
                "languages": await self.get_user_languages(username)
            }
            
            return metrics

    async def get_user_languages(self, username: str) -> Dict[str, int]:
        """Get programming languages used by a user across their repositories."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Get user's repositories
            async with session.get(
                f"https://api.github.com/users/{username}/repos",
                params={"per_page": 100, "sort": "updated"}
            ) as response:
                if response.status != 200:
                    return {}
                
                repos = await response.json()
                
                # Aggregate languages across repositories
                languages = {}
                for repo in repos[:10]:  # Limit to most recent 10 repos
                    async with session.get(repo["languages_url"]) as lang_response:
                        if lang_response.status == 200:
                            repo_languages = await lang_response.json()
                            for lang, bytes_count in repo_languages.items():
                                languages[lang] = languages.get(lang, 0) + bytes_count
                
                return languages

    async def get_repository_info(self, repo: str) -> Dict[str, Any]:
        """Get basic information about a repository."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"https://api.github.com/repos/{repo}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"GitHub API error: {response.status}")

    async def get_maintainers(self, repo: str) -> List[GitHubContributor]:
        """Get repository maintainers (users with push access)."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"https://api.github.com/repos/{repo}/collaborators?permission=push"
            ) as response:
                if response.status == 200:
                    collaborators_data = await response.json()
                    maintainers = []
                    
                    for data in collaborators_data:
                        maintainer = GitHubContributor(
                            username=data["login"],
                            contributions=0,  # Not applicable for maintainers
                            repos=[repo],
                            email=data.get("email"),
                            name=data.get("name"),
                            linkedin_url=data.get("blog"),
                        )
                        maintainers.append(maintainer)
                    
                    return maintainers
                else:
                    raise Exception(f"GitHub API error: {response.status}")

    async def get_contributors(
        self, repo: str, limit: int = 50
    ) -> List[GitHubContributor]:
        """Get contributors for a GitHub repository with additional filtering options."""
        # Get basic contributor data
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
