from pydantic import SecretStr
from pydantic_settings import BaseSettings


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

    # Rate Limits
    RATE_LIMIT_GITHUB: int = 5000  # requests per hour
    RATE_LIMIT_LINKEDIN: int = 100  # requests per hour
    RATE_LIMIT_DEFAULT: int = 1000  # requests per hour

    # Monitoring
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALLOWED_HOSTS: list = ["*"]
    CORS_ORIGINS: list = ["*"]
    API_TOKEN_EXPIRE_MINUTES: int = 60

    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    BACKOFF_FACTOR: float = 2.0

    # Scraping Settings
    SELENIUM_TIMEOUT: int = 30
    PLAYWRIGHT_TIMEOUT: int = 30
    USE_PLAYWRIGHT: bool = False  # Toggle between Selenium and Playwright

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

    missing_settings = [name for name, value in required_settings if not value]

    if missing_settings:
        raise ValueError(f"Missing required settings: {', '.join(missing_settings)}")


# Validate settings on import
validate_settings()
