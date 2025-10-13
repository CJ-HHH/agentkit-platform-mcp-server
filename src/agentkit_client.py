"""AgentKit Platform API Client Wrapper - Based on Volcengine SDK"""
import os
from typing import Dict, Any, Optional, List
import volcenginesdkcore
from volcenginesdkagentkitstg.api import agentkit_stg_api
from volcenginesdkagentkitstg import models


class AgentKitPlatformClient:
    """AgentKit Platform API Client - Using Volcengine SDK"""

    def __init__(
        self,
        region: str = "cn-beijing",
        base_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        """
        Initialize client

        Args:
            region: Region
            base_url: API service endpoint
            access_key: Access key
            secret_key: Secret key
        """
        # Configure Volcengine SDK
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = access_key or os.getenv("VOLCENGINE_ACCESS_KEY")
        configuration.sk = secret_key or os.getenv("VOLCENGINE_SECRET_KEY")
        configuration.host = base_url or os.getenv("AGENTKIT_BASE_URL")
        configuration.region = region or os.getenv("AGENTKIT_REGION", "cn-beijing")

        # Create API client
        api_client = volcenginesdkcore.ApiClient(configuration)
        self.api = agentkit_stg_api.AGENTKITSTGApi(api_client)

    async def create_runtime(
        self,
        name: str,
        artifact_type: str,
        artifact_url: str,
        role_name: str,
        authorizer_configuration: Dict[str, Any],
        description: Optional[str] = None,
        envs: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        apmplus_enable: Optional[bool] = None,
        command: Optional[str] = None,
        project_name: Optional[str] = None,
        client_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create AgentKit Runtime"""
        
        # Convert authorizer_configuration to SDK model
        auth_config_model = models.AuthorizerConfigurationForCreateAgentKitRuntimeInput()
        
        # Handle CustomJwtAuthorizer
        if 'CustomJwtAuthorizer' in authorizer_configuration or 'custom_jwt_authorizer' in authorizer_configuration:
            jwt_data = authorizer_configuration.get('CustomJwtAuthorizer') or authorizer_configuration.get('custom_jwt_authorizer')
            if jwt_data:
                # Convert field names (support both formats)
                allowed_clients = jwt_data.get('allowed_clients') or jwt_data.get('AllowedClients')
                discovery_url = jwt_data.get('discovery_url') or jwt_data.get('DiscoveryUrl')
                auth_config_model.custom_jwt_authorizer = models.CustomJwtAuthorizerForCreateAgentKitRuntimeInput(
                    allowed_clients=allowed_clients,
                    discovery_url=discovery_url
                )
        
        # Handle KeyAuth
        if 'KeyAuth' in authorizer_configuration or 'key_auth' in authorizer_configuration:
            key_data = authorizer_configuration.get('KeyAuth') or authorizer_configuration.get('key_auth')
            if key_data:
                # Extract parameters (support PascalCase and snake_case)
                api_key = key_data.get('api_key') or key_data.get('ApiKey')
                api_key_location = key_data.get('api_key_location') or key_data.get('ApiKeyLocation')
                api_key_name = key_data.get('api_key_name') or key_data.get('ApiKeyName')

                # Create KeyAuth model (SDK now has native support for api_key_name)
                key_auth_model = models.KeyAuthForCreateAgentKitRuntimeInput(
                    api_key=api_key,
                    api_key_location=api_key_location,
                    api_key_name=api_key_name
                )
                auth_config_model.key_auth = key_auth_model
        
        # Convert envs to SDK model list
        envs_models = None
        if envs:
            envs_models = [models.EnvForCreateAgentKitRuntimeInput(**env) for env in envs]
        
        # Convert tags to SDK model list
        tags_models = None
        if tags:
            tags_models = [models.TagForCreateAgentKitRuntimeInput(**tag) for tag in tags]
        
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
        response = self.api.create_agent_kit_runtime(request)
        return response.to_dict()

    async def delete_runtime(self, runtime_id: str) -> Dict[str, Any]:
        """Delete AgentKit Runtime"""
        request = models.DeleteAgentKitRuntimeRequest(runtime_id=runtime_id)
        response = self.api.delete_agent_kit_runtime(request)
        return response.to_dict()

    async def get_runtime(self, runtime_id: str) -> Dict[str, Any]:
        """Get AgentKit Runtime details"""
        request = models.GetAgentKitRuntimeRequest(runtime_id=runtime_id)
        response = self.api.get_agent_kit_runtime(request)
        return response.to_dict()

    async def update_runtime(
        self,
        runtime_id: str,
        description: Optional[str] = None,
        artifact_url: Optional[str] = None,
        role_name: Optional[str] = None,
        authorizer_configuration: Optional[Dict[str, Any]] = None,
        envs: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        release_enable: Optional[bool] = None,
        client_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update AgentKit Runtime"""

        # Convert authorizer_configuration to SDK model (only when provided)
        auth_config_model = None
        if authorizer_configuration:
            auth_config_model = models.AuthorizerConfigurationForUpdateAgentKitRuntimeInput()
            
            # Handle CustomJwtAuthorizer
            if 'CustomJwtAuthorizer' in authorizer_configuration or 'custom_jwt_authorizer' in authorizer_configuration:
                jwt_data = authorizer_configuration.get('CustomJwtAuthorizer') or authorizer_configuration.get('custom_jwt_authorizer')
                if jwt_data:
                    # Convert field names (support both formats)
                    allowed_clients = jwt_data.get('allowed_clients') or jwt_data.get('AllowedClients')
                    discovery_url = jwt_data.get('discovery_url') or jwt_data.get('DiscoveryUrl')
                    auth_config_model.custom_jwt_authorizer = models.CustomJwtAuthorizerForUpdateAgentKitRuntimeInput(
                        allowed_clients=allowed_clients,
                        discovery_url=discovery_url
                    )
            
            # Handle KeyAuth
            if 'KeyAuth' in authorizer_configuration or 'key_auth' in authorizer_configuration:
                key_data = authorizer_configuration.get('KeyAuth') or authorizer_configuration.get('key_auth')
                if key_data:
                    # Extract parameters (support PascalCase and snake_case)
                    api_key = key_data.get('api_key') or key_data.get('ApiKey')
                    api_key_location = key_data.get('api_key_location') or key_data.get('ApiKeyLocation')
                    api_key_name = key_data.get('api_key_name') or key_data.get('ApiKeyName')
                    
                    # Create KeyAuth model (SDK now has native support for api_key_name)
                    auth_config_model.key_auth = models.KeyAuthForUpdateAgentKitRuntimeInput(
                        api_key=api_key,
                        api_key_location=api_key_location,
                        api_key_name=api_key_name
                    )

        # Convert envs to SDK model list
        envs_models = None
        if envs:
            envs_models = [models.EnvForUpdateAgentKitRuntimeInput(**env) for env in envs]

        # Convert tags to SDK model list
        tags_models = None
        if tags:
            tags_models = [models.TagForUpdateAgentKitRuntimeInput(**tag) for tag in tags]

        request = models.UpdateAgentKitRuntimeRequest(
            runtime_id=runtime_id,
            description=description,
            artifact_url=artifact_url,
            role_name=role_name,
            authorizer_configuration=auth_config_model,
            envs=envs_models,
            tags=tags_models,
            release_enable=release_enable,
            client_token=client_token
        )
        response = self.api.update_agent_kit_runtime(request)
        return response.to_dict()

    async def list_runtimes(
        self,
        filters: Optional[List[Dict[str, Any]]] = None,
        create_time_before: Optional[str] = None,
        create_time_after: Optional[str] = None,
        update_time_before: Optional[str] = None,
        update_time_after: Optional[str] = None,
        next_token: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """List AgentKit Runtime list"""

        # Convert filters to SDK model list
        filters_models = None
        if filters:
            filters_models = [models.FilterForListAgentKitRuntimesInput(**f) for f in filters]

        request = models.ListAgentKitRuntimesRequest(
            filters=filters_models,
            create_time_before=create_time_before,
            create_time_after=create_time_after,
            update_time_before=update_time_before,
            update_time_after=update_time_after,
            next_token=next_token,
            max_results=max_results
        )
        response = self.api.list_agent_kit_runtimes(request)
        return response.to_dict()

    async def release_runtime(
        self,
        runtime_id: str,
        version_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Release AgentKit Runtime"""
        request = models.ReleaseAgentKitRuntimeRequest(
            runtime_id=runtime_id,
            version_number=version_number
        )
        response = self.api.release_agent_kit_runtime(request)
        return response.to_dict()

    async def get_runtime_version(
        self,
        runtime_id: str,
        version_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get Runtime version details"""
        request = models.GetAgentKitRuntimeVersionRequest(
            runtime_id=runtime_id,
            version_number=version_number
        )
        response = self.api.get_agent_kit_runtime_version(request)
        return response.to_dict()

    async def list_runtime_versions(
        self,
        runtime_id: str,
        next_token: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """List Runtime version list"""
        request = models.ListAgentKitRuntimeVersionsRequest(
            runtime_id=runtime_id,
            next_token=next_token,
            max_results=max_results
        )
        response = self.api.list_agent_kit_runtime_versions(request)
        return response.to_dict()
