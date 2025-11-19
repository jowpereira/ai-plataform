"""Agent factory para instanciar agentes configurados."""

import os
from typing import Any

from agent_framework import ChatAgent
from worker.config import AgentConfig
from worker.config.models import ModelConfig
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
        models_config: ModelConfig | None = None,
    ):
        self.resource_factory = resource_factory
        self.middleware_factory = middleware_factory
        self.global_middleware_configs = global_middleware_configs
        self.client_factory_registry = client_factory_registry or ClientFactoryRegistry()
        self.models_config = models_config or ModelConfig()
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

        # Resolver configuração de modelo
        client_type, model_id, client_params = self._resolve_model_config(config)

        # Criar chat client usando factory registry
        client = self.client_factory_registry.create_client(
            client_type=client_type,
            model_id=model_id,
            **client_params
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

    def _resolve_model_config(self, config: AgentConfig) -> tuple[str, str, dict]:
        """Resolve configuração de modelo (direto ou via profile).

        Args:
            config: Configuração do agente

        Returns:
            Tuple (client_type, model_id, client_params)

        Raises:
            ValueError: se configuração for inválida
        """
        # Configuração direta
        if config.client_type and config.model:
            model_id = self._resolve_model_id(config.model, config.id)
            client_params = config.metadata.get("client_params", {})
            return config.client_type, model_id, client_params
        
        # Model profile
        if config.model_profile:
            if config.model_profile not in self.models_config.profiles:
                raise ValueError(f"Model profile '{config.model_profile}' não encontrado")
            
            profile = self.models_config.profiles[config.model_profile]
            model_id = self._resolve_model_id(profile.model, config.id)
            client_params = {**profile.default_params, **config.metadata.get("client_params", {})}
            return profile.client_type, model_id, client_params
        
        raise ValueError(f"Agent {config.id} deve ter client_type+model ou model_profile")
    
    def _resolve_model_id(self, model: str, agent_id: str) -> str:
        """Resolve model ID de string ou env var."""
        if not model.startswith("$"):
            return model
        
        env_var = model[1:]
        value = os.getenv(env_var)
        if value:
            return value
        
        raise ValueError(f"Variável {env_var} não definida para agent {agent_id}")

    def clear_cache(self):
        """Limpa cache de agentes."""
        self._agent_cache.clear()
