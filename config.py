from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GITHUB_TOKEN: SecretStr = SecretStr("")
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: SecretStr = SecretStr("")
    ANTHROPIC_API_KEY: SecretStr = SecretStr("")
    DATABASE_URL: str = "mongodb://localhost:27017"
    RATE_LIMIT_GITHUB: int = 5000  # requests per hour
    RATE_LIMIT_LINKEDIN: int = 100  # requests per hour

    class Config:
        env_file = ".env"


settings = Settings()
