# 🔄 Workflows Mapfre

Orquestrações multi-agente para processos de seguros.

## Workflows Disponíveis

| Workflow | Tipo | Cenário | Agentes Envolvidos |
|----------|------|---------|-------------------|
| `sinistro_auto.json` | Sequential | Pipeline de sinistro auto | Extrator → Especialista → Avaliador → Resumidor |
| `atendimento_central.json` | Handoff | Central de atendimento | Triagem → Sinistros/Cotação/Dúvidas/Ouvidoria |
| `comite_sinistro.json` | Group Chat | Comitê decisório | Técnico, Jurídico, Financeiro, Coordenador |
| `classificador_docs.json` | Router | Processamento de documentos | Classificador → Processadores especializados |
| `cotacao_completa.json` | Parallel | Análise de cotação | Risco, Perfil, Precificação |
| `sinistro_vida.json` | Sequential | Pipeline sinistro vida | Extrator → Especialista → Jurídico → Parecer |

## Tipos de Workflow

### Sequential (Sequencial)
Execução em cadeia onde cada agente processa e passa para o próximo.
```
Input → Agente1 → Agente2 → Agente3 → Output
```

### Parallel (Paralelo)
Execução simultânea de múltiplos agentes com agregação de resultados.
```
         ┌→ Agente1 ─┐
Input ─→ ├→ Agente2 ─┼→ Agregador → Output
         └→ Agente3 ─┘
```

### Handoff (Transição)
Roteamento dinâmico baseado em decisão do coordenador.
```
Input → Coordenador ─┬→ Especialista1 → Output
                     ├→ Especialista2 → Output
                     └→ Especialista3 → Output
```

### Group Chat (Discussão em Grupo)
Múltiplos agentes dialogam coordenados por um manager.
```
         ┌──────────────────────────────┐
         │         Manager              │
         │    (seleciona próximo)       │
         └──────────────────────────────┘
              ↓         ↓         ↓
         Agente1   Agente2   Agente3
              └─────────┴─────────┘
                  conversação
```

### Router (Roteador)
Classificação seguida de processamento especializado.
```
Input → Classificador → switch(output):
                          "tipo_a" → ProcessadorA → Output
                          "tipo_b" → ProcessadorB → Output
                          default  → ProcessadorC → Output
```

## Estrutura de Workflow

```json
{
  "version": "1.0",
  "name": "Nome do Workflow",
  "resources": {
    "models": {
      "gpt-4o-mini": {"type": "azure-openai", "deployment": "gpt-4o-mini"}
    },
    "tools": [...]
  },
  "agents": [...],
  "workflow": {
    "type": "sequential|parallel|handoff|group_chat|router",
    "steps": [...]
  }
}
```

## Execução

```bash
# Executar workflow
uv run python run.py exemplos/workflows/sinistro_auto.json

# Com input específico
echo "Tive um acidente na Av. Paulista..." | uv run python run.py exemplos/workflows/sinistro_auto.json

# Modo debug (verbose)
LOG_LEVEL=DEBUG uv run python run.py exemplos/workflows/comite_sinistro.json
```
