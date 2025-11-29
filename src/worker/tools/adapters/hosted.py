"""
Adapter para Hosted Tools do Microsoft Agent Framework.

Integração com ferramentas nativas do framework:
- HostedCodeInterpreterTool: Execução segura de código Python
- HostedWebSearchTool: Busca na web (Bing/Google)
- HostedFileSearchTool: RAG em arquivos/vetores
- HostedMCPTool: Integração com MCP Servers

Versão: 0.9.0
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from src.worker.tools.base import ToolAdapter
from src.worker.tools.models import (
    ToolDefinition,
    ToolResult,
    ToolExecutionContext,
    ToolType,
    HostedToolType,
)

logger = logging.getLogger("worker.tools.hosted")


class HostedToolAdapter(ToolAdapter):
    """
    Adapter para Hosted Tools do Microsoft Agent Framework.
    
    Hosted Tools são ferramentas nativas do framework que executam
    em ambiente gerenciado (Azure AI, OpenAI, etc.).
    
    Tipos suportados:
    - code_interpreter: Executa código Python em sandbox
    - web_search: Busca na web via Bing/Google
    - file_search: RAG sobre arquivos em vector store
    - mcp: Conexão com servidores MCP
    """
    
    tool_type = ToolType.HOSTED
    
    def __init__(self):
        super().__init__()
        self._tool_instances: Dict[str, Any] = {}
        self._available_types = self._check_available_types()
    
    def _check_available_types(self) -> Dict[str, bool]:
        """Verifica quais Hosted Tools estão disponíveis."""
        available = {}
        
        # Tentar importar cada tipo
        try:
            from agent_framework import HostedCodeInterpreterTool
            available["code_interpreter"] = True
        except ImportError:
            available["code_interpreter"] = False
            logger.debug("HostedCodeInterpreterTool não disponível")
        
        try:
            from agent_framework import HostedWebSearchTool
            available["web_search"] = True
        except ImportError:
            available["web_search"] = False
            logger.debug("HostedWebSearchTool não disponível")
        
        try:
            from agent_framework import HostedFileSearchTool
            available["file_search"] = True
        except ImportError:
            available["file_search"] = False
            logger.debug("HostedFileSearchTool não disponível")
        
        try:
            from agent_framework import HostedMCPTool
            available["mcp"] = True
        except ImportError:
            available["mcp"] = False
            logger.debug("HostedMCPTool não disponível")
        
        return available
    
    def _get_hosted_config(self, definition: ToolDefinition) -> Dict[str, Any]:
        """Obtém configuração do Hosted Tool com defaults."""
        config = {
            "hosted_type": "code_interpreter",
            "timeout": definition.timeout,
        }
        if definition.hosted_config:
            config.update(definition.hosted_config)
        return config
    
    def _create_tool_instance(
        self,
        hosted_type: str,
        config: Dict[str, Any]
    ) -> Any:
        """
        Cria instância do Hosted Tool.
        
        Args:
            hosted_type: Tipo do hosted tool
            config: Configuração específica
            
        Returns:
            Instância do tool
        """
        if not self._available_types.get(hosted_type, False):
            raise ImportError(
                f"HostedTool '{hosted_type}' não está disponível. "
                "Verifique se o pacote agent-framework está instalado corretamente."
            )
        
        if hosted_type == "code_interpreter":
            from agent_framework import HostedCodeInterpreterTool
            # Passar timeout se definido
            kwargs = {}
            if "sandbox_timeout" in config:
                kwargs["timeout"] = config["sandbox_timeout"]
            elif "timeout" in config:
                kwargs["timeout"] = config["timeout"]
                
            return HostedCodeInterpreterTool(**kwargs)
        
        elif hosted_type == "web_search":
            from agent_framework import HostedWebSearchTool
            kwargs = {}
            if "search_provider" in config:
                kwargs["search_provider"] = config["search_provider"]
            if "max_results" in config:
                kwargs["max_results"] = config["max_results"]
                
            return HostedWebSearchTool(**kwargs)
        
        elif hosted_type == "file_search":
            from agent_framework import HostedFileSearchTool
            kwargs = {}
            if "vector_store_id" in config:
                kwargs["vector_store_id"] = config["vector_store_id"]
            if "max_results" in config:
                kwargs["max_results"] = config["max_results"]
                
            return HostedFileSearchTool(**kwargs)
        
        elif hosted_type == "mcp":
            from agent_framework import HostedMCPTool
            server_url = config.get("server_url")
            if not server_url:
                raise ValueError("mcp requer 'server_url' na configuração")
            return HostedMCPTool(
                server_url=server_url,
                tool_name=config.get("tool_name"),
                approval_mode=config.get("approval_mode", "never"),
            )
        
        else:
            raise ValueError(f"Tipo de Hosted Tool desconhecido: {hosted_type}")
    
    def get_callable(self, definition: ToolDefinition) -> Any:
        """
        Retorna a instância do Hosted Tool.
        
        Nota: Hosted Tools não são necessariamente callables, mas objetos
        que o Agent Framework entende. O tipo de retorno é Any para
        acomodar isso.
        """
        config = self._get_hosted_config(definition)
        hosted_type = config.get("hosted_type", "code_interpreter")
        
        # Cache de instâncias
        cache_key = f"{definition.name}:{hosted_type}"
        if cache_key not in self._tool_instances:
            self._tool_instances[cache_key] = self._create_tool_instance(
                hosted_type, config
            )
        
        # Retornar a instância diretamente
        # O Agent Framework saberá como usar se for um HostedTool válido
        return self._tool_instances[cache_key]
    
    async def execute(
        self,
        definition: ToolDefinition,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """
        Executa Hosted Tool.
        
        Nota: A maioria dos Hosted Tools (Code Interpreter, Web Search)
        são executados pelo backend do Agent Framework durante a inferência,
        não localmente.
        """
        start_time = time.time()
        
        try:
            config = self._get_hosted_config(definition)
            hosted_type = config.get("hosted_type", "code_interpreter")
            
            # Obter ou criar instância
            cache_key = f"{definition.name}:{hosted_type}"
            if cache_key not in self._tool_instances:
                self._tool_instances[cache_key] = self._create_tool_instance(
                    hosted_type, config
                )
            
            tool_instance = self._tool_instances[cache_key]
            
            # Verificar se é executável localmente
            if hasattr(tool_instance, "execute"):
                # Se tiver método execute, tentar chamar
                timeout = config.get("timeout", definition.timeout)
                try:
                    result = await asyncio.wait_for(
                        tool_instance.execute(**arguments),
                        timeout=timeout
                    )
                    
                    execution_time = time.time() - start_time
                    return ToolResult.success_result(
                        tool_name=definition.name,
                        result=result,
                        execution_time=execution_time,
                    )
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Timeout executando {definition.name}")
            
            # Se não for executável localmente (comum para Hosted Tools)
            raise NotImplementedError(
                f"Hosted Tool '{definition.name}' ({hosted_type}) não suporta execução local direta via worker. "
                "Esta ferramenta deve ser usada apenas dentro do contexto de um Agente."
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro ao executar Hosted Tool '{definition.name}': {e}")
            
            return ToolResult.error_result(
                tool_name=definition.name,
                error=str(e),
                execution_time=execution_time,
            )
    
    def validate(self, definition: ToolDefinition) -> List[str]:
        """Valida a definição de Hosted Tool."""
        errors = []
        
        # Verificar source
        source = definition.source
        if not source.startswith("hosted://"):
            errors.append(
                f"Source deve começar com 'hosted://' para Hosted Tools: {source}"
            )
        
        # Verificar configuração
        config = definition.hosted_config or {}
        hosted_type = config.get("hosted_type")
        
        if not hosted_type:
            # Tentar extrair do source
            if source.startswith("hosted://"):
                hosted_type = source.replace("hosted://", "")
        
        valid_types = ["code_interpreter", "web_search", "file_search", "mcp"]
        if hosted_type and hosted_type not in valid_types:
            errors.append(
                f"Tipo de Hosted Tool inválido: {hosted_type}. "
                f"Válidos: {valid_types}"
            )
        
        # Verificar disponibilidade
        if hosted_type and not self._available_types.get(hosted_type, False):
            errors.append(
                f"Hosted Tool '{hosted_type}' não está disponível. "
                "Verifique a instalação do agent-framework."
            )
        
        # Validações específicas
        # file_search pode não requerer vector_store_id se usar inputs dinâmicos?
        # Mas por segurança vamos manter o aviso se não tiver nada
        if hosted_type == "file_search" and not config.get("vector_store_id") and not config.get("inputs"):
             # Relaxar validação pois pode ser configurado de outra forma
             pass
        
        if hosted_type == "mcp" and not config.get("server_url"):
            errors.append("mcp requer 'server_url' em hosted_config")
        
        return errors
    
    def list_available_types(self) -> Dict[str, bool]:
        """Lista os tipos de Hosted Tools disponíveis."""
        return self._available_types.copy()
    
    async def close(self) -> None:
        """Fecha todos os Hosted Tools."""
        for key, tool in self._tool_instances.items():
            try:
                if hasattr(tool, "close"):
                    await tool.close()
                elif hasattr(tool, "shutdown"):
                    await tool.shutdown()
            except Exception as e:
                logger.warning(f"Erro ao fechar Hosted Tool {key}: {e}")
        self._tool_instances.clear()


# =============================================================================
# Helpers para criação rápida
# =============================================================================

def create_code_interpreter_tool(
    name: str = "code_interpreter",
    description: str = "Executa código Python em ambiente sandbox seguro",
    timeout: float = 60.0,
) -> ToolDefinition:
    """
    Factory para criar definição de Code Interpreter.
    
    Exemplo:
        tool_def = create_code_interpreter_tool()
        registry.register(tool_def)
    """
    return ToolDefinition(
        name=name,
        description=description,
        type=ToolType.HOSTED,
        source="hosted://code_interpreter",
        timeout=timeout,
        hosted_config={
            "hosted_type": "code_interpreter",
            "sandbox_timeout": timeout,
        },
        tags=["hosted", "code", "sandbox"],
    )


def create_web_search_tool(
    name: str = "web_search",
    description: str = "Busca informações na web",
    search_provider: str = "bing",
    max_results: int = 10,
) -> ToolDefinition:
    """
    Factory para criar definição de Web Search.
    
    Exemplo:
        tool_def = create_web_search_tool(max_results=5)
        registry.register(tool_def)
    """
    return ToolDefinition(
        name=name,
        description=description,
        type=ToolType.HOSTED,
        source="hosted://web_search",
        hosted_config={
            "hosted_type": "web_search",
            "search_provider": search_provider,
            "max_results": max_results,
        },
        tags=["hosted", "search", "web"],
    )


def create_file_search_tool(
    name: str = "file_search",
    description: str = "Busca em documentos usando RAG",
    vector_store_id: str = "",
    max_results: int = 5,
) -> ToolDefinition:
    """
    Factory para criar definição de File Search.
    
    Args:
        vector_store_id: ID do vector store (obrigatório)
        
    Exemplo:
        tool_def = create_file_search_tool(vector_store_id="vs_abc123")
        registry.register(tool_def)
    """
    if not vector_store_id:
        raise ValueError("vector_store_id é obrigatório para file_search")
    
    return ToolDefinition(
        name=name,
        description=description,
        type=ToolType.HOSTED,
        source="hosted://file_search",
        hosted_config={
            "hosted_type": "file_search",
            "vector_store_id": vector_store_id,
            "max_results": max_results,
        },
        tags=["hosted", "search", "rag", "documents"],
    )
