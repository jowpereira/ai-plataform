"""
Registry de Ferramentas - Sistema plug-and-play.

Permite registro automático de ferramentas via decorators,
descoberta dinâmica e categorização.

Uso:
    from ferramentas.registry import tool, get_registry
    
    @tool(category="search", name="minha_busca")
    def minha_busca(query: str) -> str:
        return f"Resultados para {query}"

Versão: 2.0.0
"""

import logging
import functools
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from agent_framework import ai_function

logger = logging.getLogger("ferramentas.registry")


class ToolCategory(str, Enum):
    """Categorias de ferramentas disponíveis."""
    SEARCH = "search"           # Busca na web, notícias, etc
    CODE = "code"               # Execução de código, cálculos
    DATA = "data"               # Processamento de dados
    UTILITY = "utility"         # Utilitários gerais
    INTEGRATION = "integration" # Integrações externas
    CUSTOM = "custom"           # Ferramentas customizadas


@dataclass
class ToolMetadata:
    """Metadados de uma ferramenta registrada."""
    name: str
    description: str
    category: ToolCategory
    callable: Callable
    is_async: bool = False
    requires_approval: bool = False
    tags: Set[str] = field(default_factory=set)
    version: str = "1.0.0"
    
    def __hash__(self):
        return hash(self.name)


class ToolRegistry:
    """
    Registry central de ferramentas.
    
    Singleton que mantém todas as ferramentas registradas,
    permite busca por categoria, tags e nome.
    """
    
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, ToolMetadata]
    _by_category: Dict[ToolCategory, Set[str]]
    _by_tag: Dict[str, Set[str]]
    
    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._by_category = {cat: set() for cat in ToolCategory}
            cls._instance._by_tag = {}
        return cls._instance
    
    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: ToolCategory = ToolCategory.CUSTOM,
        tags: Optional[Set[str]] = None,
        requires_approval: bool = False,
        version: str = "1.0.0",
    ) -> Callable:
        """
        Registra uma ferramenta no registry.
        
        Args:
            func: Função a ser registrada
            name: Nome da ferramenta (default: nome da função)
            description: Descrição (default: docstring)
            category: Categoria da ferramenta
            tags: Tags para busca
            requires_approval: Se requer aprovação humana
            version: Versão da ferramenta
            
        Returns:
            A função original (para uso como decorator)
        """
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Ferramenta {tool_name}"
        tool_tags = tags or set()
        
        # Verificar se é async
        import asyncio
        is_async = asyncio.iscoroutinefunction(func)
        
        metadata = ToolMetadata(
            name=tool_name,
            description=tool_desc,
            category=category,
            callable=func,
            is_async=is_async,
            requires_approval=requires_approval,
            tags=tool_tags,
            version=version,
        )
        
        # Registrar
        self._tools[tool_name] = metadata
        self._by_category[category].add(tool_name)
        
        for tag in tool_tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = set()
            self._by_tag[tag].add(tool_name)
        
        logger.debug(f"Ferramenta registrada: {tool_name} [{category.value}]")
        return func
    
    def get(self, name: str) -> Optional[ToolMetadata]:
        """Obtém metadados de uma ferramenta."""
        return self._tools.get(name)
    
    def get_callable(self, name: str) -> Optional[Callable]:
        """Obtém a função callable de uma ferramenta."""
        meta = self._tools.get(name)
        return meta.callable if meta else None
    
    def list_all(self) -> List[ToolMetadata]:
        """Lista todas as ferramentas registradas."""
        return list(self._tools.values())
    
    def list_names(self) -> List[str]:
        """Lista nomes de todas as ferramentas."""
        return list(self._tools.keys())
    
    def by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """Lista ferramentas de uma categoria."""
        names = self._by_category.get(category, set())
        return [self._tools[n] for n in names if n in self._tools]
    
    def by_tag(self, tag: str) -> List[ToolMetadata]:
        """Lista ferramentas com uma tag específica."""
        names = self._by_tag.get(tag, set())
        return [self._tools[n] for n in names if n in self._tools]
    
    def search(self, query: str) -> List[ToolMetadata]:
        """Busca ferramentas por nome ou descrição."""
        query_lower = query.lower()
        results = []
        for meta in self._tools.values():
            if (query_lower in meta.name.lower() or 
                query_lower in meta.description.lower() or
                any(query_lower in tag.lower() for tag in meta.tags)):
                results.append(meta)
        return results
    
    def exists(self, name: str) -> bool:
        """Verifica se uma ferramenta existe."""
        return name in self._tools
    
    def unregister(self, name: str) -> bool:
        """Remove uma ferramenta do registry."""
        if name not in self._tools:
            return False
        
        meta = self._tools.pop(name)
        self._by_category[meta.category].discard(name)
        for tag in meta.tags:
            if tag in self._by_tag:
                self._by_tag[tag].discard(name)
        
        logger.debug(f"Ferramenta removida: {name}")
        return True
    
    def clear(self) -> None:
        """Remove todas as ferramentas (útil para testes)."""
        self._tools.clear()
        for cat in self._by_category:
            self._by_category[cat].clear()
        self._by_tag.clear()
    
    def summary(self) -> Dict[str, Any]:
        """Retorna um resumo do registry."""
        return {
            "total": len(self._tools),
            "by_category": {
                cat.value: len(names) 
                for cat, names in self._by_category.items()
            },
            "tools": [
                {"name": m.name, "category": m.category.value, "description": m.description[:50]}
                for m in self._tools.values()
            ]
        }


