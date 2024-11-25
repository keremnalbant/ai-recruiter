import json
from datetime import datetime
from typing import Any, Dict

import pytest
from mypy_boto3_dynamodb.service_resource import Table

from lambda.api.handler import handler as api_handler
from lambda.github_scraper.handler import handler as github_handler
from lambda.config import LambdaConfig
from infrastructure.models.dynamo_models import WorkflowState


@pytest.mark.asyncio
async def test_api_handler_success(
    api_gateway_event: Dict[str, Any],
    lambda_context: Dict[str, Any],
    state_table: Table,
    lambda_config: LambdaConfig
) -> None:
    """Test successful API handler execution."""
    # Execute handler
    response = await api_handler(api_gateway_event, lambda_context)
    
    # Verify response
    assert response["statusCode"] == 202
    body = json.loads(response["body"])
    assert "session_id" in body
    assert body["status"] == "processing"
    
    # Verify state was saved
    items = state_table.scan()["Items"]
    assert len(items) == 1
    
    state = WorkflowState(
        session_id=body["session_id"],
        timestamp=datetime.fromisoformat(items[0]["timestamp"]),
        messages=json.loads(items[0]["state"])["messages"]
    )
    assert len(state.messages) > 0
    assert state.messages[0]["content"] == "find contributors of test/repo"


@pytest.mark.asyncio
async def test_api_handler_invalid_request(
    lambda_context: Dict[str, Any]
) -> None:
    """Test API handler with invalid request."""
    event = {
        "body": json.dumps({
            "task_description": "",  # Empty description
            "limit": -1  # Invalid limit
        })
    }
    
    response = await api_handler(event, lambda_context)
    assert response["statusCode"] == 400
    assert "error" in json.loads(response["body"])


@pytest.mark.asyncio
async def test_github_handler_success(
    mock_aiohttp_session: None,
    state_table: Table,
    lambda_context: Dict[str, Any],
    mock_github_contributors: Dict[str, Any]
) -> None:
    """Test successful GitHub scraper execution."""
    event = {
        "body": json.dumps({
            "session_id": "test-session",
            "repository": "test/repo",
            "limit": 2
        })
    }
    
    response = await github_handler(event, lambda_context)
    assert response["statusCode"] == 200
    
    # Verify state was updated
    items = state_table.scan()["Items"]
    assert len(items) > 0
    
    state_data = json.loads(items[-1]["state"])
    assert "github_data" in state_data
    assert len(state_data["github_data"].get("contributors", [])) > 0


@pytest.mark.asyncio
async def test_github_handler_rate_limit(
    mock_aiohttp_session: None,
    lambda_context: Dict[str, Any]
) -> None:
    """Test GitHub handler with rate limit response."""
    event = {
        "body": json.dumps({
            "session_id": "test-session",
            "repository": "rate-limited/repo",
            "limit": 1
        })
    }
    
    # Mock rate limit response
    class RateLimitResponse:
        status = 403
        async def text(self) -> str:
            return "API rate limit exceeded"
    
    async def mock_rate_limited_get(*args: Any, **kwargs: Any) -> RateLimitResponse:
        return RateLimitResponse()
    
    # Override mock session's get method
    mock_aiohttp_session.get = mock_rate_limited_get  # type: ignore
    
    response = await github_handler(event, lambda_context)
    assert response["statusCode"] == 429
    assert "rate limit" in json.loads(response["body"])["error"].lower()


@pytest.mark.asyncio
async def test_state_persistence(
    state_table: Table,
    lambda_context: Dict[str, Any]
) -> None:
    """Test state persistence across handler calls."""
    session_id = "test-persistence"
    
    # Initial state
    initial_state = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "state": json.dumps({
            "messages": [{"content": "Initial message", "type": "system"}],
            "github_data": {},
            "linkedin_data": {},
            "final_response": {}
        })
    }
    state_table.put_item(Item=initial_state)
    
    # Update state through GitHub handler
    event = {
        "body": json.dumps({
            "session_id": session_id,
            "repository": "test/repo",
            "limit": 1
        })
    }
    
    response = await github_handler(event, lambda_context)
    assert response["statusCode"] == 200
    
    # Verify state evolution
    items = state_table.query(
        KeyConditionExpression="session_id = :sid",
        ExpressionAttributeValues={":sid": session_id},
        ScanIndexForward=False  # Get most recent first
    )["Items"]
    
    assert len(items) > 1  # Should have multiple state versions
    latest_state = json.loads(items[0]["state"])
    
    # Verify state progression
    assert len(latest_state["messages"]) > 1  # Should have additional messages
    assert latest_state["github_data"]  # Should have GitHub data
    assert "contributors" in latest_state["github_data"]


@pytest.mark.asyncio
async def test_concurrent_updates(
    state_table: Table,
    lambda_context: Dict[str, Any],
    mock_aiohttp_session: None
) -> None:
    """Test handling of concurrent state updates."""
    session_id = "test-concurrent"
    
    # Simulate concurrent handler calls
    events = [
        {
            "body": json.dumps({
                "session_id": session_id,
                "repository": f"test/repo-{i}",
                "limit": 1
            })
        }
        for i in range(3)
    ]
    
    # Execute handlers concurrently
    import asyncio
    responses = await asyncio.gather(
        *[github_handler(event, lambda_context) for event in events]
    )
    
    # Verify all calls succeeded
    assert all(r["statusCode"] == 200 for r in responses)
    
    # Verify state consistency
    items = state_table.query(
        KeyConditionExpression="session_id = :sid",
        ExpressionAttributeValues={":sid": session_id},
        ScanIndexForward=False
    )["Items"]
    
    # Should have multiple state versions
    assert len(items) >= 3
    
    # Verify timestamps are unique
    timestamps = [item["timestamp"] for item in items]
    assert len(set(timestamps)) == len(timestamps)
