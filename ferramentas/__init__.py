"""
Sistema de Ferramentas - AI Platform

Arquitetura plug-and-play para ferramentas de agentes IA.
Auto-descoberta de ferramentas via decorators e registro automático.

Uso:
    from ferramentas import get_tool, list_tools, pesquisar_web, executar_codigo
    
    # Listar todas as ferramentas disponíveis
    tools = list_tools()
    
    # Obter uma ferramenta específica
    tool = get_tool("pesquisar_web")
    
    # Usar ferramentas diretamente
    result = pesquisar_web("Azure AI")
    result = executar_codigo("print(2 + 2)")

Versão: 2.0.0

NOTA FUTURA: Hosted Tools (Azure AI Agent Service)
--------------------------------------------------
As ferramentas locais (web_search, code_interpreter) são uma alternativa
às Hosted Tools do Azure AI Agent Service. Para usar Hosted Tools nativos:

1. Configure um projeto no Azure AI Foundry
2. Use AzureAIAgentClient ao invés de AzureOpenAIChatClient
3. Referência: https://learn.microsoft.com/azure/ai-services/agents/

TODO: Adicionar provider layer para Azure AI Agent Service
"""

from ferramentas.registry import (
    ToolRegistry,
    ToolCategory,
    ToolMetadata,
    get_registry,
    register_tool,
    get_tool,
    list_tools,
    get_tools_by_category,
    tool,
    ai_tool,
)

# Importar módulos para auto-registro das ferramentas
from ferramentas import basicas
from ferramentas import code_interpreter
from ferramentas import web_search
from ferramentas import arquivos

# Re-exportar ferramentas principais para acesso direto
from ferramentas.code_interpreter import (
    executar_codigo,
    calcular,
    analisar_dados,
    gerar_grafico_texto,
    # Aliases
    code_interpreter as execute_code,
)
from ferramentas.web_search import (
    pesquisar_web,
    buscar_noticias,
    buscar_documentacao,
    buscar_multiplo,
    # Aliases
    web_search as search_web,
)
from ferramentas.arquivos import (
    listar_arquivos,
    ler_arquivo,
    escrever_arquivo,
)

__all__ = [
    # Registry
    "ToolRegistry",
    "ToolCategory",
    "ToolMetadata",
    "get_registry",
    "register_tool",
    "get_tool",
    "list_tools",
    "get_tools_by_category",
    "tool",
    "ai_tool",
    # Code Interpreter
    "executar_codigo",
    "execute_code",
    "calcular",
    "analisar_dados",
    "gerar_grafico_texto",
    # Web Search
    "pesquisar_web",
    "search_web",
    "buscar_noticias",
    "buscar_documentacao",
    "buscar_multiplo",
    # Arquivos
    "listar_arquivos",
    "ler_arquivo",
    "escrever_arquivo",
]
