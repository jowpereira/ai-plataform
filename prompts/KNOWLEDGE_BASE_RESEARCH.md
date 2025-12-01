# Pesquisa: Sistemas de Knowledge Base para Agentes de IA

> **Data:** Junho 2025  
> **Objetivo:** Analisar soluções de mercado para implementar um sistema de Knowledge Base genérico no AI Platform

---

## 📊 Resumo Executivo

Após pesquisa exaustiva nas principais plataformas de desenvolvimento de agentes de IA, identifiquei os seguintes padrões-chave para um sistema de Knowledge Base robusto:

| Plataforma | Tipo Upload | Formatos | Vector Store | Integração Agente |
|------------|-------------|----------|--------------|-------------------|
| **CrewAI** | SDK/Code | TXT, PDF, CSV, Excel, JSON | ChromaDB, Qdrant | Agent-level, Crew-level |
| **LangChain** | SDK/Code | 160+ loaders | 40+ integrações | Tool-based |
| **Vectorize** | UI + API | Docs, SaaS data | Pinecone, Couchbase | API Retrieval |
| **Flowise** | UI Drag-Drop | Documentos | Múltiplos | Visual Builder |

---

## 🔍 Análise Detalhada por Plataforma

### 1. CrewAI Knowledge System ⭐ (Referência Principal)

**Arquitetura:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge Sources                         │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ TextFile     │ PDF          │ CSV          │ Custom         │
│ Knowledge    │ Knowledge    │ Knowledge    │ Knowledge      │
│ Source       │ Source       │ Source       │ Source         │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬───────┘
       │              │              │                │
       └──────────────┴──────────────┴────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Knowledge       │
                    │   Storage         │
                    │  (ChromaDB/Qdrant)│
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Agent/Crew      │
                    │   Integration     │
                    └───────────────────┘
```

**Knowledge Sources Disponíveis:**
- `TextFileKnowledgeSource` → arquivos .txt
- `PDFKnowledgeSource` → arquivos .pdf
- `CSVKnowledgeSource` → arquivos .csv
- `ExcelKnowledgeSource` → arquivos .xlsx
- `JSONKnowledgeSource` → arquivos .json
- `StringKnowledgeSource` → conteúdo in-memory
- `CustomKnowledgeSource` → implementação customizada

**Configurações de Embedder:**
```python
embedder_config = {
    "provider": "openai",  # ou azure, ollama, voyage, cohere
    "config": {
        "model": "text-embedding-3-small"
    }
}
```

**Níveis de Integração:**
1. **Agent-Level:** Conhecimento específico de um agente
   ```python
   agent = Agent(
       role="Analista",
       knowledge_sources=[pdf_source],
       embedder_config=embedder_config
   )
   ```

2. **Crew-Level:** Conhecimento compartilhado entre agentes
   ```python
   crew = Crew(
       agents=[agent1, agent2],
       knowledge_sources=[shared_source],
       knowledge_config=KnowledgeConfig(
           results_limit=5,
           score_threshold=0.7
       )
   )
   ```

**Recursos Avançados:**
- Query Rewriting automático para melhor recuperação
- Chunking configurável (chunk_size, chunk_overlap)
- Score threshold para filtragem de resultados
- Coleções separadas por agente ou compartilhadas

---

### 2. LangChain RAG Architecture

**Pipeline de Indexação:**
```
Load → Split → Embed → Store
```

**1. Document Loaders (160+ integrações):**
- `WebBaseLoader` - páginas web
- `PyPDFLoader` - documentos PDF
- `TextLoader` - arquivos texto
- `CSVLoader` - arquivos CSV
- `UnstructuredExcelLoader` - arquivos Excel

**2. Text Splitters:**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True
)
chunks = splitter.split_documents(docs)
```

**Estratégias de Split:**
- Text structure-based (parágrafos, sentenças)
- Length-based (tokens ou caracteres)
- Document structure-based (Markdown, HTML, JSON, Code)

**3. Vector Stores (40+ integrações):**
- In-memory
- ChromaDB
- FAISS
- Pinecone
- Qdrant
- PGVector
- Milvus

**4. Retrieval Tool para Agentes:**
```python
from langchain.tools import tool

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}"
        for doc in docs
    )
    return serialized, docs
```

---

### 3. Vectorize Platform

**Diferenciais:**
- RAG Evaluation Tools (comparação automática de estratégias)
- Real-time vector updates
- Query rewriting com histórico de conversação
- Re-ranking built-in

**Pipeline Features:**
- Conectores para SaaS (Google Drive, Notion, etc.)
- Sync automático de dados
- API de retrieval com relevancy scores

---

## 🏗️ Arquitetura Proposta para AI Platform

