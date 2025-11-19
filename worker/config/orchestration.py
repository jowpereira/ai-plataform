"""Orchestration configuration models."""

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


class RetryPolicyConfig(BaseModel):
    """Retry policy configuration."""

    strategy: Literal["fixed_delay", "exponential_backoff"] = "exponential_backoff"
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    multiplier: float = 2.0


class ErrorHandlingConfig(BaseModel):
    """Error handling configuration."""

    on_agent_error: Literal["fail", "continue", "fallback"] = "fail"
    fallback_agent: str | None = None
    max_workflow_errors: int = 3


class EdgeConfig(BaseModel):
    """Edge configuration for workflow graph."""

    kind: Literal["direct", "conditional", "fan_out", "fan_in", "switch_case"] = "direct"
    source: str = Field(..., description="Source agent/executor ID")
    target: str | list[str] | None = None
    targets: list[str] | None = None  # Para fan_out/fan_in
    condition: str | None = Field(
        None,
        description="Lambda expression string (e.g., 'lambda msg: msg.priority == \"high\"')",
    )
    cases: list[dict[str, Any]] | None = None  # Para switch_case
    default_target: str | None = None  # Para switch_case
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_targets(self):
        """Validate target/targets based on edge kind."""
        if self.kind in ["fan_out", "fan_in"]:
            if not self.targets:
                raise ValueError(f"{self.kind} requires 'targets' list")
        elif self.kind == "switch_case":
            if not self.cases:
                raise ValueError("switch_case requires 'cases' list")
        else:
            if not self.target:
                raise ValueError(f"{self.kind} requires 'target'")
        return self


class SequentialConfig(BaseModel):
    """Sequential orchestration configuration."""

    type: Literal["sequential"] = "sequential"
    start: str = Field(..., description="Starting agent/executor ID")
    edges: list[EdgeConfig] = Field(..., description="Workflow edges")
    terminal_nodes: list[str] = Field(
        default_factory=list,
        description="Explicit terminal nodes (no outgoing edges expected)",
    )
    retry_policies: dict[str, RetryPolicyConfig] = Field(default_factory=dict)
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)


class ConcurrentConfig(BaseModel):
    """Concurrent orchestration configuration (fan-out/fan-in)."""

    type: Literal["concurrent"] = "concurrent"
    dispatcher: str = Field(..., description="Dispatcher agent ID")
    workers: list[str] = Field(..., description="Worker agent IDs")
    aggregator: str = Field(..., description="Aggregator agent ID")
    selection_func: str | None = Field(
        None,
        description="Optional selection function import path",
    )
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)


class SpeakerSelectionConfig(BaseModel):
    """Speaker selection configuration for group chat."""

    strategy: Literal["round_robin", "prompt_based", "custom"] = "round_robin"
    custom_selector_path: str | None = None
    max_rounds: int = 10


class GroupChatConfig(BaseModel):
    """Group chat orchestration configuration."""

    type: Literal["group_chat"] = "group_chat"
    manager: str = Field(..., description="Manager agent ID")
    participants: list[str] = Field(..., description="Participant agent IDs")
    speaker_selection: SpeakerSelectionConfig = Field(default_factory=SpeakerSelectionConfig)
    termination_condition: str | None = Field(
        None,
        description="Lambda expression for termination",
    )


class HandoffConfig(BaseModel):
    """Handoff orchestration configuration."""

    type: Literal["handoff"] = "handoff"
    initial_agent: str = Field(..., description="Initial agent ID")
    agents: list[str] = Field(..., description="All agent IDs in handoff chain")
    handoff_conditions: dict[str, str] = Field(
        default_factory=dict,
        description="Agent ID -> condition expression mapping",
    )
    human_in_loop: bool = False
    input_handler_path: str | None = None


class TaskLedgerConfig(BaseModel):
    """Task ledger configuration for Magentic."""

    storage_path: str = "state/task_ledger.json"
    max_tasks: int = 100
    enable_backtracking: bool = True


class MagenticConfig(BaseModel):
    """Magentic orchestration configuration."""

    type: Literal["magentic"] = "magentic"
    manager: str = Field(..., description="Manager agent ID")
    agents: list[str] = Field(..., description="Specialized agent IDs")
    task_ledger: TaskLedgerConfig = Field(default_factory=TaskLedgerConfig)
    max_iterations: int = 50
    goal_evaluator_path: str | None = None


# Union discriminada para tipo de orquestração
OrchestrationConfig = (
    SequentialConfig | ConcurrentConfig | GroupChatConfig | HandoffConfig | MagenticConfig
)
