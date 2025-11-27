from typing import Callable, Awaitable, List, Any
from agent_framework import AgentMiddleware, AgentRunContext, ChatMessage

class MessageSanitizerMiddleware(AgentMiddleware):
    """
    Middleware para garantir a higiene das mensagens enviadas ao modelo.
    Corrige sequências inválidas de tool_calls e tool_outputs.
    """
    
    async def process(self, context: AgentRunContext, next: Callable[[AgentRunContext], Awaitable[None]]) -> None:
        if hasattr(context, "messages") and isinstance(context.messages, list):
            context.messages = self._sanitize(context.messages)
        await next(context)

    def _sanitize(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Sanitiza a lista de mensagens.
        
        Regras aplicadas:
        1. Remove mensagens nulas/vazias.
        2. (Futuro) Garante paridade de FunctionCall/FunctionResult.
        3. (Futuro) Reordena mensagens se necessário.
        """
        sanitized: List[ChatMessage] = []
        
        for msg in messages:
            if not msg:
                continue
            sanitized.append(msg)
            
        return sanitized
