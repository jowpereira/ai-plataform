"""
Contratos e Interfaces (ABCs) para o Worker SDK Genérico.

Este módulo define os contratos que permitem extensibilidade e desacoplamento:
- LLMProvider: Abstração para provedores de modelo (OpenAI, Azure, Ollama)
- ToolAdapter: Abstração para ferramentas (local, HTTP, MCP)
- WorkflowStrategy: Strategy para construção de workflows
- EventBus: Sistema de eventos para observabilidade
- MemoryStore: Interface para persistência de contexto

Versão: 0.8.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union

from pydantic import BaseModel


# =============================================================================
# Tipos Básicos
# =============================================================================

T = TypeVar("T")
MessageType = TypeVar("MessageType")


class ProviderType(str, Enum):
    """Tipos de provedores de LLM suportados."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure-openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    BEDROCK = "bedrock"
    CUSTOM = "custom"


class ToolType(str, Enum):
    """Tipos de ferramentas suportadas."""
    LOCAL = "local"       # Função Python local
    HTTP = "http"         # Endpoint HTTP/REST
    MCP = "mcp"           # Model Context Protocol
    CUSTOM = "custom"


class WorkerEventType(str, Enum):
    """Tipos de eventos emitidos pelo Worker."""
    # Lifecycle
    SETUP_START = "setup_start"
    SETUP_COMPLETE = "setup_complete"
    TEARDOWN_START = "teardown_start"
    TEARDOWN_COMPLETE = "teardown_complete"
    
    # Prompt/Message
    PROMPT_RENDER_START = "prompt_render_start"
    PROMPT_RENDER_COMPLETE = "prompt_render_complete"
    
    # LLM
    LLM_REQUEST_START = "llm_request_start"
    LLM_REQUEST_COMPLETE = "llm_request_complete"
    LLM_REQUEST_ERROR = "llm_request_error"
    
    # Tools
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_COMPLETE = "tool_call_complete"
    TOOL_CALL_ERROR = "tool_call_error"
    
    # Workflow
    WORKFLOW_START = "workflow_start"
    WORKFLOW_STEP = "workflow_step"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    
    # Agent
    AGENT_START = "agent_start"
    AGENT_RESPONSE = "agent_response"
    AGENT_HANDOFF = "agent_handoff"
    
    # Standalone Agent Run (para paridade com workflow)
    AGENT_RUN_START = "agent_run_start"     # Header de início de execução
    AGENT_RUN_COMPLETE = "agent_run_complete" # Footer de conclusão


@dataclass
class WorkerEvent:
    """Estrutura de um evento emitido pelo Worker."""
    type: WorkerEventType
    timestamp: float = field(default_factory=lambda: __import__("time").time())
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Contratos de Configuração
# =============================================================================

class ModelConfig(Protocol):
    """Protocolo para configuração de modelo."""
    type: str
    deployment: Optional[str]
    env_vars: Optional[Dict[str, str]]


class ToolConfig(Protocol):
    """Protocolo para configuração de ferramenta."""
    id: str
    path: str
    description: Optional[str]


# =============================================================================
# LLM Provider (Abstração de Modelo)
# =============================================================================

class LLMProvider(ABC):
    """
    Contrato abstrato para provedores de modelo de linguagem.
    
    Implementações concretas devem fornecer lógica para criar clientes
    compatíveis com o agent_framework (ChatClient).
    
    Exemplos:
        - AzureOpenAIProvider: Para Azure OpenAI Service
        - OpenAIProvider: Para API OpenAI direta
        - OllamaProvider: Para modelos locais via Ollama
    """
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Retorna o tipo do provider."""
        ...
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Lista de modelos suportados (ou vazio se qualquer um)."""
        ...
    
    @abstractmethod
    def create_client(self, config: ModelConfig) -> Any:
        """
        Cria e retorna um cliente de chat compatível com agent_framework.
        
        Args:
            config: Configuração do modelo (type, deployment, env_vars)
            
        Returns:
            Instância de ChatClient (OpenAIChatClient, AzureOpenAIChatClient, etc.)
            
        Raises:
            ValueError: Se a configuração for inválida
            ConnectionError: Se não conseguir conectar ao provider
        """
        ...
    
    def validate_config(self, config: ModelConfig) -> bool:
        """
        Valida se a configuração é válida para este provider.
        
        Args:
            config: Configuração a validar
            
        Returns:
            True se válida, False caso contrário
        """
        return config.type == self.provider_type.value
    
    def health_check(self) -> bool:
        """
        Verifica se o provider está acessível.
        
        Returns:
            True se saudável, False caso contrário
        """
        return True  # Override em implementações concretas


# =============================================================================
# Tool Adapter (Abstração de Ferramenta)
# =============================================================================

class ToolAdapter(ABC):
    """
    Contrato abstrato para adaptadores de ferramentas.
    
    Permite diferentes tipos de ferramentas (Python local, HTTP, MCP)
    serem usadas de forma uniforme pelo worker.
    """
    
    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        """Retorna o tipo do adaptador."""
        ...
    
    @abstractmethod
    def load(self, config: ToolConfig) -> Callable:
        """
        Carrega e retorna a ferramenta como um callable.
        
        Args:
            config: Configuração da ferramenta
            
        Returns:
            Função callable que executa a ferramenta
            
        Raises:
            ImportError: Se não conseguir carregar a ferramenta
            ValueError: Se a configuração for inválida
        """
        ...
    
    def supports(self, config: ToolConfig) -> bool:
        """
        Verifica se este adaptador suporta a configuração dada.
        
        Args:
            config: Configuração da ferramenta
            
        Returns:
            True se suportado, False caso contrário
        """
        # Default: verifica pelo prefixo do path
        return True


