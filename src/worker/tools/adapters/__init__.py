"""
Adapters de Ferramentas.

Implementações concretas do ToolAdapter para diferentes tipos de ferramentas.
"""

from src.worker.tools.adapters.local import LocalToolAdapter
from src.worker.tools.adapters.hosted import (
    HostedToolAdapter,
    create_code_interpreter_tool,
    create_web_search_tool,
    create_file_search_tool,
)

__all__ = [
    "LocalToolAdapter",
    "HostedToolAdapter",
    # Helpers
    "create_code_interpreter_tool",
    "create_web_search_tool",
    "create_file_search_tool",
]

# Auto-registro dos adapters padrão
def register_default_adapters() -> None:
    """Registra os adapters padrão no AdapterRegistry."""
    from src.worker.tools.base import AdapterRegistry
    
    registry = AdapterRegistry()
    registry.register(LocalToolAdapter())
    registry.register(HostedToolAdapter())
