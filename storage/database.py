import logging

import motor.motor_asyncio

from config import settings
from storage.models import DeveloperProfile

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.DATABASE_URL)
        self.db = self.client.ai_recruiter
        self.profiles = self.db.profiles

    async def save_profile(self, profile: DeveloperProfile) -> bool:
        try:
            result = await self.profiles.update_one(
                {"github_data.username": profile.github_data.username},
                {"$set": profile.dict()},
                upsert=True,
            )
            return bool(result.acknowledged)
        except Exception as e:
            logger.error(f"Error saving profile to database: {str(e)}")
            return False
