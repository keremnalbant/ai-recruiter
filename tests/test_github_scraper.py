import pytest
from unittest.mock import AsyncMock, patch

from scrapers.github_scraper import GitHubScraper
from storage.models import GitHubContributor


@pytest.mark.asyncio
async def test_validate_repository_success():
    """Test successful repository validation."""
    scraper = GitHubScraper()
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await scraper.validate_repository("test/repo")
        assert result is True


@pytest.mark.asyncio
async def test_validate_repository_not_found():
    """Test repository validation with non-existent repo."""
    scraper = GitHubScraper()
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await scraper.validate_repository("nonexistent/repo")
        assert result is False


@pytest.mark.asyncio
async def test_get_contributors_success():
    """Test successful contributor retrieval."""
    scraper = GitHubScraper()
    
    with patch('aiohttp.ClientSession') as mock_session:
        # Mock contributors response
        mock_contributors_response = AsyncMock()
        mock_contributors_response.status = 200
        mock_contributors_response.json.return_value = [
            {
                "login": "test_user",
                "contributions": 100,
                "url": "https://api.github.com/users/test_user"
            }
        ]
        
        # Mock user details response
        mock_user_response = AsyncMock()
        mock_user_response.status = 200
        mock_user_response.json.return_value = {
            "name": "Test User",
            "email": "test@example.com",
            "blog": "https://linkedin.com/in/test_user"
        }
        
        # Setup session mock to return both responses
        session = AsyncMock()
        session.get.side_effect = [
            AsyncMock(__aenter__=AsyncMock(return_value=mock_contributors_response)),
            AsyncMock(__aenter__=AsyncMock(return_value=mock_user_response))
        ]
        mock_session.return_value.__aenter__.return_value = session
        
        contributors = await scraper.get_contributors("test/repo", limit=1)
        assert len(contributors) == 1
        assert isinstance(contributors[0], GitHubContributor)
        assert contributors[0].username == "test_user"
        assert contributors[0].contributions == 100


@pytest.mark.asyncio
async def test_get_maintainers():
    """Test maintainer retrieval."""
    scraper = GitHubScraper()
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {
                "login": "maintainer",
                "permissions": {"push": True},
                "url": "https://api.github.com/users/maintainer"
            }
        ]
        
        session = AsyncMock()
        session.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = session
        
        maintainers = await scraper.get_maintainers("test/repo")
        assert len(maintainers) == 1
        assert maintainers[0].username == "maintainer"


@pytest.mark.asyncio
async def test_get_activity_metrics():
    """Test activity metrics retrieval."""
    scraper = GitHubScraper()
    
    with patch('aiohttp.ClientSession') as mock_session:
        # Mock responses for commits, PRs, and issues
        mock_commits_response = AsyncMock(status=200)
        mock_commits_response.json.return_value = [{"commit": {"author": {"date": "2024-01-01T00:00:00Z"}}}] * 5
        
        mock_prs_response = AsyncMock(status=200)
        mock_prs_response.json.return_value = [{"created_at": "2024-01-01T00:00:00Z"}] * 3
        
        mock_issues_response = AsyncMock(status=200)
        mock_issues_response.json.return_value = [{"created_at": "2024-01-01T00:00:00Z"}] * 2
        
        session = AsyncMock()
        session.get.side_effect = [
            AsyncMock(__aenter__=AsyncMock(return_value=mock_commits_response)),
            AsyncMock(__aenter__=AsyncMock(return_value=mock_prs_response)),
            AsyncMock(__aenter__=AsyncMock(return_value=mock_issues_response))
        ]
        mock_session.return_value.__aenter__.return_value = session
        
        metrics = await scraper.get_activity_metrics("test/repo", "test_user")
        assert metrics["total_commits"] == 5
        assert metrics["total_prs"] == 3
        assert metrics["total_issues"] == 2


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in GitHub scraper."""
    scraper = GitHubScraper()
    
    with patch('aiohttp.ClientSession') as mock_session:
        # Simulate rate limit error
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            await scraper.get_contributors("test/repo")
        assert "GitHub API error: 403" in str(exc_info.value)


@pytest.mark.asyncio
async def test_repository_info():
    """Test repository information retrieval."""
    scraper = GitHubScraper()
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "full_name": "test/repo",
            "description": "Test repository",
            "stargazers_count": 100,
            "language": "Python"
        }
        
        session = AsyncMock()
        session.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = session
        
        repo_info = await scraper.get_repository_info("test/repo")
        assert repo_info["full_name"] == "test/repo"
        assert repo_info["language"] == "Python"
