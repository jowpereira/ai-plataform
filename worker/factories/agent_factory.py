"""Agent factory para instanciar agentes configurados."""

import os
from typing import Any

from agent_framework import ChatAgent
from worker.config import AgentConfig
from worker.factories.client_factory import ClientFactoryRegistry
from worker.factories.middleware_factory import MiddlewareFactory
from worker.factories.resource_factory import ResourceFactory


class AgentFactory:
    """Factory para criar instâncias de agentes.

    IMPORTANTE: Middleware é aplicado no nível do agente individual,
    não no workflow. Cada agente recebe:
    1. Global middleware (de resources.global_middleware)
    2. Agent-specific middleware (de agents.<id>.middleware)
    """

    def __init__(
        self,
        resource_factory: ResourceFactory,
        middleware_factory: MiddlewareFactory,
        global_middleware_configs: list[Any],
        client_factory_registry: ClientFactoryRegistry | None = None,
    ):
        self.resource_factory = resource_factory
        self.middleware_factory = middleware_factory
        self.global_middleware_configs = global_middleware_configs
        self.client_factory_registry = client_factory_registry or ClientFactoryRegistry()
        self._agent_cache: dict[str, ChatAgent] = {}

    def create_agent(self, config: AgentConfig) -> ChatAgent:
        """Cria instância de agente a partir da config.

        Args:
            config: Configuração do agente

        Returns:
            Instância de ChatAgent

        Raises:
            ValueError: se configuração for inválida
        """
        if not config.enabled:
            raise ValueError(f"Agent {config.id} está desabilitado")

        # Resolver model ID
        model_id = self._resolve_model(config)

        # Criar chat client usando factory registry
        client = self.client_factory_registry.create_client(
            client_type=config.client_type,
            model_id=model_id,
            # Passar parâmetros adicionais do metadata se necessário
            **config.metadata.get("client_params", {})
        )

        # Obter ferramentas
        tools = self.resource_factory.get_tools(config.tools) if config.tools else []

        # Construir lista de middleware (global + agent-specific)
        middleware_list = []

        # 1. Global middleware (aplicado a TODOS os agentes)
        if self.global_middleware_configs:
            middleware_list.extend(
                self.middleware_factory.create_middleware_list(self.global_middleware_configs)
            )

        # 2. Agent-specific middleware
        if config.middleware:
            # Buscar configs de middleware do resources
            agent_middleware_configs = []
            for mid in config.middleware:
                # Procurar em resources.global_middleware por ID
                for mw_cfg in self.resource_factory.config.global_middleware:
                    if mw_cfg.id == mid:
                        agent_middleware_configs.append(mw_cfg)
                        break

            middleware_list.extend(
                self.middleware_factory.create_middleware_list(agent_middleware_configs)
            )

        # TODO: response_format via Pydantic model
        # TODO: memory configuration (AgentThread customizado)

        # Criar agente com middleware aplicado
        agent = ChatAgent(
            chat_client=client,
            name=config.name,
            instructions=config.instructions,
            description=config.metadata.get("description", ""),
            tools=tools,
            middleware=middleware_list if middleware_list else None,
        )

        return agent

    def create_agents(self, agent_configs: dict[str, AgentConfig]) -> dict[str, ChatAgent]:
        """Cria múltiplos agentes.

        Args:
            agent_configs: Dicionário de configurações de agentes

        Returns:
            Dicionário de instâncias de agentes
        """
        agents = {}
        for agent_id, config in agent_configs.items():
            if config.enabled:
                agents[agent_id] = self.create_agent(config)
        return agents

    def _resolve_model(self, config: AgentConfig) -> str:
        """Resolve model ID de config ou variável de ambiente.

        Args:
            config: Configuração do agente

        Returns:
            Model ID resolvido

        Raises:
            ValueError: se model não puder ser resolvido
        """
        # 1. Modelo explícito na config
        if config.model and not config.model.startswith("$"):
            return config.model

        # 2. Referência a variável de ambiente ($ENV_VAR)
        if config.model and config.model.startswith("$"):
            env_var = config.model[1:]  # Remove $
            value = os.getenv(env_var)
            if value:
                return value
            raise ValueError(f"Variável de ambiente {env_var} não definida para agent {config.id}")

        # 3. Default OPENAI_MODEL
        default_model = os.getenv("OPENAI_MODEL")
        if default_model:
            return default_model

        raise ValueError(
            f"Não foi possível determinar model_id para agent {config.id}. "
            "Configure config.model ou defina OPENAI_MODEL."
        )

    def clear_cache(self):
        """Limpa cache de agentes."""
        self._agent_cache.clear()
