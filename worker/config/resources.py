"""Resources configuration models."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class MiddlewareConfig(BaseModel):
    """Middleware configuration.
    
    Middleware é aplicado no nível do agente individual, não no workflow.
    """

    id: str = Field(..., description="Unique middleware identifier")
    type: Literal["function", "agent", "chat"] = Field(..., description="Middleware type")
    class_path: str = Field(..., description="Python import path (e.g., 'worker.middleware.RetryMiddleware')")
    params: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class MCPServerConfig(BaseModel):
    """MCP server connection configuration."""

    id: str = Field(..., description="Server identifier")
    command: str = Field(..., description="Server command")
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True


class ContextProviderConfig(BaseModel):
    """Context provider configuration (e.g., custom ChatMessageStore)."""

    type: Literal["default", "redis", "cosmos", "custom"] = "default"
    class_path: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    """Tool/function configuration."""

    id: str = Field(..., description="Tool identifier")
    function_path: str = Field(..., description="Python import path (e.g., 'mytools.get_weather')")
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ResourcesConfig(BaseModel):
    """Shared resources configuration."""

    global_middleware: list[MiddlewareConfig] = Field(
        default_factory=list,
        description="Middleware aplicado a TODOS os agentes (agent-level)",
    )
    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    context_providers: dict[str, ContextProviderConfig] = Field(default_factory=dict)
