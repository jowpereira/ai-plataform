"""Observability configuration models."""

from typing import Literal
from pydantic import BaseModel, Field


class LogConfig(BaseModel):
    """Logging configuration."""

    enabled: bool = True
    level: Literal["debug", "info", "warning", "error"] = "info"
    format: Literal["json", "text"] = "json"
    output_path: str = "logs/worker.jsonl"


class MetricsConfig(BaseModel):
    """Metrics configuration."""

    enabled: bool = True
    export_interval_seconds: int = 60
    providers: list[Literal["console", "file", "app_insights"]] = ["console"]
    output_path: str = "logs/metrics.jsonl"


class TracingConfig(BaseModel):
    """Distributed tracing configuration."""

    enabled: bool = True
    provider: Literal["opentelemetry", "app_insights"] = "opentelemetry"
    service_name: str = "generic-worker"
    endpoint: str | None = None
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)


class ObservabilityConfig(BaseModel):
    """Observability configuration."""

    logging: LogConfig = Field(default_factory=LogConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    tracing: TracingConfig = Field(default_factory=TracingConfig)
