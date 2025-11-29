"""
Web Search - Busca real na web.

Implementações de busca na web usando diferentes backends:
- DuckDuckGo (gratuito, sem API key)
- Bing (requer API key)
- Google (requer API key)

Versão: 2.0.0
"""

import logging
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus

from agent_framework import ai_function

logger = logging.getLogger("ferramentas.web_search")


@dataclass
class SearchResult:
    """Resultado de uma busca."""
    title: str
    url: str
    snippet: str
    source: str = "web"
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }
    
    def format(self, index: int = 1) -> str:
        return (
            f"{index}. **{self.title}**\n"
            f"   🔗 {self.url}\n"
            f"   {self.snippet}\n"
        )


class SearchBackend(ABC):
    """Interface para backends de busca."""
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Executa uma busca."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do backend."""
        pass


class DuckDuckGoBackend(SearchBackend):
    """
    Backend de busca usando DuckDuckGo.
    
    Gratuito, sem necessidade de API key.
    Usa a API HTML do DuckDuckGo.
    """
    
    BASE_URL = "https://html.duckduckgo.com/html/"
    
    @property
    def name(self) -> str:
        return "DuckDuckGo"
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Busca no DuckDuckGo."""
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                data = {"q": query, "b": ""}
                
                async with session.post(
                    self.BASE_URL,
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"DuckDuckGo retornou status {response.status}")
                        return results
                    
                    html = await response.text()
                    results = self._parse_results(html, max_results)
                    
        except asyncio.TimeoutError:
            logger.error("Timeout na busca DuckDuckGo")
        except Exception as e:
            logger.error(f"Erro na busca DuckDuckGo: {e}")
        
        return results
    
    def _parse_results(self, html: str, max_results: int) -> List[SearchResult]:
        """Parse dos resultados HTML do DuckDuckGo."""
        results = []
        
        try:
            import re
            import html as html_module
            
            # Encontrar blocos de resultado
            link_matches = re.findall(r'href="(https?://[^"]+)"[^>]*>([^<]{10,})</a>', html)
            snippet_matches = re.findall(r'class="result__snippet"[^>]*>([^<]+)</a>', html)
            
            # Filtrar links que são resultados reais
            filtered_links = [
                (url, title) for url, title in link_matches
                if not url.startswith("https://duckduckgo.com") 
                and "ad_provider" not in url
                and len(title.strip()) > 5
            ]
            
            for i, (url, title) in enumerate(filtered_links[:max_results]):
                snippet = snippet_matches[i] if i < len(snippet_matches) else ""
                
                # Limpar HTML entities
                title = html_module.unescape(title.strip())
                snippet = html_module.unescape(snippet.strip()) if snippet else "Sem descrição"
                
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="duckduckgo",
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"Erro ao fazer parse dos resultados: {e}")
        
        return results


class DuckDuckGoInstantBackend(SearchBackend):
    """
    Backend usando DuckDuckGo Instant Answer API.
    
    Mais confiável, retorna respostas diretas.
    """
    
    API_URL = "https://api.duckduckgo.com/"
    
    @property
    def name(self) -> str:
        return "DuckDuckGo Instant"
    
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Busca usando a API Instant Answer."""
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1",
                }
                
                async with session.get(
                    self.API_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return results
                    
                    data = await response.json()
                    
                    # Abstract (resposta direta)
                    if data.get("Abstract"):
                        results.append(SearchResult(
                            title=data.get("Heading", query),
                            url=data.get("AbstractURL", ""),
                            snippet=data.get("Abstract", ""),
                            source="duckduckgo_instant"
                        ))
                    
                    # Related Topics
                    for topic in data.get("RelatedTopics", [])[:max_results-len(results)]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append(SearchResult(
                                title=topic.get("Text", "")[:100],
                                url=topic.get("FirstURL", ""),
                                snippet=topic.get("Text", ""),
                                source="duckduckgo_instant"
                            ))
                    
        except Exception as e:
            logger.error(f"Erro na busca DuckDuckGo Instant: {e}")
        
        return results


# Instância global do backend
_search_backend: Optional[SearchBackend] = None


def get_search_backend() -> SearchBackend:
    """Obtém o backend de busca configurado."""
    global _search_backend
    if _search_backend is None:
        _search_backend = DuckDuckGoBackend()
    return _search_backend


def set_search_backend(backend: SearchBackend) -> None:
    """Define o backend de busca a ser usado."""
    global _search_backend
    _search_backend = backend


def _run_async(coro):
    """Executa coroutine de forma síncrona."""
    try:
        loop = asyncio.get_running_loop()
        # Se já estamos em um loop, criar task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # Não há loop rodando, criar um novo
        return asyncio.run(coro)


# ============================================================================
# Ferramentas expostas para os agentes
# ============================================================================

@ai_function(
    name="pesquisar_web",
    description=(
        "Pesquisa informações na web usando DuckDuckGo. "
        "Use para encontrar informações atualizadas, documentação, notícias, dados, etc. "
        "Retorna título, URL e resumo dos resultados."
    )
)
def pesquisar_web(query: str, max_resultados: int = 5) -> str:
    """
    Pesquisa na web.
    
    Args:
        query: Texto da busca
        max_resultados: Número máximo de resultados (1-10)
        
    Returns:
        Resultados formatados da busca
    """
    logger.info(f"[WEB_SEARCH] Pesquisando: '{query}'")
    
    # Limitar resultados
    max_resultados = min(max(1, max_resultados), 10)
    
    # Executar busca
    backend = get_search_backend()
    
    try:
        results = _run_async(backend.search(query, max_resultados))
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return f"❌ Erro ao pesquisar: {e}"
    
    if not results:
        return f"🔍 Nenhum resultado encontrado para: '{query}'"
    
    # Formatar resposta
    response_parts = [f"🔍 Resultados para: '{query}' ({backend.name})\n"]
    
    for i, result in enumerate(results, 1):
        response_parts.append(result.format(i))
    
    response_parts.append(f"\n📅 Pesquisa: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    logger.info(f"[WEB_SEARCH] Encontrados {len(results)} resultados")
    return "\n".join(response_parts)


@ai_function(
    name="buscar_multiplo",
    description=(
        "Realiza múltiplas buscas na web em sequência. "
        "Útil para pesquisar vários termos relacionados de uma vez."
    )
)
def buscar_multiplo(queries: list, max_por_busca: int = 3) -> str:
    """
    Realiza múltiplas buscas.
    
    Args:
        queries: Lista de termos para buscar
        max_por_busca: Resultados por busca
        
    Returns:
        Todos os resultados consolidados
    """
    logger.info(f"[MULTI_SEARCH] Buscando {len(queries)} termos")
    
    all_results = []
    
    for query in queries:
        result = pesquisar_web(query, max_por_busca)
        all_results.append(f"\n{'='*50}\n{result}")
    
    return "\n".join(all_results)


@ai_function(
    name="buscar_noticias",
    description=(
        "Busca notícias recentes sobre um tópico. "
        "Adiciona 'news' à busca para priorizar resultados de notícias."
    )
)
def buscar_noticias(topico: str, quantidade: int = 5) -> str:
    """
    Busca notícias sobre um tópico.
    
    Args:
        topico: Tópico das notícias
        quantidade: Quantidade de resultados
        
    Returns:
        Notícias encontradas
    """
    logger.info(f"[NEWS_SEARCH] Buscando notícias: '{topico}'")
    query = f"{topico} news latest"
    return pesquisar_web(query, quantidade)


@ai_function(
    name="buscar_documentacao",
    description=(
        "Busca documentação técnica sobre um tópico. "
        "Prioriza resultados de sites de documentação oficial."
    )
)
def buscar_documentacao(tecnologia: str, topico: str = "") -> str:
    """
    Busca documentação técnica.
    
    Args:
        tecnologia: Nome da tecnologia (ex: Python, Azure, React)
        topico: Tópico específico (ex: async, functions)
        
    Returns:
        Documentação encontrada
    """
    logger.info(f"[DOCS_SEARCH] Buscando docs: {tecnologia} {topico}")
    query = f"{tecnologia} {topico} documentation official docs"
    return pesquisar_web(query, 5)


# Aliases
web_search = pesquisar_web
search_web = pesquisar_web
multi_search = buscar_multiplo
