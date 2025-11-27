"""
Adapters de Ferramentas.

Implementações concretas do ToolAdapter para diferentes tipos de ferramentas.
"""

from src.worker.tools.adapters.local import LocalToolAdapter
from src.worker.tools.adapters.http import HttpToolAdapter
from src.worker.tools.adapters.mcp import McpToolAdapter

__all__ = [
    "LocalToolAdapter",
    "HttpToolAdapter",
    "McpToolAdapter",
]

# Auto-registro dos adapters padrão
def register_default_adapters() -> None:
    """Registra os adapters padrão no AdapterRegistry."""
    from src.worker.tools.base import AdapterRegistry
    
    registry = AdapterRegistry()
    registry.register(LocalToolAdapter())
    registry.register(HttpToolAdapter())
    registry.register(McpToolAdapter())
