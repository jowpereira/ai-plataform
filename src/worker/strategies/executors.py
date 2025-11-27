"""
Executors auxiliares para estratégias de workflow.

Fornece executors terminais e auxiliares para uso com WorkflowBuilder,
seguindo os padrões do Microsoft Agent Framework.

Referência:
    - Framework usa @executor decorator para funções
    - Framework usa classes Executor com @handler para lógica complexa
    - Padrão: ctx.send_message() para próximo nó, ctx.yield_output() para terminal
"""

from typing import Any
from typing_extensions import Never

from agent_framework import (
    WorkflowContext,
    executor,
    AgentExecutorResponse,
)


@executor(id="workflow_output")
async def yield_agent_response(
    response: AgentExecutorResponse, 
    ctx: WorkflowContext[Never, str]
) -> None:
    """
    Executor terminal padrão do framework.
    
    Captura a resposta de um AgentExecutor e emite como saída do workflow.
    Usa o decorator @executor do framework (padrão oficial).
    
    Padrão Microsoft Agent Framework:
    - Executors terminais devem chamar `ctx.yield_output()` para finalizar o caminho
    - Isso evita o warning de "dropping messages" para executors sem edges de saída
    """
    output_text = response.agent_run_response.text or ""
    await ctx.yield_output(output_text)


@executor(id="passthrough_output")
async def yield_string_output(
    text: str, 
    ctx: WorkflowContext[Never, str]
) -> None:
    """
    Executor terminal para strings diretas.
    
    Útil quando o upstream envia string ao invés de AgentExecutorResponse.
    """
    await ctx.yield_output(text)


@executor(id="any_to_output")
async def yield_any_output(
    data: Any, 
    ctx: WorkflowContext[Never, str]
) -> None:
    """
    Executor terminal genérico.
    
    Converte qualquer tipo de dados para string e emite como saída.
    """
    if hasattr(data, 'text'):
        output = data.text
    elif hasattr(data, 'agent_run_response'):
        output = data.agent_run_response.text
    else:
        output = str(data)
    
    await ctx.yield_output(output)


# Alias para compatibilidade com código existente
# DEPRECATED: Usar yield_agent_response diretamente
class OutputExecutor:
    """
    DEPRECATED: Use yield_agent_response function executor.
    
    Esta classe existe apenas para compatibilidade.
    O framework prefere o decorator @executor.
    """
    
    def __init__(self, id: str = "output"):
        import warnings
        warnings.warn(
            "OutputExecutor class is deprecated. Use yield_agent_response executor instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Retorna o executor funcional
        self._executor = yield_agent_response
    
    def __getattr__(self, name):
        return getattr(self._executor, name)

