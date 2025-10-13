"""AgentKit Platform MCP Server - Implemented with FastMCP 2.0"""
import os
import json
import argparse
from typing import Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

from src.agentkit_client import AgentKitPlatformClient

# Load environment variables
load_dotenv()

# Create FastMCP server instance
mcp = FastMCP("AgentKit Platform MCP Server")

# Global client instance (singleton pattern)
_client: Optional[AgentKitPlatformClient] = None


def get_client() -> AgentKitPlatformClient:
    """Get configured AgentKit client (singleton)"""
    global _client
    if _client is None:
        _client = AgentKitPlatformClient(
            region=os.getenv("AGENTKIT_REGION", "cn-beijing"),
            base_url=os.getenv("AGENTKIT_BASE_URL"),
            access_key=os.getenv("AGENTKIT_ACCESS_KEY"),
            secret_key=os.getenv("AGENTKIT_SECRET_KEY")
        )
    return _client


# ========== Runtime Management Tools ==========

@mcp.tool()
async def create_runtime(
    name: str,
    artifact_type: str,
    artifact_url: str,
    role_name: str,
    authorizer_configuration: str,
    description: Optional[str] = None,
    envs: Optional[str] = None,
    tags: Optional[str] = None,
    apmplus_enable: Optional[bool] = None,
    command: Optional[str] = None,
    project_name: Optional[str] = None,
    client_token: Optional[str] = None
) -> str:
    """
    Create a new AgentKit Runtime instance.
    
    Runtime is a containerized environment for deploying and running Agent applications.
    
    Args:
        name: Runtime instance name.
            - Length: 1-128 characters
            - Cannot start with: digits, hyphens, or underscores
        artifact_type: Code artifact type.
            - 'image': Container image
            - 'tos': TOS object storage code package
        artifact_url: Code artifact address.
            - For image: cr.volces.com/namespace/image:tag
            - For TOS: TOS bucket path
        role_name: IAM role name for accessing Volcengine services.
        authorizer_configuration: API authentication config (required). JSON string format:
            - KeyAuth: {"KeyAuth":{"ApiKeyName":"x-api-key","ApiKey":"secret","ApiKeyLocation":"HEADER"}}
              * ApiKeyName: Key name in Header/Query
              * ApiKey: Secret key value
              * ApiKeyLocation: 'HEADER' or 'QUERY'
            - JWT: {"CustomJwtAuthorizer":{"AllowedClients":["client1"],"DiscoveryUrl":"https://..."}}
        description: Instance description (optional).
        envs: Environment variables (optional). Format: [{"Key":"NAME","Value":"value"}]
        tags: Resource tags (optional). Format: [{"Key":"key","Value":"value"}]
        apmplus_enable: Enable APM+ monitoring (optional, default: false).
        command: Container start command (optional). Overrides default CMD/ENTRYPOINT.
        project_name: Volcengine project name (optional, default: 'default').
        client_token: Idempotency token (optional). Max 64 ASCII chars for preventing duplicate creation.
        
    Returns:
        JSON string with Runtime details: runtime_id, status, configuration, etc.
    
    Example:
        # Basic KeyAuth example
        create_runtime(
            name="my-agent-runtime",
            artifact_type="image",
            artifact_url="cr.volces.com/namespace/agent:v1.0",
            role_name="AgentKitRole",
            authorizer_configuration='{"KeyAuth":{"ApiKeyName":"x-api-key","ApiKey":"secret123","ApiKeyLocation":"HEADER"}}'
        )
        
        # With environment variables and monitoring
        create_runtime(
            name="production-runtime",
            artifact_type="image",
            artifact_url="cr.volces.com/prod/app:v2.0",
            role_name="ProdRole",
            authorizer_configuration='{"KeyAuth":{"ApiKeyName":"api-key","ApiKey":"prod-key","ApiKeyLocation":"HEADER"}}',
            envs='[{"Key":"ENV","Value":"production"},{"Key":"LOG_LEVEL","Value":"info"}]',
            apmplus_enable=true
        )
    """
    client = get_client()
    
    # Parse JSON string parameters
    auth_config = json.loads(authorizer_configuration)
    
    # Convert envs (Key/Value -> key/value)
    envs_list = None
    if envs:
        envs_data = json.loads(envs)
        envs_list = [{"key": item.get("Key") or item.get("key"), 
                      "value": item.get("Value") or item.get("value")} 
                     for item in envs_data]
    
    # Convert tags (Key/Value -> key/value)
    tags_list = None
    if tags:
        tags_data = json.loads(tags)
        tags_list = [{"key": item.get("Key") or item.get("key"), 
                      "value": item.get("Value") or item.get("value")} 
                     for item in tags_data]
    
    result = await client.create_runtime(
        name=name,
        artifact_type=artifact_type,
        artifact_url=artifact_url,
        role_name=role_name,
        authorizer_configuration=auth_config,
        description=description,
        envs=envs_list,
        tags=tags_list,
        apmplus_enable=apmplus_enable,
        command=command,
        project_name=project_name,
        client_token=client_token
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def delete_runtime(runtime_id: str) -> str:
    """
    Delete the specified AgentKit Runtime instance.
    
    WARNING: This operation is irreversible. After deletion:
    - Runtime becomes inaccessible immediately
    - All data and configurations are permanently lost
    - Cannot be recovered
    
    Args:
        runtime_id: Runtime instance ID to delete.
        
    Returns:
        JSON string with deletion result.
    
    Example:
        delete_runtime(runtime_id="r-abc123")
    """
    client = get_client()
    result = await client.delete_runtime(runtime_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def get_runtime(runtime_id: str) -> str:
    """
    Get detailed information of a Runtime instance.

    Returns complete configuration including: status, version, endpoint, image,
    environment variables, authentication config, and resource allocations.

    Args:
        runtime_id: Runtime instance ID.

    Returns:
        JSON string with complete Runtime details:
        - Basic info: name, description, status
        - Configuration: image, envs, auth, resources
        - Runtime info: endpoint, current version
        - Timestamps: created_at, updated_at
    
    Example:
        get_runtime(runtime_id="r-abc123")
    """
    client = get_client()
    result = await client.get_runtime(runtime_id)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def update_runtime(
    runtime_id: str,
    description: Optional[str] = None,
    artifact_url: Optional[str] = None,
    role_name: Optional[str] = None,
    authorizer_configuration: Optional[str] = None,
    envs: Optional[str] = None,
    tags: Optional[str] = None,
    release_enable: Optional[bool] = None,
    client_token: Optional[str] = None
) -> str:
    """
    Update configuration of the specified AgentKit Runtime instance.
    
    You can update: image, environment variables, authentication config, tags, etc.
    Changes are saved but won't take effect until you release a new version.
    
    Args:
        runtime_id: Runtime instance ID (required).
        description: Instance description (optional).
        artifact_url: New artifact address (optional). Updates image version or TOS path.
        role_name: New IAM role name (optional).
        authorizer_configuration: New authentication config (optional). Same format as create_runtime.
        envs: New environment variables (optional). Format: [{"Key":"NAME","Value":"value"}]
        tags: New resource tags (optional). Format: [{"Key":"key","Value":"value"}]
        release_enable: Auto-release after update (optional, default: false).
            - true: Update and take effect immediately
            - false: Update saved as draft, requires manual release
        client_token: Idempotency token (optional).
        
    Returns:
        JSON string with updated Runtime configuration.
    
    Example:
        # Update environment variables only
        update_runtime(
            runtime_id="r-abc123",
            envs='[{"Key":"ENV","Value":"staging"}]'
        )
        
        # Update and release immediately
        update_runtime(
            runtime_id="r-abc123",
            artifact_url="cr.volces.com/namespace/app:v2.0",
            release_enable=true
        )
    """
    client = get_client()
    
    # Parse JSON string parameters
    auth_config = json.loads(authorizer_configuration) if authorizer_configuration else None
    
    # Convert envs (Key/Value -> key/value)
    envs_list = None
    if envs:
        envs_data = json.loads(envs)
        envs_list = [{"key": item.get("Key") or item.get("key"),
                      "value": item.get("Value") or item.get("value")}
                     for item in envs_data]
    
    # Convert tags (Key/Value -> key/value)
    tags_list = None
    if tags:
        tags_data = json.loads(tags)
        tags_list = [{"key": item.get("Key") or item.get("key"),
                      "value": item.get("Value") or item.get("value")}
                     for item in tags_data]
    
    result = await client.update_runtime(
        runtime_id=runtime_id,
        description=description,
        artifact_url=artifact_url,
        role_name=role_name,
        authorizer_configuration=auth_config,
        envs=envs_list,
        tags=tags_list,
        release_enable=release_enable,
        client_token=client_token
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def list_runtimes(
    filters: Optional[str] = None,
    create_time_before: Optional[str] = None,
    create_time_after: Optional[str] = None,
    update_time_before: Optional[str] = None,
    update_time_after: Optional[str] = None,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None
) -> str:
    """
    Query list of AgentKit Runtime instances under current account.
    
    Supports filtering by status, name, project and time-based queries with pagination.
    
    Args:
        filters: Filter conditions (optional). Format: [{"Name":"filter_name","Values":["value1","value2"]}]
            Common filters:
            - Name: Filter by Runtime name
            - Status: Filter by status (Creating, Ready, Error, etc.)
            - ProjectName: Filter by project
        create_time_before: Show Runtimes created before this time (optional). Format: RFC3339.
        create_time_after: Show Runtimes created after this time (optional). Format: RFC3339.
        update_time_before: Show Runtimes updated before this time (optional). Format: RFC3339.
        update_time_after: Show Runtimes updated after this time (optional). Format: RFC3339.
        next_token: Pagination token (optional). Get from previous response for next page.
        max_results: Records per page (optional). Default: 10, max: 100.
        
    Returns:
        JSON string with: Runtime list, total count, and next_token for pagination.
    
    Example:
        # List all Ready Runtimes
        list_runtimes(
            filters='[{"Name":"Status","Values":["Ready"]}]',
            max_results=20
        )
        
        # Get next page
        list_runtimes(
            next_token="token_from_previous_response",
            max_results=20
        )
    """
    client = get_client()
    
    # Parse filter conditions (array) and convert field names (Name/Values -> name/values)
    filters_list = None
    if filters:
        filters_data = json.loads(filters)
        filters_list = [{"name": item.get("Name") or item.get("name"),
                        "values": item.get("Values") or item.get("values")}
                       for item in filters_data]
    
    result = await client.list_runtimes(
        filters=filters_list,
        create_time_before=create_time_before,
        create_time_after=create_time_after,
        update_time_before=update_time_before,
        update_time_after=update_time_after,
        next_token=next_token,
        max_results=max_results
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def release_runtime(
    runtime_id: str,
    version_number: Optional[int] = None
) -> str:
    """
    Release a Runtime version or create a new one.
    
    Configuration and code updates only take effect after release.
    You can also rollback to a previous version using this method.
    
    Args:
        runtime_id: Runtime instance ID (required).
        version_number: Version to release (optional).
            - Omit or pass 0: Create and release new version from latest config
            - Pass specific number: Release that historical version (rollback)
        
    Returns:
        JSON string with release result and version information.
    
    Example:
        # Create and release new version
        release_runtime(runtime_id="r-abc123")
        
        # Rollback to version 5
        release_runtime(
            runtime_id="r-abc123",
            version_number=5
        )
    """
    client = get_client()
    result = await client.release_runtime(runtime_id, version_number)
    return json.dumps(result, ensure_ascii=False)


# ========== Version Management Tools ==========

@mcp.tool()
async def get_runtime_version(
    runtime_id: str,
    version_number: Optional[int] = None
) -> str:
    """
    Get detailed configuration of a specific Runtime version.
    
    Includes: image, environment variables, authentication config, resource specs, etc.
    
    Args:
        runtime_id: Runtime instance ID (required).
        version_number: Version number (optional).
            - Omit: Returns currently running version
            - Specify number: Returns that specific version
        
    Returns:
        JSON string with complete version config, creation time, and status.
    
    Example:
        # Get current running version
        get_runtime_version(runtime_id="r-abc123")
        
        # Get specific version
        get_runtime_version(
            runtime_id="r-abc123",
            version_number=3
        )
    """
    client = get_client()
    result = await client.get_runtime_version(runtime_id, version_number)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
async def list_runtime_versions(
    runtime_id: str,
    next_token: Optional[str] = None,
    max_results: Optional[int] = None
) -> str:
    """
    List all historical versions of a Runtime.
    
    Shows version number, creation time, status, and config summary for each version.
    Useful for tracking changes and selecting versions for rollback.
    
    Args:
        runtime_id: Runtime instance ID (required).
        next_token: Pagination token (optional). From previous response.
        max_results: Records per page (optional). Default: 10, max: 100.
        
    Returns:
        JSON string with version list and next_token for pagination.
    
    Example:
        # List all versions
        list_runtime_versions(
            runtime_id="r-abc123",
            max_results=20
        )
    """
    client = get_client()
    result = await client.list_runtime_versions(runtime_id, next_token, max_results)
    return json.dumps(result, ensure_ascii=False)


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
