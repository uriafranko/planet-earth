# server.py
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp_app = FastMCP("Planet Earth MCP")


# Add an addition tool
@mcp_app.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
