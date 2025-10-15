# AgentKit Platform MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP 2.0](https://img.shields.io/badge/FastMCP-2.0-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Model Context Protocol (MCP) server for AgentKit Platform Runtime API, built with **FastMCP 2.0** and **uv**.

**Features:**
- 🚀 16 MCP Tools - Complete Runtime & Toolkit operations
- 🔄 3 Workflows - Local, Cloud, Hybrid deployment support
- ⚡ Official PyPI - Latest agentkit-sdk-python-inhouse-nightly
- 📦 Zero Config - Auto field conversion & singleton pattern
- 🎯 Production Ready - Comprehensive documentation & examples

## Quick Start

### Option 1: Direct Run with uvx (Recommended)

```bash
# Run directly from GitHub (no local installation needed)
uvx --from git+https://github.com/CJ-HHH/agentkit-platform-mcp-server ap-mcp-server
```

Environment variables can be set via IDE configuration or system env.

### Option 2: Local Development

```bash
# 1. Install dependencies
uv sync

# Note: agentkit-sdk-python-inhouse-nightly is installed from official PyPI
# For latest version, use: pip install -U agentkit-sdk-python-inhouse-nightly -i https://pypi.org/simple

# 2. Configure environment variables
cp .env.example .env
# Edit .env file with your credentials

# 3. Run the server (stdio mode, for IDE integration)
uv run ap-mcp-server

# Or run with HTTP server
uv run ap-mcp-server -t streamable-http
```

## Transport Modes

### stdio (Default)
- **Best for:** IDE integration (Windsurf, Claude Desktop, Cursor)
- **Communication:** Through stdin/stdout
- **Usage:** `ap-mcp-server` or `ap-mcp-server -t stdio`

### streamable-http
- **Best for:** Direct HTTP testing, web integrations
- **Server URL:** `http://127.0.0.1:8000/mcp`
- **Usage:** `ap-mcp-server -t streamable-http`

**Command Options:**
```bash
ap-mcp-server -h              # Show help
ap-mcp-server                 # Run with stdio (default)
ap-mcp-server -t stdio        # Explicitly set stdio mode
ap-mcp-server -t streamable-http  # Run HTTP server
```

## Features

### Runtime Management Tools (8 tools)

Provides AgentKit Platform Runtime API tools for managing containerized agent environments:

- **create_runtime** - Create a new Runtime instance
- **delete_runtime** - Delete a Runtime instance (with safety warnings)
- **get_runtime** - Get detailed Runtime information
- **update_runtime** - Update Runtime configuration
- **list_runtimes** - List Runtimes with filtering and pagination
- **release_runtime** - Release/rollback Runtime versions
- **get_runtime_version** - Get specific version details
- **list_runtime_versions** - List all version history

### Toolkit CLI Tools (8 tools)

Provides AgentKit Toolkit CLI operations for complete agent development lifecycle:

#### 📝 Project Setup
- **toolkit_init_project** - Initialize a new agent project from template
- **toolkit_edit_config** - Edit agentkit.yaml configuration (auto-creates if not exists)
  - Supports: entry_point, workflow_type, project_name, image_name, runtime_name, role_name, entry_port, **envs**
  - One-step configuration with environment variables support

#### 🔨 Build & Deploy
- **toolkit_build_image** - Build Docker image for the agent
- **toolkit_deploy_agent** - Deploy agent to target environment
- **toolkit_launch_agent** - Build and deploy in one command

#### 🚀 Runtime Operations
- **toolkit_invoke_agent** - Send test request to deployed agent
- **toolkit_get_status** - Check agent runtime status
- **toolkit_destroy_runtime** - Destroy running agent runtime

### Key Features

✅ **Singleton Pattern** - Client instance reused across requests for better performance  
✅ **Field Conversion** - Automatic conversion between PascalCase (API) and snake_case (SDK)  
✅ **Multi-Auth Support** - Both KeyAuth and JWT authentication  
✅ **Rich Documentation** - Detailed docstrings with examples for each tool  
✅ **Type Safety** - Full type hints and validation  

## Environment Variables

Configure the following variables in `.env` file or IDE configuration.

**Unified VOLC_* Naming (Recommended):**

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VOLC_ACCESSKEY` | Volcengine Access Key | Yes | - |
| `VOLC_SECRETKEY` | Volcengine Secret Key | Yes | - |
| `VOLC_REGION` | Volcengine region | No | `cn-beijing` |
| `VOLC_AGENTKIT_HOST` | API endpoint (without https://) | Yes | - |

**Example `.env` file:**

```env
VOLC_ACCESSKEY=AKLT***************
VOLC_SECRETKEY=****************************
VOLC_REGION=cn-beijing
VOLC_AGENTKIT_HOST=agentkit-stg.cn-beijing.volcengineapi.com
```

**Backward Compatibility:**  
Legacy `AGENTKIT_*` variable names are still supported for backward compatibility.

**Configuration Priority:**
1. `.env` file (highest priority - overrides all others)
2. IDE JSON config env variables
3. System environment variables

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
        "git+https://github.com/CJ-HHH/agentkit-platform-mcp-server",
        "ap-mcp-server"
      ],
      "env": {
        "VOLC_ACCESSKEY": "your_access_key",
        "VOLC_SECRETKEY": "your_secret_key",
        "VOLC_REGION": "cn-beijing",
        "VOLC_SERVICE": "agentkit_stg",
        "VOLC_AGENTKIT_HOST": "agentkit-stg.cn-beijing.volcengineapi.com"
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
        "git+https://github.com/CJ-HHH/agentkit-platform-mcp-server",
        "ap-mcp-server"
      ],
      "env": {
        "VOLC_ACCESSKEY": "AKLT***************",
        "VOLC_SECRETKEY": "****************************",
        "VOLC_REGION": "cn-beijing",
        "VOLC_SERVICE": "agentkit_stg",
        "VOLC_AGENTKIT_HOST": "agentkit-stg.cn-beijing.volcengineapi.com"
      }
    }
  }
}
```

**Important Notes:**
- Replace GitHub URL with your actual repository URL
- Replace `VOLC_ACCESSKEY` and `VOLC_SECRETKEY` with your credentials
- `VOLC_AGENTKIT_HOST` should be hostname only, **do not** include `https://` prefix
- `.env` file has highest priority and will override IDE JSON config
- **No local installation needed** - `uvx` downloads and runs the package automatically
- **Transport mode:** stdio is default, no need to specify `-t stdio` in args (IDEs use stdio automatically)

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
