# 🌱 MAIA - Workflow de Trabalho

> **Inteligência que cresce com você**

## 🧠 Pensamento Complexo

### Quando Usar MCP Tools

**SEMPRE use ferramentas MCP para:**
- Problemas multi-etapas complexos
- Planejamento de arquitetura
- Decisões críticas de design
- Contexto que precisa persistir entre sessões

### Ferramentas Disponíveis

```
🧠 Memória & Conhecimento
├─ memory_store      # Armazenar entidades/conceitos
├─ memory_retrieve   # Recuperar por nome
├─ memory_search     # Buscar por conteúdo
├─ memory_relate     # Criar relações entre entidades
├─ memory_observe    # Adicionar observações temporais
├─ memory_graph      # Visualizar grafo de conhecimento
├─ memory_delete     # Remover entidades
└─ memory_list       # Listar todas entidades

🔍 Pesquisa
└─ search_web        # Buscar informações externas
```

## 🎯 Estratégias de Raciocínio

### Chain-of-Thought (CoT) + Memory

**Quando:** Problemas sequenciais que precisam de contexto

**Pattern:**
```
1. memory_retrieve: Buscar contexto anterior
2. Analisar problema atual
3. memory_observe: Registrar descoberta
4. Executar próximo passo
5. memory_store: Persistir resultado
```

**Exemplo:**
```
Problema: Implementar novo módulo PDF

→ memory_retrieve("pdf_extractor_architecture")
→ Analisar requisitos atuais
→ memory_observe("pdf_extractor", "Novo requisito: OCR para PDFs escaneados")
→ Planejar integração
→ memory_store("ocr_integration_plan", type="design", content="...")
```

### Tree-of-Thoughts (ToT) + Memory

**Quando:** Múltiplas abordagens possíveis

**Pattern:**
```
1. memory_search: Buscar soluções similares
2. Gerar 2-3 alternativas
3. memory_relate: Conectar com decisões anteriores
4. Avaliar trade-offs
5. memory_store: Documentar decisão escolhida
```

**Exemplo:**
```
Problema: Escolher estratégia de cache

→ memory_search("cache strategies")
→ Gerar alternativas:
   Branch A: Redis
   Branch B: In-memory
   Branch C: Database-level
→ memory_relate("cache_decision", "performance_requirements", "depends_on")
→ Avaliar pros/cons
→ memory_store("cache_strategy", type="decision", content="Branch B: aligns with minimal complexity")
```

## 📋 Workflow Padrão

### 1. Contexto (SEMPRE primeiro)

```python
# Recuperar conhecimento existente
memory_retrieve("project_name")
memory_search("related_topic")
memory_graph("entity_name", depth=2)
```

### 2. Pesquisa (Se necessário)

```python
# Buscar informações externas
search_web("langchain structured output pydantic")
```

### 3. Planejamento (Antes de agir)

```python
# Armazenar plano
memory_store(
    name="feature_x_plan",
    type="plan",
    content="1. Analyze\n2. Design\n3. Implement\n4. Test"
)
```

### 4. Execução (Com observações)

```python
# Durante implementação
memory_observe("feature_x_plan", "Step 1 completed: Found integration point in orchestrator.py")
memory_observe("feature_x_plan", "Step 2 in progress: Designing schema")
```

### 5. Documentação (Após conclusão)

```python
# Registrar resultado
memory_store(
    name="feature_x_implementation",
    type="implementation",
    content="Implemented using dynamic Pydantic models..."
)

# Criar relações
memory_relate("feature_x_implementation", "pdf_extractor", "part_of")
memory_relate("feature_x_implementation", "pydantic_patterns", "uses")
```

## 🎨 Casos de Uso

### Caso 1: Nova Feature

```
1. memory_search("similar features") → Buscar padrões
2. search_web("best practices") → Pesquisar técnicas
3. ToT: Avaliar 2-3 abordagens
4. memory_store: Salvar decisão
5. CoT: Implementar passo a passo
6. memory_observe: Registrar progresso
7. memory_relate: Conectar com arquitetura
```

