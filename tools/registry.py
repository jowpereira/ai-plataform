"""Tool Registry - Registro centralizado de ferramentas com descoberta automática.

Pattern: Registry + Decorator
- Autodiscovery via decorators
- Metadados declarativos (Pydantic)
- Validação de assinaturas
- Namespace isolation
"""

from typing import Callable, Any
from functools import wraps
from pydantic import BaseModel, Field
import inspect


class ToolMetadata(BaseModel):
    """Metadados de uma ferramenta registrada."""

    id: str = Field(..., description="Identificador único")
    name: str = Field(..., description="Nome display")
    description: str = Field("", description="Descrição da funcionalidade")
    category: str = Field("general", description="Categoria (weather, data, etc)")
    version: str = Field("1.0.0", description="Versão semântica")
    enabled: bool = Field(True, description="Se está ativa")
    tags: list[str] = Field(default_factory=list, description="Tags para busca")


class ToolRegistry:
    """Registry global de ferramentas.

    Uso:
        @tool(id="weather", description="Get weather data")
        def fetch_weather(city: str) -> dict:
            ...

        # Descoberta
        func = ToolRegistry.get("weather")
    """

    _registry: dict[str, tuple[Callable, ToolMetadata]] = {}

    @classmethod
    def register(
        cls,
        func: Callable,
        *,
        id: str | None = None,
        name: str | None = None,
        description: str = "",
        category: str = "general",
        version: str = "1.0.0",
        tags: list[str] | None = None,
    ) -> Callable:
        """Registra ferramenta com metadados.

        Args:
            func: Função Python
            id: ID único (default: func.__name__)
            name: Nome display (default: func.__name__)
            description: Descrição funcional
            category: Categoria temática
            version: Versão semântica
            tags: Tags para busca/filtro

        Returns:
            Função original (decorator transparente)
        """
        tool_id = id or func.__name__
        tool_name = name or func.__name__.replace("_", " ").title()

        # Validar assinatura
        sig = inspect.signature(func)
        if not sig.parameters:
            raise ValueError(f"Tool {tool_id} deve ter ao menos 1 parâmetro")

        metadata = ToolMetadata(
            id=tool_id,
            name=tool_name,
            description=description or func.__doc__ or "",
            category=category,
            version=version,
            enabled=True,
            tags=tags or [],
        )

        cls._registry[tool_id] = (func, metadata)
        return func

    @classmethod
    def get(cls, tool_id: str) -> Callable:
        """Obtém função registrada.

        Args:
            tool_id: ID da ferramenta

        Returns:
            Função Python

        Raises:
            KeyError: se tool não existe
        """
        if tool_id not in cls._registry:
            raise KeyError(f"Tool '{tool_id}' não registrada. Disponíveis: {list(cls._registry.keys())}")

        func, _ = cls._registry[tool_id]
        return func

    @classmethod
    def get_metadata(cls, tool_id: str) -> ToolMetadata:
        """Obtém metadados da ferramenta.

        Args:
            tool_id: ID da ferramenta

        Returns:
            ToolMetadata validado
        """
        if tool_id not in cls._registry:
            raise KeyError(f"Tool '{tool_id}' não registrada")

        _, metadata = cls._registry[tool_id]
        return metadata

    @classmethod
    def list_tools(
        cls,
        category: str | None = None,
        enabled_only: bool = True,
        tags: list[str] | None = None,
    ) -> list[ToolMetadata]:
        """Lista ferramentas com filtros.

        Args:
            category: Filtrar por categoria
            enabled_only: Apenas tools ativas
            tags: Filtrar por tags (OR logic)

        Returns:
            Lista de metadados
        """
        results = []
        for _, metadata in cls._registry.values():
            if enabled_only and not metadata.enabled:
                continue

            if category and metadata.category != category:
                continue

            if tags and not any(tag in metadata.tags for tag in tags):
                continue

            results.append(metadata)

        return results

    @classmethod
    def unregister(cls, tool_id: str) -> None:
        """Remove ferramenta do registry.

        Args:
            tool_id: ID da ferramenta
        """
        cls._registry.pop(tool_id, None)

    @classmethod
    def clear(cls) -> None:
        """Limpa todo o registry (útil para testes)."""
        cls._registry.clear()


def tool(
    *,
    id: str | None = None,
    name: str | None = None,
    description: str = "",
    category: str = "general",
    version: str = "1.0.0",
    tags: list[str] | None = None,
) -> Callable[[Callable], Callable]:
    """Decorator para registrar ferramenta.

    Args:
        id: ID único (default: function name)
        name: Nome display
        description: Descrição
        category: Categoria
        version: Versão
        tags: Tags de busca

    Exemplo:
        @tool(id="weather_api", category="weather", tags=["api", "external"])
        def fetch_weather(city: str) -> dict:
            '''Obtém dados meteorológicos.'''
            return {"city": city, "temp": 25}
    """

    def decorator(func: Callable) -> Callable:
        ToolRegistry.register(
            func,
            id=id,
            name=name,
            description=description,
            category=category,
            version=version,
            tags=tags,
        )
        return func

    return decorator
