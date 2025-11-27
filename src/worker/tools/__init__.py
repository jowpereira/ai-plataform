"""
Sistema de Ferramentas do Worker SDK.

Este módulo fornece uma arquitetura extensível para ferramentas:
- ToolRegistry: Registry centralizado para descoberta e execução
- Adapters: LocalToolAdapter, HttpToolAdapter, McpToolAdapter
- Validação: Schema validation com Pydantic

Exemplo de uso:
    from src.worker.tools import ToolRegistry, ToolDefinition

    # Registrar ferramenta local
    registry = ToolRegistry()
    registry.register(ToolDefinition(
        name="calcular_risco",
        type="local",
        source="ferramentas.risco.calcular",
        description="Calcula score de risco"
    ))

    # Executar ferramenta
    result = await registry.execute("calcular_risco", {"valor": 1000})

Versão: 0.8.2
"""

from src.worker.tools.models import (
    ToolDefinition,
    ToolParameter,
    ToolResult,
    RetryPolicy,
    ToolExecutionContext,
    ToolType,
)
from src.worker.tools.base import ToolAdapter
from src.worker.tools.registry import ToolRegistry
from src.worker.tools.adapters import (
    LocalToolAdapter,
    HttpToolAdapter,
    McpToolAdapter,
)

__all__ = [
    # Models
    "ToolDefinition",
    "ToolParameter",
    "ToolResult",
    "RetryPolicy",
    "ToolExecutionContext",
    "ToolType",
    # Base
    "ToolAdapter",
    # Registry
    "ToolRegistry",
    # Adapters
    "LocalToolAdapter",
    "HttpToolAdapter",
    "McpToolAdapter",
]
