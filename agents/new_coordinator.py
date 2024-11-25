from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from agents.base_agent import BaseAgent
from agents.github_agent import GitHubAgent
from agents.linkedin_agent import LinkedInAgent


class CoordinatorRequest(BaseModel):
    task_description: str
    limit: int = 50


class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.github_agent = GitHubAgent()
        self.linkedin_agent = LinkedInAgent()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and coordinate tasks between agents."""
        request = CoordinatorRequest(**input_data)
        
        # Extract GitHub repository information using LLM
        repo_info = await self._extract_repository_info(request.task_description)
        
        # Get GitHub profiles
        github_result = await self.github_agent.process({
            "repository_name": repo_info,
            "type": "contributors",
            "limit": request.limit
        })
        
        # Extract LinkedIn URLs from GitHub profiles
        linkedin_urls = []
        for profile in github_result["profiles"]:
            if "social_urls" in profile and "linkedin" in profile["social_urls"]:
                linkedin_urls.append(profile["social_urls"]["linkedin"])
        
        # Get LinkedIn profiles if URLs are found
        linkedin_result = None
        if linkedin_urls:
            linkedin_result = await self.linkedin_agent.process({
                "profile_urls": linkedin_urls
            })
        
        # Combine results
        return await self._merge_results(github_result, linkedin_result)

    async def _extract_repository_info(self, task_description: str) -> str:
        """Extract repository information from task description using LLM."""
        repo_prompt = f"""Extract the GitHub repository name from this request: "{task_description}"
        Rules:
        - Return ONLY the repository path in "owner/repo" format, no other text
        - Handle various input formats:
          * Explicit paths: "owner/repo"
          * Organization mentions: "openai repository" -> "openai/openai"
          * Repository mentions: "openai's gpt-3 repo" -> "openai/gpt-3"
          * URLs: "https://github.com/owner/repo" -> "owner/repo"
        - If only organization is mentioned without specific repo:
          * Use the organization name as both owner and repo
        - If URL is provided, extract only owner/repo part
        """
        
        repo = await self._parse_with_llm(repo_prompt)
        if "/" not in repo or len(repo.split("/")) != 2:
            raise ValueError(f"Invalid repository format: {repo}. Expected format: owner/repo")
        return repo

    async def _merge_results(
        self, 
        github_result: Dict[str, Any], 
        linkedin_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge GitHub and LinkedIn results into a single response."""
        merged_profiles = []
        
        # Create a map of LinkedIn profiles by URL for easier lookup
        linkedin_profiles_map = {}
        if linkedin_result:
            linkedin_profiles_map = {
                p["linkedin_url"]: p 
                for p in linkedin_result["profiles"] 
                if "error" not in p
            }
        
        # Merge each GitHub profile with its corresponding LinkedIn data
        for github_profile in github_result["profiles"]:
            merged_profile = {
                "github_info": {
                    "username": github_profile["github_username"],
                    "url": github_profile["github_url"],
                    "contributions": github_profile["contributions"],
                    "email": github_profile["email"]
                },
                "name": github_profile["name"],
                "social_urls": github_profile["social_urls"],
            }
            
            # Add LinkedIn data if available
            if "linkedin" in github_profile["social_urls"]:
                linkedin_url = github_profile["social_urls"]["linkedin"]
                if linkedin_url in linkedin_profiles_map:
                    linkedin_data = linkedin_profiles_map[linkedin_url]
                    merged_profile["linkedin_info"] = {
                        "url": linkedin_url,
                        "current_position": linkedin_data["current_position"],
                        "company": linkedin_data["company"],
                        "location": linkedin_data["location"],
                        "experience": linkedin_data["experience"]
                    }
            
            merged_profiles.append(merged_profile)
        
        return {
            "repository": github_result["repository"],
            "total_profiles": len(merged_profiles),
            "profiles_with_linkedin": len([p for p in merged_profiles if "linkedin_info" in p]),
            "profiles": merged_profiles
        }
