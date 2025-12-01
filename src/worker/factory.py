import importlib
import os
import functools
import logging
from typing import Any, Callable, Dict, List, Optional

from agent_framework import ChatAgent

from src.worker.config import AgentConfig, ModelConfig, ToolConfig, WorkerConfig
from src.worker.providers import ProviderRegistry
from src.worker.rag import configure_rag_runtime, get_context_provider, create_agent_context_provider
from src.worker.tools import ToolRegistry, ToolDefinition, ToolType, ApprovalMode
from src.worker.middleware import EventMiddleware
from src.worker.middleware.hygiene import MessageSanitizerMiddleware

logger = logging.getLogger("worker.factory")


class ToolFactory:
    """
    Factory para carregamento de ferramentas.
    
    Suporta dois modos:
    1. Legacy: Carrega via path string (module:function)
    2. Registry: Usa ToolRegistry para ferramentas registradas
    
    O modo Registry é preferido e oferece suporte a HTTP, MCP além de local.
    """
    
    _registry: Optional[ToolRegistry] = None
    
    @classmethod
    def get_registry(cls) -> ToolRegistry:
        """Obtém ou cria o registry de ferramentas."""
        if cls._registry is None:
            cls._registry = ToolRegistry()
        return cls._registry
    
    @classmethod
    def register_tool(cls, definition: ToolDefinition) -> None:
        """Registra uma ferramenta no registry."""
        cls.get_registry().register(definition)
    
    @classmethod
    def load_from_registry(cls, tool_name: str) -> Callable:
        """Carrega ferramenta do registry."""
        return cls.get_registry().get_callable(tool_name)
    
    @staticmethod
    def load_tool(tool_config: ToolConfig) -> Callable:
        """
        Carrega uma ferramenta a partir da configuração.
        
        Tenta primeiro via ToolRegistry (se ferramenta registrada),
        senão faz fallback para carregamento via importlib (legacy).
        
        Args:
            tool_config: Configuração da ferramenta
            
        Returns:
            Função callable para uso pelo agente
        """
        registry = ToolFactory.get_registry()
        
        # Tentar via registry primeiro
        if registry.exists(tool_config.id):
            logger.debug(f"Carregando ferramenta '{tool_config.id}' via ToolRegistry")
            return registry.get_callable(tool_config.id)
            
        # Tentar registrar automaticamente se for Hosted
        if (tool_config.hosted_config or 
            tool_config.path.startswith("hosted://")):
            try:
                logger.debug(f"Registrando ferramenta '{tool_config.id}' automaticamente")
                ToolFactory.register_from_config(tool_config)
                if registry.exists(tool_config.id):
                    return registry.get_callable(tool_config.id)
            except Exception as e:
                logger.warning(f"Falha ao registrar ferramenta automática '{tool_config.id}': {e}")
        
        # Fallback: modo legacy via importlib
        logger.debug(f"Carregando ferramenta '{tool_config.id}' via importlib (legacy)")
        return ToolFactory._load_legacy(tool_config)
    
    @staticmethod
    def _load_legacy(tool_config: ToolConfig) -> Callable:
        """
        Carrega ferramenta via importlib (modo legacy).
        
        Suporta:
        - AIFunction: Retorna diretamente (framework já tem observabilidade)
        - Funções simples: Envolve com wrapper de eventos
        """
        try:
            module_path, func_name = tool_config.path.split(":")
        except ValueError:
            raise ValueError(
                f"Formato de caminho de ferramenta inválido: {tool_config.path}. "
                f"Esperado 'modulo:funcao'"
            )

        try:
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            if not callable(func):
                raise ValueError(
                    f"Objeto {func_name} em {module_path} não é chamável (callable)"
                )
            
            # Se já é AIFunction, criar wrapper para manter observabilidade
            from agent_framework import AIFunction
            if isinstance(func, AIFunction):
                logger.debug(f"Ferramenta '{tool_config.id}' é AIFunction nativa")
                
                # Criar wrapper que emite eventos e delega para AIFunction
                original_ai_func = func
                
                @functools.wraps(original_ai_func.func)
                def ai_function_wrapper(*args, **kwargs):
                    logger.info(f"[TOOL] {tool_config.id} ({func_name})")
                    logger.debug(f"  Input: args={args} kwargs={kwargs}")
                    
                    # Emitir evento START
                    from src.worker.events import get_event_bus, WorkerEventType
                    bus = get_event_bus()
                    bus.emit_simple(
                        WorkerEventType.TOOL_CALL_START, 
                        {"tool": tool_config.id, "arguments": kwargs}
                    )
                    
                    try:
                        # Chamar a função original (não o AIFunction)
                        result = original_ai_func.func(*args, **kwargs)
                        
                        # Emitir evento COMPLETE
                        bus.emit_simple(
                            WorkerEventType.TOOL_CALL_COMPLETE, 
                            {"tool": tool_config.id, "result": result}
                        )
                        
                        result_str = str(result)
                        if len(result_str) > 200:
                            logger.debug(f"  Output: {result_str[:200]}...")
                        else:
                            logger.debug(f"  Output: {result}")
                        return result
                    except Exception as e:
                        logger.error(f"  Error: {e}")
                        
                        # Emitir evento ERROR
                        bus.emit_simple(
                            WorkerEventType.TOOL_CALL_ERROR, 
                            {"tool": tool_config.id, "error": str(e)}
                        )
                        raise e
                
                # Retornar nova AIFunction com o wrapper
                from agent_framework import ai_function
                return ai_function(
                    name=original_ai_func.name,
                    description=original_ai_func.description,
                )(ai_function_wrapper)
            
            # Wrapper para logging e eventos (funções simples)
            @functools.wraps(func)
            def logged_tool(*args, **kwargs):
                logger.info(f"[TOOL] {tool_config.id} ({func_name})")
                logger.debug(f"  Input: args={args} kwargs={kwargs}")
                
                # Emitir evento START
                from src.worker.events import get_event_bus, WorkerEventType
                bus = get_event_bus()
                bus.emit_simple(
                    WorkerEventType.TOOL_CALL_START, 
                    {"tool": tool_config.id, "arguments": kwargs}
                )
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Emitir evento COMPLETE
                    bus.emit_simple(
                        WorkerEventType.TOOL_CALL_COMPLETE, 
                        {"tool": tool_config.id, "result": result}
                    )
                    
                    result_str = str(result)
                    if len(result_str) > 200:
                        logger.debug(f"  Output: {result_str[:200]}...")
                    else:
                        logger.debug(f"  Output: {result}")
                    return result
                except Exception as e:
                    logger.error(f"  Error: {e}")
                    
                    # Emitir evento ERROR
                    bus.emit_simple(
                        WorkerEventType.TOOL_CALL_ERROR, 
                        {"tool": tool_config.id, "error": str(e)}
                    )
                    raise e

            return logged_tool
            
        except ImportError as e:
            raise ImportError(f"Não foi possível importar o módulo {module_path}: {e}")
        except AttributeError:
            raise AttributeError(
                f"Função {func_name} não encontrada no módulo {module_path}"
            )
    
    @classmethod
    def register_from_config(cls, tool_config: ToolConfig) -> None:
        """
        Registra uma ferramenta a partir de ToolConfig.
        
        Converte ToolConfig para ToolDefinition e registra no registry.
        """
        # Determinar tipo baseado no path
        path = tool_config.path
        
        if tool_config.hosted_config or path.startswith("hosted://"):
            tool_type = ToolType.HOSTED
            source = path
        else:
            # Assumir local (module:function -> module.function)
            tool_type = ToolType.LOCAL
            source = path.replace(":", ".")
        
        # Converter string de config para Enum
        approval_mode = ApprovalMode.NEVER
        if tool_config.approval_mode:
            try:
                # Mapear valores do config (always, never, custom) para Enum
                mode_map = {
                    "always": ApprovalMode.ALWAYS,
                    "never": ApprovalMode.NEVER,
                    "custom": ApprovalMode.CONDITIONAL
                }
                approval_mode = mode_map.get(tool_config.approval_mode, ApprovalMode.NEVER)
            except (ValueError, KeyError):
                pass
        
        definition = ToolDefinition(
            name=tool_config.id,
            description=tool_config.description or f"Ferramenta {tool_config.id}",
            type=tool_type,
            source=source,
            approval_mode=approval_mode,
            hosted_config=tool_config.hosted_config
        )
        
        cls.register_tool(definition)


