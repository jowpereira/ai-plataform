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


