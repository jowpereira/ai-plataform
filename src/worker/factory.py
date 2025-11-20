import importlib
import os
from typing import Any, Callable, Dict, List, Optional

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
# from agent_framework.azure import AzureOpenAIChatClient # Uncomment when available/needed

from src.worker.config import AgentConfig, ModelConfig, ToolConfig, WorkerConfig


class ToolFactory:
    @staticmethod
    def load_tool(tool_config: ToolConfig) -> Callable:
        """Carrega uma função Python dinamicamente a partir de uma string 'module:function'."""
        try:
            module_path, func_name = tool_config.path.split(":")
        except ValueError:
            raise ValueError(f"Formato de caminho de ferramenta inválido: {tool_config.path}. Esperado 'modulo:funcao'")

        try:
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            if not callable(func):
                raise ValueError(f"Objeto {func_name} em {module_path} não é chamável (callable)")
            return func
        except ImportError as e:
            raise ImportError(f"Não foi possível importar o módulo {module_path}: {e}")
        except AttributeError:
            raise AttributeError(f"Função {func_name} não encontrada no módulo {module_path}")


class AgentFactory:
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.tool_map = {t.id: t for t in config.resources.tools}
        self.model_map = config.resources.models

    def _create_client(self, model_ref: str) -> Any:
        if model_ref not in self.model_map:
            raise ValueError(f"Referência de modelo '{model_ref}' não encontrada nos recursos")

        model_config = self.model_map[model_ref]

        # Configurar variáveis de ambiente específicas do modelo, se houver
        if model_config.env_vars:
            for k, v in model_config.env_vars.items():
                os.environ[k] = v

        if model_config.type == "openai":
            return OpenAIChatClient(model_id=model_config.deployment)
        elif model_config.type == "azure-openai":
            # Placeholder para Azure - assumindo que as env vars padrão ou params sejam usados
            # return AzureOpenAIChatClient(deployment_name=model_config.deployment)
            # Por enquanto, usando OpenAIChatClient como fallback ou se a lib azure não estiver instalada
            # Ajuste conforme a disponibilidade da lib agent_framework.azure
            return OpenAIChatClient(model_id=model_config.deployment)
        else:
            raise ValueError(f"Tipo de modelo não suportado: {model_config.type}")

    def create_agent(self, agent_id: str, middleware: Optional[List[Any]] = None) -> ChatAgent:
        # Encontrar config do agente
        agent_conf = next((a for a in self.config.agents if a.id == agent_id), None)
        if not agent_conf:
            raise ValueError(f"Agente '{agent_id}' não encontrado na configuração")

        # Criar Cliente
        client = self._create_client(agent_conf.model)

        # Carregar Tools
        loaded_tools = []
        for tool_id in agent_conf.tools:
            if tool_id not in self.tool_map:
                raise ValueError(f"Ferramenta '{tool_id}' referenciada pelo agente '{agent_id}' não encontrada nos recursos")
            
            tool_config = self.tool_map[tool_id]
            loaded_tools.append(ToolFactory.load_tool(tool_config))

        # Criar Agente
        return ChatAgent(
            name=agent_conf.role,
            description=agent_conf.description,
            instructions=agent_conf.instructions,
            chat_client=client,
            tools=loaded_tools if loaded_tools else None,
            middleware=middleware
        )
