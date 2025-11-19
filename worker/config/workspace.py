"""Workspace configuration models."""

from typing import Literal
from pydantic import BaseModel, Field


class CheckpointStorageConfig(BaseModel):
    """Checkpoint storage configuration."""

    type: Literal["in_memory", "file", "cosmos", "redis"] = "file"
    base_path: str = "state/checkpoints"
    cosmos_connection: str | None = None
    redis_url: str | None = None


class TelemetryConfig(BaseModel):
    """Telemetry configuration."""

    providers: list[Literal["console", "file", "app_insights"]] = ["console", "file"]
    file_path: str = "logs/worker.jsonl"
    level: Literal["debug", "info", "warning", "error"] = "info"
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    app_insights_connection_string: str | None = None


class StorageConfig(BaseModel):
    """Local storage paths configuration."""

    audit_log: str = "logs/audit.jsonl"
    guardrails_cache: str = "guardrails/decisions.json"
    session_store: str = "state/sessions.json"
    memory_store: str = "state/memory"


class RuntimeFlagsConfig(BaseModel):
    """Runtime behavior flags."""

    allow_plan_only: bool = True
    allow_stream: bool = True
    default_language: str = "pt"
    max_retries: int = 3
    timeout_seconds: int | None = None


class WorkspaceConfig(BaseModel):
    """Workspace-level configuration."""

    name: str = Field(..., description="Workspace name")
    description: str = ""
    max_iterations: int = Field(default=12, ge=1)
    session_strategy: Literal["uuid", "timestamp", "custom"] = "uuid"
    checkpoint_storage: CheckpointStorageConfig = Field(default_factory=CheckpointStorageConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    runtime_flags: RuntimeFlagsConfig = Field(default_factory=RuntimeFlagsConfig)
