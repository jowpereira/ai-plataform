# 🤖 Agentes Mapfre

Agentes especializados para operações de seguros.

## Agentes Disponíveis

| Agente | Função | Ferramentas | Uso Principal |
|--------|--------|-------------|---------------|
| `analista_sinistro.json` | Analista de Sinistros | - | Análise técnica de sinistros |
| `extrator_documentos.json` | Extrator de Dados | - | OCR e extração estruturada |
| `avaliador_risco.json` | Avaliador de Risco | `calcular_risco` | Scoring de risco |
| `especialista_auto.json` | Especialista Auto | - | Sinistros de veículos |
| `especialista_vida.json` | Especialista Vida/Saúde | - | Sinistros vida e saúde |
| `especialista_patrimonial.json` | Especialista Patrimônio | - | Sinistros residenciais |
| `consultor_juridico.json` | Consultor Jurídico | - | Compliance e legal |
| `atendente_triagem.json` | Atendente Triagem | - | Primeiro atendimento |
| `cotador_seguro.json` | Cotador de Seguros | `calcular_premio` | Cotações e simulações |
| `assistente_mapfre.json` | Assistente Virtual | RAG | Autoatendimento |
| `coordenador_sinistro.json` | Coordenador | - | Gestão de comitês |

## Estrutura Padrão

```json
{
  "id": "identificador_unico",
  "role": "Nome do Papel",
  "description": "Descrição para orquestração",
  "model": "gpt-4o-mini",
  "instructions": "Instruções detalhadas do agente...",
  "tools": ["ferramenta_1", "ferramenta_2"],
  "knowledge": {
    "enabled": true,
    "collection_ids": ["base_mapfre"],
    "top_k": 5
  }
}
```

## Modelos Utilizados

- **gpt-4o-mini**: Análises rápidas e custo otimizado
- **gpt-4o**: Decisões complexas e análise jurídica
- **text-embedding-ada-002**: Busca semântica na base de conhecimento
