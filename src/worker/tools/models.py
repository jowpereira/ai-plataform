"""
Modelos Pydantic para o Sistema de Ferramentas.

Define as estruturas de dados para definição, execução e resultado de ferramentas.

Versão: 0.9.0 - Adicionado suporte a Hosted Tools e ApprovalMode
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator
import time


class ToolType(str, Enum):
    """Tipos de ferramentas suportadas."""
    LOCAL = "local"      # Função Python local via importlib
    HOSTED = "hosted"    # Hosted Tools do Agent Framework
    CUSTOM = "custom"    # Adapter customizado


class ApprovalMode(str, Enum):
    """Modos de aprovação para ferramentas com human-in-the-loop."""
    NEVER = "never"                    # Nunca requer aprovação
    ALWAYS = "always_require"          # Sempre requer aprovação
    ON_FIRST = "on_first_invocation"   # Apenas na primeira chamada
    CONDITIONAL = "conditional"         # Baseado em condição customizada


class HostedToolType(str, Enum):
    """Tipos de Hosted Tools do Agent Framework."""
    CODE_INTERPRETER = "code_interpreter"  # HostedCodeInterpreterTool
    WEB_SEARCH = "web_search"              # HostedWebSearchTool
    FILE_SEARCH = "file_search"            # HostedFileSearchTool
    MCP = "mcp"                            # HostedMCPTool


class RetryPolicy(BaseModel):
    """Política de retry para execução de ferramentas."""
    
    max_attempts: int = Field(default=3, ge=1, le=10, description="Número máximo de tentativas")
    initial_delay: float = Field(default=1.0, ge=0.1, description="Delay inicial em segundos")
    max_delay: float = Field(default=30.0, ge=1.0, description="Delay máximo em segundos")
    exponential_base: float = Field(default=2.0, ge=1.0, description="Base para backoff exponencial")
    retryable_errors: List[str] = Field(
        default_factory=lambda: ["TimeoutError", "ConnectionError", "HTTPError"],
        description="Lista de erros que devem ser retentados"
    )
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcula o delay para uma tentativa específica."""
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        return min(delay, self.max_delay)


class ToolParameter(BaseModel):
    """Definição de um parâmetro de ferramenta."""
    
    name: str = Field(..., description="Nome do parâmetro")
    type: str = Field(default="string", description="Tipo JSON Schema (string, number, boolean, object, array)")
    description: str = Field(default="", description="Descrição do parâmetro")
    required: bool = Field(default=False, description="Se o parâmetro é obrigatório")
    default: Optional[Any] = Field(default=None, description="Valor padrão")
    enum: Optional[List[Any]] = Field(default=None, description="Valores permitidos")
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Converte para formato JSON Schema."""
        schema: Dict[str, Any] = {"type": self.type}
        if self.description:
            schema["description"] = self.description
        if self.default is not None:
            schema["default"] = self.default
        if self.enum:
            schema["enum"] = self.enum
        return schema


class ToolDefinition(BaseModel):
    """Definição completa de uma ferramenta."""
    
    name: str = Field(..., min_length=1, max_length=128, description="Nome único da ferramenta")
    description: str = Field(..., min_length=1, description="Descrição para o LLM")
    type: ToolType = Field(default=ToolType.LOCAL, description="Tipo de ferramenta")
    source: str = Field(..., description="Fonte: dotted path, URL, ou MCP server")
    
    # Parâmetros
    parameters: List[ToolParameter] = Field(default_factory=list, description="Lista de parâmetros")
    
    # Configuração
    timeout: float = Field(default=30.0, ge=1.0, description="Timeout em segundos")
    retry_policy: Optional[RetryPolicy] = Field(default=None, description="Política de retry")
    
    # Approval Mode (Human-in-the-loop)
    approval_mode: ApprovalMode = Field(
        default=ApprovalMode.NEVER,
        description="Modo de aprovação humana para esta ferramenta"
    )
    approval_message: Optional[str] = Field(
        default=None,
        description="Mensagem customizada para solicitação de aprovação"
    )
    
    # Metadados
    tags: List[str] = Field(default_factory=list, description="Tags para categorização")
    version: str = Field(default="1.0.0", description="Versão da ferramenta")
    enabled: bool = Field(default=True, description="Se a ferramenta está habilitada")
    
    # Limites de invocação
    max_invocations: Optional[int] = Field(
        default=None,
        ge=1,
        description="Número máximo de invocações permitidas por sessão"
    )
    max_invocation_exceptions: Optional[int] = Field(
        default=None,
        ge=1,
        description="Número máximo de exceções antes de desabilitar"
    )
    
    # Configurações específicas por tipo
    http_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configurações HTTP (method, headers, auth)"
    )
    mcp_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configurações MCP (server_url, transport)"
    )
    hosted_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configurações para Hosted Tools (hosted_type, vector_store_id, etc.)"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que o nome é um identificador válido."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Nome da ferramenta deve ser alfanumérico: {v}")
        return v
    
    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str, info) -> str:
        """Valida source baseado no tipo."""
        # A validação completa é feita no adapter específico
        if not v:
            raise ValueError("Source não pode ser vazio")
        return v
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Converte para formato de function do OpenAI."""
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
    
    def to_agent_framework_tool(self) -> Dict[str, Any]:
        """Converte para formato do Agent Framework."""
        # O Agent Framework usa um formato similar ao OpenAI
        return self.to_openai_function()


class ToolResult(BaseModel):
    """Resultado da execução de uma ferramenta."""
    
    tool_name: str = Field(..., description="Nome da ferramenta executada")
    success: bool = Field(..., description="Se a execução foi bem sucedida")
    result: Optional[Any] = Field(default=None, description="Resultado da execução")
    error: Optional[str] = Field(default=None, description="Mensagem de erro se falhou")
    
    # Métricas
    execution_time: float = Field(default=0.0, description="Tempo de execução em segundos")
    attempts: int = Field(default=1, description="Número de tentativas realizadas")
    
    # Metadados
    timestamp: float = Field(default_factory=time.time, description="Timestamp da execução")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")
    
    @classmethod
    def success_result(
        cls,
        tool_name: str,
        result: Any,
        execution_time: float = 0.0,
        attempts: int = 1,
    ) -> "ToolResult":
        """Factory para resultado de sucesso."""
        return cls(
            tool_name=tool_name,
            success=True,
            result=result,
            execution_time=execution_time,
            attempts=attempts,
        )
    
    @classmethod
    def error_result(
        cls,
        tool_name: str,
        error: str,
        execution_time: float = 0.0,
        attempts: int = 1,
    ) -> "ToolResult":
        """Factory para resultado de erro."""
        return cls(
            tool_name=tool_name,
            success=False,
            error=error,
            execution_time=execution_time,
            attempts=attempts,
        )


class ToolExecutionContext(BaseModel):
    """Contexto de execução de uma ferramenta."""
    
    session_id: Optional[str] = Field(default=None, description="ID da sessão")
    user_id: Optional[str] = Field(default=None, description="ID do usuário")
    workflow_id: Optional[str] = Field(default=None, description="ID do workflow")
    agent_name: Optional[str] = Field(default=None, description="Nome do agente")
    
    # Headers e auth para HTTP
    headers: Dict[str, str] = Field(default_factory=dict, description="Headers HTTP")
    auth_token: Optional[str] = Field(default=None, description="Token de autenticação")
    
    # Variáveis de ambiente
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Variáveis de ambiente")
    
    # Tracing
    trace_id: Optional[str] = Field(default=None, description="ID de trace")
    span_id: Optional[str] = Field(default=None, description="ID do span")
