from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from agents.base_agent import BaseAgent
from scrapers.linkedin_scraper import LinkedInScraper
from storage.models import LinkedInProfile


class LinkedInRequest(BaseModel):
    profile_urls: List[str]


class LinkedInAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.scraper = LinkedInScraper()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process LinkedIn profile requests."""
        request = LinkedInRequest(**input_data)
        
        profiles_data = []
        for url in request.profile_urls:
            try:
                profile = await self.scraper.get_profile_from_url(url)
                if profile:
                    profile_data = {
                        "linkedin_url": profile.profile_url,
                        "name": profile.name,
                        "current_position": profile.current_position,
                        "company": profile.company,
                        "location": profile.location,
                        "experience": await self._extract_experience(profile)
                    }
                    profiles_data.append(profile_data)
            except Exception as e:
                # Log error and continue with next profile
                profiles_data.append({
                    "linkedin_url": url,
                    "error": str(e)
                })

        return {
            "total_profiles": len(profiles_data),
            "successful_scrapes": len([p for p in profiles_data if "error" not in p]),
            "profiles": profiles_data
        }

    async def _extract_experience(self, profile: LinkedInProfile) -> Dict[str, Any]:
        """Extract structured experience information from LinkedIn profile."""
        # Note: This would require extending the LinkedInProfile model and scraper
        # to include detailed experience information
        return {
            "years_of_experience": self._calculate_years_of_experience(profile),
            "current_position": profile.current_position,
            "current_company": profile.company
        }

    def _calculate_years_of_experience(self, profile: LinkedInProfile) -> Optional[int]:
        """Calculate total years of experience based on profile data."""
        # This is a placeholder - actual implementation would depend on
        # enhanced LinkedIn profile data including work history
        return None
