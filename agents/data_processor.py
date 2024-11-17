import logging
from datetime import datetime
from typing import List, Optional

from storage.database import Database
from storage.models import DeveloperProfile, GitHubContributor, LinkedInProfile

logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self):
        self.db = Database()

    async def process_profiles(
        self,
        github_profiles: List[GitHubContributor],
        linkedin_profiles: List[Optional[LinkedInProfile]],
    ) -> List[DeveloperProfile]:
        processed_profiles = []

        for github_profile, linkedin_profile in zip(github_profiles, linkedin_profiles):
            try:
                profile = DeveloperProfile(
                    github_data=github_profile,
                    linkedin_data=linkedin_profile,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                await self.db.save_profile(profile)
                processed_profiles.append(profile)

            except Exception as e:
                logger.error(
                    f"Error processing profile for {github_profile.username}: {str(e)}"
                )
                continue

        return processed_profiles
