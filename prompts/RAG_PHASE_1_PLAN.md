# Plano de Implementação RAG - Fase 1: Stub In-Memory & Azure OpenAI

## Contexto
Estamos implementando o suporte a RAG (Retrieval Augmented Generation) no backend (`src/worker`). O objetivo final continua sendo o **Azure AI Search** com o `AzureAISearchContextProvider`, cujo comportamento está descrito no repositório oficial (`python/packages/azure-ai-search/_search_provider.py`, métodos `invoking` e `_semantic_search`, linhas 474-756). Para acelerar desenvolvimento e validar integrações com o Microsoft Agent Framework, esta Fase 1 entrega uma versão **In-Memory** consistente com os contratos descritos em `Context Provider Examples` (`python/samples/getting_started/context_providers/README.md`). Todas as configurações de RAG devem seguir o mesmo fluxo declarativo já utilizado para ferramentas (persistido em storage e exposto via UI), evitando variáveis de ambiente específicas.

## Objetivos
- Criar infraestrutura base de RAG desacoplada, permitindo a troca futura do armazenamento (Store) sem alterar a lógica de consumo (Agents/Tools).
- Reutilizar ao máximo o padrão de `ContextProvider` para que a migração para `AzureAISearchContextProvider` seja meramente uma troca de implementação.
- Garantir que todo o pipeline (config → embeddings → store → context → ferramenta) funcione com **Azure OpenAI** para embeddings, conforme previsto pela documentação do agente (`Azure OpenAI resource URL` exigida em agentic mode, README Azure AI Search linhas 46-78).

## Referências de Documentação
- `python/packages/azure-ai-search/agent_framework_azure_ai_search/_search_provider.py`: comportamento esperado do provider (auto-descoberta de campos vetoriais, `Context messages`, limpeza de clientes async).
- `python/samples/getting_started/context_providers/README.md`: tabela de escolha de providers e estrutura básica para providers customizados (Simple/Custom vs Azure AI Search).
- `dotnet/src/Microsoft.Agents.AI/Data/TextSearchProvider.cs`: exemplo de provider custom que injeta contexto antes do invoke (útil para entender as expectativas de `InvokingAsync`).

## Requisitos Técnicos

### 1. Configuração (`src/worker/config.py` + storage declarativo)
Atualizar `Settings` (pydantic) ou criar um `RagConfig` embutido, porém **sem** depender de variáveis de ambiente. O `RagConfig` deve ser persistido exatamente como fazemos com ferramentas hoje (ex.: registro declarativo utilizado por `ferramentas/registry.py`, bancos ou arquivos de configuração versionados). A API do backend expõe operações CRUD para o Admin UI popular/atualizar esses dados.

Campos previstos (armazenados no banco/config compartilhada):
- `enabled`: bool (default `False`).
- `provider`: `"memory" | "azure_search"` (default `memory`).
- `top_k`: int (default `4`) para consistência com `top_k` do provider oficial.
- `min_score`: float opcional (`0.25` default) para filter.
- `embedding`: objeto com `deployment`, `api_version`, `dimensions` e `normalize`.

