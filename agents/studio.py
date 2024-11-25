from typing import Any, Dict, List, TypedDict

from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import SystemMessage
from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage

from agents.github_agent import GitHubAgent
from agents.linkedin_agent import LinkedInAgent
from agents.new_coordinator import CoordinatorAgent


def get_node_description(node_name: str) -> Dict[str, str]:
    """Get description and color for nodes in the graph visualization."""
    nodes = {
        "coordinator_node": {
            "description": "Processes user input and extracts repository information",
            "color": "#4CAF50"  # Green
        },
        "github_node": {
            "description": "Fetches and processes GitHub repository data",
            "color": "#2196F3"  # Blue
        },
        "linkedin_node": {
            "description": "Retrieves and processes LinkedIn profile data",
            "color": "#0077B5"  # LinkedIn Blue
        },
        "merge_node": {
            "description": "Combines GitHub and LinkedIn data into final result",
            "color": "#9C27B0"  # Purple
        }
    }
    return nodes.get(node_name, {"description": "Unknown node", "color": "#757575"})


def get_edge_description(from_node: str, to_node: str) -> str:
    """Get description for edges in the graph visualization."""
    edges = {
        ("coordinator_node", "github_node"): "Repository information extracted, fetching GitHub data",
        ("github_node", "linkedin_node"): "GitHub profiles found, fetching LinkedIn data",
        ("github_node", "merge_node"): "GitHub-only profiles ready for merging",
        ("linkedin_node", "merge_node"): "LinkedIn data retrieved, proceeding to merge"
    }
    return edges.get((from_node, to_node), "Transition between nodes")


class MessageDisplay(TypedDict, total=False):
    type: str
    content: str
    style: Dict[str, str]
    name: str

def format_message_for_display(message: BaseMessage) -> MessageDisplay:
    """Format message for visualization in LangGraph Studio."""
    if isinstance(message, HumanMessage):
        return {
            "type": message.type,
            "content": str(message.content),
            "style": {"color": "#000000", "background": "#E3F2FD"},
            "name": "user"
        }
    elif isinstance(message, FunctionMessage):
        return {
            "type": message.type,
            "content": str(message.content),
            "name": message.name,
            "style": {"color": "#FFFFFF", "background": "#0D47A1"}
        }
    else:
        return {
            "type": message.type,
            "content": str(message.content),
            "style": {"color": "#000000", "background": "#EEEEEE"},
            "name": "system"
        }


def get_tools_description() -> List[Dict[str, str]]:
    """Get descriptions of available tools for Studio documentation."""
    return [
        {
            "name": "GitHub Agent",
            "description": "Fetches repository contributors, maintainers, and activity metrics",
            "parameters": ["repository_name", "type", "limit", "include_metrics"]
        },
        {
            "name": "LinkedIn Agent",
            "description": "Retrieves detailed professional profiles from LinkedIn",
            "parameters": ["profile_urls"]
        },
        {
            "name": "Coordinator Agent",
            "description": "Orchestrates the workflow and merges data from other agents",
            "parameters": ["task_description", "limit"]
        }
    ]


def create_studio_config() -> Dict[str, Any]:
    """Create configuration for LangGraph Studio."""
    return {
        "title": "GitHub & LinkedIn Profile Analyzer",
        "description": "Analyze GitHub contributors and their LinkedIn profiles",
        "version": "1.0.0",
        "nodes": {
            node: get_node_description(node)
            for node in ["coordinator_node", "github_node", "linkedin_node", "merge_node"]
        },
        "tools": get_tools_description(),
        "message_formatters": {
            "human": lambda m: format_message_for_display(m),
            "function": lambda m: format_message_for_display(m),
            "system": lambda m: format_message_for_display(m)
        }
    }
