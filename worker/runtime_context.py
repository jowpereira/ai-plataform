"""Runtime context utilities for the GenericWorker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from agent_framework import FileCheckpointStorage, InMemoryCheckpointStorage

from worker.config import ObservabilityConfig, WorkspaceConfig

CheckpointInstance = FileCheckpointStorage | InMemoryCheckpointStorage


@dataclass(slots=True, frozen=True)
class RuntimeContext:
    """Aggregates workspace + observability data for a worker run."""

    workspace: WorkspaceConfig
    observability: ObservabilityConfig
    session_id: str
    checkpoint_storage: CheckpointInstance | None
    allow_plan_only: bool
    allow_stream: bool

    @property
    def max_iterations(self) -> int:
        """Return the maximum number of workflow iterations allowed."""
        return self.workspace.max_iterations

    @classmethod
    def build(
        cls,
        workspace: WorkspaceConfig,
        observability: ObservabilityConfig,
    ) -> "RuntimeContext":
        session_id = _generate_session_id(workspace.session_strategy)
        checkpoint_storage = _create_checkpoint_storage(workspace)
        flags = workspace.runtime_flags
        return cls(
            workspace=workspace,
            observability=observability,
            session_id=session_id,
            checkpoint_storage=checkpoint_storage,
            allow_plan_only=flags.allow_plan_only,
            allow_stream=flags.allow_stream,
        )


def _generate_session_id(strategy: Literal["uuid", "timestamp", "custom"]) -> str:
    if strategy == "timestamp":
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    # Custom strategy reservado para implementações específicas; fallback em UUID
    return str(uuid4())


def _create_checkpoint_storage(workspace: WorkspaceConfig) -> CheckpointInstance | None:
    cfg = workspace.checkpoint_storage
    if cfg.type == "file":
        base_path = Path(cfg.base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        return FileCheckpointStorage(storage_path=base_path)
    if cfg.type == "in_memory":
        return InMemoryCheckpointStorage()
    # TODO: implementar Cosmos e Redis quando os provedores estiverem disponíveis
    return None
