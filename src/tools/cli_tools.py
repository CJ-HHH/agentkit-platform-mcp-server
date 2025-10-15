"""AgentKit CLI Tools - Direct function calls"""
import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from fastmcp import FastMCP

# Import AgentKit SDK components
from agentkit.toolkit.config import get_config
from agentkit.toolkit.workflows import WORKFLOW_REGISTRY

# Import shared utilities
from src.utils.tool_helpers import (
    get_workflow_instance,
    create_success_response,
    create_error_response,
    parse_env_vars,
    update_common_config,
    update_local_workflow_config,
    update_cloud_workflow_config
)


def register_cli_tools(mcp: FastMCP):
    """Register all CLI-related MCP tools"""

    @mcp.tool()
    async def toolkit_init_project(
        project_name: Optional[str] = None,
        template: str = "basic",
        directory: Optional[str] = None
    ) -> str:
        """
        Initialize a new AgentKit project.

        Creates a new agent project file from template.

        Args:
            project_name: Project name (default: my_agent)
                ⚠️ NAMING RULES: Use only lowercase letters, numbers, and underscores.
                Must start with a letter. This will be used as the Python module name.
                Good: "my_agent", "agent123"  Bad: "my-agent", "123agent"
            template: Project template to use (default: basic)
            directory: Target directory for the project (default: current directory)
                ⚠️ RECOMMENDATION: Always use absolute path (e.g., /tmp/myproject)
                to avoid confusion about file location.

        Returns:
            JSON string with execution result including file path

        Example:
            toolkit_init_project(
                project_name="my_agent",
                template="basic",
                directory="/tmp/myproject"
            )
        """
        try:
            target_dir = Path(directory) if directory else Path.cwd()
            project_name = project_name or "my_agent"

            file_name = f"{project_name}.py"
            agent_file_path = target_dir / file_name

            if agent_file_path.exists():
                return json.dumps({
                    "success": False,
                    "error": f"File {file_name} already exists"
                }, ensure_ascii=False)

            # Get template source path
            from agentkit.toolkit.cli import cli
            source_path = Path(cli.__file__).parent.parent / "resources" / "samples" / "simple_app_veadk.py"

            if not source_path.exists():
                return json.dumps({
                    "success": False,
                    "error": f"Template not found at {source_path}"
                }, ensure_ascii=False)

            with open(source_path, 'r', encoding='utf-8') as source_file:
                content = source_file.read()

            with open(agent_file_path, 'w', encoding='utf-8') as agent_file:
                agent_file.write(content)

            return json.dumps({
                "success": True,
                "message": f"Successfully created {file_name}",
                "file_path": str(agent_file_path)
            }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False)

    @mcp.tool()
    async def toolkit_build_image(
        config_file: str = "agentkit.yaml",
        platform: str = "auto",
        push: bool = True
    ) -> str:
        """
        Build Docker image for the Agent.
        
        ⚠️ IMPORTANT: This tool automatically switches to the config file's directory
        during execution to ensure correct file paths and configuration updates.

        Args:
            config_file: Configuration file path (default: agentkit.yaml)
                ⚠️ RECOMMENDATION: Always use absolute path (e.g., /tmp/myproject/agentkit.yaml)
                This ensures the build happens in the correct directory.
            platform: Build platform (default: auto)
            push: Whether to push image to registry (default: True)
                - For local workflow: pushes to local Docker daemon
                - For cloud workflow: pushes to container registry (CR)

        Workflow-Specific Behavior:
            - Local: Builds Docker image locally, updates config with image_id
            - Cloud: Uploads to TOS, triggers CR build pipeline, updates config with image URL
            
        Configuration Updates:
            After successful build, the config file will be updated with:
            - ve_cr_image_full_url (cloud): Full CR image URL
            - build_timestamp: Build completion time
            - tos_object_key, tos_object_url: TOS upload info (cloud only)

        Returns:
            JSON string with execution result

        Example:
            toolkit_build_image(
                config_file="/tmp/myproject/agentkit.yaml",
                push=True
            )
        """
        try:
            # Change to config file directory to ensure SDK updates the correct file
            config_path = Path(config_file).resolve()
            original_cwd = os.getcwd()
            if config_path.parent.exists():
                os.chdir(config_path.parent)
            
            try:
                config = get_config(config_path=config_path.name)
                common_config = config.get_common_config()

                if not common_config.entry_point:
                    return json.dumps({
                        "success": False,
                        "error": "Entry point not configured, cannot build image"
                    }, ensure_ascii=False)

                workflow_name = common_config.current_workflow
                
                if workflow_name not in WORKFLOW_REGISTRY:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown workflow type '{workflow_name}'"
                    }, ensure_ascii=False)

                workflow_config = config.get_workflow_config(workflow_name)
                workflow = WORKFLOW_REGISTRY[workflow_name]()
                
                # Call build and capture result
                success = workflow.build(workflow_config)
                
                if success:
                    return json.dumps({
                        "success": True,
                        "message": "Build completed successfully"
                    }, ensure_ascii=False)
                else:
                    return json.dumps({
                        "success": False,
                        "error": "Build failed. Check if Dockerfile exists and Docker is running.",
                        "workflow": workflow_name,
                        "config": workflow_config
                    }, ensure_ascii=False)
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Configuration error: {str(e)}"
            }, ensure_ascii=False)

    @mcp.tool()
    async def toolkit_deploy_agent(
        config_file: str = "agentkit.yaml"
    ) -> str:
        """
        Deploy the Agent to target environment.
        
        ⚠️ PREREQUISITE: You must run toolkit_build_image first!
        This tool reads the built image information from the config file.
        
        ⚠️ IMPORTANT: This tool automatically switches to the config file's directory
        during execution to ensure correct file paths.

        Args:
            config_file: Configuration file path (default: agentkit.yaml)
                ⚠️ RECOMMENDATION: Always use absolute path (e.g., /tmp/myproject/agentkit.yaml)

        Workflow-Specific Behavior:
            - Local: Starts Docker container from built image
            - Cloud: Creates/updates AgentKit Runtime with the CR image URL
            
        Configuration Requirements:
            - Cloud: Requires ve_cr_image_full_url (set by toolkit_build_image)
            - Local: Requires image_id or full_image_name

        Returns:
            JSON string with execution result

        Example:
            # Step 1: Build first
            toolkit_build_image(config_file="/tmp/myproject/agentkit.yaml")
            
            # Step 2: Then deploy
            toolkit_deploy_agent(config_file="/tmp/myproject/agentkit.yaml")
        """
        try:
            # Change to config file directory to ensure SDK updates the correct file
            config_path = Path(config_file).resolve()
            original_cwd = os.getcwd()
            if config_path.parent.exists():
                os.chdir(config_path.parent)
            
            try:
                # Use unified helper to get workflow instance
                workflow, workflow_name, error = get_workflow_instance(config_path.name)
                if error:
                    return json.dumps(error, ensure_ascii=False)
                
                # Validate entry point configuration
                config = get_config(config_path=config_path.name)
                common_config = config.get_common_config()
                if not common_config.entry_point:
                    return create_error_response(
                        error="Entry point not configured, cannot deploy",
                        hint="Use toolkit_edit_config to set entry_point"
                    )
                
                # Get workflow config and deploy
                workflow_config = config.get_workflow_config(workflow_name)
                success = workflow.deploy(workflow_config)
                
                if success:
                    return json.dumps({
                        "success": True,
                        "message": "Deploy completed successfully",
                        "workflow": workflow_name
                    }, ensure_ascii=False)
                else:
                    # Deploy failed, provide detailed troubleshooting info
                    error_hints = []
                    if workflow_name == "local":
                        error_hints.append("Check if image exists")
                        error_hints.append("Check if port is already in use")
                        error_hints.append("Check Docker daemon logs for details")
                    elif workflow_name == "cloud":
                        error_hints.append("Check if runtime configuration is correct")
                        error_hints.append("Check if IAM role has proper permissions")
                    
                    return json.dumps({
                        "success": False,
                        "error": "Deploy failed. See hints for troubleshooting.",
                        "hints": error_hints,
                        "workflow": workflow_name,
                        "config": workflow_config
                    }, ensure_ascii=False)
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

        except Exception as e:
            import traceback
            error_detail = str(e)
            
            # Extract useful info from error message
            if "address already in use" in error_detail:
                error_detail = f"Port conflict detected: {error_detail}"
            elif "permission denied" in error_detail.lower():
                error_detail = f"Permission error: {error_detail}"
                
            return json.dumps({
                "success": False,
                "error": f"Configuration error: {error_detail}",
                "traceback": traceback.format_exc() if len(traceback.format_exc()) < 500 else "See logs for full traceback"
            }, ensure_ascii=False)

    @mcp.tool()
    async def toolkit_launch_agent(
        config_file: str = "agentkit.yaml"
    ) -> str:
        """
        Build and deploy Agent in one command.

        This is a convenience command that runs toolkit_build_image followed by toolkit_deploy_agent.
        ⚠️ IMPORTANT: This tool automatically switches to the config file's directory.

        Args:
            config_file: Configuration file path (default: agentkit.yaml)
                ⚠️ RECOMMENDATION: Always use absolute path (e.g., /tmp/myproject/agentkit.yaml)

        Execution Flow:
            1. Step 1: Build - Creates Docker image (local) or triggers CR build (cloud)
            2. Step 2: Deploy - Starts container (local) or creates Runtime (cloud)
            
        If build fails, deploy will be skipped and error returned immediately.

        Returns:
            JSON string with execution result including which stage succeeded/failed

        Example:
            toolkit_launch_agent(config_file="/tmp/myproject/agentkit.yaml")
        """
        try:
            # Change to config file directory to ensure SDK updates the correct file
            config_path = Path(config_file).resolve()
            original_cwd = os.getcwd()
            if config_path.parent.exists():
                os.chdir(config_path.parent)
            
            try:
                config = get_config(config_path=config_path.name)
                common_config = config.get_common_config()

                if not common_config.entry_point:
                    return json.dumps({
                        "success": False,
                        "error": "Entry point not configured, cannot launch"
                    }, ensure_ascii=False)

                workflow_name = common_config.current_workflow
                
                if workflow_name not in WORKFLOW_REGISTRY:
                    return json.dumps({
                        "success": False,
                        "error": f"Unknown workflow type '{workflow_name}'"
                    }, ensure_ascii=False)

                workflow_config = config.get_workflow_config(workflow_name)
                workflow = WORKFLOW_REGISTRY[workflow_name]()
                
                # Step 1: Build
                build_success = workflow.build(workflow_config)
                if not build_success:
                    return json.dumps({
                        "success": False,
                        "error": "Build failed. Launch aborted.",
                        "stage": "build",
                        "workflow": workflow_name
                    }, ensure_ascii=False)
                
                # ✅ Reload config after build to get updated fields (e.g., ve_cr_image_full_url)
                config = get_config(config_path=config_path.name)
                workflow_config = config.get_workflow_config(workflow_name)
                
                # Step 2: Deploy
                deploy_success = workflow.deploy(workflow_config)
                
                if deploy_success:
                    return json.dumps({
                        "success": True,
                        "message": "Launch completed successfully (build + deploy)",
                        "workflow": workflow_name
                    }, ensure_ascii=False)
                else:
                    return json.dumps({
                        "success": False,
                        "error": "Deploy failed. Build succeeded but deploy failed.",
                        "stage": "deploy",
                        "workflow": workflow_name
                    }, ensure_ascii=False)
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

        except Exception as e:
            import traceback
            return json.dumps({
                "success": False,
                "error": f"Configuration error: {str(e)}",
                "traceback": traceback.format_exc() if len(traceback.format_exc()) < 500 else "See logs for full traceback"
            }, ensure_ascii=False)

    @mcp.tool()
    async def toolkit_invoke_agent(
        payload: str,
        config_file: str = "agentkit.yaml",
        apikey: Optional[str] = None
    ) -> str:
        """
        Send a test request to deployed Agent.

        Args:
            payload: JSON payload to send to the agent
            config_file: Configuration file path (default: agentkit.yaml)
            apikey: API key for authentication (optional)

        Returns:
            JSON string with execution result

        Example:
            toolkit_invoke_agent(
                payload='{"message": "Hello, agent!"}',
                apikey="your_api_key"
            )
        """
        try:
            config = get_config(config_path=config_file)
            common_config = config.get_common_config()

            workflow_name = common_config.current_workflow
            if workflow_name not in WORKFLOW_REGISTRY:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown workflow type '{workflow_name}'"
                }, ensure_ascii=False)

            workflow_config = config.get_workflow_config(workflow_name)
            workflow = WORKFLOW_REGISTRY[workflow_name]()
            
            try:
                # Parse payload JSON string to dict
                try:
                    payload_dict = json.loads(payload)
                except json.JSONDecodeError as e:
                    return json.dumps({
                        "success": False,
                        "error": f"Invalid payload JSON: {str(e)}"
                    }, ensure_ascii=False)
                
                # Different workflows have different invoke() signatures
                if workflow_name == "cloud":
                    # Cloud: invoke(config: VeAgentkitConfig, payload: Dict, headers: Dict) -> Tuple[bool, Any]
                    from agentkit.toolkit.workflows.ve_agentkit_workflow import VeAgentkitConfig
                    config_obj = VeAgentkitConfig.from_dict(workflow_config)
                    
                    # ⚠️ SDK bug workaround: Add simplified property names
                    # SDK's invoke() uses config.runtime_id, config.endpoint, config.api_key
                    # but VeAgentkitConfig only has ve_runtime_id, ve_runtime_endpoint, ve_runtime_apikey
                    config_obj.runtime_id = config_obj.ve_runtime_id
                    config_obj.endpoint = config_obj.ve_runtime_endpoint
                    config_obj.api_key = config_obj.ve_runtime_apikey
                    
                    # Build headers with API key
                    headers = {}
                    if apikey:
                        apikey_name = workflow_config.get("ve_runtime_apikey_name", "X-API-Key")
                        headers[apikey_name] = apikey
                    
                    success, result = workflow.invoke(config_obj, payload_dict, headers)
                    
                elif workflow_name == "hybrid":
                    # Hybrid: invoke(config: Dict, args: Dict) -> bool
                    # args contains payload and apikey
                    args = {"payload": payload_dict}
                    if apikey:
                        args["apikey"] = apikey
                    
                    success = workflow.invoke(workflow_config, args)
                    result = None  # Hybrid doesn't return result
                    
                else:
                    # Local workflow - check signature
                    return json.dumps({
                        "success": False,
                        "error": f"Invoke not supported for {workflow_name} workflow"
                    }, ensure_ascii=False)
                
                if success:
                    return json.dumps({
                        "success": True,
                        "message": "Invoke completed successfully",
                        "result": result
                    }, ensure_ascii=False)
                else:
                    return json.dumps({
                        "success": False,
                        "error": "Invoke failed. Check if agent is deployed and running.",
                        "workflow": workflow_name,
                        "details": result
                    }, ensure_ascii=False)
            except Exception as invoke_error:
                return json.dumps({
                    "success": False,
                    "error": f"Invoke error: {str(invoke_error)}",
                    "workflow": workflow_name
                }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Configuration error: {str(e)}"
            }, ensure_ascii=False)

    @mcp.tool()
    async def toolkit_get_status(
        config_file: str = "agentkit.yaml"
    ) -> str:
        """
        Check current status of the agent runtime.
        
        ⚠️ IMPORTANT: Always use absolute path for config_file to ensure correct configuration loading.

        Args:
            config_file: Configuration file path (MUST be absolute path, e.g., /tmp/myproject/agentkit.yaml)

        Returns:
            JSON string with agent status information

        Example:
            toolkit_get_status(config_file="/tmp/myproject/agentkit.yaml")
        """
        # Use unified helper to get workflow instance
        workflow, workflow_type, error = get_workflow_instance(config_file)
        if error:
            return json.dumps(error, ensure_ascii=False)
        
        try:
            # Get workflow config for status()
            config = get_config(config_path=config_file)
            workflow_config = config.get_workflow_config(workflow_type)
            
            # Call workflow.status()
            status_result = workflow.status(workflow_config)

            # Check if status returned an error
            if isinstance(status_result, dict) and status_result.get('error'):
                return create_error_response(
                    error=status_result['error'],
                    workflow=workflow_type
                )

            # Return success response
            return json.dumps({
                "success": True,
                "workflow": workflow_type,
                "status": status_result
            }, ensure_ascii=False)
            
        except Exception as status_error:
            return create_error_response(
                error=f"Status check error: {str(status_error)}",
                workflow=workflow_type
            )

    @mcp.tool()
    async def toolkit_destroy_runtime(
        config_file: str = "agentkit.yaml",
        force: bool = False
    ) -> str:
        """
        Destroy running Agent runtime.

        ⚠️ WARNING: This will terminate your running agent!
        
        ⚠️ IMPORTANT: Always use absolute path for config_file to ensure correct configuration loading.
        
        ⚠️ KNOWN ISSUES:
        - Hybrid workflow: May show "Runtime ID not configured" even when Runtime exists (SDK bug)
        - Local workflow: May return success but container still running (SDK bug)
        - Workaround: Manually verify with `docker ps` or Runtime API after destroy

        Args:
            config_file: Configuration file path (MUST be absolute path, e.g., /tmp/myproject/agentkit.yaml)
            force: Force destroy without confirmation (default: False)

        Returns:
            JSON string with execution result

        Example:
            toolkit_destroy_runtime(config_file="/tmp/myproject/agentkit.yaml", force=True)
        """
        if not force:
            return json.dumps({
                "success": False,
                "error": "Confirmation required. Set force=True to proceed.",
                "warning": "This will terminate your running agent!"
            }, ensure_ascii=False)

        # Use unified helper to get workflow instance
        workflow, workflow_name, error = get_workflow_instance(config_file)
        if error:
            return json.dumps(error, ensure_ascii=False)
        
        try:
            # Call workflow.destroy()
            # Note: Different workflows have inconsistent destroy() signatures (SDK design issue)
            workflow.destroy()
            
            return create_success_response(
                message=f"{workflow_name} runtime destroyed successfully",
                workflow=workflow_name
            )
            
        except Exception as destroy_error:
            return create_error_response(
                error=f"Destroy error: {str(destroy_error)}",
                workflow=workflow_name
            )

    # ========== Configuration Management Tools ==========

    @mcp.tool()
    async def toolkit_edit_config(
        config_file: str = "agentkit.yaml",
        entry_point: Optional[str] = None,
        workflow_type: Optional[str] = None,
        project_name: Optional[str] = None,
        image_name: Optional[str] = None,
        runtime_name: Optional[str] = None,
        role_name: Optional[str] = None,
        entry_port: Optional[int] = None,
        envs: Optional[str] = None,
        ve_cr_instance_name: Optional[str] = None,
        ve_cr_namespace_name: Optional[str] = None,
        ve_cr_repo_name: Optional[str] = None
    ) -> str:
        """
        Edit AgentKit configuration file (create if not exists).

        This tool allows AI to modify the agent's configuration. If the config file
        doesn't exist, SDK will auto-create it with defaults on first use (build/deploy).
        
        Only provided parameters will be updated; others remain unchanged.

        Args:
            config_file: Configuration file path (default: agentkit.yaml)
                ⚠️ IMPORTANT: Use absolute path (e.g., /tmp/myproject/agentkit.yaml)
                or ensure current working directory is correct.
            entry_point: Python entry point file (optional)
            workflow_type: Workflow type - 'local', 'cloud', or 'hybrid' (optional)
            project_name: Project name (optional)
                ⚠️ NAMING RULES: Use only lowercase letters and numbers, no hyphens/underscores at start.
                Good: "myagent", "agent123"  Bad: "my-agent", "_agent", "123agent"
            image_name: (Deprecated - not used by SDK) Use project_name instead.
                SDK uses common.agent_name (set via project_name) for image naming.
            runtime_name: Runtime name for cloud workflow (optional)
            role_name: IAM role name for cloud workflow (optional, e.g., "TestRoleForAgentKit")
            entry_port: Agent service port (optional, default: 8000)
                ⚠️ **LOCAL WORKFLOW PORT CONFIGURATION - CRITICAL**:
                - For Local workflow, this configures host-to-container port mapping
                - Format: entry_port:8000 (e.g., 8100:8000 means host 8100 → container 8000)
                - **CRITICAL ISSUE**: Port 8000 is typically occupied by the MCP server itself!
                - **DO NOT use port 8000** - it will conflict with the running MCP server
                - **ALWAYS use a different port** (e.g., 8100, 8200, 9000, 9100)
                - The MCP server usually runs on port 8000, so your agent must use another port
                - Check if port is in use: `docker ps --filter "publish=PORT"` or `lsof -i :PORT`
                
                📋 **Port Selection Guide**:
                - Development: 8100-8199 (less likely to conflict)
                - Testing: 8200-8299
                - Local services: 9000-9199
                - **Avoid**: 8000 (commonly used), 8080 (proxy), 3000 (Node.js)
                
                💡 **Best Practice**:
                1. Check available ports first
                2. Use uncommon port numbers (e.g., 8100, 8200, 9100)
                3. Document your port usage in project README
                4. For multiple local deployments, use different ports for each
            envs: Environment variables JSON string (optional).
                Input formats (both supported):
                - Format 1 (array): '[{"key":"KEY1","value":"val1"},{"key":"KEY2","value":"val2"}]'
                - Format 2 (dict, recommended): '{"KEY1":"val1","KEY2":"val2"}'
                
                📋 RECOMMENDED ENVIRONMENT VARIABLES FOR AGENTKIT APPLICATIONS:
                
                1. **Logging & Debugging** (Optional):
                   - LOG_LEVEL: "INFO" | "DEBUG" | "WARNING" | "ERROR"
                   - DEBUG: "true" | "false"
                   - PYTHONUNBUFFERED: "1" (for real-time logs)
                
                2. **Observability & Tracing** (Optional, auto-configured by Runtime):
                   - ENABLE_APMPLUS: "true" | "false" (auto-set when apmplus_enable=true)
                   - ENABLE_COZELOOP: "true" | "false"
                   - ENABLE_TLS: "true" | "false"
                   - OTEL_SERVICE_NAME: Auto-set by Runtime
                   - OTEL_RESOURCE_ATTRIBUTES: Auto-set by Runtime
                
                3. **Application-Specific** (Required by your app logic):
                   - API keys, credentials, endpoints, etc.
                   - Example: API_KEY, DB_URL, SERVICE_ENDPOINT
                
                4. **Service Configuration** (Optional):
                   - REGION: "cn-beijing" | "cn-shanghai" | etc.
                   - ENVIRONMENT: "production" | "staging" | "development"
                   - SERVICE_NAME: Your service name
                
                ⚠️ IMPORTANT NOTES:
                - Most observability vars are auto-configured by Runtime platform
                - Only set application-specific variables your code actually needs
                - Use descriptive names and document them in your code
                - Avoid hardcoding sensitive data (use IAM roles when possible)
                
                ⚠️ CRITICAL - Output format differs by workflow type (verified from CLI SDK source):
                - Cloud/Hybrid: Saved as `ve_runtime_envs` (dict) → Runtime API format
                  ```yaml
                  launch_types:
                    hybrid:
                      ve_runtime_envs:
                        KEY1: val1
                        KEY2: val2
                  ```
                - Local: Saved as `environment` (dict) → Docker environment format
                  ```yaml
                  launch_types:
                    local:
                      environment:
                        KEY1: val1
                        KEY2: val2
                  ```
                This tool automatically converts to the correct format based on workflow_type.
                The SDK's update_workflow_config() will OVERWRITE the entire workflow config,
                so we must match the exact field names expected by LocalDockerRunnerConfig/CloudRunnerConfig.
            ve_cr_instance_name: Container Registry instance name (optional, for cloud/hybrid workflows)
                - Pre-configuration for SDK Build stage
                - If not provided, SDK attempts "Auto" creation (may fail)
                - Provide existing instance name to skip creation
            ve_cr_namespace_name: CR namespace name (optional, for cloud/hybrid workflows)
                - Pre-configuration for SDK Build stage
                - If not provided, SDK attempts "Auto" creation (may fail)
                - Provide existing namespace name to skip creation
            ve_cr_repo_name: CR repository name (optional, for cloud/hybrid workflows)
                - ⚠️ STRONGLY RECOMMENDED: Pre-configure to avoid SDK auto-generation issues
                - SDK may auto-generate invalid names (e.g., starting with hyphen)
                - Must be valid DNS name (lowercase letters, numbers, hyphens, no leading hyphen)

        Returns:
            JSON string with update result and current configuration

        Example:
            # Cloud workflow with comprehensive environment variables
            toolkit_edit_config(
                config_file="/tmp/myproject/agentkit.yaml",
                entry_point="agent.py",
                workflow_type="cloud",
                project_name="myagent",
                runtime_name="myagent-runtime",
                role_name="TestRoleForAgentKit",
                ve_cr_instance_name="existing-cr-instance",  # Or skip for Auto
                ve_cr_namespace_name="existing-namespace",   # Or skip for Auto
                ve_cr_repo_name="myagent",  # Recommended to avoid invalid auto-generated names
                envs='''{
                    "LOG_LEVEL": "INFO",
                    "DEBUG": "false",
                    "REGION": "cn-beijing",
                    "ENVIRONMENT": "production",
                    "API_KEY": "your-api-key",
                    "SERVICE_ENDPOINT": "https://api.example.com"
                }'''
            )
            
            # Minimal configuration (most vars are auto-configured)
            toolkit_edit_config(
                config_file="/tmp/myproject/agentkit.yaml",
                workflow_type="cloud",
                project_name="myagent",
                runtime_name="myagent-runtime",
                role_name="TestRoleForAgentKit",
                envs='{"ENVIRONMENT":"production"}'  # Only set what you need
            )
        """
        try:
            config_path = Path(config_file)
            updates = []

            # Load or create configuration
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {
                    "common": {
                        "agent_name": project_name or Path.cwd().name,
                        "entry_point": entry_point or "",
                        "current_workflow": workflow_type or "local"
                    },
                    "launch_types": {}
                }

            # Ensure required sections exist
            config.setdefault("common", {})
            config.setdefault("launch_types", {})

            # Parse environment variables if provided
            env_dict = None
            if envs:
                try:
                    env_dict = parse_env_vars(envs)
                except ValueError as e:
                    return create_error_response(error=str(e))

            # Update common configuration
            try:
                update_common_config(
                    config, updates,
                    entry_point=entry_point,
                    workflow_type=workflow_type,
                    project_name=project_name,
                    entry_port=entry_port
                )
            except ValueError as e:
                return create_error_response(error=str(e))

            # Determine current workflow for conditional updates
            current_workflow = workflow_type or config.get("common", {}).get("current_workflow", "local")

            # Update workflow-specific configuration
            if current_workflow == "local":
                update_local_workflow_config(
                    config, updates,
                    entry_port=entry_port,
                    envs=env_dict
                )
            elif current_workflow in ["cloud", "hybrid"]:
                update_cloud_workflow_config(
                    config, updates,
                    workflow_type=current_workflow,
                    runtime_name=runtime_name,
                    role_name=role_name,
                    ve_cr_instance_name=ve_cr_instance_name,
                    ve_cr_namespace_name=ve_cr_namespace_name,
                    ve_cr_repo_name=ve_cr_repo_name,
                    envs=env_dict
                )

            # Validate that at least one update was made
            if not updates:
                return create_error_response(error="No updates provided")

            # Write updated configuration to file
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            return json.dumps({
                "success": True,
                "message": f"Configuration updated: {', '.join(updates)}",
                "file_path": str(config_path.absolute()),
                "config": config
            }, ensure_ascii=False)

        except Exception as e:
            return create_error_response(error=f"Configuration error: {str(e)}")
