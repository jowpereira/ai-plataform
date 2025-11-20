import asyncio
from typing import Any, List, Union, AsyncIterable
from agent_framework import BaseAgent, AgentRunResponse, ChatMessage

class HumanAgent(BaseAgent):
    def __init__(self, id: str, name: str = "Human", instructions: str = ""):
        super().__init__(id=id, name=name, description=instructions)
        self.instructions = instructions

    async def run(self, messages: Union[str, List[Any]], *, thread: Any = None, **kwargs) -> AgentRunResponse:
        # Extrair texto para exibir ao humano
        prompt_text = ""
        if isinstance(messages, str):
            prompt_text = messages
        elif isinstance(messages, list) and messages:
            last = messages[-1]
            prompt_text = str(last.content) if hasattr(last, "content") else str(last)
        
        print(f"\n👤 [Entrada Humana Necessária] Passo: {self.id}")
        print(f"❓ Prompt: {prompt_text}")
        if self.instructions:
            print(f"ℹ️ Instruções: {self.instructions}")
            
        user_response = await asyncio.to_thread(input, ">> ")
        
        # Retornar resposta no formato esperado pelo framework
        # O framework espera uma lista de mensagens ou um valor.
        return AgentRunResponse(
            messages=[ChatMessage(role="user", content=user_response)],
            value=user_response
        )

    async def run_stream(self, messages: Union[str, List[Any]], *, thread: Any = None, **kwargs) -> AsyncIterable[Any]:
        """Implementação de streaming para compatibilidade com AgentProtocol."""
        response = await self.run(messages, thread=thread, **kwargs)
        yield response
