# 🔗 Sistema de Citações RAG - MAIA

## 📋 Resumo da Implementação

Implementação completa de sistema de citações RAG inspirado no **Azure Search OpenAI Demo**, integrado ao **Microsoft Agent Framework**.

## 🎯 Componentes Implementados

### 🎨 Frontend (React/TypeScript)

#### 1. **CitationRenderer.tsx**
```typescript
// Componente principal para renderizar citações
export function CitationRenderer({ citations }: { citations: Citation[] })

// Hook para extrair citações do texto
export function useCitationExtraction(text: string, availableCitations: Citation[])
```

**Funcionalidades:**
- ✅ Cards expansíveis para cada citação
- ✅ Preview do conteúdo com "Ver mais/menos"
- ✅ Score de relevância visual
- ✅ Links para documentos originais
- ✅ Metadados estruturados

#### 2. **MarkdownRenderer.tsx** (Atualizado)
```typescript
// Suporte a marcadores de citação: [1], [2], [doc1], [fonte: file.pdf]
const citationPattern = /\[(\d+)\]|\[doc(\d+)\]|\[(fonte|source):\s*([^\]]+)\]/
```

**Funcionalidades:**
- ✅ Detecção automática de marcadores `[1]`, `[2]`
- ✅ Tooltips com preview da citação
- ✅ Integração com anotações OpenAI
- ✅ Suporte a múltiplos formatos de citação

#### 3. **OpenAIContentRenderer.tsx** (Atualizado)
```typescript
// Conversão de anotações OpenAI para formato Citation
const citations: Citation[] = annotations
  .filter((a): a is FileCitationAnnotation => a.type === "file_citation")
  .map(annotation => ({ ... }))
```

### 🔧 Backend (Python)

#### 1. **CitationProcessor** (`src/worker/rag/citation_processor.py`)
```python
class CitationProcessor:
    def extract_citations_from_search_results(self, search_results) -> List[Citation]
    def format_citations_for_llm(self, citations) -> str
    def create_openai_annotations(self, text, citations) -> List[Dict]
```

**Funcionalidades:**
- ✅ Extração de citações de resultados de busca
- ✅ Formatação para prompts LLM
- ✅ Criação de anotações compatíveis com OpenAI
- ✅ Processamento de marcadores no texto

#### 2. **RAG Tools** (`ferramentas/rag_tools.py`) (Atualizado)
```python
@ai_function(name="search_knowledge_base")
async def search_knowledge_base(payload) -> str:
    # Agora retorna citações estruturadas
    return json.dumps({
        "results": formatted,
        "citations": [citation.dict() for citation in citations]
    })
```

## 🔄 Fluxo de Integração RAG

### 1. **Busca de Documentos**
```python
# 1. Usuário faz pergunta
query = "Como funciona a política de reembolso?"

# 2. Busca vetorial na base de conhecimento
search_results = await search_knowledge_base(query)

# 3. Extração de citações
processor = CitationProcessor()
citations = processor.extract_citations_from_search_results(search_results)
```

### 2. **Formatação para LLM**
```python
# 4. Contexto enriquecido para o LLM
citation_context = processor.format_citations_for_llm(citations)
enhanced_prompt = f"{query}\n\n{citation_context}"

# Resultado:
# """
# Fontes disponíveis para citação:
# 
# [1] politica_reembolso.pdf
# Conteúdo: Os reembolsos são processados em até 5 dias úteis...
# 
# [2] manual_funcionario.pdf  
# Conteúdo: Para solicitar reembolso, acesse o portal...
# 
# Instruções: Use [1], [2], etc. para citar as fontes no seu texto.
# """
```

### 3. **Resposta com Citações**
```python
# 5. LLM gera resposta com marcadores
llm_response = """
Os reembolsos são processados conforme nossa política [1]. 
Para solicitar, acesse o portal interno [2] e preencha o formulário.
"""

# 6. Processamento das citações na resposta
used_citations = processor.extract_citation_markers(llm_response)  # [1, 2]
frontend_citations = processor.format_citations_for_frontend(citations, used_citations)
openai_annotations = processor.create_openai_annotations(llm_response, citations)
```

### 4. **Renderização no Frontend**
```typescript
// 7. Frontend recebe resposta estruturada
const response = {
  text: "Os reembolsos são processados conforme nossa política [1]...",
  citations: [
    {
      id: "doc_1",
      filename: "politica_reembolso.pdf", 
      content: "Os reembolsos são processados em até 5 dias úteis...",
      score: 0.95
    }
  ],
  annotations: [
    {
      type: "file_citation",
      text: "[1]",
      file_id: "doc_1",
      filename: "politica_reembolso.pdf"
    }
  ]
}

// 8. Renderização com citações interativas
<MarkdownRenderer content={response.text} annotations={response.annotations} />
<CitationRenderer citations={response.citations} />
```

## 🎨 Exemplo Visual

### Antes (Sem Citações)
```
❓ Como funciona a política de reembolso?

🤖 Os reembolsos são processados em até 5 dias úteis após aprovação.
```

### Depois (Com Citações)
```
❓ Como funciona a política de reembolso?

🤖 Os reembolsos são processados em até 5 dias úteis após aprovação [1].
    Para solicitar, acesse o portal interno [2].

📚 Fontes consultadas (2) ▼
    [1] 📄 politica_reembolso.pdf
        "Os reembolsos são processados em até 5 dias úteis..."
        95% relevância
    
    [2] 📄 manual_funcionario.pdf  
        "Para solicitar reembolso, acesse o portal..."
        87% relevância
```

## ✅ Compatibilidade

### Microsoft Agent Framework
- ✅ Integração nativa com `@ai_function`
- ✅ Suporte a ferramentas RAG existentes
- ✅ Compatível com workflows sequenciais/paralelos
- ✅ Funciona com Azure OpenAI e OpenAI

### OpenAI Assistants API
- ✅ Formato de anotações compatível
- ✅ Suporte a `file_citation` annotations
- ✅ Campos flat e aninhados suportados
- ✅ Migração transparente de sistemas existentes

## 🚀 Próximos Passos

1. **Testar integração** com workflows existentes
2. **Configurar Azure AI Search** para produção
3. **Implementar cache** de citações para performance
4. **Adicionar métricas** de uso de citações
5. **Documentar padrões** para novos agentes RAG

## 📖 Referências

- [Azure Search OpenAI Demo](https://github.com/Azure-Samples/azure-search-openai-demo)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants/overview)