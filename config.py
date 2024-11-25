from pydantic import SecretStr
from pydantic_settings import BaseSettings


from typing import Dict, Optional

class Settings(BaseSettings):
    # Version
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "production"

    # API Credentials
    GITHUB_TOKEN: SecretStr = SecretStr("")
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: SecretStr = SecretStr("")
    ANTHROPIC_API_KEY: SecretStr = SecretStr("")

    # Database
    DATABASE_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "github_linkedin_analyzer"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limits
    RATE_LIMIT_GITHUB: int = 5000  # requests per hour
    RATE_LIMIT_LINKEDIN: int = 100  # requests per hour
    RATE_LIMIT_DEFAULT: int = 1000  # requests per hour

    # Job Queue Settings
    JOB_TIMEOUT: int = 3600  # 1 hour
    JOB_RESULT_TTL: int = 86400  # 24 hours
    MAX_JOBS_PER_USER: int = 10
    CLEANUP_INTERVAL: int = 86400  # 24 hours

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALLOWED_HOSTS: list = ["*"]
    CORS_ORIGINS: list = ["*"]
    API_TOKEN_EXPIRE_MINUTES: int = 60

    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_PREFIX: str = "gcache"
    
    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    BACKOFF_FACTOR: float = 2.0

    # Scraping Settings
    SELENIUM_TIMEOUT: int = 30
    PLAYWRIGHT_TIMEOUT: int = 30
    USE_PLAYWRIGHT: bool = False  # Toggle between Selenium and Playwright

    # Feature Flags
    FEATURES: Dict[str, bool] = {
        "linkedin_scraping": True,
        "github_metrics": True,
        "async_processing": True,
        "caching": True,
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Validate settings
def validate_settings() -> None:
    """Validate required settings are properly configured."""
    required_settings = [
        ("GITHUB_TOKEN", settings.GITHUB_TOKEN.get_secret_value()),
        ("DATABASE_URL", settings.DATABASE_URL),
        ("SECRET_KEY", settings.SECRET_KEY),
    ]
    
    missing_settings = [
        name for name, value in required_settings
        if not value
    ]
    
    if missing_settings:
        raise ValueError(
            f"Missing required settings: {', '.join(missing_settings)}"
        )

# Validate settings on import
validate_settings()
