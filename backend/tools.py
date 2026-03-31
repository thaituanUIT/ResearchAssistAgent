from langchain_core.tools import tool
from typing import List

@tool
def generate_flowchart(nodes: List[str], edges: List[List[str]]) -> str:
    """
    Creates a mermaid flowchart from a list of nodes and a list of edges.
    Use this tool when the user asks to generate a flowchart, process flow, or concept map.
    Nodes should be short, descriptive strings representing steps or concepts.
    Edges should be exactly two strings representing a connection from the first to the second.
    """
    s = "```mermaid\ngraph TD\n"
    for i, n in enumerate(nodes):
        safe_n = str(n).replace('"', "'").replace('\n', ' ')
        s += f'{i}["{safe_n}"]\n'
    for a, b in edges:
        try:
            s += f"{nodes.index(a)} --> {nodes.index(b)}\n"
        except ValueError:
            pass
    s += "```"
    return s
