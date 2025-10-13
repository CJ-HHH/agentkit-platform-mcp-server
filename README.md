# AgentKit Platform MCP Server

Model Context Protocol (MCP) server for AgentKit Platform Runtime API, built with **FastMCP 2.0** and **uv**.

## Quick Start

### Option 1: Direct Run with uvx (Recommended)

```bash
# Run directly from GitHub (no local installation needed)
uvx --from git+https://github.com/your-org/agentkit-platform-mcp-server ap-mcp-server
```

Environment variables can be set via IDE configuration or system env.

### Option 2: Local Development

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment variables
cp .env.example .env
# Edit .env file with your credentials

# 3. Run the server
uv run ap-mcp-server
```

Server URL: `http://127.0.0.1:8000/mcp`

## Features

Provides 8 AgentKit Platform Runtime API tools with comprehensive documentation:

- **create_runtime** - Create a new Runtime instance
- **delete_runtime** - Delete a Runtime instance (with safety warnings)
- **get_runtime** - Get detailed Runtime information
- **update_runtime** - Update Runtime configuration
- **list_runtimes** - List Runtimes with filtering and pagination
- **release_runtime** - Release/rollback Runtime versions
- **get_runtime_version** - Get specific version details
- **list_runtime_versions** - List all version history

### Key Features

✅ **Singleton Pattern** - Client instance reused across requests for better performance  
✅ **Field Conversion** - Automatic conversion between PascalCase (API) and snake_case (SDK)  
✅ **Multi-Auth Support** - Both KeyAuth and JWT authentication  
✅ **Rich Documentation** - Detailed docstrings with examples for each tool  
✅ **Type Safety** - Full type hints and validation  

## Environment Variables

Configure the following variables in `.env` file or IDE configuration:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AGENTKIT_REGION` | Volcengine region | No | `cn-beijing` |
| `AGENTKIT_BASE_URL` | API endpoint (without https://) | Yes | - |
| `AGENTKIT_ACCESS_KEY` | Volcengine Access Key | Yes | - |
| `AGENTKIT_SECRET_KEY` | Volcengine Secret Key | Yes | - |

**Example `.env` file:**

```env
AGENTKIT_REGION=cn-beijing
AGENTKIT_BASE_URL=open.volcengineapi.com
AGENTKIT_ACCESS_KEY=AKLT***************
AGENTKIT_SECRET_KEY=****************************
```

**Configuration Priority:**
1. IDE JSON config env (highest priority)
2. System environment variables
3. `.env` file (loaded by `load_dotenv()`, won't override existing vars)

## IDE Integration

### Claude Desktop

Edit config file: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "agentkit-platform": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/your-org/agentkit-platform-mcp-server",
        "ap-mcp-server"
      ],
      "env": {
        "AGENTKIT_REGION": "cn-beijing",
        "AGENTKIT_BASE_URL": "open.volcengineapi.com",
        "AGENTKIT_ACCESS_KEY": "your_access_key",
        "AGENTKIT_SECRET_KEY": "your_secret_key"
      }
    }
  }
}
```

### Trae / Cursor / Windsurf

Add to IDE MCP configuration:

**Windsurf:** `~/.codeium/windsurf/mcp_config.json`  
**Cursor:** Settings → Features → Model Context Protocol

```json
{
  "mcpServers": {
    "agentkit-platform": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/your-org/agentkit-platform-mcp-server",
        "ap-mcp-server"
      ],
      "env": {
        "AGENTKIT_REGION": "cn-beijing",
        "AGENTKIT_BASE_URL": "open.volcengineapi.com",
        "AGENTKIT_ACCESS_KEY": "AKLT***************",
        "AGENTKIT_SECRET_KEY": "****************************"
      }
    }
  }
}
```

**Important Notes:**
- Replace GitHub URL with your actual repository URL
- Replace `AGENTKIT_ACCESS_KEY` and `AGENTKIT_SECRET_KEY` with your credentials
- `AGENTKIT_BASE_URL` should be hostname only, **do not** include `https://` prefix
- IDE JSON config env variables have highest priority (override `.env` file)
- **No local installation needed** - `uvx` downloads and runs the package automatically

## Tool Parameters

### Authentication Configuration

