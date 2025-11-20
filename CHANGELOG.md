# Changelog

Todos os marcos notáveis deste projeto serão documentados neste arquivo.

## [Não lançado]

### Adicionado
- Criação inicial do `TODO.md` e `CHANGELOG.md`.
- Implementação do módulo `src.worker` com:
    - `config.py`: Modelos Pydantic e ConfigLoader.
    - `factory.py`: ToolFactory e AgentFactory.
    - `engine.py`: WorkflowEngine (suporte inicial sequencial).
- Atualização do arquivo de configuração `worker.json` para o novo schema v1.0.

### Alterado
- Finalizada Fase 1: Worker funcional com execução sequencial.
- `run_worker.py` validado com sucesso (Hello World com 2 agentes).

## [Em desenvolvimento]

### Adicionado
- Implementado suporte a workflows paralelos (`type: parallel`).
- Criado teste de integração `worker_parallel.json`.
- Implementado suporte a roteamento dinâmico (`type: router`).
- Criado teste de integração `worker_router.json`.
- Implementado suporte a Human-in-the-loop (`type: human`).
- Criado teste de integração `worker_hitl.json`.
- Implementado suporte a persistência básica (checkpoint em JSON).
- Criado teste de integração `worker_persistence.json`.
