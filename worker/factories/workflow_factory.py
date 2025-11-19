"""Workflow factory para instanciar workflows baseado em configuração.

IMPORTANTE: Python Agent Framework não tem classes SequentialOrchestration, etc.
Todos os padrões são construídos com WorkflowBuilder + edges específicas.
"""

from typing import Any

from agent_framework import Case, Default, Workflow, WorkflowBuilder

from worker.config import (
    ConcurrentConfig,
    GroupChatConfig,
    HandoffConfig,
    MagenticConfig,
    OrchestrationConfig,
    SequentialConfig,
)
from worker.runtime_context import RuntimeContext


class WorkflowFactory:
    """Factory para criar workflows a partir de configuração.

    Constrói workflows usando WorkflowBuilder com edges específicas
    para cada padrão de orquestração.
    """

    def __init__(self, agents: dict[str, Any], runtime_context: RuntimeContext | None = None):
        """Inicializa factory com agentes já criados.

        Args:
            agents: Dicionário de agentes por ID
        """
        self.agents = agents
        self.runtime_context = runtime_context

    def _create_builder(self, name: str | None = None) -> WorkflowBuilder:
        """Create a WorkflowBuilder honoring workspace limits/checkpointing."""

        max_iterations = 12
        checkpoint_storage = None

        if self.runtime_context:
            max_iterations = self.runtime_context.max_iterations
            checkpoint_storage = self.runtime_context.checkpoint_storage

        builder = WorkflowBuilder(max_iterations=max_iterations, name=name)

        if checkpoint_storage:
            builder = builder.with_checkpointing(checkpoint_storage)

        return builder

    def create_workflow(self, config: OrchestrationConfig) -> Workflow:
        """Cria workflow baseado no tipo de orquestração.

        Args:
            config: Configuração de orquestração (union discriminada)

        Returns:
            Workflow construído e validado

        Raises:
            ValueError: se configuração for inválida
        """
        match config:
            case SequentialConfig():
                return self._build_sequential(config)
            case ConcurrentConfig():
                return self._build_concurrent(config)
            case GroupChatConfig():
                return self._build_group_chat(config)
            case HandoffConfig():
                return self._build_handoff(config)
            case MagenticConfig():
                return self._build_magentic(config)
            case _:
                raise ValueError(f"Unknown orchestration type: {type(config)}")

    def _build_sequential(self, config: SequentialConfig) -> Workflow:
        """Constrói workflow Sequential usando WorkflowBuilder + edges.

        Sequential = cadeia de agents conectados por edges (diretas ou condicionais).
        
        Terminal nodes:
        - Nós listados em config.terminal_nodes não terão outgoing edges
        - Se não especificado, detecta automaticamente o último nó da cadeia
        """
        builder = self._create_builder(name=config.start)

        # Detectar terminal nodes (explícitos ou auto-detectados)
        if config.terminal_nodes:
            terminal_nodes = set(config.terminal_nodes)
        else:
            # Auto-detect: nós que não são source de nenhuma edge
            all_sources = {e.source for e in config.edges}
            all_targets = set()
            for e in config.edges:
                if isinstance(e.target, str):
                    all_targets.add(e.target)
                elif isinstance(e.target, list):
                    all_targets.update(e.target)
                if e.targets:
                    all_targets.update(e.targets)
            
            terminal_nodes = all_targets - all_sources

        # Add agents ao builder com seus IDs
        agents_added = set()
        for edge_config in config.edges:
            if edge_config.source not in agents_added:
                source_agent = self.agents[edge_config.source]
                is_terminal = edge_config.source in terminal_nodes
                builder.add_agent(source_agent, id=edge_config.source, output_response=is_terminal)
                agents_added.add(edge_config.source)

            # Handle target (pode ser str ou list)
            if isinstance(edge_config.target, str):
                target_id = edge_config.target
                if target_id and target_id not in agents_added:
                    target_agent = self.agents[target_id]
                    is_terminal = target_id in terminal_nodes
                    builder.add_agent(target_agent, id=target_id, output_response=is_terminal)
                    agents_added.add(target_id)
            elif isinstance(edge_config.target, list):
                for target_id in edge_config.target:
                    if target_id not in agents_added:
                        target_agent = self.agents[target_id]
                        is_terminal = target_id in terminal_nodes
                        builder.add_agent(target_agent, id=target_id, output_response=is_terminal)
                        agents_added.add(target_id)
            
            # Handle targets (fan-out/fan-in)
            if edge_config.targets:
                for target_id in edge_config.targets:
                    if target_id not in agents_added:
                        target_agent = self.agents[target_id]
                        is_terminal = target_id in terminal_nodes
                        builder.add_agent(target_agent, id=target_id, output_response=is_terminal)
                        agents_added.add(target_id)

        # Set starting executor
        builder.set_start_executor(config.start)

        # Add edges conforme configuração
        for edge_config in config.edges:
            source_agent = self.agents[edge_config.source]

            if edge_config.kind == "direct":
                target_agent = self.agents[edge_config.target]  # type: ignore
                builder.add_edge(source_agent, target_agent)

            elif edge_config.kind == "conditional":
                target_agent = self.agents[edge_config.target]  # type: ignore
                # TODO: converter edge_config.condition (string) para lambda
                condition_func = eval(edge_config.condition) if edge_config.condition else None  # type: ignore
                builder.add_edge(source_agent, target_agent, condition=condition_func)

            elif edge_config.kind == "fan_out":
                target_agents = [self.agents[tid] for tid in edge_config.targets]  # type: ignore
                # TODO: selection_func se especificado
                builder.add_fan_out_edges(source_agent, target_agents)

            elif edge_config.kind == "fan_in":
                source_agents = [self.agents[sid] for sid in edge_config.targets]  # type: ignore
                target_agent = self.agents[edge_config.target]  # type: ignore
                builder.add_fan_in_edges(source_agents, target_agent)

            elif edge_config.kind == "switch_case":
                cases = []
                for case_config in edge_config.cases or []:
                    condition = eval(case_config["when"])  # type: ignore
                    target = self.agents[case_config["target"]]
                    cases.append(Case(condition=condition, target=target))

                if edge_config.default_target:
                    default_agent = self.agents[edge_config.default_target]
                    cases.append(Default(target=default_agent))

                builder.add_switch_case_edge_group(source_agent, cases)

        return builder.build()

    def _build_concurrent(self, config: ConcurrentConfig) -> Workflow:
        """Constrói workflow Concurrent (fan-out/fan-in).

        Concurrent = dispatcher -> [workers] -> aggregator
        """
        builder = self._create_builder(name="concurrent")

        dispatcher = self.agents[config.dispatcher]
        workers = [self.agents[wid] for wid in config.workers]
        aggregator = self.agents[config.aggregator]

        builder.set_start_executor(dispatcher)

        # Fan-out to workers
        # TODO: selection_func se especificado
        builder.add_fan_out_edges(dispatcher, workers)

        # Fan-in to aggregator
        builder.add_fan_in_edges(workers, aggregator)

        return builder.build()

    def _build_group_chat(self, config: GroupChatConfig) -> Workflow:
        """Constrói workflow Group Chat.

        Group Chat = manager + conditional edges para speaker selection
        """
        builder = self._create_builder(name="group-chat")

        manager = self.agents[config.manager]
        participants = [self.agents[pid] for pid in config.participants]

        builder.set_start_executor(manager)

        # TODO: implementar speaker selection strategies
        # Round-robin: manager escolhe próximo speaker em ordem
        # Prompt-based: manager usa LLM para escolher speaker
        # Custom: função customizada de seleção

        # Por ora, conditional edges simples
        for participant in participants:
            builder.add_edge(
                manager,
                participant,
                condition=lambda msg, p=participant: msg.get("speaker") == p.name,  # type: ignore
            )
            builder.add_edge(participant, manager)  # Volta para manager

        return builder.build()

    def _build_handoff(self, config: HandoffConfig) -> Workflow:
        """Constrói workflow Handoff.

        Handoff = conditional edges baseadas em context/rules
        """
        builder = self._create_builder(name="handoff")

        initial = self.agents[config.initial_agent]
        builder.set_start_executor(initial)

        # Add handoff edges com condições
        for agent_id, condition_str in config.handoff_conditions.items():
            source = self.agents[agent_id]
            # TODO: mapear targets baseado em condições
            # Por ora, placeholder
            pass

        # TODO: human-in-loop via RequestInfoEvent

        return builder.build()

    def _build_magentic(self, config: MagenticConfig) -> Workflow:
        """Constrói workflow Magentic.

        Magentic = manager + dynamic delegation + task ledger
        """
        builder = self._create_builder(name="magentic")

        manager = self.agents[config.manager]
        specialized_agents = [self.agents[aid] for aid in config.agents]

        builder.set_start_executor(manager)

        # TODO: implementar task ledger + goal evaluator
        # TODO: dynamic conditional routing baseado em task progress

        # Por ora, edges básicas
        for agent in specialized_agents:
            builder.add_edge(manager, agent)
            builder.add_edge(agent, manager)

        return builder.build()
