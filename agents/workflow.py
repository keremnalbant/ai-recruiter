from typing import Annotated, Any, Dict, List, TypedDict
from langgraph.graph import Graph, MessageGraph
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage

from agents.github_agent import GitHubAgent
from agents.linkedin_agent import LinkedInAgent
from agents.new_coordinator import CoordinatorAgent


class AgentState(TypedDict):
    """State of the workflow."""
    messages: List[BaseMessage]
    github_data: Dict[str, Any]
    linkedin_data: Dict[str, Any]
    final_response: Dict[str, Any]


def create_workflow() -> Graph:
    """Create the workflow graph."""
    
    # Initialize agents
    coordinator = CoordinatorAgent()
    github_agent = GitHubAgent()
    linkedin_agent = LinkedInAgent()

    # Create workflow graph
    workflow = MessageGraph()

    # Define agent nodes
    @workflow.node()
    async def coordinator_node(state: AgentState) -> Dict[str, Any]:
        """Process user input and determine next steps."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if not isinstance(last_message, HumanMessage):
            return {"decision": "end"}
            
        # Extract repository from user input
        result = await coordinator._extract_repository_info(last_message.content)
        
        # Add decision to state
        messages.append(FunctionMessage(
            content={
                "decision": "github",
                "repository": result
            },
            name="coordinator"
        ))
        return {"messages": messages}

    @workflow.node()
    async def github_node(state: AgentState) -> Dict[str, Any]:
        """Process GitHub repository information."""
        messages = state["messages"]
        last_decision = messages[-1]
        if isinstance(last_decision, FunctionMessage):
            decision_data = last_decision.content
            repository = decision_data.get("repository", "")
        else:
            raise ValueError("Expected function message with decision")
        
        github_result = await github_agent.process({
            "repository_name": repository,
            "type": "contributors",
            "limit": 50
        })
        
        # Store GitHub data in state
        state["github_data"] = github_result
        
        # Check if we have LinkedIn URLs to process
        linkedin_urls = []
        for profile in github_result["profiles"]:
            if "social_urls" in profile and "linkedin" in profile["social_urls"]:
                linkedin_urls.append(profile["social_urls"]["linkedin"])
        
        # Add decision to state
        if linkedin_urls:
            messages.append(FunctionMessage(
                content={
                    "decision": "linkedin",
                    "urls": linkedin_urls
                },
                name="github"
            ))
        else:
            messages.append(FunctionMessage(
                content={"decision": "end"},
                name="github"
            ))
        
        return {"messages": messages, "github_data": github_result}

    @workflow.node()
    async def linkedin_node(state: AgentState) -> Dict[str, Any]:
        """Process LinkedIn profiles."""
        messages = state["messages"]
        last_decision = messages[-1]
        if isinstance(last_decision, FunctionMessage):
            decision_data = last_decision.content
            urls = decision_data.get("urls", [])
        else:
            raise ValueError("Expected function message with decision")
        
        # Process LinkedIn profiles
        linkedin_result = await linkedin_agent.process({
            "profile_urls": urls
        })
        
        # Store LinkedIn data and add decision
        state["linkedin_data"] = linkedin_result
        messages.append(FunctionMessage(
            content={"decision": "merge"},
            name="linkedin"
        ))
        
        return {"messages": messages, "linkedin_data": linkedin_result}

    @workflow.node()
    async def merge_node(state: AgentState) -> Dict[str, Any]:
        """Merge GitHub and LinkedIn data."""
        # Get data from state
        github_data = state.get("github_data", {})
        linkedin_data = state.get("linkedin_data", {})
        
        # Merge results
        merged_result = await coordinator._merge_results(github_data, linkedin_data)
        
        # Store final response and add decision
        state["final_response"] = merged_result
        messages = state["messages"]
        messages.append(FunctionMessage(
            content={
                "decision": "end",
                "result": merged_result
            },
            name="merge"
        ))
        
        return {
            "messages": messages,
            "final_response": merged_result
        }

    # Define edges
    workflow.add_edge("coordinator_node", "github_node")
    workflow.add_edge("github_node", "linkedin_node")
    workflow.add_edge("linkedin_node", "merge_node")
    
    # Define conditional edges
    @workflow.edge("github_node")
    def github_conditional(state: AgentState) -> str:
        """Route based on GitHub node decision."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, FunctionMessage):
            decision = last_message.content.get("decision", "end")
            if decision == "linkedin":
                return "linkedin_node"
            elif decision == "end":
                return "merge_node"
        
        return "merge_node"

    @workflow.edge("linkedin_node")
    def linkedin_conditional(state: AgentState) -> str:
        """Route based on LinkedIn node decision."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, FunctionMessage):
            return "merge_node"
        
        return "merge_node"

    # Set entry point
    workflow.set_entry_point("coordinator_node")

    # Compile the graph
    app = workflow.compile()

    return app
