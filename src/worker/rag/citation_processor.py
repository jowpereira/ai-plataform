"""
Citation Processor - Processamento de citações RAG
Inspirado no Azure Search OpenAI Demo para integração com Microsoft Agent Framework
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Citation:
    """Estrutura de uma citação RAG"""
    id: str
    filename: str
    content: str
    url: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class CitationProcessor:
    """
    Processador de citações para RAG no Microsoft Agent Framework
    
    Funcionalidades:
    - Extrai citações de documentos recuperados
    - Formata citações para o frontend
    - Integra com responses do Agent Framework
    """
    
    def __init__(self):
        self.citation_pattern = re.compile(r'\[(\d+)\]')
    
    def extract_citations_from_search_results(
        self, 
        search_results: List[Dict[str, Any]]
    ) -> List[Citation]:
        """
        Extrai citações de resultados de busca (Azure AI Search, etc.)
        
        Args:
            search_results: Lista de documentos retornados pela busca
            
        Returns:
            Lista de citações formatadas
        """
        citations = []
        
        for idx, result in enumerate(search_results):
            citation = Citation(
                id=result.get('id', f'doc_{idx}'),
                filename=result.get('filename', result.get('title', f'Documento {idx + 1}')),
                content=result.get('content', result.get('text', '')),
                url=result.get('url'),
                page=result.get('page'),
                score=result.get('@search.score', result.get('score')),
                metadata={
                    'source': result.get('source'),
                    'category': result.get('category'),
                    'last_updated': result.get('last_updated'),
                    **result.get('metadata', {})
                }
            )
            citations.append(citation)
        
        return citations
    
    def format_citations_for_llm(self, citations: List[Citation]) -> str:
        """
        Formata citações para inclusão no prompt do LLM
        
        Args:
            citations: Lista de citações
            
        Returns:
            String formatada para o LLM
        """
        if not citations:
            return ""
        
        formatted = "Fontes disponíveis para citação:\n\n"
        
        for idx, citation in enumerate(citations, 1):
            formatted += f"[{idx}] {citation.filename}\n"
            formatted += f"Conteúdo: {citation.content[:500]}...\n"
            if citation.page:
                formatted += f"Página: {citation.page}\n"
            formatted += "\n"
        
        formatted += "\nInstruções: Use [1], [2], etc. para citar as fontes no seu texto.\n"
        
        return formatted
    
    def extract_citation_markers(self, text: str) -> List[int]:
        """
        Extrai marcadores de citação do texto gerado pelo LLM
        
        Args:
            text: Texto com possíveis marcadores [1], [2], etc.
            
        Returns:
            Lista de números das citações encontradas
        """
        matches = self.citation_pattern.findall(text)
        return [int(match) for match in matches]
    
    def format_citations_for_frontend(
        self, 
        citations: List[Citation],
        used_citation_numbers: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Formata citações para o frontend React
        
        Args:
            citations: Lista completa de citações
            used_citation_numbers: Números das citações usadas no texto
            
        Returns:
            Lista de citações formatadas para JSON
        """
        frontend_citations = []
        
        for num in used_citation_numbers:
            if 1 <= num <= len(citations):
                citation = citations[num - 1]
                frontend_citations.append({
                    'id': citation.id,
                    'filename': citation.filename,
                    'content': citation.content,
                    'url': citation.url,
                    'page': citation.page,
                    'score': citation.score,
                    'metadata': citation.metadata or {}
                })
        
        return frontend_citations
    
    def create_openai_annotations(
        self, 
        text: str, 
        citations: List[Citation]
    ) -> List[Dict[str, Any]]:
        """
        Cria anotações no formato OpenAI para compatibilidade
        
        Args:
            text: Texto com marcadores de citação
            citations: Lista de citações disponíveis
            
        Returns:
            Lista de anotações no formato OpenAI
        """
        annotations = []
        used_numbers = self.extract_citation_markers(text)
        
        for num in used_numbers:
            if 1 <= num <= len(citations):
                citation = citations[num - 1]
                
                # Formato OpenAI Assistants API
                annotation = {
                    'type': 'file_citation',
                    'text': f'[{num}]',
                    'file_citation': {
                        'file_id': citation.id,
                        'filename': citation.filename,
                        'quote': citation.content[:200] + '...' if len(citation.content) > 200 else citation.content
                    },
                    # Campos flat para compatibilidade
                    'file_id': citation.id,
                    'filename': citation.filename,
                    'quote': citation.content[:200] + '...' if len(citation.content) > 200 else citation.content,
                    'score': citation.score,
                    'metadata': citation.metadata
                }
                annotations.append(annotation)
        
        return annotations


def integrate_rag_with_agent_framework(
    query: str,
    search_function: callable,
    llm_function: callable
) -> Dict[str, Any]:
    """
    Integração completa RAG com Microsoft Agent Framework
    
    Args:
        query: Pergunta do usuário
        search_function: Função de busca que retorna documentos
        llm_function: Função do LLM que gera resposta
        
    Returns:
        Resposta com citações formatadas
    """
    processor = CitationProcessor()
    
    # 1. Buscar documentos relevantes
    search_results = search_function(query)
    
    # 2. Extrair citações
    citations = processor.extract_citations_from_search_results(search_results)
    
    # 3. Formatar para o LLM
    citation_context = processor.format_citations_for_llm(citations)
    
    # 4. Gerar resposta com LLM
    enhanced_prompt = f"{query}\n\n{citation_context}"
    llm_response = llm_function(enhanced_prompt)
    
    # 5. Processar citações na resposta
    used_citations = processor.extract_citation_markers(llm_response)
    frontend_citations = processor.format_citations_for_frontend(citations, used_citations)
    openai_annotations = processor.create_openai_annotations(llm_response, citations)
    
    return {
        'text': llm_response,
        'citations': frontend_citations,
        'annotations': openai_annotations,
        'metadata': {
            'total_sources': len(citations),
            'used_sources': len(used_citations),
            'search_results_count': len(search_results)
        }
    }