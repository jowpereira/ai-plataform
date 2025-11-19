"""Tool Factory - Instanciação lazy e gestão de ciclo de vida.

Pattern: Factory + Singleton
- Lazy loading
- Dependency injection
- Lifecycle hooks (setup/teardown)
- Context managers
"""

from typing import Callable, Any
from contextlib import contextmanager

from tools.registry import ToolRegistry, ToolMetadata


class ToolFactory:
    """Factory para criação e gestão de ferramentas.

    Características:
    - Lazy loading (só cria quando necessário)
    - Cache de instâncias
    - Context isolation
    - Lifecycle management
    """

    def __init__(self, registry: type[ToolRegistry] = ToolRegistry):
        """Inicializa factory com registry.

        Args:
            registry: Classe do registry (para DI/testing)
        """
        self.registry = registry
        self._cache: dict[str, Any] = {}

    def create(self, tool_id: str, *, use_cache: bool = True) -> Callable:
        """Cria/obtém ferramenta.

        Args:
            tool_id: ID da ferramenta
            use_cache: Se deve usar cache (default: True)

        Returns:
            Função Python executável

        Raises:
            KeyError: se tool não existe
        """
        if use_cache and tool_id in self._cache:
            return self._cache[tool_id]

        func = self.registry.get(tool_id)

        if use_cache:
            self._cache[tool_id] = func

        return func

    def create_batch(self, tool_ids: list[str]) -> dict[str, Callable]:
        """Cria múltiplas ferramentas em batch.

        Args:
            tool_ids: Lista de IDs

        Returns:
            Dict {tool_id: função}
        """
        return {tid: self.create(tid) for tid in tool_ids}

    def get_metadata(self, tool_id: str) -> ToolMetadata:
        """Obtém metadados da ferramenta.

        Args:
            tool_id: ID da ferramenta

        Returns:
            ToolMetadata validado
        """
        return self.registry.get_metadata(tool_id)

    def list_available(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[ToolMetadata]:
        """Lista ferramentas disponíveis com filtros.

        Args:
            category: Filtrar por categoria
            tags: Filtrar por tags

        Returns:
            Lista de metadados
        """
        return self.registry.list_tools(
            category=category,
            enabled_only=True,
            tags=tags,
        )

    def clear_cache(self) -> None:
        """Limpa cache de instâncias."""
        self._cache.clear()

    @contextmanager
    def isolated_context(self):
        """Context manager para execução isolada (útil para testes).

        Uso:
            with factory.isolated_context():
                tool = factory.create("my_tool")
                # Cache local, não afeta global
        """
        original_cache = self._cache.copy()
        self._cache.clear()
        try:
            yield self
        finally:
            self._cache = original_cache

    def __repr__(self) -> str:
        """Representação debug."""
        cached = len(self._cache)
        available = len(self.registry.list_tools(enabled_only=False))
        return f"ToolFactory(cached={cached}, available={available})"
