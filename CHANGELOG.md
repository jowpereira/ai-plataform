# Changelog

Todos os marcos notáveis deste projeto serão documentados neste arquivo.

## [0.3.0] - 2025-11-21

### Adicionado

- **MAIA (Microsoft Agent Interface for Arnaldo):** Integração completa da interface de desenvolvimento (antiga DevUI).
  - Interface gráfica para visualização e teste de agentes e workflows.
  - Rebranding completo de "DevUI" para "MAIA".
  - Execução via `python run.py --ui`.
  - Build do frontend React integrado ao projeto.
- Suporte a carregamento automático de exemplos na interface.

### Alterado

- Atualização do `run.py` para suportar a flag `--ui` e servir a aplicação web.

## [0.2.0] - 2025-11-20

### Adicionado
- Suporte completo a **Group Chat** (`type: group_chat`) com gerenciador automático.
- Suporte a **Handoff** (`type: handoff`) para transições explícitas entre agentes.
- Diretório `exemplos/` centralizando todos os casos de uso (Sequencial, Paralelo, Router, Group Chat, Handoff, Humano).
- Diretório `ferramentas/` para centralizar funções Python usadas pelos agentes.
- Script `run.py` (antigo `executar.py`) como ponto único de entrada via CLI.

### Alterado
- **Refatoração Maior:** Limpeza da estrutura do projeto.
    - Removido diretório `scripts/` e testes antigos.
    - Renomeado `executar.py` para `run.py`.
    - Padronização dos nomes dos arquivos JSON em `exemplos/`.
- Atualização da documentação (`README.md` e `exemplos/README.md`).

## [0.1.0] - 2025-11-19

### Adicionado
- Implementado suporte a workflows paralelos (`type: parallel`).
- Implementado suporte a roteamento dinâmico (`type: router`).
- Implementado suporte a Human-in-the-loop (`type: human`).
- Estrutura base do Worker (`src/worker`).

### Alterado
- Finalizada Fase 1: Worker funcional com execução sequencial.

## [Início]

### Adicionado
- Criação inicial do `TODO.md` e `CHANGELOG.md`.
- Implementação do módulo `src.worker` com:
    - `config.py`: Modelos Pydantic e ConfigLoader.
    - `factory.py`: ToolFactory e AgentFactory.
    - `engine.py`: WorkflowEngine (suporte inicial sequencial).
