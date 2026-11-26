"""Model Context Protocol adapter for PIX.

``pix.mcp.tools`` holds the agent-facing tool logic and depends only on PIX.
``pix.mcp.server`` registers those tools with the official MCP Python SDK,
which is the optional ``pix[mcp]`` extra. Start the server with ``pix-mcp``.

The adapter exposes existing PIX operators. It adds no process-mining
algorithm of its own: an operation PIX does not implement is reported as
``unavailable`` instead of being approximated.
"""

from pix.mcp.tools import PixToolbox, ToolError

__all__ = ["PixToolbox", "ToolError"]
