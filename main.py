from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
        result = await coordinator.process(
            {"task_description": request.task_description, "limit": request.limit}
        )
        return RecruitmentResponse(**result)
    except ValueError as e:
        # Handle validation errors (invalid repo format, repo not found)
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except aiohttp.ClientError:
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
            "final_response": {},
        }

        # Execute workflow
        final_state = await workflow_app.ainvoke(state)

        # Return both results and execution trace
        return JSONResponse(
            {
                "result": final_state["final_response"],
                "execution_trace": workflow_app.get_trace(),
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Workflow execution failed: {str(e)}"
        )


# Add LangGraph Studio support
from agents.studio import create_studio_config

studio_config = create_studio_config()


@app.get("/studio/config")
async def get_studio_config():
    """Return the LangGraph Studio configuration."""
    return JSONResponse(studio_config)


@app.get("/studio/graph")
async def get_graph():
    """Return the workflow graph structure for visualization."""
    graph_json = workflow_app.get_graph_json()

    # Enhance graph with studio configurations
    for node in graph_json["nodes"]:
        node_config = studio_config["nodes"].get(node["id"], {})
        node["description"] = node_config.get("description", "")
        node["style"] = {"backgroundColor": node_config.get("color", "#757575")}

    return JSONResponse(graph_json)


@app.get("/studio/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Return a specific execution trace with enhanced visualization."""
    trace = workflow_app.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    # Format messages in the trace
    for step in trace["steps"]:
        if "messages" in step:
            formatted_messages = []
            for msg in step["messages"]:
                try:
                    msg_type = getattr(msg, "type", "system")
                    formatter = studio_config["message_formatters"].get(
                        msg_type, studio_config["message_formatters"]["system"]
                    )
                    formatted_messages.append(formatter(msg))
                except Exception as e:
                    formatted_messages.append(
                        {
                            "type": "system",
                            "content": f"Error formatting message: {str(e)}",
                            "style": {"color": "#000000", "background": "#FFCDD2"},
                            "name": "error",
                        }
                    )
            step["messages"] = formatted_messages

    return JSONResponse(trace)


@app.get("/studio/tools")
async def get_tools():
    """Return available tools and their descriptions."""
    return JSONResponse(studio_config["tools"])


@app.get("/studio/traces")
async def list_traces(limit: int = 10):
    """List recent execution traces."""
    traces = workflow_app.list_traces(limit)
    return JSONResponse(
        {
            "total": len(traces),
            "traces": [
                {
                    "id": trace["id"],
                    "timestamp": trace["timestamp"],
                    "status": trace["status"],
                    "duration": trace["duration"],
                }
                for trace in traces
            ],
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
