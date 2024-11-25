# Usage Examples and Implementation Guide

## 1. Basic Usage Examples

### 1.1 Simple Repository Analysis
```python
# Example 1: Basic repository analysis
from agents.workflow import create_workflow

async def analyze_repository():
    workflow = create_workflow()
    
    # Initialize request
    initial_state = {
        "messages": [{
            "content": "find contributors of openai/gpt-3",
            "type": "human"
        }],
        "github_data": {},
        "linkedin_data": {},
        "final_response": {}
    }
    
    # Execute workflow
    result = await workflow.ainvoke(initial_state)
    return result["final_response"]
```

### 1.2 Custom Analysis Parameters
```python
# Example 2: Analysis with custom parameters
async def analyze_with_params(
    repo: str,
    limit: int = 50,
    include_metrics: bool = True
):
    request = {
        "task_description": f"analyze top {limit} contributors of {repo}",
        "limit": limit,
        "include_metrics": include_metrics
    }
    
    async with AsyncClient() as client:
        response = await client.post(
            "/recruit",
            json=request
        )
        return response.json()
```

## 2. Advanced Use Cases

### 2.1 Contributor Activity Analysis
```python
# Example 3: Detailed activity analysis
async def analyze_contributor_activity(
    repo: str,
    timeframe_days: int = 90
):
    github_client = AsyncGitHubClient(token=settings.GITHUB_TOKEN)
    
    # Get contributors
    contributors = await github_client.get_contributors(repo)
    
    # Analyze each contributor
    results = []
    for contributor in contributors:
        activity = await github_client.get_user_activity(
            repo=repo,
            username=contributor["login"]
        )
        
        metrics = {
            "username": contributor["login"],
            "total_commits": activity["total_commits"],
            "recent_activity": activity["recent_commits"],
            "engagement_score": calculate_engagement(activity)
        }
        results.append(metrics)
    
    return results
```

### 2.2 LinkedIn Profile Matching
```python
# Example 4: Enhanced LinkedIn matching
async def match_linkedin_profiles(
    github_profiles: List[Dict[str, Any]]
):
    linkedin_client = LinkedInAgent()
    matches = []
    
    for profile in github_profiles:
        # Try direct URL match
        if profile.get("linkedin_url"):
            result = await linkedin_client.process({
                "profile_urls": [profile["linkedin_url"]]
            })
            if result["profiles"]:
                matches.append({
                    "github": profile,
                    "linkedin": result["profiles"][0]
                })
                continue
        
        # Try name-based search
        if profile.get("name"):
            result = await linkedin_client.search_by_name(
                name=profile["name"],
                company=profile.get("company")
            )
            if result:
                matches.append({
                    "github": profile,
                    "linkedin": result
                })
    
    return matches
```

## 3. State Management Examples

### 3.1 Custom State Handling
```python
# Example 5: Manual state management
async def manage_workflow_state(session_id: str):
    state_manager = StateManager(table_name=settings.STATE_TABLE)
    
    # Save state
    await state_manager.save_state(
        session_id=session_id,
        messages=[{
            "content": "Processing started",
            "type": "system"
        }],
        github_data={"status": "pending"}
    )
    
    # Retrieve state
    current_state = await state_manager.get_latest_state(session_id)
    
    # Update specific data
    await state_manager.update_github_data(
        session_id=session_id,
        github_data={"status": "completed"}
    )
    
    return current_state
```

### 3.2 Workflow Recovery
```python
# Example 6: Handle workflow interruption
async def recover_workflow(session_id: str):
    state_manager = StateManager(table_name=settings.STATE_TABLE)
    
    # Get last valid state
    last_state = await state_manager.get_latest_state(session_id)
    
    if last_state["github_data"] and not last_state["linkedin_data"]:
        # Resume from LinkedIn processing
        workflow = create_workflow()
        result = await workflow.ainvoke(last_state)
        return result
    
    return last_state
```

## 4. Integration Examples

### 4.1 AWS Lambda Integration
```python
# Example 7: Lambda handler integration
async def lambda_handler(event: Dict[str, Any], context: Any):
    # Initialize workflow
    workflow = create_workflow()
    
    try:
        # Parse request
        body = json.loads(event["body"])
        session_id = str(uuid.uuid4())
        
        # Create initial state
        initial_state = {
            "session_id": session_id,
            "messages": [{
                "content": body["task_description"],
                "type": "human"
            }],
            "github_data": {},
            "linkedin_data": {},
            "final_response": {}
        }
        
        # Execute workflow
        result = await workflow.ainvoke(initial_state)
        
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
```

### 4.2 Custom Agent Integration
```python
# Example 8: Custom agent implementation
class CustomAnalysisAgent(BaseAgent):
    async def process(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Custom processing logic
        github_data = input_data["github_data"]
        metrics = await self.calculate_metrics(github_data)
        insights = await self.generate_insights(metrics)
        
        return {
            "metrics": metrics,
            "insights": insights,
            "recommendations": await self.get_recommendations(insights)
        }
    
    async def calculate_metrics(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, float]:
        # Custom metric calculation
        return {
            "contribution_score": self._calculate_contribution_score(data),
            "engagement_rate": self._calculate_engagement_rate(data),
            "consistency_score": self._calculate_consistency_score(data)
        }
```

## 5. Error Handling Examples

### 5.1 Rate Limit Handling
```python
# Example 9: Rate limit management
async def handle_rate_limits():
    github_client = AsyncGitHubClient(token=settings.GITHUB_TOKEN)
    
    try:
        with RateLimitHandler(
            max_retries=3,
            delay=60
        ):
            result = await github_client.get_contributors("high-traffic/repo")
            return result
    except RateLimitExceeded:
        # Queue request for later
        await queue_request(
            function="get_contributors",
            params={"repo": "high-traffic/repo"}
        )
```

### 5.2 Error Recovery
```python
# Example 10: Error recovery workflow
async def recover_from_error(
    error: Exception,
    state: Dict[str, Any]
):
    error_handler = ErrorHandler()
    
    try:
        # Log error
        await error_handler.log_error(error, state)
        
        # Attempt recovery
        recovered_state = await error_handler.recover_state(state)
        
        # Resume workflow
        workflow = create_workflow()
        result = await workflow.ainvoke(recovered_state)
        
        return result
    except Exception as e:
        # Terminal error
        await error_handler.handle_terminal_error(e)
        raise
```
