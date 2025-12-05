# 🛡️ Demonstração AI Platform - Mapfre Seguros

Esta pasta contém exemplos práticos de agentes e workflows de IA desenvolvidos especificamente para demonstrar as capacidades da plataforma para a **Mapfre Seguros**.

---

## 📁 Estrutura

```
exemplos/
├── agentes/           # Agentes individuais especializados
│   ├── README.md      # Documentação dos agentes
│   └── *.json         # Definições de agentes
├── workflows/         # Orquestrações multi-agente
│   ├── README.md      # Documentação dos workflows
│   └── *.json         # Definições de workflows
└── README.md          # Este arquivo
```

---

## 🎯 Casos de Uso Demonstrados

### 1. **Abertura de Sinistro Inteligente** (Sequential)
Pipeline completo de processamento de sinistros com extração de dados, análise de risco e geração de parecer automático.

### 2. **Central de Atendimento Omnichannel** (Handoff)
Triagem inteligente que direciona clientes para o especialista correto: sinistros, cotações, dúvidas ou ouvidoria.

### 3. **Comitê de Aprovação de Sinistros** (Group Chat)
Simulação de comitê decisório com múltiplos especialistas: técnico, jurídico, financeiro e coordenador.

### 4. **Classificador de Documentos** (Router)
Processamento automático de documentos recebidos: apólices, avisos de sinistro, procurações, laudos médicos.

### 5. **Análise de Cotação Multi-Dimensional** (Parallel)
Avaliação simultânea de risco técnico, perfil do cliente e precificação para seguros complexos.

### 6. **Assistente Virtual Mapfre** (Standalone Agent com RAG)
Agente de autoatendimento com acesso à base de conhecimento da seguradora.

---

## 🚀 Como Executar

### Via CLI
```bash
# Executar um workflow
uv run python run.py exemplos/workflows/sinistro_auto.json

# Executar um agente standalone
uv run python run.py exemplos/agentes/assistente_mapfre.json
```

### Via Interface Web
```bash
# Iniciar o servidor (em desenvolvimento)
uv run python -m src.maia_ui

# Acessar: http://localhost:8000
# Navegar até a aba "Debug" e carregar o workflow desejado
```

---

## 💡 Benefícios para a Mapfre

| Benefício | Descrição |
|-----------|-----------|
| ⚡ **Velocidade** | Processamento de sinistros em segundos vs. horas |
| 🎯 **Precisão** | IA treinada com regras de negócio Mapfre |
| 💰 **Economia** | Redução de custos operacionais com automação |
| 🔍 **Auditabilidade** | Logs completos de cada decisão da IA |
| 🔗 **Integração** | Conecta com sistemas legados via APIs |
| 📊 **Escalabilidade** | Processa milhares de casos simultaneamente |

---

## 🛠️ Tecnologia

- **Microsoft Agent Framework** - Motor de orquestração de agentes
- **Azure OpenAI** - Modelos de linguagem (GPT-4o-mini, embeddings)
- **RAG** - Retrieval Augmented Generation para base de conhecimento
- **Python/Async** - Performance e escalabilidade

---

## 📞 Contato

Para dúvidas sobre a demonstração, entre em contato com a equipe de inovação.
