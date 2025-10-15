"""AgentKit Platform Runtime Management Tools"""
import os
import json
from typing import Optional
from fastmcp import FastMCP
import volcenginesdkcore
from volcenginesdkagentkitstg.api import agentkit_stg_api
from volcenginesdkagentkitstg import models


# Global API client instance (singleton pattern)
_api_client = None


def get_api_client():
    """Get configured Volcengine API client (singleton)"""
    global _api_client
    if _api_client is None:
        # Configure Volcengine SDK
        configuration = volcenginesdkcore.Configuration()
        # Unified with CLI SDK: use VOLC_* naming convention
        configuration.ak = os.getenv("VOLC_ACCESSKEY") or os.getenv("AGENTKIT_ACCESS_KEY") or os.getenv("VOLCENGINE_ACCESS_KEY")
        configuration.sk = os.getenv("VOLC_SECRETKEY") or os.getenv("AGENTKIT_SECRET_KEY") or os.getenv("VOLCENGINE_SECRET_KEY")
        configuration.host = os.getenv("VOLC_AGENTKIT_HOST") or os.getenv("AGENTKIT_BASE_URL")
        configuration.region = os.getenv("VOLC_REGION") or os.getenv("AGENTKIT_REGION", "cn-beijing")

        # Create API client
        api_client = volcenginesdkcore.ApiClient(configuration)
        _api_client = agentkit_stg_api.AGENTKITSTGApi(api_client)
    
    return _api_client


