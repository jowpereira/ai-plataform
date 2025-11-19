"""Tools module - Sistema moderno de registro e descoberta de ferramentas.

Arquitetura:
- Registry pattern para descoberta automática
- Decorators para metadados declarativos
- Factory para instanciação lazy
- Type-safe com Pydantic
"""

from tools.registry import ToolRegistry, tool
from tools.factory import ToolFactory
from tools.loader import ToolLoader

__all__ = [
    "ToolRegistry",
    "tool",
    "ToolFactory",
    "ToolLoader",
]
