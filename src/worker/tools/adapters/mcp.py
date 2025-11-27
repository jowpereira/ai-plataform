"""
Adapter para Ferramentas MCP (Model Context Protocol).

Integração com servidores MCP para ferramentas externas.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from src.worker.tools.base import ToolAdapter
from src.worker.tools.models import (
    ToolDefinition,
    ToolResult,
    ToolExecutionContext,
    ToolType,
)

logger = logging.getLogger("worker.tools.mcp")


class McpToolAdapter(ToolAdapter):
    """
    Adapter para execução de ferramentas via MCP (Model Context Protocol).
    
    O source deve ser o identificador do servidor MCP:
    - "mcp://localhost:5000/weather"
    - "azure-mcp://subscription/resource"
    
    Configurações MCP via mcp_config:
        {
            "server_url": "http://localhost:5000",
            "transport": "stdio",  # stdio, http, websocket
            "tool_name": "weather_lookup",
            "timeout": 60.0
        }
    
    Nota: Esta é uma implementação placeholder. A integração real
    depende do SDK MCP específico em uso (ex: mcp-python).
    
    Exemplo:
        definition = ToolDefinition(
            name="azure_resources",
            description="Consulta recursos Azure",
            type=ToolType.MCP,
            source="mcp://azure-mcp",
            mcp_config={
                "transport": "stdio",
                "tool_name": "query_resources"
            }
        )
    """
    
    tool_type = ToolType.MCP
    
    def __init__(self):
        super().__init__()
        self._clients: Dict[str, Any] = {}  # Cache de clientes MCP
    
    def _get_mcp_config(self, definition: ToolDefinition) -> Dict[str, Any]:
        """Obtém configuração MCP com defaults."""
        config = {
            "transport": "stdio",
            "timeout": 60.0,
        }
        if definition.mcp_config:
            config.update(definition.mcp_config)
        return config
    
    async def _get_client(self, source: str, config: Dict[str, Any]) -> Any:
        """
        Obtém ou cria cliente MCP.
        
        Nota: Implementação placeholder - requer SDK MCP real.
        """
        cache_key = f"{source}:{config.get('transport', 'stdio')}"
        
        if cache_key in self._clients:
            return self._clients[cache_key]
        
        # Tentar importar SDK MCP
        try:
            # Tentar mcp-python (SDK oficial)
            from mcp import Client as McpClient
            
            client = McpClient()
            await client.connect(source, transport=config.get("transport", "stdio"))
            self._clients[cache_key] = client
            return client
            
        except ImportError:
            logger.warning(
                "SDK MCP não encontrado. Instale 'mcp' para suporte completo. "
                "Usando mock client."
            )
            # Retornar mock client para desenvolvimento
            return _MockMcpClient(source, config)
    
    async def execute(
        self,
        definition: ToolDefinition,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
    ) -> ToolResult:
        """Executa ferramenta via MCP."""
        start_time = time.time()
        
        try:
            config = self._get_mcp_config(definition)
            client = await self._get_client(definition.source, config)
            
            # Nome da ferramenta no servidor MCP
            tool_name = config.get("tool_name", definition.name)
            
            # Executar via cliente MCP
            timeout = config.get("timeout", definition.timeout)
            
            try:
                result = await asyncio.wait_for(
                    client.call_tool(tool_name, arguments),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"MCP tool '{tool_name}' timeout após {timeout}s")
            
            execution_time = time.time() - start_time
            
            logger.debug(
                f"MCP tool '{definition.name}' executada em {execution_time:.3f}s"
            )
            
            return ToolResult.success_result(
                tool_name=definition.name,
                result=result,
                execution_time=execution_time,
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro ao executar MCP tool '{definition.name}': {e}")
            
            return ToolResult.error_result(
                tool_name=definition.name,
                error=str(e),
                execution_time=execution_time,
            )
    
    def validate(self, definition: ToolDefinition) -> List[str]:
        """Valida a definição de ferramenta MCP."""
        errors = []
        
        # Verificar source
        source = definition.source
        if not source:
            errors.append("Source não pode ser vazio para ferramentas MCP")
        
        # Verificar configuração
        config = definition.mcp_config or {}
        transport = config.get("transport", "stdio")
        valid_transports = ["stdio", "http", "websocket", "sse"]
        
        if transport not in valid_transports:
            errors.append(
                f"Transport MCP inválido: {transport}. "
                f"Válidos: {valid_transports}"
            )
        
        return errors
    
    async def close(self) -> None:
        """Fecha todos os clientes MCP."""
        for key, client in self._clients.items():
            try:
                if hasattr(client, "close"):
                    await client.close()
            except Exception as e:
                logger.warning(f"Erro ao fechar cliente MCP {key}: {e}")
        self._clients.clear()


class _MockMcpClient:
    """
    Cliente MCP mock para desenvolvimento/testes.
    
    Usado quando o SDK MCP real não está instalado.
    """
    
    def __init__(self, source: str, config: Dict[str, Any]):
        self.source = source
        self.config = config
        logger.info(f"MockMcpClient inicializado para: {source}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Simula chamada de ferramenta MCP."""
        logger.warning(
            f"MockMcpClient.call_tool({tool_name}, {arguments}) - "
            "Instale o SDK MCP para funcionalidade real"
        )
        
        # Retornar resultado mock
        return {
            "_mock": True,
            "tool": tool_name,
            "arguments": arguments,
            "message": "SDK MCP não instalado. Este é um resultado mock.",
        }
    
    async def close(self) -> None:
        """Mock close."""
        pass