def register_runtime_tools(mcp: FastMCP):
    """Register all Runtime management-related MCP tools"""

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
                - ⚠️ NAMING RULES: Cannot start with digits, hyphens, or underscores
                - Good: "myagent", "agent-prod"  Bad: "123agent", "-agent", "_agent"
            artifact_type: Code artifact type.
                - 'image': Container image (most common)
                - 'tos': TOS object storage code package
            artifact_url: Code artifact address.
                - For image: Full CR URL with tag (e.g., "xxx.cr.volces.com/namespace/image:tag")
                - For TOS: TOS bucket path
                - ⚠️ Get this from toolkit_build_image output (ve_cr_image_full_url)
            role_name: IAM role name for accessing Volcengine services (e.g., "TestRoleForAgentKit").
            authorizer_configuration: API authentication config (required). JSON string format:
                - KeyAuth: {"KeyAuth":{"ApiKeyName":"x-api-key","ApiKey":"secret","ApiKeyLocation":"HEADER"}}
                  * ApiKeyName: Key name in Header/Query
                  * ApiKey: Secret key value
                  * ApiKeyLocation: 'HEADER' or 'QUERY'
                - JWT: {"CustomJwtAuthorizer":{"AllowedClients":["client1"],"DiscoveryUrl":"https://..."}}
            description: Instance description (optional).
            envs: Environment variables (optional). JSON string format: [{"Key":"NAME","Value":"value"}]
            tags: Resource tags (optional). JSON string format: [{"Key":"key","Value":"value"}]
            apmplus_enable: Enable APM+ monitoring (optional, default: false).
            command: Container start command (optional). Overrides default CMD/ENTRYPOINT.
            project_name: Volcengine project name (optional, default: 'default').
            client_token: Idempotency token (optional). Max 64 ASCII chars for preventing duplicate creation.

        ⚠️ Environment Variables:
            Requires VOLC_ACCESSKEY, VOLC_SECRETKEY, VOLC_REGION, VOLC_AGENTKIT_HOST to be set.

        Returns:
            JSON string with Runtime ID. Status will be "Creating" initially.
            Use get_runtime() to check status and get full details.

        Example:
            # Basic KeyAuth example
            create_runtime(
                name="my-agent-runtime",
                artifact_type="image",
                artifact_url="agentkit-xxx.cr.volces.com/namespace/agent:latest",
                role_name="TestRoleForAgentKit",
                authorizer_configuration='{"KeyAuth":{"ApiKeyName":"x-api-key","ApiKey":"secret123","ApiKeyLocation":"HEADER"}}'
            )

            # With environment variables and monitoring
            create_runtime(
                name="production-runtime",
                artifact_type="image",
                artifact_url="agentkit-xxx.cr.volces.com/prod/app:v2.0",
                role_name="TestRoleForAgentKit",
                authorizer_configuration='{"KeyAuth":{"ApiKeyName":"api-key","ApiKey":"prod-key","ApiKeyLocation":"HEADER"}}',
                envs='[{"Key":"ENV","Value":"production"},{"Key":"LOG_LEVEL","Value":"info"}]',
                apmplus_enable=True
            )
        """
        api = get_api_client()

        # Parse and convert authorizer_configuration
        auth_config_dict = json.loads(authorizer_configuration)
        auth_config_model = models.AuthorizerConfigurationForCreateAgentKitRuntimeInput()
        
        # Handle KeyAuth
        if 'KeyAuth' in auth_config_dict or 'key_auth' in auth_config_dict:
            key_data = auth_config_dict.get('KeyAuth') or auth_config_dict.get('key_auth')
            if key_data:
                api_key = key_data.get('api_key') or key_data.get('ApiKey')
                api_key_location = key_data.get('api_key_location') or key_data.get('ApiKeyLocation')
                api_key_name = key_data.get('api_key_name') or key_data.get('ApiKeyName')
                
                auth_config_model.key_auth = models.KeyAuthForCreateAgentKitRuntimeInput(
                    api_key=api_key,
                    api_key_location=api_key_location,
                    api_key_name=api_key_name
                )
        
        # Handle CustomJwtAuthorizer
        if 'CustomJwtAuthorizer' in auth_config_dict or 'custom_jwt_authorizer' in auth_config_dict:
            jwt_data = auth_config_dict.get('CustomJwtAuthorizer') or auth_config_dict.get('custom_jwt_authorizer')
            if jwt_data:
                allowed_clients = jwt_data.get('allowed_clients') or jwt_data.get('AllowedClients')
                discovery_url = jwt_data.get('discovery_url') or jwt_data.get('DiscoveryUrl')
                auth_config_model.custom_jwt_authorizer = models.CustomJwtAuthorizerForCreateAgentKitRuntimeInput(
                    allowed_clients=allowed_clients,
                    discovery_url=discovery_url
                )
        
        # Convert envs to SDK model list
        envs_models = None
        if envs:
            envs_data = json.loads(envs)
            envs_models = [models.EnvForCreateAgentKitRuntimeInput(
                key=item.get("Key") or item.get("key"),
                value=item.get("Value") or item.get("value")
            ) for item in envs_data]
        
        # Convert tags to SDK model list
        tags_models = None
        if tags:
            tags_data = json.loads(tags)
            tags_models = [models.TagForCreateAgentKitRuntimeInput(
                key=item.get("Key") or item.get("key"),
                value=item.get("Value") or item.get("value")
            ) for item in tags_data]
        
        # Build request
        request = models.CreateAgentKitRuntimeRequest(
            name=name,
            artifact_type=artifact_type,
            artifact_url=artifact_url,
            role_name=role_name,
            authorizer_configuration=auth_config_model,
            description=description,
            envs=envs_models,
            tags=tags_models,
            apmplus_enable=apmplus_enable,
            command=command,
            project_name=project_name,
            client_token=client_token
        )
        
        # Call SDK
        response = api.create_agent_kit_runtime(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)

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
        api = get_api_client()
        request = models.DeleteAgentKitRuntimeRequest(runtime_id=runtime_id)
        response = api.delete_agent_kit_runtime(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)

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
        api = get_api_client()
        request = models.GetAgentKitRuntimeRequest(runtime_id=runtime_id)
        response = api.get_agent_kit_runtime(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)

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
        Update an existing AgentKit Runtime configuration.

        Only provided parameters will be updated; others remain unchanged.

        Args:
            runtime_id: Runtime instance ID to update.
            description: New description (optional).
            artifact_url: New code artifact address (optional).
            role_name: New IAM role name (optional).
            authorizer_configuration: New authentication config (optional). JSON string format.
            envs: New environment variables (optional). Format: [{"Key":"NAME","Value":"value"}]
            tags: New resource tags (optional). Format: [{"Key":"key","Value":"value"}]
            release_enable: Auto-release after update (optional, default: false).
            client_token: Idempotency token (optional).

        Returns:
            JSON string with update result.

        Example:
            update_runtime(
                runtime_id="r-abc123",
                description="Updated description",
                artifact_url="cr.volces.com/namespace/agent:v2.0",
                release_enable=True
            )
        """
        api = get_api_client()
        
        # Build request with only provided parameters
        request = models.UpdateAgentKitRuntimeRequest(
            runtime_id=runtime_id,
            description=description,
            artifact_url=artifact_url,
            role_name=role_name,
            release_enable=release_enable,
            client_token=client_token
        )
        
        response = api.update_agent_kit_runtime(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)

    @mcp.tool()
    async def list_runtimes(
        filters: Optional[str] = None,
        create_time_before: Optional[str] = None,
        create_time_after: Optional[str] = None,
        update_time_before: Optional[str] = None,
        update_time_after: Optional[str] = None,
        next_token: Optional[str] = None,
        max_results: Optional[int] = 20
    ) -> str:
        """
        List AgentKit Runtime instances with filtering and pagination.

        Args:
            filters: Filter conditions (optional). JSON string format:
                [{"Type":"Name","Operator":"Contain","Values":["keyword"]}]
            create_time_before: Filter by creation time before (optional). RFC3339 format.
            create_time_after: Filter by creation time after (optional). RFC3339 format.
            update_time_before: Filter by update time before (optional). RFC3339 format.
            update_time_after: Filter by update time after (optional). RFC3339 format.
            next_token: Pagination token (optional).
            max_results: Maximum items per page (optional, default: 20, max: 100).

        Returns:
            JSON string with Runtime list and next_token for pagination.

        Example:
            # List all runtimes
            list_runtimes(max_results=50)

            # With name filter
            list_runtimes(
                filters='[{"Type":"Name","Operator":"Contain","Values":["agent"]}]',
                max_results=20
            )
        """
        api = get_api_client()
        
        request = models.ListAgentKitRuntimesRequest(
            next_token=next_token,
            max_results=max_results
        )
        
        response = api.list_agent_kit_runtimes(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)

    @mcp.tool()
    async def release_runtime(
        runtime_id: str,
        version_number: Optional[int] = None
    ) -> str:
        """
        Release a specific version of the Runtime or rollback to a previous version.

        Args:
            runtime_id: Runtime instance ID.
            version_number: Version number to release (optional).
                - If not provided: release the latest version
                - If provided: rollback to specified version

        Returns:
            JSON string with release result.

        Example:
            # Release latest version
            release_runtime(runtime_id="r-abc123")

            # Rollback to version 3
            release_runtime(runtime_id="r-abc123", version_number=3)
        """
        api = get_api_client()
        request = models.ReleaseAgentKitRuntimeRequest(
            runtime_id=runtime_id,
            version_number=version_number
        )
        response = api.release_agent_kit_runtime(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)

    @mcp.tool()
    async def get_runtime_version(
        runtime_id: str,
        version_number: Optional[int] = None
    ) -> str:
        """
        Get details of a specific Runtime version.

        Args:
            runtime_id: Runtime instance ID.
            version_number: Version number (optional). If not provided, returns current version.

        Returns:
            JSON string with version details including configuration and status.

        Example:
            # Get current version
            get_runtime_version(runtime_id="r-abc123")

            # Get specific version
            get_runtime_version(runtime_id="r-abc123", version_number=5)
        """
        api = get_api_client()
        request = models.GetAgentKitRuntimeVersionRequest(
            runtime_id=runtime_id,
            version_number=version_number
        )
        response = api.get_agent_kit_runtime_version(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)

    @mcp.tool()
    async def list_runtime_versions(
        runtime_id: str,
        next_token: Optional[str] = None,
        max_results: Optional[int] = 20
    ) -> str:
        """
        List all versions of a Runtime instance.

        Returns version history including version numbers, creation times, and status.

        Args:
            runtime_id: Runtime instance ID.
            next_token: Pagination token (optional).
            max_results: Maximum items per page (optional, default: 20, max: 100).

        Returns:
            JSON string with version list and next_token for pagination.

        Example:
            # List all versions
            list_runtime_versions(
                runtime_id="r-abc123",
                max_results=20
            )
        """
        api = get_api_client()
        request = models.ListAgentKitRuntimeVersionsRequest(
            runtime_id=runtime_id,
            next_token=next_token,
            max_results=max_results
        )
        response = api.list_agent_kit_runtime_versions(request)
        return json.dumps(response.to_dict(), ensure_ascii=False)
