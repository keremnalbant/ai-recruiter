import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from main import app
from config import Settings, settings
from storage.database import Database


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings with mock credentials."""
    return Settings(
        GITHUB_TOKEN="test_github_token",
        LINKEDIN_EMAIL="test@example.com",
        LINKEDIN_PASSWORD="test_password",
        ANTHROPIC_API_KEY="test_anthropic_key",
        DATABASE_URL="mongodb://localhost:27017/test_db",
        RATE_LIMIT_GITHUB=100,
        RATE_LIMIT_LINKEDIN=10
    )


@pytest.fixture
def mock_chrome_driver() -> Generator[Mock, None, None]:
    """Provide a mock Chrome driver for testing."""
    driver_mock = Mock(spec=webdriver.Chrome)
    driver_mock.current_url = "https://linkedin.com/in/test"
    driver_mock.page_source = "<html>Test Page</html>"
    
    # Mock common Selenium methods
    driver_mock.find_element.return_value = Mock(text="Test Text")
    driver_mock.find_elements.return_value = [Mock(text="Test Item")]
    driver_mock.quit = Mock()
    
    yield driver_mock


@pytest.fixture
async def test_db() -> AsyncGenerator[Database, None]:
    """Provide a test database instance."""
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    db_name = "test_db"
    
    # Clear test database before each test
    await client.drop_database(db_name)
    
    database = Database()
    database.client = client
    database.db = client[db_name]
    
    yield database
    
    # Cleanup after tests
    await client.drop_database(db_name)
    client.close()


@pytest.fixture
def test_client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Provide a test client with mock settings."""
    app.dependency_overrides = {}  # Reset overrides
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_github_api() -> AsyncMock:
    """Provide mock GitHub API responses."""
    mock = AsyncMock()
    
    # Mock repository data
    mock.get_repository.return_value = {
        "full_name": "test/repo",
        "description": "Test Repository",
        "stargazers_count": 100
    }
    
    # Mock contributors data
    mock.get_contributors.return_value = [
        {
            "login": "test_user",
            "contributions": 50,
            "html_url": "https://github.com/test_user",
            "type": "User"
        }
    ]
    
    return mock


@pytest.fixture
def mock_linkedin_api() -> AsyncMock:
    """Provide mock LinkedIn API responses."""
    mock = AsyncMock()
    
    # Mock profile data
    mock.get_profile.return_value = {
        "profile_url": "https://linkedin.com/in/test_user",
        "name": "Test User",
        "current_position": "Software Engineer",
        "company": "Test Company",
        "location": "Test Location"
    }
    
    return mock


@pytest.fixture
def mock_anthropic() -> AsyncMock:
    """Provide mock Anthropic API responses."""
    mock = AsyncMock()
    mock.ainvoke.return_value.content = "test/repo"
    return mock


@pytest.fixture
def mock_selenium() -> Mock:
    """Provide mock Selenium WebDriver."""
    mock = Mock(spec=webdriver.Chrome)
    mock.page_source = "<html>Test Page</html>"
    mock.current_url = "https://linkedin.com/test"
    return mock


@pytest.fixture(autouse=True)
def env_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up environment variables for testing."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("LINKEDIN_EMAIL", "test@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "test_password")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
