# 🌱 MAIA - Padrões Técnicos

> **MAIA - Inteligência que cresce com você**  
> Hub de IA para agentes e workflows empresariais

## 🎯 Identidade

- **Nome**: MAIA (não "AI Hub" ou "Sistema")
- **Tom**: Feminino, acolhedor, inteligente, evolutivo
- **Emoji**: 🌱 (crescimento e potencial)
- **Cores**: 🟢 Verde MAPFRE (#00A651) + 🔵 Azul Tech (#0066CC)

### Comunicação
- ✅ "Ops! Encontrei um problema aqui..."
- ✅ "Vamos tentar de outra forma?"
- ❌ "Erro fatal no sistema"
- ❌ "Operação não permitida"

## 🏗️ Arquitetura

### Princípios Core
- **Config-driven**: NUNCA hardcode projetos ou ferramentas
- **Binding explícito**: Ferramentas vinculadas via project_tools.json
- **Desacoplamento**: Orchestrator → Worker → Template
- **Evolutivo**: Sistema aprende e se adapta

### Estrutura de Código
```
src/
├── config/*.json          # Configurações dinâmicas
├── core/                  # Orchestrator, Factory, Auth
├── governance/            # RBAC, Audit, Binding
├── workers/               # Processamento desacoplado
├── projects/templates/    # UI dos projetos
└── modules/               # Módulos especializados
```

## 🔐 Segurança & Governança

### RBAC
- Sempre validar permissões antes de executar ferramentas
- Roles: ADMIN, GROUP_ADMIN, USER
- Permissions: WEB_SEARCH, CODE_EXECUTION, API_ACCESS, FILE_ACCESS

### Auditoria
- Registrar todas operações em audit.json
- Nunca expor credenciais em logs
- Incluir contexto: usuário, projeto, ferramenta, timestamp

## 💡 Boas Práticas

### Desenvolvimento
- **Minimal code**: Evitar implementações verbosas
- **Hot reload**: Usar `orchestrator.reload()` após mudanças
- **Debug**: Configurar via .env (DEBUG_ENABLED, DEBUG_LEVEL)
- **Schemas dinâmicos**: Usar Pydantic `create_model()` para runtime

### Técnicas Avançadas
- **Structured Output**: LangChain `with_structured_output()` para garantir schemas
- **LLM Enhancement**: Melhorar descrições de usuário com IA
- **Batch Processing**: ThreadPoolExecutor para paralelização
- **Dynamic Models**: Pydantic models criados em runtime

### Logs & Mensagens
```python
# ✅ Estilo MAIA
logger.info("🌱 MAIA iniciando... 18 ferramentas descobertas")
logger.info("✨ Pronta para ajudar!")
logger.error("😅 Ops! Algo não saiu como esperado")
```

## 🎨 UI/UX

### Princípios
- **Simplicidade**: Interface clara e intuitiva
- **Feedback**: Sempre informar o que está acontecendo
- **Empatia**: Mensagens acolhedoras em erros
- **Celebração**: Reconhecer sucessos

### Componentes
- Usar emojis com moderação (🌱 ✨ 💚 ✅ 🔍)
- Sidebar para configurações
- Tabs para múltiplas funcionalidades
- Progress bars para operações longas

## 📦 Módulos Especializados

### PDF Extractor
- Schema dinâmico definido em runtime
- LLM enhancement de descrições
- Structured output com Pydantic
- Batch processing paralelo

### Contrato Comparator
- Análise comparativa de documentos
- Extração de cláusulas
- Identificação de divergências

## 🚀 Deployment

### Configuração
1. Definir projeto em `src/config/projects.json`
2. Vincular ferramentas em `src/config/project_tools.json`
3. Criar template em `src/projects/templates/`
4. Testar com usuário do grupo
5. Promover para production

### Stages
- **development**: Testes iniciais
- **staging**: Validação com usuários
- **production**: Uso geral

## 🧠 Workflow & Raciocínio

**Para instruções de trabalho e uso de ferramentas MCP:**
- `reasoning.md` - Estratégias CoT e ToT
- `maia-workflow.md` - Uso de memory e search tools

## 🌟 Valores MAIA

1. **Crescimento contínuo**: Sistema evolui com uso
2. **Adaptabilidade**: Flexível às necessidades
3. **Confiabilidade**: Seguro e auditável
4. **Simplicidade**: Complexidade técnica, uso simples

---

**MAIA** - Inteligência que cresce com você 🌱