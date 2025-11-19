"""Configuration models for generic worker.

Pydantic models para validação type-safe de configurações JSON.
Alinhado ao blueprint com correções do validation report.
"""

from .workspace import WorkspaceConfig, CheckpointStorageConfig, TelemetryConfig, StorageConfig
from .resources import ResourcesConfig, MiddlewareConfig, MCPServerConfig, ContextProviderConfig, ToolConfig
from .agents import AgentConfig, MemoryConfig
from .orchestration import (
    OrchestrationConfig,
    SequentialConfig,
    ConcurrentConfig,
    GroupChatConfig,
    HandoffConfig,
    MagenticConfig,
    EdgeConfig,
    RetryPolicyConfig,
    ErrorHandlingConfig,
)
from .observability import ObservabilityConfig, LogConfig, MetricsConfig, TracingConfig

__all__ = [
    # Workspace
    "WorkspaceConfig",
    "CheckpointStorageConfig",
    "TelemetryConfig",
    "StorageConfig",
    # Resources
    "ResourcesConfig",
    "MiddlewareConfig",
    "MCPServerConfig",
    "ContextProviderConfig",
    # Agents
    "AgentConfig",
    "MemoryConfig",
    "ToolConfig",
    # Orchestration
    "OrchestrationConfig",
    "SequentialConfig",
    "ConcurrentConfig",
    "GroupChatConfig",
    "HandoffConfig",
    "MagenticConfig",
    "EdgeConfig",
    "RetryPolicyConfig",
    "ErrorHandlingConfig",
    # Observability
    "ObservabilityConfig",
    "LogConfig",
    "MetricsConfig",
    "TracingConfig",
]
