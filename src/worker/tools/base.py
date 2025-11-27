"""
Classe base abstrata para Adapters de Ferramentas.

Define o contrato que todos os adapters devem implementar.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type
import logging

from src.worker.tools.models import (
    ToolDefinition,
    ToolResult,
    ToolExecutionContext,
    ToolType,
)

logger = logging.getLogger("worker.tools")


class ToolAdapter(ABC):
    """
    Classe base abstrata para adapters de ferramentas.
    
    Cada adapter é responsável por:
    1. Validar a definição da ferramenta para seu tipo
    2. Executar a ferramenta com os argumentos fornecidos
    3. Retornar resultado padronizado (ToolResult)
    
    Exemplo de implementação:
        class LocalToolAdapter(ToolAdapter):
            tool_type = ToolType.LOCAL
            
            async def execute(self, definition, arguments, context):
                func = self._load_function(definition.source)
                result = await func(**arguments)
                return ToolResult.success_result(definition.name, result)
    """
    
    # Tipo de ferramenta que este adapter suporta
    tool_type: ToolType
    
    def __init__(self):
        """Inicializa o adapter."""
        self._cache: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(
        self,
        definition: ToolDefinition,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """
        Executa a ferramenta com os argumentos fornecidos.
        
        Args:
            definition: Definição da ferramenta
            arguments: Argumentos para execução
            context: Contexto de execução opcional
            
        Returns:
            ToolResult com o resultado da execução
        """
        pass
    
    @abstractmethod
    def validate(self, definition: ToolDefinition) -> List[str]:
        """
        Valida a definição da ferramenta.
        
        Args:
            definition: Definição a ser validada
            
        Returns:
            Lista de erros de validação (vazia se válido)
        """
        pass
    
    def get_callable(self, definition: ToolDefinition) -> Callable:
        """
        Retorna um callable wrapper para a ferramenta.
        
        Usado para integração com o Agent Framework que espera funções.
        
        Args:
            definition: Definição da ferramenta
            
        Returns:
            Função callable que encapsula a execução
        """
        import asyncio
        # Import local para evitar ciclo
        from src.worker.events import get_event_bus, WorkerEventType
        
        async def async_wrapper(**kwargs) -> Any:
            bus = get_event_bus()
            bus.emit_simple(
                WorkerEventType.TOOL_CALL_START,
                {"tool": definition.name, "arguments": kwargs}
            )
            
            try:
                result = await self.execute(definition, kwargs)
                
                if result.success:
                    bus.emit_simple(
                        WorkerEventType.TOOL_CALL_COMPLETE,
                        {"tool": definition.name, "result": result.result}
                    )
                    return result.result
                else:
                    bus.emit_simple(
                        WorkerEventType.TOOL_CALL_ERROR,
                        {"tool": definition.name, "error": result.error}
                    )
                    raise RuntimeError(f"Tool execution failed: {result.error}")
            except Exception as e:
                bus.emit_simple(
                    WorkerEventType.TOOL_CALL_ERROR,
                    {"tool": definition.name, "error": str(e)}
                )
                raise e
        
        def sync_wrapper(**kwargs) -> Any:
            """Wrapper síncrono para ambientes que não suportam async."""
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Já está em um loop async, usar run_coroutine_threadsafe
                import concurrent.futures
                future = asyncio.run_coroutine_threadsafe(
                    async_wrapper(**kwargs),
                    loop
                )
                return future.result()
            else:
                return asyncio.run(async_wrapper(**kwargs))
        
        # Preservar metadata para o Agent Framework
        sync_wrapper.__name__ = definition.name
        sync_wrapper.__doc__ = definition.description
        
        return sync_wrapper
    
    def clear_cache(self) -> None:
        """Limpa o cache interno do adapter."""
        self._cache.clear()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.tool_type})"


class AdapterRegistry:
    """
    Registry para adapters de ferramentas.
    
    Gerencia os adapters disponíveis por tipo de ferramenta.
    """
    
    _instance: Optional["AdapterRegistry"] = None
    _adapters: Dict[ToolType, ToolAdapter]
    
    def __new__(cls) -> "AdapterRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._adapters = {}
        return cls._instance
    
    def register(self, adapter: ToolAdapter) -> None:
        """
        Registra um adapter.
        
        Args:
            adapter: Instância do adapter a registrar
        """
        self._adapters[adapter.tool_type] = adapter
        logger.debug(f"Adapter registrado: {adapter.tool_type} -> {adapter.__class__.__name__}")
    
    def get(self, tool_type: ToolType) -> Optional[ToolAdapter]:
        """
        Obtém um adapter pelo tipo.
        
        Args:
            tool_type: Tipo de ferramenta
            
        Returns:
            Adapter correspondente ou None
        """
        return self._adapters.get(tool_type)
    
    def get_or_raise(self, tool_type: ToolType) -> ToolAdapter:
        """
        Obtém um adapter ou levanta exceção.
        
        Args:
            tool_type: Tipo de ferramenta
            
        Returns:
            Adapter correspondente
            
        Raises:
            ValueError: Se adapter não encontrado
        """
        adapter = self.get(tool_type)
        if adapter is None:
            raise ValueError(f"Nenhum adapter registrado para tipo: {tool_type}")
        return adapter
    
    def list_types(self) -> List[ToolType]:
        """Lista tipos de ferramentas com adapters registrados."""
        return list(self._adapters.keys())
    
    @classmethod
    def reset(cls) -> None:
        """Reset do singleton (para testes)."""
        cls._instance = None
