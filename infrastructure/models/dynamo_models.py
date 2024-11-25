from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Union

from mypy_boto3_dynamodb.type_defs import (
    AttributeValueTypeDef,
    PutItemInputRequestTypeDef,
    QueryInputRequestTypeDef,
    GetItemInputRequestTypeDef
)
from pydantic import BaseModel


class MessageDict(TypedDict):
    content: str
    type: str
    name: Optional[str]
    metadata: Optional[Dict[str, Any]]


class StateData(TypedDict):
    messages: List[MessageDict]
    github_data: Dict[str, Any]
    linkedin_data: Dict[str, Any]
    final_response: Dict[str, Any]


class DynamoStateItem(TypedDict):
    session_id: str
    timestamp: str
    state: str  # JSON string of StateData
    ttl: int


class DynamoCacheItem(TypedDict):
    profile_id: str
    data: str  # JSON string of profile data
    cached_at: str
    ttl: int


class StateQueryParams(TypedDict):
    KeyConditionExpression: str
    ExpressionAttributeValues: Dict[str, AttributeValueTypeDef]
    ScanIndexForward: bool
    Limit: int


class StatePutParams(TypedDict):
    Item: DynamoStateItem


class CacheGetParams(TypedDict):
    Key: Dict[str, str]


class CachePutParams(TypedDict):
    Item: DynamoCacheItem


class WorkflowState(BaseModel):
    """Workflow state model with validation."""
    session_id: str
    timestamp: datetime
    messages: List[MessageDict]
    github_data: Dict[str, Any] = {}
    linkedin_data: Dict[str, Any] = {}
    final_response: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True


class ProfileCache(BaseModel):
    """Profile cache model with validation."""
    profile_id: str
    data: Dict[str, Any]
    cached_at: datetime
    ttl: int

    class Config:
        arbitrary_types_allowed = True


def create_state_query_params(session_id: str) -> QueryInputRequestTypeDef:
    """Create type-safe query parameters for state lookup."""
    return {
        "KeyConditionExpression": "session_id = :sid",
        "ExpressionAttributeValues": {":sid": {"S": session_id}},
        "ScanIndexForward": False,
        "Limit": 1
    }


def create_state_put_params(
    session_id: str,
    state: StateData,
    ttl: Optional[int] = None
) -> PutItemInputRequestTypeDef:
    """Create type-safe put parameters for state storage."""
    if ttl is None:
        ttl = int((datetime.now().timestamp() + 86400))  # 24 hour default TTL

    return {
        "Item": {
            "session_id": {"S": session_id},
            "timestamp": {"S": datetime.now().isoformat()},
            "state": {"S": str(state)},
            "ttl": {"N": str(ttl)}
        }
    }


def create_cache_get_params(profile_id: str) -> GetItemInputRequestTypeDef:
    """Create type-safe get parameters for cache lookup."""
    return {
        "Key": {
            "profile_id": {"S": profile_id}
        }
    }


def create_cache_put_params(
    profile_id: str,
    data: Dict[str, Any],
    ttl: Optional[int] = None
) -> PutItemInputRequestTypeDef:
    """Create type-safe put parameters for cache storage."""
    if ttl is None:
        ttl = int((datetime.now().timestamp() + 3600))  # 1 hour default TTL

    return {
        "Item": {
            "profile_id": {"S": profile_id},
            "data": {"S": str(data)},
            "cached_at": {"S": datetime.now().isoformat()},
            "ttl": {"N": str(ttl)}
        }
    }


def parse_dynamo_state(item: Dict[str, AttributeValueTypeDef]) -> WorkflowState:
    """Parse DynamoDB state item into validated WorkflowState."""
    return WorkflowState(
        session_id=item["session_id"]["S"],
        timestamp=datetime.fromisoformat(item["timestamp"]["S"]),
        messages=eval(item["state"]["S"])["messages"],
        github_data=eval(item["state"]["S"]).get("github_data", {}),
        linkedin_data=eval(item["state"]["S"]).get("linkedin_data", {}),
        final_response=eval(item["state"]["S"]).get("final_response", {})
    )


def parse_dynamo_cache(item: Dict[str, AttributeValueTypeDef]) -> ProfileCache:
    """Parse DynamoDB cache item into validated ProfileCache."""
    return ProfileCache(
        profile_id=item["profile_id"]["S"],
        data=eval(item["data"]["S"]),
        cached_at=datetime.fromisoformat(item["cached_at"]["S"]),
        ttl=int(item["ttl"]["N"])
    )
