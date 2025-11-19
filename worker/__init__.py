"""Generic Worker Module.

Módulo extremamente genérico e eficiente para executar workflows
declarativos do Microsoft Agent Framework.

Componentes principais:
- config: Pydantic models para validação type-safe
- factories: Padrão Factory para instanciar componentes
- builders: Helpers para construir workflows específicos
- execution: Camada de execução e event handling
- storage: Persistência local JSON
- runtime: Orquestrador principal (GenericWorker)

Uso:
    from worker import GenericWorker, WorkerConfig

    # Carrega configuração
    config = WorkerConfig.from_json("worker.json")

    # Cria runtime
    worker = GenericWorker(config)
    await worker.initialize()

    # Executa workflow
    results = await worker.run("input message")

    # Ou streaming
    async for event in worker.run_stream("input message"):
        print(event)
"""

from worker.config import (
    AgentConfig,
    ConcurrentConfig,
    GroupChatConfig,
    HandoffConfig,
    MagenticConfig,
    ObservabilityConfig,
    OrchestrationConfig,
    ResourcesConfig,
    SequentialConfig,
    WorkspaceConfig,
)
from worker.factories import AgentFactory, MiddlewareFactory, ResourceFactory, WorkflowFactory
from worker.logging_filters import (
    TerminalNodeWarningFilter,
    configure_workflow_logging,
    reset_workflow_logging,
)
from worker.runtime import GenericWorker, WorkerConfig

__version__ = "0.1.0"

__all__ = [
    # Runtime
    "GenericWorker",
    "WorkerConfig",
    # Config
    "WorkspaceConfig",
    "ResourcesConfig",
    "AgentConfig",
    "OrchestrationConfig",
    "SequentialConfig",
    "ConcurrentConfig",
    "GroupChatConfig",
    "HandoffConfig",
    "MagenticConfig",
    "ObservabilityConfig",
    # Factories
    "AgentFactory",
    "MiddlewareFactory",
    "ResourceFactory",
    "WorkflowFactory",
    # Logging
    "TerminalNodeWarningFilter",
    "configure_workflow_logging",
    "reset_workflow_logging",
]

