from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.schema.runnable import RunnableLambda
from langserve import add_routes
from pydantic import BaseModel

from agents.coordinator import CoordinatorAgent
from storage.models import DeveloperProfile

app = FastAPI(title="AI Recruiter POC")

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


class RecruitmentRequest(BaseModel):
    task_description: str
    limit: int = 50


class RecruitmentResponse(BaseModel):
    developers: List[DeveloperProfile]
    total: int


@app.post("/recruit", response_model=RecruitmentResponse)
async def recruit_developers(request: RecruitmentRequest):
    try:
        developers = await coordinator.execute_task(
            request.task_description, limit=request.limit
        )
        return RecruitmentResponse(developers=developers, total=len(developers))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Create a runnable chain from the execute_task function
async def execute_task_wrapper(input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        developers = await coordinator.execute_task(
            input_data["task_description"], limit=input_data.get("limit", 50)
        )
        return {"developers": developers, "total": len(developers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Create the runnable chain using the pipe operator
runnable_chain = RunnableLambda(execute_task_wrapper)

# Add LangServe routes for LangGraph UI
add_routes(
    app,
    runnable_chain,
    path="/langserve",
    input_type=RecruitmentRequest,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
