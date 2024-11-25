from typing import Any, Dict, List, Optional, cast

import aiohttp
from langchain_core.messages import HumanMessage
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.schema.runnable import RunnableLambda
from langserve import add_routes
from langgraph.prebuilt import ToolExecutor
from pydantic import BaseModel

from agents.new_coordinator import CoordinatorAgent
from agents.workflow import AgentState, create_workflow

app = FastAPI(title="GitHub & LinkedIn Profile Analyzer")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
coordinator = CoordinatorAgent()


class SocialProfile(BaseModel):
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None


class GitHubInfo(BaseModel):
    username: str
    url: str
    contributions: int
    email: Optional[str] = None


class LinkedInInfo(BaseModel):
    url: str
    current_position: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    experience: Dict[str, Any]


class DeveloperProfile(BaseModel):
    github_info: GitHubInfo
    name: Optional[str] = None
    social_urls: SocialProfile
    linkedin_info: Optional[LinkedInInfo] = None


class RecruitmentRequest(BaseModel):
    task_description: str
    limit: int = 50

    @property
    def is_valid_request(self) -> bool:
        """Check if the request is valid for GitHub contributors search."""
        return (
            isinstance(self.task_description, str)
            and "github" in self.task_description.lower()
            and isinstance(self.limit, int)
            and 1 <= self.limit <= 100
        )


class RecruitmentResponse(BaseModel):
    repository: str
    total_profiles: int
    profiles_with_linkedin: int
    profiles: List[DeveloperProfile]


@app.post("/recruit", response_model=RecruitmentResponse)
async def recruit_developers(request: RecruitmentRequest):
    if not request.is_valid_request:
        raise HTTPException(
            status_code=400,
            detail="Invalid request. Must include 'github' and limit between 1-100",
        )

    try:
        result = await coordinator.process({
            "task_description": request.task_description,
            "limit": request.limit
        })
        return RecruitmentResponse(**result)
    except ValueError as e:
        # Handle validation errors (invalid repo format, repo not found)
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except aiohttp.ClientError as e:
        # Handle GitHub API connection errors
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub API. Please try again later.",
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}",
        )


# Initialize the workflow
workflow_app = create_workflow()

@app.post("/workflow")
async def execute_workflow(request: RecruitmentRequest) -> JSONResponse:
    """Execute the workflow and return results with trace information."""
    try:
        # Initialize workflow state
        state: AgentState = {
            "messages": [HumanMessage(content=request.task_description)],
            "github_data": {},
            "linkedin_data": {},
            "final_response": {}
        }
        
        # Execute workflow
        final_state = await workflow_app.ainvoke(state)
        
        # Return both results and execution trace
        return JSONResponse({
            "result": final_state["final_response"],
            "execution_trace": workflow_app.get_trace()
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )

# Add LangGraph Studio support
@app.get("/graph")
async def get_graph():
    """Return the workflow graph structure for visualization."""
    return JSONResponse(workflow_app.get_graph_json())

@app.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Return a specific execution trace."""
    trace = workflow_app.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return JSONResponse(trace)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
