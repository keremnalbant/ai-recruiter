import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from infrastructure.models.dynamo_models import MessageDict
from infrastructure.state.manager import StateManager

logger = Logger()
tracer = Tracer()

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
STATE_TABLE = os.environ["STATE_TABLE"]


class AsyncGitHubClient:
    """Async GitHub API client."""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def get_contributors(
        self,
        repo: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get repository contributors with async HTTP."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"{self.base_url}/repos/{repo}/contributors"
            params = {"per_page": limit}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    contributors = await response.json()
                    return contributors[:limit]
                else:
                    error_msg = await response.text()
                    raise Exception(f"GitHub API error: {response.status} - {error_msg}")

    async def get_user_details(self, username: str) -> Dict[str, Any]:
        """Get detailed user information."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            url = f"{self.base_url}/users/{username}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = await response.text()
                    raise Exception(f"GitHub API error: {response.status} - {error_msg}")

    async def get_user_activity(
        self,
        repo: str,
        username: str
    ) -> Dict[str, Any]:
        """Get user activity metrics for a repository."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Get commits
            commits_url = f"{self.base_url}/repos/{repo}/commits"
            params = {"author": username, "per_page": 100}
            
            async with session.get(commits_url, params=params) as response:
                commits = await response.json() if response.status == 200 else []

            # Get PRs
            prs_url = f"{self.base_url}/repos/{repo}/pulls"
            params = {"creator": username, "state": "all", "per_page": 100}
            
            async with session.get(prs_url, params=params) as response:
                prs = await response.json() if response.status == 200 else []

            # Calculate metrics
            return {
                "total_commits": len(commits),
                "total_prs": len(prs),
                "recent_activity": {
                    "commits": len([c for c in commits if _is_recent(c["commit"]["author"]["date"])]),
                    "prs": len([pr for pr in prs if _is_recent(pr["created_at"])])
                }
            }


def _is_recent(date_str: str, days: int = 90) -> bool:
    """Check if a date is within the last N days."""
    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return (datetime.now() - date).days <= days


@logger.inject_lambda_context
@tracer.capture_lambda_handler
async def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for GitHub scraping."""
    try:
        # Parse event
        body = json.loads(event['body'])
        session_id = body['session_id']
        repo = body['repository']
        limit = body.get('limit', 50)

        # Initialize clients
        github_client = AsyncGitHubClient(GITHUB_TOKEN)
        state_manager = StateManager(STATE_TABLE)

        # Add processing message
        await state_manager.add_message(
            session_id=session_id,
            content=f"Processing GitHub repository: {repo}",
            message_type="system"
        )

        # Get contributors
        contributors = await github_client.get_contributors(repo, limit)
        
        # Process each contributor
        enriched_contributors = []
        for contributor in contributors:
            username = contributor['login']
            
            # Get detailed user info
            user_details = await github_client.get_user_details(username)
            
            # Get activity metrics
            activity = await github_client.get_user_activity(repo, username)
            
            # Combine data
            enriched_contributor = {
                "username": username,
                "contributions": contributor['contributions'],
                "profile_url": user_details['html_url'],
                "name": user_details.get('name'),
                "email": user_details.get('email'),
                "company": user_details.get('company'),
                "location": user_details.get('location'),
                "bio": user_details.get('bio'),
                "blog": user_details.get('blog'),
                "activity_metrics": activity
            }
            enriched_contributors.append(enriched_contributor)

        # Update state with GitHub data
        github_data = {
            "repository": repo,
            "total_contributors": len(enriched_contributors),
            "contributors": enriched_contributors,
            "scraped_at": datetime.now().isoformat()
        }
        
        await state_manager.update_github_data(session_id, github_data)
        
        # Add completion message
        await state_manager.add_message(
            session_id=session_id,
            content=f"Successfully processed {len(enriched_contributors)} contributors",
            message_type="system",
            metadata={"status": "success"}
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'session_id': session_id,
                'message': 'GitHub data processed successfully'
            })
        }

    except Exception as e:
        logger.exception('Error processing GitHub data')
        
        if 'session_id' in locals() and 'state_manager' in locals():
            await state_manager.add_message(
                session_id=session_id,
                content=f"Error processing GitHub data: {str(e)}",
                message_type="error"
            )

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Error processing GitHub data'
            })
        }
