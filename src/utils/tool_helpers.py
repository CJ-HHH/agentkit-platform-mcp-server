"""
MCP Tools 辅助函数

提供 MCP tools 的通用功能封装，减少重复代码。
"""

import os
import json
from typing import Dict, Any, Tuple, Optional

from agentkit.toolkit.config import get_config
from agentkit.toolkit.workflows import WORKFLOW_REGISTRY


def get_workflow_instance(config_file: str) -> Tuple[Optional[Any], Optional[str], Optional[Dict]]:
    """
    Unified wrapper for getting workflow instance.
    
    This function encapsulates the repeated logic in all MCP tools:
    1. Load configuration file
    2. Get workflow type
    3. Validate workflow exists
    4. Create workflow instance
    
    Args:
        config_file: Configuration file path (absolute path recommended)
    
    Returns:
        Tuple of (workflow_instance, workflow_name, error_dict)
        - On success: (workflow instance, workflow name, None)
        - On failure: (None, None, error dict)
    
    Example:
        workflow, workflow_name, error = get_workflow_instance(config_file)
        if error:
            return json.dumps(error, ensure_ascii=False)
        
        # Use workflow instance
        # At this point, workflow and workflow_name are guaranteed non-None
        workflow.deploy(...)
    
    Note:
        When error is None, both workflow and workflow_name are guaranteed to be non-None.
        This allows type checkers to understand the control flow correctly.
    """
    try:
        # Load configuration file
        config = get_config(config_path=config_file)
        common_config = config.get_common_config()
        
        # Get workflow type from configuration
        workflow_name = common_config.current_workflow
        
        # Validate workflow type exists in registry
        if workflow_name not in WORKFLOW_REGISTRY:
            return None, None, {
                "success": False,
                "error": f"Unknown workflow type '{workflow_name}'",
                "available_workflows": list(WORKFLOW_REGISTRY.keys())
            }
        
        # Create workflow instance from registry
        workflow = WORKFLOW_REGISTRY[workflow_name]()
        
        return workflow, workflow_name, None
        
    except FileNotFoundError:
        return None, None, {
            "success": False,
            "error": f"Configuration file not found: {config_file}",
            "hint": "Please check if the config_file path is correct."
        }
    except Exception as e:
        return None, None, {
            "success": False,
            "error": f"Failed to load configuration: {str(e)}"
        }


def init_cloud_credentials():
    """
    Initialize cloud service credentials with unified mapping.
    
    Maps legacy AGENTKIT_* environment variables to the unified VOLC_* naming convention
    for backward compatibility. The CLI SDK natively supports VOLC_* variables.
    
    This function is called once at server startup (similar to the get_api_client
    singleton pattern in runtime_tools.py), ensuring credentials are set up before
    any tool execution.
    
    Note: Unlike the previous ensure_cloud_credentials() which was called on each
    tool invocation, this initialization occurs only once at server startup for
    better performance.
    
    Supported environment variables:
    - VOLC_ACCESSKEY (or AGENTKIT_ACCESS_KEY, VOLCENGINE_ACCESS_KEY)
    - VOLC_SECRETKEY (or AGENTKIT_SECRET_KEY, VOLCENGINE_SECRET_KEY)
    - VOLC_REGION (or AGENTKIT_REGION)
    - VOLC_AGENTKIT_SERVICE (or AGENTKIT_SERVICE)
    - VOLC_AGENTKIT_HOST (or AGENTKIT_BASE_URL)
    """
    # Map legacy naming to unified VOLC_* naming for backward compatibility
    credential_mapping = [
        # (Unified VOLC_* naming, Legacy variants for backward compatibility)
        ("VOLC_ACCESSKEY", ["AGENTKIT_ACCESS_KEY", "VOLCENGINE_ACCESS_KEY"]),
        ("VOLC_SECRETKEY", ["AGENTKIT_SECRET_KEY", "VOLCENGINE_SECRET_KEY"]),
        ("VOLC_REGION", ["AGENTKIT_REGION"]),
        ("VOLC_AGENTKIT_SERVICE", ["AGENTKIT_SERVICE"]),
        ("VOLC_AGENTKIT_HOST", ["AGENTKIT_BASE_URL"]),
    ]
    
    for sdk_key, legacy_keys in credential_mapping:
        if not os.getenv(sdk_key):  # SDK key not set
            # Try to find value from legacy keys
            for legacy_key in legacy_keys:
                value = os.getenv(legacy_key)
                if value:
                    os.environ[sdk_key] = value
                    break


def create_success_response(message: str, workflow: str, **extra_data) -> str:
    """
    Create a standardized success response format.
    
    Args:
        message: Success message
        workflow: Workflow type
        **extra_data: Additional response data
    
    Returns:
        JSON string
    """
    response = {
        "success": True,
        "message": message,
        "workflow": workflow,
        **extra_data
    }
    return json.dumps(response, ensure_ascii=False)


