# Guia de Investigação e Limpeza de Código: AI Platform

## 🎯 Objetivo
Realizar uma auditoria profunda no repositório `ai-plataform` para identificar códigos mortos, funcionalidades duplicadas e desvios arquiteturais. O objetivo final é reduzir a complexidade do projeto, garantindo que o `src/worker` seja **100% genérico, desacoplado** e alinhado com o `agent_framework` nativo.

## 📂 Contexto e Referências
- **Repositório Alvo:** `src/` (com foco em `src/worker`)
- **Fonte da Verdade (Framework):** `C:\Users\jonperei\Desktop\Workspace\ai-plataform\.agent_framework_comparison`
  - *Nota:* Esta pasta contém o código fonte original do framework da Microsoft. Qualquer funcionalidade reimplementada no `src/` que já exista aqui é candidata à exclusão.

---

## 🕵️‍♂️ Etapas da Investigação

### 1. Análise Crítica: Engine de Prompts vs. Framework Types
**Contexto:** Existe uma implementação customizada em `src/worker/prompts/` (inspirada no LangChain) para lidar com templates e construção de mensagens.
**Ação:**
1. Compare `src/worker/prompts/messages.py` e `models.py` com `agent_framework._types` (especificamente `ChatMessage`, `TextContent`, `Role`).
2. **Verificação:** O framework nativo possui classes para estruturar mensagens?
   - *Se SIM:* A nossa implementação customizada de `MessageBuilder` é redundante? Ela apenas "envelopa" dicionários ou traz valor real?
   - *Se NÃO:* A implementação atual converte corretamente para os tipos esperados pelo framework na hora da execução?
3. **Decisão sobre Templating:** O framework possui sistema de injeção de variáveis em strings (ex: `Olá {nome}`)? Se não, o módulo de templates deve ser mantido, mas adaptado para gerar objetos do framework, não dicionários genéricos.

### 2. Varredura de Código Morto (Dead Code)
Percorra os módulos listando itens que não possuem referências de entrada (entry points) ou testes associados.
- **Imports não utilizados:** Identificar e listar.
- **Funções órfãs:** Funções definidas em `utils` ou `tools` que não são chamadas por nenhum `agent`, `workflow` ou `api`.
- **Arquivos de "Tentativa e Erro":** Identificar arquivos com nomes como `test_old.py`, `backup_*.py`, ou módulos em `mock_tools` que não são usados nos testes atuais.

### 3. Análise de Acoplamento do Worker
O `src/worker` deve ser agnóstico ao negócio.
- Procure por lógicas de negócio "hardcoded" (ex: regras específicas de fraude, strings fixas de clientes) dentro da engine de execução.
- Verifique se os `strategies` (ex: `src/worker/strategies/`) estão genéricos o suficiente ou se foram criados para um caso de uso específico e nunca mais usados.

---

## 📝 Formato do Relatório de Saída

Para cada item suspeito encontrado, classifique-o rigorosamente em uma das três categorias abaixo:

### 🔴 EXCLUIR (Delete)
*Código que deve ser removido imediatamente.*
- **Critério:** Funcionalidade 100% coberta pelo `agent_framework` nativo.
- **Critério:** Código morto (sem referências).
- **Critério:** Arquivos de teste/mock obsoletos.

### 🟡 ADAPTAR (Refactor)
*Código útil, mas implementado da forma errada.*
- **Critério:** Funcionalidade necessária (ex: Templating de Prompt), mas que retorna tipos customizados em vez de tipos do framework.
- **Ação Recomendada:** Descrever como refatorar para usar os tipos de `.agent_framework_comparison`.

### 🟢 MANTER (Keep)
*Código essencial e exclusivo.*
- **Critério:** Extensão legítima do framework (ex: um Middleware de Log específico, um conector de banco de dados customizado).
- **Justificativa:** Explicar por que o framework nativo não atende a essa necessidade.

---

## 🚀 Execução
Ao analisar, seja **imparcial**. Não tenha apego ao código legado. Se uma pasta inteira parece inútil (ex: `src/maia_ui` se não estiver sendo usada pelo frontend atual), sugira a investigação de sua remoção.

**Foco Especial:**
- `src/worker/prompts/` (Redundância com Framework?)
- `src/maia_ui/` (Está sendo usado ou foi substituído?)
- `mock_tools/` (Necessário para produção?)