# =============================================================================
# Workflow Strategy (Abstração de Orquestração)
# =============================================================================

class WorkflowStrategy(ABC):
    """
    Strategy para construção de workflows.
    
    Cada tipo de workflow (sequential, parallel, group_chat, etc.)
    tem sua própria estratégia de construção.
    """
    
    @property
    @abstractmethod
    def workflow_type(self) -> str:
        """Retorna o tipo de workflow que esta estratégia constrói."""
        ...
    
    @abstractmethod
    def build(
        self,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Constrói e retorna um Workflow.
        
        Args:
            agents: Lista de agentes participantes
            config: Configuração do workflow (WorkflowConfig)
            agent_factory: Factory para criar agentes adicionais se necessário
            
        Returns:
            Instância de Workflow do agent_framework
            
        Raises:
            ValueError: Se a configuração for inválida
            NotImplementedError: Se o tipo não for suportado
        """
        ...
    
    def validate(self, config: Any) -> List[str]:
        """
        Valida a configuração do workflow.
        
        Args:
            config: Configuração a validar
            
        Returns:
            Lista de erros (vazia se válido)
        """
        return []


# =============================================================================
# Event Bus (Sistema de Eventos)
# =============================================================================

EventHandler = Callable[[WorkerEvent], None]


class EventBus(ABC):
    """
    Sistema de eventos para observabilidade e hooks.
    
    Permite que componentes externos se inscrevam para receber
    notificações sobre eventos do worker.
    """
    
    @abstractmethod
    def subscribe(
        self,
        event_type: Union[WorkerEventType, List[WorkerEventType]],
        handler: EventHandler
    ) -> str:
        """
        Inscreve um handler para um ou mais tipos de evento.
        
        Args:
            event_type: Tipo(s) de evento para escutar
            handler: Função a ser chamada quando o evento ocorrer
            
        Returns:
            ID da inscrição (para cancelamento posterior)
        """
        ...
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Cancela uma inscrição.
        
        Args:
            subscription_id: ID retornado por subscribe()
            
        Returns:
            True se cancelado, False se não encontrado
        """
        ...
    
    @abstractmethod
    def emit(self, event: WorkerEvent) -> None:
        """
        Emite um evento para todos os handlers inscritos.
        
        Args:
            event: Evento a emitir
        """
        ...
    
    def emit_simple(
        self,
        event_type: WorkerEventType,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Helper para emitir eventos simples.
        
        Args:
            event_type: Tipo do evento
            data: Dados opcionais do evento
        """
        self.emit(WorkerEvent(type=event_type, data=data or {}))


# =============================================================================
# Memory Store (Stub para Persistência)
# =============================================================================

class MemoryStore(ABC):
    """
    Interface stub para persistência de contexto conversacional.
    
    Implementações futuras podem incluir:
    - Redis
    - CosmosDB
    - SQLite
    - In-Memory (para testes)
    """
    
    @abstractmethod
    async def save_context(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Salva o contexto de uma sessão.
        
        Args:
            session_id: Identificador único da sessão
            context: Dados do contexto a persistir
            
        Returns:
            True se salvo com sucesso
        """
        ...
    
    @abstractmethod
    async def load_context(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Carrega o contexto de uma sessão.
        
        Args:
            session_id: Identificador único da sessão
            
        Returns:
            Contexto salvo ou None se não existir
        """
        ...
    
    @abstractmethod
    async def delete_context(self, session_id: str) -> bool:
        """
        Remove o contexto de uma sessão.
        
        Args:
            session_id: Identificador único da sessão
            
        Returns:
            True se removido, False se não existia
        """
        ...
    
    async def exists(self, session_id: str) -> bool:
        """
        Verifica se existe contexto para uma sessão.
        
        Args:
            session_id: Identificador único da sessão
            
        Returns:
            True se existe
        """
        return await self.load_context(session_id) is not None


# =============================================================================
# Worker Contract (Interface Principal)
# =============================================================================

class Worker(ABC):
    """
    Interface principal do Worker SDK.
    
    Define o ciclo de vida completo: setup → run → teardown
    """
    
    @abstractmethod
    def setup(self) -> None:
        """
        Inicializa o worker e valida configurações.
        
        Raises:
            ValueError: Se a configuração for inválida
        """
        ...
    
    @abstractmethod
    async def run(self, input_message: str) -> Any:
        """
        Executa o workflow com a mensagem de entrada.
        
        Args:
            input_message: Mensagem inicial do usuário
            
        Returns:
            Resultado da execução
        """
        ...
    
    @abstractmethod
    def teardown(self) -> None:
        """
        Libera recursos e finaliza o worker.
        """
        ...
    
    @property
    @abstractmethod
    def event_bus(self) -> Optional[EventBus]:
        """Retorna o event bus para hooks externos."""
        ...


# =============================================================================
# Registry Protocol (Para Registries)
# =============================================================================

class Registry(ABC):
    """Interface genérica para registries."""
    
    @abstractmethod
    def register(self, key: str, item: T) -> None:
        """Registra um item."""
        ...
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Obtém um item registrado."""
        ...
    
    @abstractmethod
    def list_keys(self) -> List[str]:
        """Lista todas as chaves registradas."""
        ...
    
    def has(self, key: str) -> bool:
        """Verifica se uma chave existe."""
        return self.get(key) is not None