def create_error_response(error: str, stage: Optional[str] = None, **extra_data) -> str:
    """
    Create a standardized error response format.
    
    Args:
        error: Error message
        stage: Failed stage (optional)
        **extra_data: Additional response data
    
    Returns:
        JSON string
    """
    response = {
        "success": False,
        "error": error,
        **extra_data
    }
    if stage:
        response["stage"] = stage
    return json.dumps(response, ensure_ascii=False)


# ========== Configuration Management Helpers ==========

def parse_env_vars(envs_json: str) -> Dict[str, str]:
    """
    Parse environment variables from JSON string to dict.
    
    Supports two input formats:
    1. Array format: [{"key":"KEY1","value":"val1"}]
    2. Dict format: {"KEY1":"val1"} (recommended)
    
    Args:
        envs_json: JSON string containing environment variables
    
    Returns:
        Dict of environment variables
    
    Raises:
        ValueError: If JSON is invalid or format is unsupported
    
    Example:
        >>> parse_env_vars('{"API_KEY":"secret","ENV":"prod"}')
        {"API_KEY": "secret", "ENV": "prod"}
    """
    try:
        parsed = json.loads(envs_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    
    # Already a dict - return as is
    if isinstance(parsed, dict):
        return parsed
    
    # Array format - convert to dict
    if isinstance(parsed, list):
        env_dict = {}
        for item in parsed:
            if not isinstance(item, dict):
                raise ValueError("Array items must be objects with 'key' and 'value' fields")
            if "key" not in item or "value" not in item:
                raise ValueError("Each env item must have 'key' and 'value' fields")
            env_dict[item["key"]] = item["value"]
        return env_dict
    
    raise ValueError("envs must be either a dict or array of {key, value} objects")


def update_common_config(config: Dict, updates: list, **kwargs) -> None:
    """
    Update common configuration fields.
    
    Args:
        config: Configuration dict to update
        updates: List to append update messages
        **kwargs: Configuration fields to update (entry_point, workflow_type, etc.)
    """
    if "common" not in config:
        config["common"] = {}
    
    # Map of parameter names to config keys
    field_mapping = {
        "entry_point": "entry_point",
        "workflow_type": "current_workflow",
        "project_name": "agent_name",
        "entry_port": "entry_port"
    }
    
    for param_name, config_key in field_mapping.items():
        value = kwargs.get(param_name)
        if value is not None:
            # Validate workflow_type
            if param_name == "workflow_type" and value not in ["local", "cloud", "hybrid"]:
                raise ValueError(f"Invalid workflow_type: {value}. Must be 'local', 'cloud', or 'hybrid'")
            
            config["common"][config_key] = value
            updates.append(f"common.{config_key} -> {value}")


def update_local_workflow_config(config: Dict, updates: list, **kwargs) -> None:
    """
    Update local workflow specific configuration.
    
    Args:
        config: Configuration dict to update
        updates: List to append update messages
        **kwargs: Local workflow fields (entry_port, envs)
    """
    if "local" not in config["launch_types"]:
        config["launch_types"]["local"] = {}
    
    local_config = config["launch_types"]["local"]
    
    # Update port mapping
    entry_port = kwargs.get("entry_port")
    if entry_port:
        port_mapping = f"{entry_port}:8000"
        local_config["ports"] = [port_mapping]
        updates.append(f"launch_types.local.ports -> [{port_mapping}]")
    
    # Update environment variables (dict format for local)
    envs = kwargs.get("envs")
    if envs:
        local_config["environment"] = envs
        updates.append(f"launch_types.local.environment -> {len(envs)} variables")


def update_cloud_workflow_config(config: Dict, updates: list, **kwargs) -> None:
    """
    Update cloud/hybrid workflow specific configuration.
    
    Args:
        config: Configuration dict to update
        updates: List to append update messages
        **kwargs: Cloud workflow fields (runtime_name, role_name, envs, CR fields)
    """
    workflow = kwargs.get("workflow_type", "cloud")
    if workflow not in config["launch_types"]:
        config["launch_types"][workflow] = {}
    
    cloud_config = config["launch_types"][workflow]
    
    # Map of parameter names to config keys
    field_mapping = {
        "runtime_name": "ve_runtime_name",
        "role_name": "ve_runtime_role_name",
        "ve_cr_instance_name": "ve_cr_instance_name",
        "ve_cr_namespace_name": "ve_cr_namespace_name",
        "ve_cr_repo_name": "ve_cr_repo_name"
    }
    
    for param_name, config_key in field_mapping.items():
        value = kwargs.get(param_name)
        if value is not None:
            cloud_config[config_key] = value
            updates.append(f"launch_types.{workflow}.{config_key} -> {value}")
    
    # Update environment variables (dict format for cloud/hybrid)
    envs = kwargs.get("envs")
    if envs:
        cloud_config["ve_runtime_envs"] = envs
        updates.append(f"launch_types.{workflow}.ve_runtime_envs -> {len(envs)} variables")
