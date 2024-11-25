from typing import Dict, Optional

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.parameters import get_secret
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings

logger = Logger()


class LambdaSecrets(BaseModel):
    """Secrets retrieved from AWS Secrets Manager."""
    github_token: SecretStr
    anthropic_key: SecretStr
    linkedin_email: str
    linkedin_password: SecretStr


class LambdaSettings(BaseSettings):
    """Lambda function configuration."""
    # Environment
    environment: str = "dev"
    region: str = "us-east-1"
    
    # DynamoDB Tables
    state_table: str
    cache_table: Optional[str] = None
    
    # Rate Limits
    github_rate_limit: int = 5000
    linkedin_rate_limit: int = 100
    
    # Timeouts and Retries
    function_timeout: int = 900  # 15 minutes
    max_retries: int = 3
    retry_delay: int = 1
    backoff_factor: float = 2.0
    
    # Cache TTL (in seconds)
    github_cache_ttl: int = 3600  # 1 hour
    linkedin_cache_ttl: int = 7200  # 2 hours
    state_ttl: int = 86400  # 24 hours
    
    # Feature Flags
    use_cache: bool = True
    enable_metrics: bool = True
    scrape_linkedin: bool = True
    
    class Config:
        env_prefix = "LAMBDA_"
        case_sensitive = False


async def get_secrets(environment: str) -> LambdaSecrets:
    """Retrieve secrets from AWS Secrets Manager."""
    try:
        secret_name = f"github-linkedin-analyzer/{environment}"
        secret_value = await get_secret(secret_name)
        
        return LambdaSecrets(**secret_value)
    except Exception as e:
        logger.error(f"Error retrieving secrets: {e}")
        raise


class DynamoDBConfig(BaseModel):
    """DynamoDB configuration."""
    table_name: str
    ttl_attribute: str = "ttl"
    index_name: Optional[str] = None
    
    class Config:
        frozen = True


class RetryConfig(BaseModel):
    """Retry configuration for API calls."""
    max_attempts: int
    base_delay: float
    max_delay: float
    exponential_base: float = 2.0
    
    class Config:
        frozen = True


class MetricsConfig(BaseModel):
    """Metrics configuration."""
    namespace: str
    service_name: str
    dimensions: Dict[str, str]
    
    class Config:
        frozen = True


class LambdaConfig:
    """Main configuration for Lambda functions."""
    
    def __init__(self, environment: str):
        self.settings = LambdaSettings()
        self.environment = environment
        
        # DynamoDB Configuration
        self.state_table = DynamoDBConfig(
            table_name=self.settings.state_table,
            ttl_attribute="ttl"
        )
        
        if self.settings.cache_table:
            self.cache_table = DynamoDBConfig(
                table_name=self.settings.cache_table,
                ttl_attribute="ttl"
            )
        
        # Retry Configuration
        self.retry_config = RetryConfig(
            max_attempts=self.settings.max_retries,
            base_delay=self.settings.retry_delay,
            max_delay=30.0
        )
        
        # Metrics Configuration
        self.metrics_config = MetricsConfig(
            namespace="GitHubLinkedInAnalyzer",
            service_name=f"lambda-{environment}",
            dimensions={
                "Environment": environment,
                "Service": "GitHubLinkedInAnalyzer"
            }
        )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "prod"
    
    def get_table_name(self, table_type: str) -> str:
        """Get DynamoDB table name based on type."""
        if table_type == "state":
            return self.state_table.table_name
        elif table_type == "cache" and hasattr(self, 'cache_table'):
            return self.cache_table.table_name
        raise ValueError(f"Unknown table type: {table_type}")
    
    def get_ttl(self, data_type: str) -> int:
        """Get TTL for different data types."""
        ttl_map = {
            "github": self.settings.github_cache_ttl,
            "linkedin": self.settings.linkedin_cache_ttl,
            "state": self.settings.state_ttl
        }
        return ttl_map.get(data_type, self.settings.state_ttl)


# Global config instance
config: Optional[LambdaConfig] = None


def get_config(environment: str = "dev") -> LambdaConfig:
    """Get or create config instance."""
    global config
    if config is None:
        config = LambdaConfig(environment)
    return config
