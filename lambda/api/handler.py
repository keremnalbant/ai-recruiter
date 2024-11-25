import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import aioboto3
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from agents.workflow import AgentState

# Initialize utilities
logger = Logger()
tracer = Tracer()

# Initialize async session
session = aioboto3.Session()


class StateManager:
    """Manage agent state in DynamoDB."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    async def save_state(self, session_id: str, state: AgentState) -> None:
        """Save agent state to DynamoDB."""
        async with session.resource('dynamodb') as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            # Convert state to DynamoDB format
            item = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'state': json.dumps({
                    'messages': [msg.dict() for msg in state['messages']],
                    'github_data': state.get('github_data', {}),
                    'linkedin_data': state.get('linkedin_data', {}),
                    'final_response': state.get('final_response', {})
                }),
                'ttl': int((datetime.now().timestamp() + 86400))  # 24 hour TTL
            }
            
            await table.put_item(Item=item)
    
    async def get_state(self, session_id: str) -> Optional[AgentState]:
        """Retrieve agent state from DynamoDB."""
        async with session.resource('dynamodb') as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            # Get latest state for session
            response = await table.query(
                KeyConditionExpression='session_id = :sid',
                ExpressionAttributeValues={':sid': session_id},
                ScanIndexForward=False,  # Sort by timestamp descending
                Limit=1
            )
            
            if response['Items']:
                state_data = json.loads(response['Items'][0]['state'])
                return AgentState(**state_data)
            
            return None


class CacheManager:
    """Manage profile cache in DynamoDB."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
    
    async def get_cached_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get cached profile data."""
        async with session.resource('dynamodb') as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            response = await table.get_item(
                Key={'profile_id': profile_id}
            )
            
            return response.get('Item')
    
    async def cache_profile(self, profile_id: str, data: Dict[str, Any]) -> None:
        """Cache profile data with TTL."""
        async with session.resource('dynamodb') as dynamodb:
            table = await dynamodb.Table(self.table_name)
            
            item = {
                'profile_id': profile_id,
                'data': json.dumps(data),
                'cached_at': datetime.now().isoformat(),
                'ttl': int((datetime.now().timestamp() + 3600))  # 1 hour TTL
            }
            
            await table.put_item(Item=item)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
async def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for API requests."""
    try:
        # Initialize managers
        state_manager = StateManager(table_name=context.env.get('STATE_TABLE'))
        cache_manager = CacheManager(table_name=context.env.get('CACHE_TABLE'))
        
        # Parse request
        body = json.loads(event['body'])
        task_description = body['task_description']
        limit = body.get('limit', 50)
        
        # Generate session ID
        session_id = str(uuid4())
        
        # Initialize agent state
        initial_state: AgentState = {
            'messages': [{'content': task_description, 'type': 'human'}],
            'github_data': {},
            'linkedin_data': {},
            'final_response': {}
        }
        
        # Save initial state
        await state_manager.save_state(session_id, initial_state)
        
        # Start workflow execution
        response = {
            'session_id': session_id,
            'status': 'processing',
            'message': 'Request accepted for processing'
        }
        
        return {
            'statusCode': 202,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        logger.exception('Error processing request')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error'
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