# Instância global do registry
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Obtém a instância global do registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: ToolCategory = ToolCategory.CUSTOM,
    tags: Optional[Set[str]] = None,
    requires_approval: bool = False,
    version: str = "1.0.0",
) -> Callable:
    """
    Decorator para registrar uma ferramenta automaticamente.
    
    Uso:
        @tool(category=ToolCategory.SEARCH, tags={"web", "busca"})
        def minha_busca(query: str) -> str:
            return f"Resultados para {query}"
    """
    def decorator(func: Callable) -> Callable:
        registry = get_registry()
        registry.register(
            func=func,
            name=name,
            description=description,
            category=category,
            tags=tags,
            requires_approval=requires_approval,
            version=version,
        )
        return func
    return decorator


def ai_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: ToolCategory = ToolCategory.CUSTOM,
    tags: Optional[Set[str]] = None,
    requires_approval: bool = False,
    version: str = "1.0.0",
) -> Callable:
    """
    Decorator que combina @ai_function com registro no ToolRegistry.
    
    Uso:
        @ai_tool(name="buscar", category=ToolCategory.SEARCH)
        def buscar(query: str) -> str:
            '''Busca informações na web.'''
            return f"Resultados para {query}"
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Ferramenta {tool_name}"
        
        # Aplicar @ai_function primeiro
        ai_func = ai_function(name=tool_name, description=tool_desc)(func)
        
        # Registrar no registry
        registry = get_registry()
        registry.register(
            func=ai_func,
            name=tool_name,
            description=tool_desc,
            category=category,
            tags=tags,
            requires_approval=requires_approval,
            version=version,
        )
        
        return ai_func
    return decorator


# Funções de conveniência
def register_tool(
    func: Callable,
    name: Optional[str] = None,
    category: ToolCategory = ToolCategory.CUSTOM,
    **kwargs
) -> None:
    """Registra uma ferramenta manualmente."""
    get_registry().register(func, name=name, category=category, **kwargs)


def get_tool(name: str) -> Optional[Callable]:
    """Obtém uma ferramenta pelo nome."""
    return get_registry().get_callable(name)


def list_tools() -> List[str]:
    """Lista nomes de todas as ferramentas."""
    return get_registry().list_names()


def get_tools_by_category(category: ToolCategory) -> List[ToolMetadata]:
    """Lista ferramentas de uma categoria."""
    return get_registry().by_category(category)
