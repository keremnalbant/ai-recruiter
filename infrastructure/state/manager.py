from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, cast

import aioboto3
from aws_lambda_powertools.logging import Logger
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from mypy_boto3_dynamodb.type_defs import QueryOutputTypeDef

from infrastructure.models.dynamo_models import (
    MessageDict,
    StateData,
    WorkflowState,
    create_state_put_params,
    create_state_query_params,
    parse_dynamo_state
)

logger = Logger()
T = TypeVar('T', bound=Dict[str, Any])

class StateManager:
    """Type-safe state management for serverless workflow."""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.session = aioboto3.Session()

    async def _get_table(self) -> Table:
        """Get DynamoDB table with type safety."""
        async with self.session.resource('dynamodb') as dynamodb:
            # Cast to ensure type safety with mypy
            typed_dynamodb = cast(DynamoDBServiceResource, dynamodb)
            return await typed_dynamodb.Table(self.table_name)

    async def save_state(
        self,
        session_id: str,
        messages: List[MessageDict],
        github_data: Optional[Dict[str, Any]] = None,
        linkedin_data: Optional[Dict[str, Any]] = None,
        final_response: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> None:
        """Save workflow state to DynamoDB with type checking."""
        try:
            table = await self._get_table()

            state_data: StateData = {
                "messages": messages,
                "github_data": github_data or {},
                "linkedin_data": linkedin_data or {},
                "final_response": final_response or {}
            }

            put_params = create_state_put_params(session_id, state_data, ttl)
            await table.put_item(**put_params)

            logger.info(f"Saved state for session {session_id}")

        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
            raise

    async def get_latest_state(self, session_id: str) -> Optional[WorkflowState]:
        """Retrieve latest state for a session with type safety."""
        try:
            table = await self._get_table()

            query_params = create_state_query_params(session_id)
            response: QueryOutputTypeDef = await table.query(**query_params)

            if response['Items']:
                return parse_dynamo_state(response['Items'][0])

            logger.info(f"No state found for session {session_id}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving state: {str(e)}")
            raise

    async def update_github_data(
        self,
        session_id: str,
        github_data: Dict[str, Any]
    ) -> None:
        """Update GitHub data in the workflow state."""
        current_state = await self.get_latest_state(session_id)
        if not current_state:
            raise ValueError(f"No state found for session {session_id}")

        await self.save_state(
            session_id=session_id,
            messages=current_state.messages,
            github_data=github_data,
            linkedin_data=current_state.linkedin_data,
            final_response=current_state.final_response
        )

    async def update_linkedin_data(
        self,
        session_id: str,
        linkedin_data: Dict[str, Any]
    ) -> None:
        """Update LinkedIn data in the workflow state."""
        current_state = await self.get_latest_state(session_id)
        if not current_state:
            raise ValueError(f"No state found for session {session_id}")

        await self.save_state(
            session_id=session_id,
            messages=current_state.messages,
            github_data=current_state.github_data,
            linkedin_data=linkedin_data,
            final_response=current_state.final_response
        )

    async def finalize_state(
        self,
        session_id: str,
        final_response: Dict[str, Any]
    ) -> None:
        """Mark workflow state as complete with final response."""
        current_state = await self.get_latest_state(session_id)
        if not current_state:
            raise ValueError(f"No state found for session {session_id}")

        # Add completion message
        messages = current_state.messages + [{
            "content": "Workflow completed",
            "type": "system",
            "metadata": {
                "completed_at": datetime.now().isoformat(),
                "status": "success"
            }
        }]

        await self.save_state(
            session_id=session_id,
            messages=messages,
            github_data=current_state.github_data,
            linkedin_data=current_state.linkedin_data,
            final_response=final_response
        )

    async def add_message(
        self,
        session_id: str,
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a new message to the workflow state."""
        current_state = await self.get_latest_state(session_id)
        if not current_state:
            raise ValueError(f"No state found for session {session_id}")

        messages = current_state.messages + [{
            "content": content,
            "type": message_type,
            "metadata": metadata or {}
        }]

        await self.save_state(
            session_id=session_id,
            messages=messages,
            github_data=current_state.github_data,
            linkedin_data=current_state.linkedin_data,
            final_response=current_state.final_response
        )
