from typing import Any, Callable, Awaitable
from agent_framework import AgentMiddleware, AgentRunContext, ChatMessage

class EventMiddleware(AgentMiddleware):
    """Middleware para emitir eventos de execução do agente."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        
    async def process(self, context: AgentRunContext, next: Callable[[AgentRunContext], Awaitable[None]]) -> None:
        from src.worker.events import get_event_bus, WorkerEventType
        bus = get_event_bus()
        
        # Emitir evento de início
        bus.emit_simple(
            WorkerEventType.AGENT_START, 
            {"agent_name": self.agent_name}
        )
        
        try:
            await next(context)
            
            # Tentar capturar resultado se disponível no context
            # Nota: Depende da implementação do AgentRunContext no framework
            result = getattr(context, "result", None)
            content = "Completed"
            
            if result:
                if hasattr(result, "text"):
                    content = result.text
                elif hasattr(result, "content"):
                    content = result.content
                else:
                    content = str(result)
            
            bus.emit_simple(
                WorkerEventType.AGENT_RESPONSE, 
                {"agent_name": self.agent_name, "content": content}
            )
            
        except Exception as e:
            bus.emit_simple(
                WorkerEventType.WORKFLOW_ERROR,
                {"agent_name": self.agent_name, "error": str(e)}
            )
            raise e


class EnhancedTemplateMiddleware(AgentMiddleware):
    def __init__(self, template: str):
        self.template = template

    async def process(self, context: AgentRunContext, next: Callable[[AgentRunContext], Awaitable[None]]) -> None:
        messages = context.messages
        last_content = ""
        
        # Extrair conteúdo da última mensagem
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "text"):
                last_content = str(last_msg.text)
            elif isinstance(last_msg, dict) and "content" in last_msg:
                last_content = str(last_msg["content"])
            else:
                last_content = str(last_msg)
        elif isinstance(messages, str):
            last_content = messages
            
        # Aplicar template PRESERVANDO o input original
        if "{{user_input}}" in self.template:
            new_content = self.template.replace("{{user_input}}", last_content)
        elif "{{previous_output}}" in self.template:
            new_content = self.template.replace("{{previous_output}}", last_content)
        else:
            # Se não tem placeholders, adiciona o template como contexto
            new_content = f"{self.template}\n\nInput do usuário: {last_content}"
        
        # Atualizar mensagem preservando role
        if isinstance(messages, list) and messages:
            last_msg = messages[-1]
            if isinstance(last_msg, ChatMessage):
                new_msg = ChatMessage(role=last_msg.role, text=new_content)
                messages[-1] = new_msg
            elif isinstance(last_msg, dict):
                last_msg["content"] = new_content
            else:
                messages[-1] = new_content

        await next(context)
