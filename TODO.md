# Roadmap de Desenvolvimento - Worker Genérico AI Platform

Este documento rastrea o progresso detalhado do desenvolvimento do módulo worker genérico.

## Fase 1: Fundamentos e Estrutura (MVP)
- [ ] **Setup Inicial**
    - [ ] Criar estrutura de diretórios `src/worker`.
    - [ ] Criar `CHANGELOG.md` para registro de marcos.
- [ ] **Modelagem de Configuração (`src/worker/config.py`)**
    - [ ] Definir modelo `ToolConfig` (id, path).
    - [ ] Definir modelo `ModelConfig` (type, deployment, env vars).
    - [ ] Definir modelo `AgentConfig` (role, instructions, tools, model).
    - [ ] Definir modelo `WorkflowStep` (id, agent, input_template, next).
    - [ ] Definir modelo `WorkerConfig` (root).
    - [ ] Implementar `ConfigLoader` com suporte a resolução de variáveis de ambiente (`${VAR}`).
- [ ] **Fábrica de Componentes (`src/worker/factory.py`)**
    - [ ] Implementar `ToolFactory` para importação dinâmica (`importlib`).
    - [ ] Implementar `AgentFactory` para instanciar `ChatAgent` do framework.
    - [ ] Implementar suporte a `OpenAIChatClient` e `AzureOpenAIChatClient`.
- [ ] **Motor de Execução (`src/worker/engine.py`)**
    - [ ] Criar classe `WorkflowEngine`.
    - [ ] Implementar construção de workflow sequencial básico.
    - [ ] Implementar método `run`.
- [ ] **Refatoração e Teste**
    - [ ] Migrar `scripts/worker_test/config/worker.json` para o novo schema.
    - [ ] Atualizar `scripts/worker_test/run_worker.py` para usar o novo módulo `src.worker`.
    - [ ] Validar execução ponta a ponta (Hello World).

## Fase 2: Workflows Avançados
- [ ] **Suporte a Paralelismo**
    - [ ] Adicionar tipo `parallel` no schema de workflow.
    - [ ] Implementar construção de branches paralelos no `WorkflowEngine`.
- [ ] **Roteamento Dinâmico**
    - [ ] Adicionar tipo `router` no schema.
    - [ ] Implementar lógica de decisão baseada em output de agente.

## Fase 3: Human-in-the-loop e Persistência
- [ ] **Interação Humana**
    - [ ] Adicionar step type `human_approval`.
    - [ ] Implementar mecanismo de callback para input externo.
- [ ] **Persistência**
    - [ ] Integrar mecanismo de checkpoint do framework (se disponível) ou customizado.

## Fase 4: Robustez e Observabilidade
- [ ] **Tratamento de Erros**
    - [ ] Adicionar políticas de Retry na configuração.
    - [ ] Implementar Global Exception Handler.
- [ ] **Telemetria**
    - [ ] Estruturar logs em JSON.
    - [ ] Adicionar tracing básico.
