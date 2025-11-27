import asyncio
import os
from dataclasses import dataclass
from typing import Any, List, Union, AsyncIterable
from agent_framework import BaseAgent, AgentRunResponse, ChatMessage, Executor, handler, response_handler, WorkflowContext
from pydantic import BaseModel, Field
from src.worker.strategies.confirmation import ConfirmationStrategy, CLIConfirmationStrategy, StructuredConfirmationStrategy, AutoApprovalStrategy

@dataclass
class HumanInputRequest:
    prompt: str
    instructions: str = ""

class HumanInputResponse(BaseModel):
    content: str = Field(description="Sua resposta")

class HumanAgent(Executor):
    def __init__(self, id: str, name: str = "Human", instructions: str = "", confirmation_mode: str = "cli"):
        super().__init__(id=id)
        self.name = name
        self.instructions = instructions
        self.strategy = self._get_strategy(confirmation_mode)

    def _get_strategy(self, mode: str) -> ConfirmationStrategy:
        if mode == "structured":
            return StructuredConfirmationStrategy()
        elif mode == "auto":
            return AutoApprovalStrategy()
        return CLIConfirmationStrategy()

    @handler
    async def handle_message(self, message: Any, ctx: WorkflowContext[Union[HumanInputRequest, ChatMessage]]) -> Any:
        # Extrair texto para exibir ao humano
        prompt_text = ""
        if isinstance(message, str):
            prompt_text = message
        elif isinstance(message, list) and message:
            last = message[-1]
            prompt_text = str(last.text) if hasattr(last, "text") else str(last)
        elif isinstance(message, ChatMessage):
            prompt_text = message.text
        else:
            prompt_text = str(message)
        
        # Delegar para a estratégia configurada
        return await self.strategy.request_approval(self.id, prompt_text, self.instructions)

        
        # Send request for human input (triggers HIL in DevUI)
        req = HumanInputRequest(prompt=str(prompt_text), instructions=self.instructions)
        await ctx.send_message(req)
        # Note: In HIL mode, we don't return here because the response comes via handle_response

    @response_handler
    async def handle_response(self, request: HumanInputRequest, response: HumanInputResponse, ctx: WorkflowContext[ChatMessage]) -> Any:
        print(f"👤 Resposta recebida: {response.content}")
        # Return the human response as a ChatMessage
        await ctx.send_message(ChatMessage(role="user", text=response.content))
        return response.content

    # Manter compatibilidade com BaseAgent se necessário (para testes fora do workflow engine novo)
    async def run(self, messages: Union[str, List[Any]], *, thread: Any = None, **kwargs) -> AgentRunResponse:
        # Fallback para modo console legado se chamado diretamente
        prompt_text = ""
        if isinstance(messages, str):
            prompt_text = messages
        elif isinstance(messages, list) and messages:
            last = messages[-1]
            prompt_text = str(last.content) if hasattr(last, "content") else str(last)
        
        print(f"\n👤 [Entrada Humana Necessária (Legacy)] Passo: {self.id}")
        print(f"❓ Prompt: {prompt_text}")
        
        user_response = await asyncio.to_thread(input, ">> ")
        
        return AgentRunResponse(
            messages=[ChatMessage(role="user", text=user_response)],
            value=user_response
        )