**KeyAuth (API Key):**
```json
{
  "KeyAuth": {
    "ApiKeyName": "x-api-key",
    "ApiKey": "your_secret_key",
    "ApiKeyLocation": "HEADER"
  }
}
```

**JWT (JSON Web Token):**
```json
{
  "CustomJwtAuthorizer": {
    "AllowedClients": ["client1", "client2"],
    "DiscoveryUrl": "https://example.com/.well-known/openid-configuration"
  }
}
```

### Environment Variables & Tags

Format for `envs` and `tags` parameters:

```json
[
  {"Key": "ENV_NAME", "Value": "value1"},
  {"Key": "DEBUG", "Value": "true"}
]
```

**Field Conversion:**  
The server automatically converts between PascalCase (`Key`/`Value`) and snake_case (`key`/`value`) for SDK compatibility.

### Filters

Format for `list_runtimes` filters:

```json
[
  {"Name": "Status", "Values": ["Ready", "Creating"]},
  {"Name": "ProjectName", "Values": ["default"]}
]
```

**Available Filters:**
- `Name` - Filter by Runtime name
- `Status` - Filter by status (Creating, Ready, Releasing, Error, etc.)
- `ProjectName` - Filter by project name

## Tool Examples

### Create Runtime with Full Parameters

```python
create_runtime(
    name="production-runtime",
    artifact_type="image",
    artifact_url="cr.volces.com/namespace/app:v2.0",
    role_name="AgentKitRole",
    authorizer_configuration='{"KeyAuth":{"ApiKeyName":"api-key","ApiKey":"secret","ApiKeyLocation":"HEADER"}}',
    envs='[{"Key":"ENV","Value":"production"},{"Key":"LOG_LEVEL","Value":"info"}]',
    tags='[{"Key":"Owner","Value":"DevTeam"},{"Key":"Project","Value":"MainApp"}]',
    apmplus_enable=true,
    command="python3 -m uvicorn main:app --host 0.0.0.0",
    project_name="default"
)
```

### Update and Release

```python
# Update configuration
update_runtime(
    runtime_id="r-abc123",
    envs='[{"Key":"ENV","Value":"staging"}]',
    release_enable=false  # Save as draft
)

# Release new version
release_runtime(runtime_id="r-abc123")

# Or rollback to previous version
release_runtime(runtime_id="r-abc123", version_number=5)
```

### List with Filters

```python
# Find all Ready runtimes
list_runtimes(
    filters='[{"Name":"Status","Values":["Ready"]}]',
    max_results=20
)

# With time range
list_runtimes(
    create_time_after="2025-01-01T00:00:00Z",
    max_results=50
)
```

## Development

```bash
# Run the server locally
uv run ap-mcp-server

# Or run with Python directly
uv run python src/server.py

# List all available tools
uv run fastmcp list src.server:mcp

# Development mode (hot reload)
uv run fastmcp dev src.server:mcp

# Run tests
uv run pytest tests/
```

## Architecture

### Client Singleton Pattern

The AgentKit client uses a singleton pattern to improve performance:

```python
# Global client instance (singleton)
_client: Optional[AgentKitPlatformClient] = None

def get_client() -> AgentKitPlatformClient:
    """Get configured AgentKit client (singleton)"""
    global _client
    if _client is None:
        _client = AgentKitPlatformClient(...)
    return _client
```

**Benefits:**
- ✅ Client instance created only once
- ✅ Reduces initialization overhead
- ✅ Shared connection pooling

### Field Name Conversion

Automatic conversion between API format and SDK format:

| API Format (PascalCase) | SDK Format (snake_case) |
|-------------------------|-------------------------|
| `Key` / `Value` | `key` / `value` |
| `Name` / `Values` | `name` / `values` |
| `ApiKeyName` | `api_key_name` |
| `AllowedClients` | `allowed_clients` |

This is handled transparently - you use PascalCase in JSON strings, server converts to snake_case for SDK.

## Tech Stack

- **FastMCP 2.0** - Modern MCP framework
- **uv** - Fast Python package manager
- **Volcengine Python SDK** - Official AgentKit API SDK
- **httpx** - Async HTTP client
- **pydantic** - Data validation

## License

MIT License
