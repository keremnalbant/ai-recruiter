import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from agents.workflow import create_workflow
from main import app


@pytest.mark.asyncio
async def test_recruit_endpoint_success(
    test_client: TestClient,
    mock_github_api: AsyncMock,
    mock_linkedin_api: AsyncMock,
    mock_anthropic: AsyncMock,
):
    """Test successful recruitment analysis."""
    with patch('agents.github_agent.GitHubAgent') as mock_github_agent, \
         patch('agents.linkedin_agent.LinkedInAgent') as mock_linkedin_agent, \
         patch('agents.new_coordinator.CoordinatorAgent') as mock_coordinator:
        
        # Configure mocks
        mock_github_agent.return_value.process.return_value = {
            "profiles": [
                {
                    "github_username": "test_user",
                    "github_url": "https://github.com/test_user",
                    "contributions": 50,
                    "social_urls": {"linkedin": "https://linkedin.com/in/test_user"}
                }
            ]
        }
        
        mock_linkedin_agent.return_value.process.return_value = {
            "profiles": [
                {
                    "url": "https://linkedin.com/in/test_user",
                    "name": "Test User",
                    "current_position": "Software Engineer",
                    "company": "Test Company"
                }
            ]
        }
        
        # Test request
        response = test_client.post(
            "/recruit",
            json={
                "task_description": "bring me last 50 contributors of test/repo",
                "limit": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "repository" in data
        assert "profiles" in data
        assert len(data["profiles"]) > 0


@pytest.mark.asyncio
async def test_recruit_endpoint_invalid_request(test_client: TestClient):
    """Test recruitment analysis with invalid request."""
    response = test_client.post(
        "/recruit",
        json={
            "task_description": "",  # Empty description
            "limit": -1  # Invalid limit
        }
    )
    
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_studio_config_endpoint(test_client: TestClient):
    """Test LangGraph Studio configuration endpoint."""
    response = test_client.get("/studio/config")
    
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "nodes" in data


@pytest.mark.asyncio
async def test_studio_graph_endpoint(test_client: TestClient):
    """Test workflow graph endpoint."""
    response = test_client.get("/studio/graph")
    
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data


@pytest.mark.asyncio
async def test_trace_endpoint_not_found(test_client: TestClient):
    """Test trace endpoint with non-existent trace ID."""
    response = test_client.get("/studio/trace/nonexistent")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_workflow_integration():
    """Test complete workflow integration."""
    workflow = create_workflow()
    
    # Test workflow with mock state
    state = {
        "messages": [{"content": "find contributors of test/repo", "type": "human"}],
        "github_data": {},
        "linkedin_data": {},
        "final_response": {}
    }
    
    result = await workflow.ainvoke(state)
    assert "final_response" in result


@pytest.mark.asyncio
async def test_error_handling(test_client: TestClient):
    """Test error handling in recruitment endpoint."""
    with patch('agents.github_agent.GitHubAgent') as mock_github_agent:
        # Simulate GitHub API error
        mock_github_agent.return_value.process.side_effect = Exception("GitHub API error")
        
        response = test_client.post(
            "/recruit",
            json={
                "task_description": "find contributors of test/repo",
                "limit": 10
            }
        )
        
        assert response.status_code == 500
        assert "detail" in response.json()