Secrets sensíveis (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`) já existem no cofre global do app e **não** serão copiados para o `RagConfig`; apenas referenciamos o alias/nome do recurso. O backend carrega o `RagConfig` por tenant/projeto atualmente carregado, semelhante ao que fazemos para toolchains.

### 2. Interfaces Base (`src/worker/rag/interfaces.py`)
Definir classes abstratas (ABC) seguindo `typing.Protocol` ou `abc.ABC` para garantir testabilidade:
- **`EmbeddingProvider`**:
    - `async embed_query(text: str) -> list[float]`.
    - `async embed_documents(texts: Sequence[str]) -> list[list[float]]`.
- **`VectorStore`**:
    - `async add_documents(documents: Sequence[VectorDocument]) -> None`.
    - `async similarity_search(query: list[float], *, top_k: int, score_threshold: float | None = None) -> list[VectorMatch]`.
    - `async clear(namespace: str | None = None) -> None`.
    - Utilizar `@dataclass` ou `pydantic.BaseModel` para `VectorDocument` (id, text, metadata, embedding opcional) e `VectorMatch` (content, score, metadata).
- **`ContextProvider`**: interface fina (provavelmente basta reexportar `ContextProvider` oficial e documentar o contrato `async invoking(...) -> Context`).

### 3. Implementação de Embeddings (`src/worker/rag/embeddings/azure.py`)
Implementar `AzureOpenAIEmbeddings` herdando de `EmbeddingProvider`.
- Usar cliente `AsyncAzureOpenAI` já empregado pelo restante da plataforma (ou instanciar um dedicado com `azure-openai` SDK caso necessário, garantindo reuse de `AZURE_OPENAI_ENDPOINT/API_KEY`).
- Implementar retries exponenciais e mapear exceções (`APIRateLimitError`, `ServiceUnavailableError`) para erros internos claros.
- Configurar deployment e api version vindos do `RagConfig`.
- Retornar embeddings normalizados para estabilidade da similaridade.

### 4. Implementação do Store (`src/worker/rag/stores/memory.py`)
Implementar `InMemoryVectorStore` herdando de `VectorStore`.
- Estrutura interna: `defaultdict[list[VectorDocument]]` para suportar namespaces (útil para múltiplos agentes/workspaces).
- Similaridade: cosine manual (sem depender de NumPy) para manter footprint baixo; normalizar embeddings ao inserir para otimizar.
- Suporte a filtros simples por metadata (`metadata.get("tags")` etc.).
- Métodos auxiliares para carregar lotes iniciais (útil para testes) e exportar estado (para comparar futuramente com Azure Search).

### 5. Context Provider (`src/worker/rag/context.py`)
Criar `RAGContextProvider` inspirado no fluxo de `AzureAISearchContextProvider.invoking`:
- Recebe `messages` e filtra apenas `USER/ASSISTANT` com texto, exatamente como o provider oficial faz (linhas 474-514).
- Concatena texto recente ou utiliza apenas a última pergunta dependendo de `RagConfig.strategy` (por enquanto, foco em última pergunta).
- Gera embedding com `EmbeddingProvider`, realiza `similarity_search` no Store e formata resultado em múltiplos `ChatMessage` (`context_prompt + trechos`), replicando o formato do provider oficial para facilitar a troca por Azure Search depois.
- Garantir que o provider seja `async context manager` (mesma assinatura `__aenter__/__aexit__`).

### 6. Ferramenta (`ferramentas/rag_tools.py`)
Criar ferramenta `search_knowledge_base` registrada no `registry.py`.
- Input schema Pydantic (`SearchKnowledgeBaseInput` com `query: constr(min_length=3)`).
- Output contendo lista de trechos + score, permitindo que agentes decidam citar fonte.
- Internamente, reutilizar o mesmo provider para evitar duplicidade de consulta.

## Estrutura de Arquivos Proposta
```
src/worker/rag/
├── __init__.py               # Factory e helpers
├── interfaces.py             # ABCs e modelos
├── context.py                # Provider compatível com agent-framework
├── embeddings/
│   ├── __init__.py
│   └── azure.py              # Azure OpenAI embeddings
└── stores/
        ├── __init__.py
        └── memory.py             # Vector store in-memory
```

## Fluxo Operacional
1. **Config Loader**: `get_settings()` lê `.env`, popula `RagConfig` e injeta dependências via `worker.factory`.
2. **Document Loader (futuro)**: scripts ou ferramentas adicionam documentos ao `VectorStore` (Fase 1 pode ter um seed em memória carregado no boot).
3. **Consulta**: `RAGContextProvider.invoking` recebe mensagens, chama `EmbeddingProvider`, consulta `VectorStore`, formata contexto e retorna `Context` para o modelo, como descrito no provider oficial.
4. **Ferramenta opcional**: agentes podem chamar `search_knowledge_base` manualmente (similar ao `TextSearchProvider` .NET, que expõe função de busca quando `SearchBehavior = OnDemand`).

## Nuances & Atenção
- **Assincronismo:** Todo o I/O (OpenAI, store) deve ser `async` para obedecer ao contrato do `ContextProvider` oficial.
- **Tipagem:** Usar `pydantic`/`typing` estrito para refletir contratos e facilitar futura serialização (`serialize()` do provider, se necessário).
- **Factory:** `src/worker/rag/__init__.py` expõe `get_rag_provider(settings: Settings) -> ContextProvider | None`, permitindo fallback para `None` caso `RAG_ENABLED=False`.
- **Observabilidade:** Adicionar logs estruturados (nível DEBUG) ao provider (tempo de embedding, tempo de busca, `top_k`, `score_avg`).
- **Testabilidade:** `InMemoryVectorStore` deve permitir carga inicial via parâmetro/arquivo JSON para facilitar testes automatizados.

## Estratégia de Testes (Backend)
- **Unitários**: validar cosine similarity, ordenação por score e corte por threshold.
- **Contract tests**: garantir que `RAGContextProvider.invoking` retorna `Context` com mensagens no formato `[context_prompt, chunk1, chunk2...]` tal qual `AzureAISearchContextProvider`.
- **Integração**: mock de `AsyncAzureOpenAI` para validar fluxos sem bater na API real.

## Próximos Passos (Fase 2)
- Substituir `InMemoryVectorStore` por `AzureAISearchContextProvider` oficial, respeitando parâmetros `mode="semantic"` ou `"agentic"` e reutilizando embeddings ou vectorizer server-side.
- Sincronizar documentos via pipelines (Azure AI Search indexer ou ingestão manual) para garantir paridade entre stub e produção.

## Plano UI/UX Frontend (Fase 1)

### Objetivos
- Permitir que usuários carreguem (upload) suas bases de conhecimento, acompanhem o status de indexação local e associem esses índices aos agentes existentes.
- Oferecer UX semelhante ao fluxo atual de ferramentas (cards/listas gerenciáveis), garantindo familiaridade e governança.

### Fluxo Principal
1. **Knowledge Base Hub** (`/platform/knowledge-bases`): página derivada de `PlatformLayout` exibindo cards/list com bases criadas. Cada base possui status (`draft`, `indexing`, `ready`), contagem de documentos e data de atualização.
2. **Wizard de Criação**:
     - **Passo 1 – Metadados**: nome, descrição, tags e seleção do tipo de ingestão (upload manual, link, API futura).
     - **Passo 2 – Upload**: componente `Dropzone` (semelhante ao usado para assets) permitindo múltiplos arquivos; mostrar progresso e validar formatos (`pdf`, `docx`, `txt`, `json`).
     - **Passo 3 – Configuração de Index**: parâmetros `top_k`, `min_score`, estratégia de chunking (pré-config para stub). Campos avançados ficam em acordeão.
     - **Passo 4 – Revisão & Criar**: resumo antes de disparar ingestão.
3. **Monitoramento de Ingestão**: modal lateral (drawer) mostrando logs/erros por documento, estados de fila e tempo estimado. Atualização via SSE/WebSocket para feedback em tempo real.

### Associação a Agentes
- Expandir a página de edição de agentes (`/platform/agents/:id`) adicionando seção “Conhecimento” no mesmo bloco onde selecionamos ferramentas.
- UI proposta: multiselect de bases disponíveis + indicador de compatibilidade (ex.: “somente bases ready podem ser associadas”).
- Cada associação pode ter overrides (`top_k`, `context_prompt`) por agente; UI exibe “Configuração avançada” em modal.

### Componentização
- Criar `KnowledgeBaseCard`, `KnowledgeBaseForm`, `UploadListItem` em `frontend/src/components`. Reaproveitar `mode-toggle` e estilos existentes.
- Hooks: `useKnowledgeBases` (CRUD via API), `useRagUploads` (status via polling/SSE), `useAgentKnowledge` (manage bindings).
- Store (Zustand ou equivalente) para manter estado local e permitir otimizações otimistas.

### API & Integração
- Endpoints REST/GraphQL:
    - `GET /rag/bases`, `POST /rag/bases`, `PATCH /rag/bases/:id`, `DELETE`.
    - `POST /rag/bases/:id/uploads` para arquivos com suporte multipart.
    - `POST /agents/:id/rag-bindings` para associar bases (payload com overrides).
- UI deve refletir erros de validação vindos do backend e permitir reprocessar documentos específicos.

### Observabilidade & UX Detalhes
- Barra de progresso global indicando quantos documentos ainda faltam indexar.
- Empty states com CTA (“Nenhuma base cadastrada” → botão “Criar base”).
- Alertas toast com status (sucesso, falha, warnings de conversão).
- Documentação inline (tooltip) explicando diferença entre stub local e futuro Azure Search.

### Roadmap Frontend (Fase 2)
1. Habilitar visualização de métricas (tokens consumidos, latência de busca).
2. Suporte a múltiplos workspaces/tenants com RBAC.
3. Tela de diagnóstico para comparar respostas com e sem contexto (A/B) aproveitando o RAG provider.

---
**Ação:** Gere o código para implementar esta arquitetura, começando pelas interfaces e configurações, seguido pelas implementações concretas.
