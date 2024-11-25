import json
import os
from typing import Any, AsyncGenerator, Dict, Generator

import aioboto3
import boto3
import pytest
import pytest_asyncio
from moto import mock_aws
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table

from lambda.config import LambdaConfig, get_config


@pytest.fixture
def aws_credentials() -> None:
    """Mock AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def lambda_config() -> LambdaConfig:
    """Provide test configuration."""
    os.environ["LAMBDA_STATE_TABLE"] = "test-state-table"
    os.environ["LAMBDA_CACHE_TABLE"] = "test-cache-table"
    return get_config("test")


@pytest.fixture
def mock_dynamodb(aws_credentials: None) -> Generator[None, None, None]:
    """Provide mock DynamoDB instance."""
    with mock_aws():
        yield


@pytest.fixture
def dynamodb_resource(mock_dynamodb: None) -> DynamoDBServiceResource:
    """Provide DynamoDB resource."""
    return boto3.resource("dynamodb")


@pytest.fixture
def state_table(dynamodb_resource: DynamoDBServiceResource, lambda_config: LambdaConfig) -> Table:
    """Create and provide state table."""
    table = dynamodb_resource.create_table(
        TableName=lambda_config.state_table.table_name,
        KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "session_id", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    return table


@pytest.fixture
def cache_table(dynamodb_resource: DynamoDBServiceResource, lambda_config: LambdaConfig) -> Table:
    """Create and provide cache table."""
    table = dynamodb_resource.create_table(
        TableName=lambda_config.cache_table.table_name,
        KeySchema=[
            {"AttributeName": "profile_id", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "profile_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    return table


@pytest_asyncio.fixture
async def async_dynamodb_session() -> AsyncGenerator[aioboto3.Session, None]:
    """Provide async DynamoDB session."""
    session = aioboto3.Session()
    yield session


@pytest.fixture
def mock_github_response() -> Dict[str, Any]:
    """Provide mock GitHub API response."""
    return {
        "login": "test-user",
        "id": 1,
        "html_url": "https://github.com/test-user",
        "name": "Test User",
        "company": "Test Company",
        "email": "test@example.com",
        "location": "Test Location",
        "bio": "Test Bio",
        "public_repos": 10,
        "followers": 100,
        "following": 50
    }


@pytest.fixture
def mock_github_contributors() -> Dict[str, Any]:
    """Provide mock GitHub contributors response."""
    return [
        {
            "login": "contributor1",
            "contributions": 100,
            "html_url": "https://github.com/contributor1"
        },
        {
            "login": "contributor2",
            "contributions": 50,
            "html_url": "https://github.com/contributor2"
        }
    ]


@pytest.fixture
def mock_state_data() -> Dict[str, Any]:
    """Provide mock workflow state data."""
    return {
        "session_id": "test-session",
        "timestamp": "2024-01-01T00:00:00Z",
        "state": json.dumps({
            "messages": [
                {"content": "Test message", "type": "system"}
            ],
            "github_data": {"repository": "test/repo"},
            "linkedin_data": {},
            "final_response": {}
        })
    }


@pytest.fixture
def mock_cache_data() -> Dict[str, Any]:
    """Provide mock cache data."""
    return {
        "profile_id": "github:test-user",
        "data": json.dumps({
            "username": "test-user",
            "profile_url": "https://github.com/test-user",
            "cached_at": "2024-01-01T00:00:00Z"
        }),
        "ttl": 1704067200  # 2024-01-01T00:00:00Z
    }


@pytest.fixture
def lambda_context() -> Dict[str, Any]:
    """Provide mock Lambda context."""
    return {
        "function_name": "test-function",
        "function_version": "$LATEST",
        "invoked_function_arn": "arn:aws:lambda:us-east-1:123456789012:function:test-function",
        "memory_limit_in_mb": 128,
        "aws_request_id": "test-request-id",
        "log_group_name": "/aws/lambda/test-function",
        "log_stream_name": "2024/01/01/[$LATEST]test-stream",
        "identity": None,
        "client_context": None
    }


@pytest.fixture
def api_gateway_event() -> Dict[str, Any]:
    """Provide mock API Gateway event."""
    return {
        "body": json.dumps({
            "task_description": "find contributors of test/repo",
            "limit": 10
        }),
        "requestContext": {
            "http": {
                "method": "POST",
                "path": "/recruit"
            }
        },
        "headers": {
            "Content-Type": "application/json"
        }
    }


class AsyncMockResponse:
    """Mock aiohttp response."""
    def __init__(self, data: Dict[str, Any], status: int = 200):
        self.data = data
        self.status = status

    async def json(self) -> Dict[str, Any]:
        return self.data

    async def __aenter__(self) -> 'AsyncMockResponse':
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


@pytest.fixture
def mock_aiohttp_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock aiohttp ClientSession."""
    class MockClientSession:
        async def __aenter__(self) -> 'MockClientSession':
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def get(self, url: str, **kwargs: Any) -> AsyncMockResponse:
            if "github.com" in url:
                return AsyncMockResponse({"login": "test-user"})
            return AsyncMockResponse({})

    monkeypatch.setattr("aiohttp.ClientSession", MockClientSession)
