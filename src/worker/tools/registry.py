"""
Registry Central de Ferramentas.

Gerencia o registro, descoberta e execução de ferramentas.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Set, Type

from src.worker.tools.base import ToolAdapter, AdapterRegistry
from src.worker.tools.models import (
    ToolDefinition,
    ToolResult,
    ToolExecutionContext,
    ToolType,
)

logger = logging.getLogger("worker.tools.registry")


class ToolRegistry:
    """
    Registry centralizado para gerenciamento de ferramentas.
    
    Responsabilidades:
    1. Registrar definições de ferramentas
    2. Validar ferramentas contra seus adapters
    3. Fornecer callables para integração com Agent Framework
    4. Executar ferramentas via adapter apropriado
    
    Exemplo:
        registry = ToolRegistry()
        
        # Registrar ferramenta
        registry.register(ToolDefinition(
            name="calcular",
            description="Calcula valores",
            type=ToolType.LOCAL,
            source="math_tools.calcular"
        ))
        
        # Obter callable para Agent Framework
        calc_func = registry.get_callable("calcular")
        
        # Ou executar diretamente
        result = await registry.execute("calcular", {"x": 10})
    """
    
    _instance: Optional["ToolRegistry"] = None
    
    def __new__(cls) -> "ToolRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, ToolDefinition] = {}
            cls._instance._adapter_registry = AdapterRegistry()
            cls._instance._initialized = False
        return cls._instance
    
    def _ensure_initialized(self) -> None:
        """Garante que os adapters padrão estão registrados."""
        if not self._initialized:
            from src.worker.tools.adapters import register_default_adapters
            register_default_adapters()
            self._initialized = True
    
    def register(self, definition: ToolDefinition) -> None:
        """
        Registra uma ferramenta.
        
        Args:
            definition: Definição da ferramenta
            
        Raises:
            ValueError: Se a ferramenta já existe ou é inválida
        """
        self._ensure_initialized()
        
        if definition.name in self._tools:
            raise ValueError(f"Ferramenta já registrada: {definition.name}")
        
        # Validar via adapter
        adapter = self._adapter_registry.get(definition.type)
        if adapter:
            errors = adapter.validate(definition)
            if errors:
                raise ValueError(
                    f"Ferramenta '{definition.name}' inválida: {errors}"
                )
        
        self._tools[definition.name] = definition
        logger.info(f"Ferramenta registrada: {definition.name} ({definition.type})")
    
    def register_many(self, definitions: List[ToolDefinition]) -> Dict[str, str]:
        """
        Registra múltiplas ferramentas.
        
        Returns:
            Dict com nome -> resultado ("ok" ou mensagem de erro)
        """
        results = {}
        for definition in definitions:
            try:
                self.register(definition)
                results[definition.name] = "ok"
            except Exception as e:
                results[definition.name] = str(e)
                logger.warning(f"Falha ao registrar {definition.name}: {e}")
        return results
    
    def unregister(self, name: str) -> bool:
        """
        Remove uma ferramenta do registry.
        
        Returns:
            True se removida, False se não existia
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Ferramenta removida: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Obtém definição de ferramenta pelo nome."""
        return self._tools.get(name)
    
    def get_or_raise(self, name: str) -> ToolDefinition:
        """Obtém definição ou levanta exceção."""
        definition = self.get(name)
        if definition is None:
            raise KeyError(f"Ferramenta não encontrada: {name}")
        return definition
    
    def exists(self, name: str) -> bool:
        """Verifica se ferramenta existe."""
        return name in self._tools
    
    def list_tools(
        self,
        tool_type: Optional[ToolType] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[ToolDefinition]:
        """
        Lista ferramentas com filtros opcionais.
        
        Args:
            tool_type: Filtrar por tipo
            tags: Filtrar por tags (OR)
            enabled_only: Apenas ferramentas habilitadas
            
        Returns:
            Lista de definições que correspondem aos filtros
        """
        tools = list(self._tools.values())
        
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        
        if tool_type:
            tools = [t for t in tools if t.type == tool_type]
        
        if tags:
            tag_set = set(tags)
            tools = [t for t in tools if tag_set.intersection(t.tags)]
        
        return tools
    
    def get_callable(self, name: str) -> Callable:
        """
        Obtém um callable wrapper para a ferramenta.
        
        Usado para integração com Agent Framework.
        
        Args:
            name: Nome da ferramenta
            
        Returns:
            Função callable
            
        Raises:
            KeyError: Se ferramenta não encontrada
            ValueError: Se adapter não disponível
        """
        self._ensure_initialized()
        
        definition = self.get_or_raise(name)
        adapter = self._adapter_registry.get_or_raise(definition.type)
        
        return adapter.get_callable(definition)
    
    def get_callables(
        self,
        names: Optional[List[str]] = None,
        tool_type: Optional[ToolType] = None,
    ) -> Dict[str, Callable]:
        """
        Obtém múltiplos callables.
        
        Args:
            names: Lista de nomes (se None, todas)
            tool_type: Filtrar por tipo
            
        Returns:
            Dict nome -> callable
        """
        if names:
            tools = [self.get_or_raise(n) for n in names]
        else:
            tools = self.list_tools(tool_type=tool_type)
        
        return {t.name: self.get_callable(t.name) for t in tools}
    
    async def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """
        Executa uma ferramenta.
        
        Args:
            name: Nome da ferramenta
            arguments: Argumentos para execução
            context: Contexto de execução opcional
            
        Returns:
            ToolResult com o resultado
        """
        self._ensure_initialized()
        
        definition = self.get_or_raise(name)
        
        if not definition.enabled:
            return ToolResult.error_result(
                tool_name=name,
                error=f"Ferramenta '{name}' está desabilitada"
            )
        
        adapter = self._adapter_registry.get_or_raise(definition.type)
        
        return await adapter.execute(definition, arguments, context)
    
    def to_openai_functions(
        self,
        names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Converte ferramentas para formato OpenAI functions.
        
        Args:
            names: Lista de nomes (se None, todas habilitadas)
            
        Returns:
            Lista de definições no formato OpenAI
        """
        if names:
            tools = [self.get_or_raise(n) for n in names]
        else:
            tools = self.list_tools(enabled_only=True)
        
        return [t.to_openai_function() for t in tools]
    
    def clear(self) -> None:
        """Remove todas as ferramentas."""
        self._tools.clear()
        logger.info("Registry de ferramentas limpo")
    
    @classmethod
    def reset(cls) -> None:
        """Reset do singleton (para testes)."""
        if cls._instance:
            cls._instance._tools.clear()
            cls._instance._initialized = False
        cls._instance = None
        AdapterRegistry.reset()
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
    
    def __repr__(self) -> str:
        return f"ToolRegistry({len(self._tools)} tools)"


# Funções de conveniência para uso global
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Obtém o registry global de ferramentas."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(definition: ToolDefinition) -> None:
    """Registra ferramenta no registry global."""
    get_tool_registry().register(definition)


async def execute_tool(
    name: str,
    arguments: Dict[str, Any],
    context: Optional[ToolExecutionContext] = None,
) -> ToolResult:
    """Executa ferramenta via registry global."""
    return await get_tool_registry().execute(name, arguments, context)
