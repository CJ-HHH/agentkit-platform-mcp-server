"""AgentKit Platform MCP Server - Implemented with FastMCP 2.0"""
import argparse
from pathlib import Path
from fastmcp import FastMCP
from dotenv import load_dotenv

from src.tools.runtime_tools import register_runtime_tools
from src.tools.cli_tools import register_cli_tools
from src.utils.tool_helpers import init_cloud_credentials

# Load environment variables from project root
# Use override=True to ensure .env values take precedence over existing env vars
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Initialize cloud credentials (map legacy env vars to VOLC_* naming)
# This ensures both runtime_tools and cli_tools can access credentials
init_cloud_credentials()

# Create FastMCP server instance
mcp = FastMCP("AgentKit Platform MCP Server")

# Register all tools
register_runtime_tools(mcp)
register_cli_tools(mcp)


# Entry point for command line tool
def main():
    """Main entry point for ap-mcp-server command"""
    parser = argparse.ArgumentParser(
        description="AgentKit Platform MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio (default, for IDE integration)
  ap-mcp-server

  # Run with HTTP server
  ap-mcp-server -t streamable-http
  ap-mcp-server --transport streamable-http
        """
    )
    parser.add_argument(
        "-t", "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)"
    )

    args = parser.parse_args()
    mcp.run(transport=args.transport)


# Start server
if __name__ == "__main__":
    main()
