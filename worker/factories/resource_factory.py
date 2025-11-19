"""Resource factory para instanciar ferramentas, MCP servers, etc."""

from typing import Any, Callable

from worker.config import MCPServerConfig, ResourcesConfig, ToolConfig
from tools import ToolFactory, ToolLoader


class ResourceFactory:
    """Factory para criar recursos compartilhados (tools, MCP, etc)."""

    def __init__(self, config: ResourcesConfig):
        self.config = config
        self.tool_factory = ToolFactory()
        self._tool_cache: dict[str, Callable] = {}
        self._mcp_connections: dict[str, Any] = {}

        # Auto-load tools via import paths
        self._load_tools_from_config()

    def _load_tools_from_config(self) -> None:
        """Carrega tools configuradas via import paths."""
        for tool_id, tool_config in self.config.tools.items():
            if not tool_config.enabled:
                continue

            try:
                # Load via import path (auto-registra se não existir)
                ToolLoader.load_from_import_path(tool_config.function_path)
            except Exception as e:
                raise RuntimeError(f"Falha ao carregar tool '{tool_id}' de {tool_config.function_path}: {e}")

    def get_tool(self, tool_id: str) -> Callable:
        """Obtém função de ferramenta por ID.

        Args:
            tool_id: ID da ferramenta em resources.tools

        Returns:
            Função Python da ferramenta

        Raises:
            KeyError: se tool_id não existir
            ImportError: se function_path não puder ser importado
        """
        if tool_id in self._tool_cache:
            return self._tool_cache[tool_id]

        if tool_id not in self.config.tools:
            raise KeyError(f"Tool {tool_id} não encontrado em resources.tools")

        tool_config = self.config.tools[tool_id]
        if not tool_config.enabled:
            raise ValueError(f"Tool {tool_id} está desabilitado")

        # Get from ToolFactory (que usa ToolRegistry)
        func = self.tool_factory.create(tool_id)
        self._tool_cache[tool_id] = func
        return func

        self._tool_cache[tool_id] = func
        return func

    def get_tools(self, tool_ids: list[str]) -> list[Callable]:
        """Obtém lista de funções de ferramentas.

        Args:
            tool_ids: Lista de IDs de ferramentas

        Returns:
            Lista de funções Python
        """
        return [self.get_tool(tid) for tid in tool_ids]

    def get_mcp_server_config(self, server_id: str) -> MCPServerConfig:
        """Obtém configuração de MCP server.

        Args:
            server_id: ID do servidor MCP

        Returns:
            Configuração do servidor

        Raises:
            KeyError: se server_id não existir
        """
        if server_id not in self.config.mcp_servers:
            raise KeyError(f"MCP server {server_id} não encontrado")

        return self.config.mcp_servers[server_id]

    def clear_cache(self):
        """Limpa caches."""
        self._tool_cache.clear()
        # TODO: fechar conexões MCP se necessário
        self._mcp_connections.clear()
