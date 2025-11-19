"""Generic Worker Runtime - Orquestrador principal.

Runtime genérico que:
1. Lê configuração JSON
2. Instancia recursos, middleware, agentes
3. Constrói workflow baseado em tipo de orquestração
4. Executa workflow (streaming ou non-streaming)
5. Coleta telemetria e logs
"""

import json
from pathlib import Path
from typing import Any

from agent_framework import WorkflowOutputEvent

from worker.config import (
    AgentConfig,
    ObservabilityConfig,
    OrchestrationConfig,
    ResourcesConfig,
    SequentialConfig,
    WorkspaceConfig,
)
from worker.config.models import ModelConfig
from worker.factories import AgentFactory, MiddlewareFactory, ResourceFactory, WorkflowFactory
from worker.logging_filters import configure_workflow_logging
from worker.observability import ObservabilityManager
from worker.runtime_context import RuntimeContext


class WorkerConfig:
    """Configuração completa do worker."""

    def __init__(
        self,
        workspace: WorkspaceConfig,
        resources: ResourcesConfig,
        agents: dict[str, AgentConfig],
        orchestration: OrchestrationConfig,
        observability: ObservabilityConfig,
        models: ModelConfig | None = None,
    ):
        self.workspace = workspace
        self.resources = resources
        self.agents = agents
        self.orchestration = orchestration
        self.observability = observability
        self.models = models or ModelConfig()

    @classmethod
    def from_json(cls, path: str | Path) -> "WorkerConfig":
        """Carrega configuração de arquivo JSON.

        Args:
            path: Caminho para worker.json

        Returns:
            WorkerConfig validado

        Raises:
            ValidationError: se JSON for inválido
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        workspace = WorkspaceConfig(**data["workspace"])
        resources = ResourcesConfig(**data["resources"])
        models = ModelConfig(**data.get("models", {}))
        agents = {aid: AgentConfig(**cfg) for aid, cfg in data["agents"].items()}
        observability = ObservabilityConfig(**data.get("observability", {}))

        # Orchestration é union discriminada
        orch_data = data["orchestration"]
        orch_type = orch_data["type"]

        # Import correto baseado no tipo
        from worker.config.orchestration import (
            ConcurrentConfig,
            GroupChatConfig,
            HandoffConfig,
            MagenticConfig,
            SequentialConfig,
        )

        orchestration_map = {
            "sequential": SequentialConfig,
            "concurrent": ConcurrentConfig,
            "group_chat": GroupChatConfig,
            "handoff": HandoffConfig,
            "magentic": MagenticConfig,
        }

        if orch_type not in orchestration_map:
            raise ValueError(f"Unknown orchestration type: {orch_type}")

        orchestration = orchestration_map[orch_type](**orch_data)

        return cls(
            workspace=workspace,
            resources=resources,
            agents=agents,
            orchestration=orchestration,
            observability=observability,
            models=models,
        )


class GenericWorker:
    """Runtime genérico para executar workflows declarativos.

    IMPORTANTE: Não usa InProcessRuntime (não existe no Python).
    Execução é direta via workflow.run() ou workflow.run_stream().
    """

    def __init__(self, config: WorkerConfig):
        self.config = config
        self.middleware_factory = MiddlewareFactory()
        self.resource_factory = ResourceFactory(config.resources)
        self.agent_factory: AgentFactory | None = None
        self.workflow_factory: WorkflowFactory | None = None
        self.runtime_context: RuntimeContext | None = None
        self.observability_manager = ObservabilityManager(config.observability)

    async def initialize(self):
        """Inicializa factories e cria agentes.

        IMPORTANTE: Middleware é aplicado no nível do agente individual.
        AgentFactory injeta global_middleware + agent_middleware em cada agente.
        """
        # Create AgentFactory com global middleware e model config
        self.agent_factory = AgentFactory(
            resource_factory=self.resource_factory,
            middleware_factory=self.middleware_factory,
            global_middleware_configs=self.config.resources.global_middleware,
            models_config=self.config.models,
        )

        # Observability e contexto precisam estar prontos antes de criar workflows
        self.observability_manager.setup()
        self.runtime_context = RuntimeContext.build(
            workspace=self.config.workspace,
            observability=self.config.observability,
        )

        # Create agents (middleware já aplicado) - SÍNCRONO
        agents = self.agent_factory.create_agents(self.config.agents)

        # Create WorkflowFactory
        self.workflow_factory = WorkflowFactory(
            agents=agents,
            runtime_context=self.runtime_context,
        )

        # Configure logging para suprimir warnings de terminal nodes
        self._configure_logging()

    async def run(self, input_message: Any) -> list[Any]:
        """Executa workflow (non-streaming).

        Args:
            input_message: Input para workflow

        Returns:
            Lista de eventos gerados

        Raises:
            RuntimeError: se workflow não estiver inicializado
        """
        if not self.workflow_factory:
            raise RuntimeError("Worker não inicializado. Chame initialize() primeiro.")
        if not self.runtime_context:
            raise RuntimeError("RuntimeContext não inicializado.")

        # Build workflow
        workflow = self.workflow_factory.create_workflow(self.config.orchestration)

        # Execute workflow (Python não usa InProcessRuntime)
        events = await workflow.run(input_message)

        # Processar eventos
        results = []
        for event in events:
            if isinstance(event, WorkflowOutputEvent):
                results.append(event.data)

        return results

    async def run_stream(self, input_message: Any):
        """Executa workflow (streaming).

        Args:
            input_message: Input para workflow

        Yields:
            Eventos de workflow em tempo real

        Raises:
            RuntimeError: se workflow não estiver inicializado
        """
        if not self.workflow_factory:
            raise RuntimeError("Worker não inicializado. Chame initialize() primeiro.")
        if not self.runtime_context:
            raise RuntimeError("RuntimeContext não inicializado.")
        if not self.runtime_context.allow_stream:
            raise RuntimeError("Streaming está desabilitado pelo runtime_flags.")

        # Build workflow
        workflow = self.workflow_factory.create_workflow(self.config.orchestration)

        # Execute workflow streaming (Python usa workflow.run_stream diretamente)
        async for event in workflow.run_stream(input_message):
            # TODO: enviar para observability handlers
            yield event

    async def plan_only(self) -> dict[str, Any]:
        """Valida workflow sem executar (dry-run).

        Returns:
            Informações sobre o workflow validado
        """
        if not self.workflow_factory:
            raise RuntimeError("Worker não inicializado. Chame initialize() primeiro.")
        if not self.runtime_context:
            raise RuntimeError("RuntimeContext não inicializado.")
        if not self.runtime_context.allow_plan_only:
            raise RuntimeError("Plan-only está desabilitado pelo runtime_flags.")

        workflow = self.workflow_factory.create_workflow(self.config.orchestration)

        # TODO: extrair informações do workflow (executors, edges, etc)
        return {
            "status": "valid",
            "workflow_type": self.config.orchestration.type,
            # TODO: adicionar mais metadados
        }

    def _configure_logging(self):
        """Configura logging com filtros para terminal nodes."""
        # Extrair terminal nodes do config se for Sequential
        terminal_nodes = set()
        if isinstance(self.config.orchestration, SequentialConfig):
            if self.config.orchestration.terminal_nodes:
                terminal_nodes = set(self.config.orchestration.terminal_nodes)
        
        # Aplicar filtro para suprimir warnings esperados
        if terminal_nodes:
            configure_workflow_logging(
                level="INFO",
                suppress_terminal_warnings=True,
                terminal_nodes=terminal_nodes,
            )