Baseado na pesquisa, proponho a seguinte arquitetura:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ File Upload  │  │ Knowledge    │  │ Collection Manager   │  │
│  │ Component    │  │ List View    │  │ (CRUD)               │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └─────────────────┴──────────────────────┘              │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼──────────────────────────────────────┐
│                     Backend (FastAPI)                            │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  /v1/knowledge                           │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  POST /collections          → criar coleção             │    │
│  │  GET  /collections          → listar coleções           │    │
│  │  DELETE /collections/{id}   → deletar coleção           │    │
│  │                                                          │    │
│  │  POST /collections/{id}/documents  → upload documento   │    │
│  │  GET  /collections/{id}/documents  → listar documentos  │    │
│  │  DELETE /documents/{id}            → deletar documento  │    │
│  │                                                          │    │
│  │  POST /collections/{id}/query      → busca semântica    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Document Processing Pipeline                │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  1. File Upload → Temp Storage                          │    │
│  │  2. Document Loader (PDF, CSV, TXT, XLSX)               │    │
│  │  3. Text Splitter (chunk_size, chunk_overlap)           │    │
│  │  4. Embeddings (Azure OpenAI)                           │    │
│  │  5. Vector Store (ChromaDB)                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Retriever Tool Factory                      │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Gera ferramentas de retrieval para agentes baseado     │    │
│  │  nas coleções existentes                                │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                     Storage Layer                                │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │    ChromaDB      │  │    File Storage  │                     │
│  │  (Vector Store)  │  │   (Documents)    │                     │
│  └──────────────────┘  └──────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📋 Modelos de Dados Propostos

### Collection (Coleção de Conhecimento)
```python
class KnowledgeCollection(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    embedding_provider: Literal["azure"] #pega a versão do .env
    embedding_model: str #pega a versão do .env
    chunk_size: int = 1000
    chunk_overlap: int = 200
    created_at: datetime
    document_count: int = 0
```

### Document (Documento na Coleção)
```python
class KnowledgeDocument(BaseModel):
    id: str
    collection_id: str
    filename: str
    file_type: Literal["txt", "pdf", "csv", "xlsx", "json"]
    file_size: int
    chunk_count: int
    status: Literal["processing", "ready", "error"]
    created_at: datetime
    error_message: Optional[str] = None
```

### Retriever Tool (Ferramenta para Agentes)
```python
class KnowledgeRetrieverTool(BaseModel):
    name: str  # "retrieve_from_{collection_name}"
    description: str
    collection_id: str
    top_k: int = 5
    score_threshold: float = 0.7
```

---

## 🔧 Implementação Sugerida - Fases

### Fase 1: MVP
- [ ] Upload de arquivos TXT, CSV
- [ ] Processamento básico (chunking + embedding)
- [ ] Armazenamento ChromaDB
- [ ] Endpoint de query
- [ ] UI básica com upload e listagem

### Fase 2: Formatos Adicionais
- [ ] Suporte a PDF (PyPDF2 ou pdfplumber)
- [ ] Suporte a Excel (openpyxl)
- [ ] Suporte a JSON
- [ ] Melhorias na UI (preview de chunks)

### Fase 3: Integração com Agentes
- [ ] Retriever Tool Factory
- [ ] Registro automático de ferramentas
- [ ] Configuração no JSON de workflow
- [ ] Testes de integração

### Fase 4: Features Avançadas
- [ ] Query rewriting
- [ ] Múltiplos embedders (Azure, Ollama)
- [ ] Re-ranking
- [ ] Métricas de uso

---

## 📚 Dependências Python Necessárias

```toml
[project.dependencies]
# Document Loaders
pypdf2 = "^3.0.0"
pdfplumber = "^0.10.0"
openpyxl = "^3.1.0"

# Text Splitting
langchain-text-splitters = "^0.2.0"

# Vector Store
chromadb = "^0.5.0"

# Embeddings (escolher um ou mais)
openai = "^1.0.0"
azure-ai-inference = "^1.0.0"

# File Handling
python-multipart = "^0.0.9"
aiofiles = "^24.0.0"
```

---

## 🎯 Conclusão

A arquitetura proposta combina o melhor de cada plataforma:
- **CrewAI**: Conceito de Knowledge Sources + integração agent-level/crew-level
- **LangChain**: Pipeline robusto de indexação + 160+ document loaders
- **Vectorize**: API de retrieval com query rewriting + real-time updates

O diferencial do AI Platform será a **genericidade** - permitir que qualquer workflow use conhecimento como ferramenta, configurável via JSON.

---

## 🔗 Referências

1. [CrewAI Knowledge Documentation](https://docs.crewai.com/concepts/knowledge)
2. [LangChain RAG Tutorial](https://docs.langchain.com/oss/python/langchain/rag)
3. [LangChain Text Splitters](https://docs.langchain.com/oss/python/integrations/splitters/index)
4. [Vectorize Platform](https://docs.vectorize.io/)
5. [Flowise Documentation](https://docs.flowiseai.com/)