class AgentFactory:
    """
    Factory para criação de agentes usando providers desacoplados.
    
    Usa ProviderRegistry para criar clientes de forma agnóstica ao provider.
    """
    
    def __init__(self, config: WorkerConfig, preloaded_agents: Optional[Dict[str, Any]] = None):
        self.config = config
        self.tool_map = {t.id: t for t in config.resources.tools}
        self.model_map = config.resources.models
        self.preloaded_agents = preloaded_agents or {}
        # Inicializa o registry de providers
        self._provider_registry = ProviderRegistry()
        self._rag_runtime = configure_rag_runtime(config)
        self._rag_provider = get_context_provider()

    def create_client(self, model_ref: str) -> Any:
        """
        Cria um cliente LLM usando o ProviderRegistry.
        
        Args:
            model_ref: Referência ao modelo definido em resources.models
            
        Returns:
            Cliente de chat compatível com agent_framework
            
        Raises:
            ValueError: Se modelo não encontrado ou provider não suportado
        """
        if model_ref not in self.model_map:
            raise ValueError(f"Referência de modelo '{model_ref}' não encontrada nos recursos")

        model_config = self.model_map[model_ref]
        
        # Delegar criação ao ProviderRegistry (desacoplado!)
        return self._provider_registry.create_client(model_config)

    def create_agent(self, agent_id: str, middleware: Optional[List[Any]] = None) -> ChatAgent:
        applied_middleware: list[Any] = list(middleware or [])
        
        # Adicionar MessageSanitizerMiddleware para robustez
        # Garante que mensagens estejam limpas antes de processamento
        applied_middleware.insert(0, MessageSanitizerMiddleware())
        
        # Adicionar EventMiddleware para observabilidade
        # Inserir no início para capturar tudo
        applied_middleware.insert(0, EventMiddleware(agent_id))

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
                logging.warning(f"Failed to copy agent {agent_id}: {e}. Using original.")
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
        client = self.create_client(agent_conf.model)

        # Carregar Tools
        loaded_tools = []
        has_hosted_tools = False
        hosted_tool_names = []
        
        for tool_id in agent_conf.tools:
            if tool_id not in self.tool_map:
                raise ValueError(f"Ferramenta '{tool_id}' referenciada pelo agente '{agent_id}' não encontrada nos recursos")
            
            tool_config = self.tool_map[tool_id]
            tool = ToolFactory.load_tool(tool_config)
            
            # Detectar Hosted Tools
            tool_type_name = type(tool).__name__
            if "Hosted" in tool_type_name:
                has_hosted_tools = True
                hosted_tool_names.append(tool_id)
            
            loaded_tools.append(tool)
        
        # Alertar se Hosted Tools com cliente que não suporta
        if has_hosted_tools:
            client_type = type(client).__name__
            if "ChatClient" in client_type and "Agent" not in client_type:
                logger.warning(
                    f"⚠️ Agente '{agent_id}' usa Hosted Tools ({hosted_tool_names}) com {client_type}. "
                    f"Hosted Tools (code_interpreter, web_search, file_search) requerem "
                    f"Azure AI Agent Service (AzureAIAgentClient), não Azure OpenAI Chat. "
                    f"As ferramentas serão IGNORADAS pelo modelo."
                )

        agent_name = agent_conf.id
        display_name = agent_conf.role or agent_conf.id
        # Incluir ID na descrição para ajudar o Manager a selecionar corretamente
        base_desc = agent_conf.description or display_name
        description = f"Participant ID: {agent_name}. Role/Description: {base_desc}"

        # Determinar context_provider: específico por agente ou global
        context_provider = None
        if agent_conf.knowledge and agent_conf.knowledge.enabled and agent_conf.knowledge.collection_ids:
            # Criar provider específico com filtros de coleção
            context_provider = create_agent_context_provider(
                collection_ids=agent_conf.knowledge.collection_ids,
                top_k=agent_conf.knowledge.top_k,
                min_score=agent_conf.knowledge.min_score,
            )
            if context_provider:
                logger.info(
                    f"🔗 Agente '{agent_id}' usando Knowledge Base com collections: "
                    f"{agent_conf.knowledge.collection_ids}"
                )
            else:
                logger.warning(
                    f"⚠️ Agente '{agent_id}' tem knowledge configurada mas RAG runtime não está ativo. "
                    f"Verifique se o RAG está habilitado na configuração."
                )
        else:
            # Usar provider global (se disponível)
            context_provider = self._rag_provider

        agent = ChatAgent(
            id=agent_conf.id,
            name=agent_name,
            description=description,
            instructions=agent_conf.instructions,
            chat_client=client,
            tools=loaded_tools if loaded_tools else None,
            context_providers=context_provider,
            middleware=applied_middleware or None,
        )

        if display_name and display_name != agent_name:
            agent.additional_properties["display_name"] = display_name

        return agent

    def create_manager_agent(self, model_ref: str, instructions: str, name: str = "GroupManager") -> ChatAgent:
        """Cria um agente manager dedicado para orquestração."""
        client = self.create_client(model_ref)
        
        agent = ChatAgent(
            name=name,
            description="Coordenador do grupo",
            instructions=instructions,
            chat_client=client,
            middleware=[EventMiddleware(name)]
        )
        return agent