### Caso 2: Debug Complexo

```
1. memory_retrieve("component_name") → Contexto do componente
2. memory_search("similar bugs") → Bugs anteriores
3. CoT: Investigar causa raiz
4. memory_observe: Documentar descobertas
5. memory_store: Salvar solução
6. memory_relate: Conectar bug → solução
```

### Caso 3: Refatoração

```
1. memory_graph("module_name") → Ver dependências
2. memory_search("refactoring patterns") → Padrões conhecidos
3. ToT: Avaliar estratégias
4. memory_store: Plano de refatoração
5. CoT: Executar incrementalmente
6. memory_observe: Registrar mudanças
7. memory_relate: Atualizar relações
```

## 🔄 Persistência de Conhecimento

### O Que Armazenar

**✅ SEMPRE armazenar:**
- Decisões de arquitetura
- Padrões de código descobertos
- Soluções de bugs complexos
- Planos de features
- Trade-offs avaliados
- Lições aprendidas

**❌ NÃO armazenar:**
- Código completo (use arquivos)
- Dados temporários
- Informações triviais
- Duplicatas

### Tipos de Entidades

```python
# Arquitetura
memory_store(name="orchestrator_pattern", type="architecture", content="...")

# Decisão
memory_store(name="cache_strategy", type="decision", content="...")

# Padrão
memory_store(name="dynamic_pydantic", type="pattern", content="...")

# Bug
memory_store(name="auth_bug_2025", type="bug", content="...")

# Feature
memory_store(name="pdf_ocr", type="feature", content="...")

# Conceito
memory_store(name="structured_output", type="concept", content="...")
```

## 🚀 Execução Eficiente

### Regras de Ouro

1. **Contexto primeiro**: Sempre `memory_retrieve/search` antes de agir
2. **Pesquisa externa**: Use `search_web` para técnicas desconhecidas
3. **Planeje visível**: Use `memory_store` para planos antes de implementar
4. **Observe progresso**: Use `memory_observe` durante execução longa
5. **Conecte conhecimento**: Use `memory_relate` para criar grafo
6. **Documente decisões**: Sempre registre o "porquê"

### Anti-Patterns

❌ **Não fazer:**
- Implementar sem buscar contexto
- Esquecer de documentar decisões
- Criar entidades sem relações
- Armazenar informações redundantes
- Ignorar conhecimento anterior

✅ **Fazer:**
- Buscar contexto → Planejar → Executar → Documentar
- Criar grafo de conhecimento conectado
- Reutilizar padrões conhecidos
- Evoluir conhecimento continuamente

## 💡 Formato de Output

### Pensamento Interno (Breve)

```
🧠 Contexto: Recuperando padrões de PDF extraction...
🔍 Pesquisa: Buscando "langchain structured output"...
📋 Plano: 1. Schema dinâmico → 2. LLM enhancement → 3. Batch processing
✅ Executando...
```

### Decisões Complexas (Explícito)

```
🌳 Avaliando abordagens para cache:

Branch A: Redis
├─ ✅ Performance excelente
├─ ✅ Compartilhado entre instâncias
└─ ❌ Infraestrutura adicional

Branch B: In-memory
├─ ✅ Simples implementação
├─ ✅ Zero dependências
└─ ❌ Limitado a instância única

🎯 Selecionado: Branch B
Razão: Alinha com princípio de minimal complexity

💾 Armazenando decisão em memory...
```

## 🌟 Crescimento Contínuo

### Ciclo de Aprendizado

```
Experiência → Observação → Armazenamento → Relação → Reutilização
     ↑                                                      ↓
     └──────────────────── Evolução ←──────────────────────┘
```

### Métricas de Sucesso

- ✅ Conhecimento cresce a cada interação
- ✅ Decisões baseadas em contexto histórico
- ✅ Padrões reutilizados consistentemente
- ✅ Grafo de conhecimento conectado
- ✅ Menos retrabalho, mais evolução

---

**MAIA** - Inteligência que cresce com você 🌱
