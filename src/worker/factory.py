import importlib
import os
import functools
from typing import Any, Callable, Dict, List, Optional

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

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
            
            # Wrapper para logging
            @functools.wraps(func)
            def logged_tool(*args, **kwargs):
                print(f"\n🛠️ [TOOL EXECUTION] {tool_config.id} ({func_name})")
                print(f"   📥 Input: args={args} kwargs={kwargs}")
                try:
                    result = func(*args, **kwargs)
                    print(f"   📤 Output: {str(result)[:200]}..." if len(str(result)) > 200 else f"   📤 Output: {result}")
                    return result
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    raise e

            return logged_tool
            
        except ImportError as e:
            raise ImportError(f"Não foi possível importar o módulo {module_path}: {e}")
        except AttributeError:
            raise AttributeError(f"Função {func_name} não encontrada no módulo {module_path}")


class AgentFactory:
    def __init__(self, config: WorkerConfig, preloaded_agents: Optional[Dict[str, Any]] = None):
        self.config = config
        self.tool_map = {t.id: t for t in config.resources.tools}
        self.model_map = config.resources.models
        self.preloaded_agents = preloaded_agents or {}

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
            return AzureOpenAIChatClient(
                credential=AzureCliCredential(),
                deployment_name=model_config.deployment
            )
        else:
            raise ValueError(f"Tipo de modelo não suportado: {model_config.type}")

    def create_agent(self, agent_id: str, middleware: Optional[List[Any]] = None) -> ChatAgent:
        applied_middleware: list[Any] = list(middleware or [])

        # 0. Verificar se já foi pré-carregado
        if agent_id in self.preloaded_agents:
            original_agent = self.preloaded_agents[agent_id]
            
            # Create a copy to ensure unique instances for the graph (avoiding shared node issues)
            import copy
            try:
                # Try Pydantic copy first if available
                if hasattr(original_agent, "model_copy"):
                    agent = original_agent.model_copy()
                else:
                    agent = copy.copy(original_agent)
            except Exception as e:
                print(f"Warning: Failed to copy agent {agent_id}: {e}. Using original.")
                agent = original_agent

            if applied_middleware:
                existing = list(agent.middleware or [])
                agent.middleware = existing + applied_middleware
            return agent

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

        agent_name = agent_conf.id
        display_name = agent_conf.role or agent_conf.id
        description = agent_conf.description or display_name

        agent = ChatAgent(
            id=agent_conf.id,
            name=agent_name,
            description=description,
            instructions=agent_conf.instructions,
            chat_client=client,
            tools=loaded_tools if loaded_tools else None,
            middleware=applied_middleware or None,
        )

        if display_name and display_name != agent_name:
            agent.additional_properties["display_name"] = display_name

        return agent
